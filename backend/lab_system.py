import json
import logging
import hashlib
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from datetime import datetime
from openai import Client

logger = logging.getLogger(__name__)

class LabSystem:
    """
    Enhanced laboratory system for managing test orders, validation, and result generation.
    Provides structured lab results with appropriate reference ranges and abnormal flagging.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        self.results_cache = {}  # Cache to store generated results
        self.test_history = {}   # Track results over time
        self.standard_test_groups = self._define_test_groups()
        
    def _define_test_groups(self) -> Dict[str, List[str]]:
        """
        Define standard test groupings/panels.
        """
        return {
            "CBC": ["WBC", "RBC", "Hemoglobin", "Hematocrit", "Platelets", "MCV", "MCH", "MCHC"],
            "BMP": ["Sodium", "Potassium", "Chloride", "CO2", "BUN", "Creatinine", "Glucose", "Calcium"],
            "CMP": ["Sodium", "Potassium", "Chloride", "CO2", "BUN", "Creatinine", "Glucose", "Calcium", 
                   "Total Protein", "Albumin", "AST", "ALT", "Alkaline Phosphatase", "Bilirubin"],
            "Cardiac Enzymes": ["Troponin I", "Troponin T", "CK-MB", "BNP"],
            "Coagulation": ["PT", "INR", "PTT"],
            "Lipid Panel": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
            "Liver Function": ["AST", "ALT", "Alkaline Phosphatase", "Bilirubin", "Albumin", "Total Protein"],
            "Thyroid": ["TSH", "Free T4", "Free T3"],
            "ABG": ["pH", "pO2", "pCO2", "HCO3", "O2 Saturation", "Base Excess"]
        }
    
    def validate_test_order(self, tests: List[str], ordered_tests: Set[str], 
                           ordered_imaging: Set[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates if a test can be ordered based on clinical requirements.
        
        Args:
            tests: List of tests being ordered
            ordered_tests: Set of tests already ordered
            ordered_imaging: Set of imaging studies already ordered
            
        Returns:
            Tuple containing (is_valid, error_message)
        """
        # Define test prerequisites and restrictions
        prerequisite_rules = {
            "ABG": {"required": ["CXR"], "message": "Arterial blood gas typically requires a chest X-ray first"},
            "Troponin": {"required": ["ECG"], "message": "Cardiac enzymes should be ordered with an ECG"},
            "D-dimer": {"required": ["CBC"], "message": "D-dimer should be ordered with a CBC"},
            "BNP": {"required": ["ECG"], "message": "BNP should be ordered with an ECG"},
            "Lactate": {"required": ["Vitals"], "message": "Lactate requires current vital signs assessment"},
            "Blood Culture": {"required": ["CBC", "CMP"], "message": "Blood cultures should be ordered with CBC and basic labs"}
        }
        
        contraindicated_combinations = [
            ({"HbA1c"}, {"Glucose"}, "HbA1c and glucose are redundant for acute assessment"),
            ({"PT", "INR"}, {"PTT"}, "Consider ordering a complete coagulation panel")
        ]
        
        # Expand test groups
        expanded_tests = set()
        for test in tests:
            if test in self.standard_test_groups:
                expanded_tests.update(self.standard_test_groups[test])
            else:
                expanded_tests.add(test)
        
        # Check prerequisites
        for test in tests:
            if test in prerequisite_rules:
                required = set(prerequisite_rules[test]["required"])
                
                # Check if any required tests/imaging are missing
                missing_requirements = required - ordered_tests - ordered_imaging - set(tests)
                
                if missing_requirements:
                    return False, prerequisite_rules[test]["message"]
        
        # Check contraindicated combinations
        all_tests = ordered_tests.union(set(tests))
        for test_set_a, test_set_b, message in contraindicated_combinations:
            if test_set_a.issubset(all_tests) and test_set_b.issubset(all_tests):
                # This is a warning, not an error - so we still return True
                logger.warning(f"Advisory: {message}")
        
        return True, None
    
    def _get_cache_key(self, case: Dict[str, Any], tests: List[str]) -> str:
        """
        Generate a unique cache key for a case and test combination.
        """
        case_id = case.get("id", "unknown")
        tests_key = "-".join(sorted(tests))
        key_string = f"{case_id}:{tests_key}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_demographic_references(self, case: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Get reference ranges adjusted for patient demographics.
        """
        age = case.get("age", 35)
        gender = case.get("gender", "Unknown").lower()
        
        # Default reference ranges with demographic adjustments
        references = {
            "Hemoglobin": {
                "units": "g/dL",
                "ref_range": "12.0-16.0" if gender == "female" else "13.5-17.5",
                "critical_low": 7.0,
                "critical_high": 20.0
            },
            "WBC": {
                "units": "x10^9/L",
                "ref_range": "4.5-11.0",
                "critical_low": 2.0,
                "critical_high": 25.0
            },
            "Platelets": {
                "units": "x10^9/L",
                "ref_range": "150-450",
                "critical_low": 50,
                "critical_high": 1000
            },
            "Sodium": {
                "units": "mmol/L",
                "ref_range": "135-145",
                "critical_low": 125,
                "critical_high": 155
            },
            "Potassium": {
                "units": "mmol/L",
                "ref_range": "3.5-5.0",
                "critical_low": 2.8,
                "critical_high": 6.0
            },
            "Creatinine": {
                "units": "mg/dL",
                "ref_range": "0.6-1.1" if gender == "female" else "0.7-1.3",
                "critical_low": None,
                "critical_high": 4.0
            },
            "Glucose": {
                "units": "mg/dL",
                "ref_range": "70-99",
                "critical_low": 40,
                "critical_high": 500
            },
            "pH": {
                "units": "",
                "ref_range": "7.35-7.45",
                "critical_low": 7.2,
                "critical_high": 7.6
            },
            "Troponin I": {
                "units": "ng/mL",
                "ref_range": "0.00-0.04",
                "critical_low": None,
                "critical_high": 0.5
            },
            "CK-MB": {
                "units": "ng/mL",
                "ref_range": "0-3.6" if gender == "female" else "0-7.8",
                "critical_low": None,
                "critical_high": 25.0
            },
            "PT": {
                "units": "seconds",
                "ref_range": "11.0-13.5",
                "critical_low": None,
                "critical_high": 30.0
            },
            "INR": {
                "units": "",
                "ref_range": "0.9-1.1",
                "critical_low": None,
                "critical_high": 5.0
            }
        }
        
        # Age-specific adjustments (simplified)
        if age < 18:
            references["Creatinine"]["ref_range"] = "0.5-1.0"
        elif age > 65:
            references["Creatinine"]["ref_range"] = "0.6-1.2" if gender == "female" else "0.7-1.4"
        
        return references
    
    def generate_report(self, case: Dict[str, Any], tests: List[str]) -> Dict[str, Any]:
        """
        Generate structured lab results based on the case and tests ordered.
        
        Args:
            case: The patient case information
            tests: List of tests ordered
            
        Returns:
            Dict containing structured lab results
        """
        # Check cache first
        cache_key = self._get_cache_key(case, tests)
        if cache_key in self.results_cache:
            logger.info(f"Using cached results for {cache_key}")
            cached_result = self.results_cache[cache_key].copy()
            
            # Update timestamp for the cached result
            cached_result["timestamp"] = datetime.now().isoformat()
            return cached_result
        
        # Expand test groups into individual tests
        expanded_tests = []
        for test in tests:
            if test in self.standard_test_groups:
                expanded_tests.extend(self.standard_test_groups[test])
            else:
                expanded_tests.append(test)
        
        # Get demographic-adjusted reference ranges
        reference_ranges = self._get_demographic_references(case)
        
        try:
            # Generate results using LLM
            system_prompt = f"""Generate realistic lab test results for a patient case.

Patient information:
- Age: {case.get('age', 'Unknown')}
- Gender: {case.get('gender', 'Unknown')}
- Presenting complaint: {case.get('presenting_complaint', 'Unknown')}
- Diagnosis: {case.get('diagnosis', 'Unknown')} (use to guide abnormal values)

Generate lab results for these tests: {json.dumps(expanded_tests)}

For each test, include:
1. Test name
2. Result value (numeric or categorical)
3. Units (if applicable)
4. Reference range
5. Flag (H for high, L for low, C for critical, or blank if normal)

Make the values related to the diagnosis: {case.get('diagnosis', 'Unknown')} as abnormal

Return as JSON object with array of test results and a short interpretation summary.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate lab results for: {', '.join(tests)}"}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            # Parse the generated results
            generated_results = json.loads(response.choices[0].message.content)
            
            # Ensure proper structure and enhance with reference information
            structured_results = self._structure_lab_results(generated_results, reference_ranges)
            
            # Add metadata
            result_report = {
                "case_id": case.get("id", "unknown"),
                "ordered_by": "Medical Student",
                "timestamp": datetime.now().isoformat(),
                "results": structured_results["results"],
                "interpretation": structured_results.get("interpretation", "No interpretation provided."),
                "critical_values": structured_results.get("critical_values", []),
                "result_id": f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Store in cache
            self.results_cache[cache_key] = result_report
            
            # Track test history
            self._update_test_history(case["id"] if "id" in case else "unknown", result_report)
            
            return result_report
            
        except Exception as e:
            logger.error(f"Error generating lab results: {str(e)}")
            
            # Generate fallback results
            fallback_results = self._generate_fallback_results(expanded_tests, reference_ranges, case)
            
            # Add metadata
            result_report = {
                "case_id": case.get("id", "unknown"),
                "ordered_by": "Medical Student",
                "timestamp": datetime.now().isoformat(),
                "results": fallback_results,
                "interpretation": "Results generated using fallback system. Please interpret with caution.",
                "critical_values": [],
                "result_id": f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            return result_report
    
    def _structure_lab_results(self, generated_results: Dict[str, Any], 
                              reference_ranges: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Structure and validate the generated lab results.
        """
        structured_results = {"results": []}
        critical_values = []
        
        for test_result in generated_results.get("results", []):
            test_name = test_result.get("test_name", "Unknown Test")
            value = test_result.get("result", "N/A")
            units = test_result.get("units", "")
            reference = test_result.get("reference_range", "")
            flag = test_result.get("flag", "")
            
            # Get reference data if available
            ref_data = reference_ranges.get(test_name, {})
            
            # Use our reference ranges if available
            if ref_data:
                units = ref_data.get("units", units)
                reference = ref_data.get("ref_range", reference)
                
                # Check for critical values
                try:
                    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
                        numeric_value = float(value)
                        critical_low = ref_data.get("critical_low")
                        critical_high = ref_data.get("critical_high")
                        
                        if critical_low is not None and numeric_value < critical_low:
                            flag = "C"
                            critical_values.append({
                                "test": test_name,
                                "value": value,
                                "units": units,
                                "threshold": f"< {critical_low}"
                            })
                        elif critical_high is not None and numeric_value > critical_high:
                            flag = "C"
                            critical_values.append({
                                "test": test_name,
                                "value": value,
                                "units": units,
                                "threshold": f"> {critical_high}"
                            })
                except (ValueError, TypeError):
                    # Not a numeric value, skip critical checks
                    pass
            
            # Add to structured results
            structured_results["results"].append({
                "test_name": test_name,
                "result": value,
                "units": units,
                "reference_range": reference,
                "flag": flag
            })
        
        # Keep the interpretation if provided
        if "interpretation" in generated_results:
            structured_results["interpretation"] = generated_results["interpretation"]
        
        # Add critical values
        structured_results["critical_values"] = critical_values
        
        return structured_results
    
    def _generate_fallback_results(self, tests: List[str], 
                                  reference_ranges: Dict[str, Dict[str, Any]],
                                  case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate simple fallback results when LLM generation fails.
        """
        results = []
        
        for test in tests:
            if test in reference_ranges:
                ref_data = reference_ranges[test]
                
                # Parse reference range into min and max
                try:
                    ref_range = ref_data["ref_range"]
                    if "-" in ref_range:
                        min_val, max_val = map(float, ref_range.split("-"))
                        # Generate a value in the normal range
                        import random
                        value = round(min_val + (max_val - min_val) * random.random(), 1)
                    else:
                        value = ref_range
                except:
                    value = "N/A"
                
                results.append({
                    "test_name": test,
                    "result": value,
                    "units": ref_data.get("units", ""),
                    "reference_range": ref_data["ref_range"],
                    "flag": ""
                })
            else:
                # Generic test with no reference data
                results.append({
                    "test_name": test,
                    "result": "Within normal limits",
                    "units": "",
                    "reference_range": "N/A",
                    "flag": ""
                })
                
        return results
    
    def _update_test_history(self, case_id: str, result_report: Dict[str, Any]) -> None:
        """
        Track test results over time to allow for trending.
        """
        if case_id not in self.test_history:
            self.test_history[case_id] = []
            
        self.test_history[case_id].append({
            "timestamp": result_report["timestamp"],
            "result_id": result_report["result_id"],
            "results": result_report["results"]
        })
    
    def get_test_history(self, case_id: str, test_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the history of test results for trending purposes.
        
        Args:
            case_id: The ID of the case
            test_name: Optional specific test to get history for
            
        Returns:
            List of test results over time
        """
        if case_id not in self.test_history:
            return []
            
        history = self.test_history[case_id]
        
        if not test_name:
            return history
            
        # Filter for specific test
        filtered_history = []
        for entry in history:
            for result in entry["results"]:
                if result["test_name"] == test_name:
                    filtered_history.append({
                        "timestamp": entry["timestamp"],
                        "result_id": entry["result_id"],
                        "result": result
                    })
                    break
                    
        return filtered_history
    
    def generate_markdown_report(self, lab_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable markdown report from structured results.
        
        Args:
            lab_results: Structured lab results
            
        Returns:
            Markdown formatted report
        """
        report = f"# Laboratory Results\n\n"
        report += f"**Case ID:** {lab_results.get('case_id', 'Unknown')}\n"
        report += f"**Ordered By:** {lab_results.get('ordered_by', 'Unknown')}\n"
        report += f"**Date/Time:** {lab_results.get('timestamp', 'Unknown')}\n\n"
        
        # Check for critical values
        critical_values = lab_results.get('critical_values', [])
        if critical_values:
            report += "## ⚠️ CRITICAL VALUES\n\n"
            for critical in critical_values:
                report += f"* **{critical['test']}:** {critical['value']} {critical['units']} ({critical['threshold']})\n"
            report += "\n"
        
        # Add table of results
        report += "## Results\n\n"
        report += "| Test | Result | Flag | Reference Range | Units |\n"
        report += "|------|--------|------|----------------|-------|\n"
        
        for result in lab_results.get('results', []):
            test_name = result.get('test_name', 'Unknown')
            value = result.get('result', 'N/A')
            flag = result.get('flag', '')
            reference = result.get('reference_range', '')
            units = result.get('units', '')
            
            # Add emphasis to abnormal results
            if flag:
                test_name = f"**{test_name}**"
                value = f"**{value}**"
                flag = f"**{flag}**"
            
            report += f"| {test_name} | {value} | {flag} | {reference} | {units} |\n"
        
        # Add interpretation
        if 'interpretation' in lab_results and lab_results['interpretation']:
            report += "\n## Interpretation\n\n"
            report += lab_results['interpretation']
            
        return report