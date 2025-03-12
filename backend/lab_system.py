import json
import logging
import hashlib
import aiohttp
import asyncio
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from datetime import datetime
from openai import Client

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


logger = logging.getLogger(__name__)

class PerplexityLabGenerator:
    """
    Uses Perplexity AI to generate medically accurate laboratory test results
    based on the patient case and clinical diagnosis.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    async def generate_lab_results_async(self, 
                                   case: Dict[str, Any], 
                                   tests: List[str],
                                   reference_ranges: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate medically accurate lab results using Perplexity AI.
        
        Args:
            case: The patient case information
            tests: List of tests ordered
            reference_ranges: Dictionary of reference ranges by test
            
        Returns:
            Dict containing the generated lab results
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        # Create a detailed prompt with all relevant medical information
        prompt = self._create_detailed_prompt(case, tests, reference_ranges)
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a laboratory medicine specialist generating realistic lab test results. "
                        "Create medically accurate lab results based on the case information and tests ordered. "
                        "Return ONLY valid JSON with precise lab values, ensuring all test values are appropriate for the diagnosis."
                    )
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "options": {
                "search_focus": "internet"
            },
            "max_tokens": 4096,
            "temperature": 0.2
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, 
                    headers=self.headers,
                    json=payload,
                    timeout=60
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        logger.error(f"Perplexity API error: {response.status} - {response_text[:500]}")
                        return {"error": f"Perplexity API error: {response.status}"}
                    
                    result = json.loads(response_text)
                    
                    # Extract the content from Perplexity's response
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        
                        try:
                            # Find JSON in the response
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            
                            if json_start >= 0 and json_end > json_start:
                                json_content = content[json_start:json_end]
                                lab_results = json.loads(json_content)
                                
                                # Add additional metadata 
                                lab_results["generated_by"] = "perplexity"
                                lab_results["timestamp"] = datetime.now().isoformat()
                                
                                return lab_results
                            else:
                                logger.error(f"No valid JSON found in response. Content: {content}")
                                return {"error": "No valid JSON found in response"}
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON from Perplexity: {str(e)}")
                            return {"error": f"Invalid JSON in response: {str(e)}"}
                    else:
                        logger.error("No content in Perplexity response")
                        return {"error": "No content in Perplexity response"}
        except Exception as e:
            error_details = str(e)
            logger.error(f"Error in Perplexity search: {error_details}")
            return {"error": f"Perplexity API error: {error_details}"}
    
    def generate_lab_results(self, 
                          case: Dict[str, Any], 
                          tests: List[str],
                          reference_ranges: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synchronous wrapper for generate_lab_results_async.
        
        Args:
            case: The patient case information
            tests: List of tests ordered
            reference_ranges: Dictionary of reference ranges by test
            
        Returns:
            Dict containing the generated lab results
        """
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Run the async method in the event loop
            results = loop.run_until_complete(
                self.generate_lab_results_async(case, tests, reference_ranges)
            )
            return results
        except Exception as e:
            logger.error(f"Error in synchronous Perplexity generation: {str(e)}")
            return {"error": f"Perplexity generation error: {str(e)}"}
            
    def _create_detailed_prompt(self, 
                              case: Dict[str, Any], 
                              tests: List[str],
                              reference_ranges: Dict[str, Dict[str, Any]]) -> str:
        """
        Create a detailed prompt for Perplexity with all relevant medical information.
        
        Args:
            case: The patient case information
            tests: List of tests ordered
            reference_ranges: Dictionary of reference ranges by test
            
        Returns:
            Detailed prompt string for Perplexity
        """
        # Extract key case information
        diagnosis = case.get("diagnosis", 
                         case.get("expected_diagnosis", "Unknown"))
        
        age = case.get("age", "Unknown")
        gender = case.get("gender", "Unknown")
        presenting_complaint = case.get("presenting_complaint", "Unknown")
        
        # Collect symptoms if available
        symptoms = []
        if "symptoms" in case and isinstance(case["symptoms"], list):
            symptoms = case["symptoms"]
        
        # Collect comorbidities if available
        comorbidities = []
        if "past_medical_conditions" in case and isinstance(case["past_medical_conditions"], list):
            comorbidities = case["past_medical_conditions"]
            
        # Build the reference range information to include in prompt
        ref_range_text = "Reference ranges for these tests:\n"
        for test in tests:
            if test in reference_ranges:
                ref_data = reference_ranges[test]
                ref_range_text += f"- {test}: {ref_data.get('ref_range', 'Not specified')} {ref_data.get('units', '')}\n"
        
        # Build the prompt
        prompt = f"""Generate lab test results for a {age}-year-old {gender} patient with {diagnosis}.

Patient Information:
- Presenting complaint: {presenting_complaint}
- Diagnosis: {diagnosis}
- Symptoms: {', '.join(symptoms) if symptoms else 'Not specified'}
- Comorbidities: {', '.join(comorbidities) if comorbidities else 'None'}

Tests ordered: {', '.join(tests)}

{ref_range_text}

Create REALISTIC and MEDICALLY ACCURATE lab results that would be expected in a patient with {diagnosis}. 
Include appropriate abnormalities that would be present in this case.

For each test, provide:
1. Test name
2. Numeric result value
3. Units
4. Reference range
5. Flag (H for high, L for low, C for critical, or empty for normal)

Return the results in this JSON format:
{{
  "results": [
    {{
      "test_name": "Test Name",
      "result": "Value",
      "units": "Units",
      "reference_range": "Range",
      "flag": ""
    }},
    ...
  ],
  "interpretation": "Brief interpretation of results",
  "critical_values": [
    {{
      "test": "Test name",
      "value": "Critical value",
      "units": "Units",
      "threshold": "> or < threshold value"
    }},
    ...
  ]
}}

Use Medline, PubMed, medical journals, and other reliable sources to ensure the lab values are MEDICALLY ACCURATE and REALISTIC for this specific diagnosis.
"""
        return prompt


class LabSystem:
    """
    Enhanced laboratory system for managing test orders, validation, and result generation.
    Provides structured lab results with appropriate reference ranges and abnormal flagging.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        # Initialize Perplexity client if API key is available
        self.perplexity_client = PerplexityLabGenerator(config.perplexity_api_key) if hasattr(config, 'perplexity_api_key') and config.perplexity_api_key else None
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
            },
            "RBC": {
                "units": "x10^12/L",
                "ref_range": "4.2-5.4" if gender == "female" else "4.5-5.9",
                "critical_low": 2.5,
                "critical_high": 7.0
            },
            "Hematocrit": {
                "units": "%",
                "ref_range": "37-47" if gender == "female" else "40-52",
                "critical_low": 20,
                "critical_high": 60
            },
            "MCV": {
                "units": "fL",
                "ref_range": "80-100",
                "critical_low": None,
                "critical_high": None
            },
            "MCH": {
                "units": "pg",
                "ref_range": "27-34",
                "critical_low": None,
                "critical_high": None
            },
            "MCHC": {
                "units": "g/dL",
                "ref_range": "32-36",
                "critical_low": None,
                "critical_high": None
            },
            "BUN": {
                "units": "mg/dL",
                "ref_range": "7-20",
                "critical_low": None,
                "critical_high": 100
            },
            "Calcium": {
                "units": "mg/dL",
                "ref_range": "8.5-10.5",
                "critical_low": 6.0,
                "critical_high": 13.0
            },
            "Chloride": {
                "units": "mmol/L",
                "ref_range": "96-106",
                "critical_low": 80,
                "critical_high": 120
            },
            "CO2": {
                "units": "mmol/L",
                "ref_range": "23-29",
                "critical_low": 10,
                "critical_high": 40
            },
            "AST": {
                "units": "U/L",
                "ref_range": "5-40",
                "critical_low": None,
                "critical_high": 1000
            },
            "ALT": {
                "units": "U/L",
                "ref_range": "5-40",
                "critical_low": None,
                "critical_high": 1000
            },
            "Alkaline Phosphatase": {
                "units": "U/L",
                "ref_range": "35-105",
                "critical_low": None,
                "critical_high": 1000
            },
            "Total Bilirubin": {
                "units": "mg/dL",
                "ref_range": "0.1-1.2",
                "critical_low": None,
                "critical_high": 15.0
            },
            "Albumin": {
                "units": "g/dL",
                "ref_range": "3.5-5.0",
                "critical_low": 1.5,
                "critical_high": None
            },
            "Total Protein": {
                "units": "g/dL",
                "ref_range": "6.0-8.0",
                "critical_low": 3.0,
                "critical_high": 12.0
            },
            "TSH": {
                "units": "mIU/L",
                "ref_range": "0.4-4.0",
                "critical_low": 0.01,
                "critical_high": 50.0
            },
            "Free T4": {
                "units": "ng/dL",
                "ref_range": "0.8-1.8",
                "critical_low": 0.2,
                "critical_high": 5.0
            },
            "Free T3": {
                "units": "pg/mL",
                "ref_range": "2.3-4.2",
                "critical_low": 0.5,
                "critical_high": 20.0
            },
            "Total Cholesterol": {
                "units": "mg/dL",
                "ref_range": "< 200",
                "critical_low": None,
                "critical_high": 300
            },
            "LDL": {
                "units": "mg/dL",
                "ref_range": "< 100",
                "critical_low": None,
                "critical_high": 190
            },
            "HDL": {
                "units": "mg/dL",
                "ref_range": "> 40" if gender == "male" else "> 50",
                "critical_low": 20,
                "critical_high": None
            },
            "Triglycerides": {
                "units": "mg/dL",
                "ref_range": "< 150",
                "critical_low": None,
                "critical_high": 500
            },
            "pO2": {
                "units": "mmHg",
                "ref_range": "80-100",
                "critical_low": 55,
                "critical_high": None
            },
            "pCO2": {
                "units": "mmHg",
                "ref_range": "35-45",
                "critical_low": 20,
                "critical_high": 70
            },
            "HCO3": {
                "units": "mmol/L",
                "ref_range": "22-26",
                "critical_low": 10,
                "critical_high": 40
            },
            "O2 Saturation": {
                "units": "%",
                "ref_range": "95-100",
                "critical_low": 85,
                "critical_high": None
            },
            "Base Excess": {
                "units": "mmol/L",
                "ref_range": "-2 to +2",
                "critical_low": -10,
                "critical_high": 10
            },
            "Troponin T": {
                "units": "ng/mL",
                "ref_range": "< 0.01",
                "critical_low": None,
                "critical_high": 0.1
            },
            "BNP": {
                "units": "pg/mL",
                "ref_range": "< 100",
                "critical_low": None,
                "critical_high": 2000
            },
            "D-dimer": {
                "units": "μg/mL",
                "ref_range": "< 0.5",
                "critical_low": None,
                "critical_high": 5.0
            },
            "HbA1c": {
                "units": "%",
                "ref_range": "< 5.7",
                "critical_low": None,
                "critical_high": 14.0
            },
            "PTT": {
                "units": "seconds",
                "ref_range": "25-35",
                "critical_low": None,
                "critical_high": 100
            },
            "Lactate": {
                "units": "mmol/L",
                "ref_range": "0.5-1.5",
                "critical_low": None,
                "critical_high": 4.0
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
        Uses Perplexity AI if available or falls back to OpenAI.
        
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
            # Try to use Perplexity for more medically accurate results if available
            if self.perplexity_client:
                try:
                    logger.info("Generating lab results using Perplexity AI")
                    
                    # Use the synchronous method
                    perplexity_results = self.perplexity_client.generate_lab_results(
                        case, expanded_tests, reference_ranges
                    )
                    
                    # Check if we got valid results or an error
                    if "error" not in perplexity_results:
                        # Process the Perplexity results
                        structured_results = self._structure_lab_results(perplexity_results, reference_ranges)
                        
                        # Add metadata
                        result_report = {
                            "case_id": case.get("id", "unknown"),
                            "ordered_by": "Medical Student",
                            "timestamp": datetime.now().isoformat(),
                            "results": structured_results["results"],
                            "interpretation": structured_results.get("interpretation", "No interpretation provided."),
                            "critical_values": structured_results.get("critical_values", []),
                            "result_id": f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            "source": "perplexity"
                        }
                        
                        # Store in cache
                        self.results_cache[cache_key] = result_report
                        
                        # Track test history
                        self._update_test_history(case["id"] if "id" in case else "unknown", result_report)
                        
                        return result_report
                    else:
                        # Log the error but continue with OpenAI fallback
                        logger.warning(f"Perplexity generation failed: {perplexity_results.get('error')}")
                        logger.info("Falling back to OpenAI for lab results generation")
                except Exception as e:
                    logger.error(f"Error using Perplexity for lab results: {str(e)}")
                    logger.info("Falling back to OpenAI for lab results generation")
            
            # OpenAI implementation for fallback
            logger.info("Generating lab results using OpenAI API")
            
            # Generate results using LLM
            system_prompt = f"""Generate realistic lab test results for a patient case.

Patient information:
- Age: {case.get('age', 'Unknown')}
- Gender: {case.get('gender', 'Unknown')}
- Presenting complaint: {case.get('presenting_complaint', 'Unknown')}
- Diagnosis: {case.get('diagnosis', case.get('expected_diagnosis', 'Unknown'))} (use to guide abnormal values)

Generate lab results for these tests: {json.dumps(expanded_tests)}

For each test, include:
1. Test name
2. Result value (numeric or categorical)
3. Units (if applicable)
4. Reference range
5. Flag (H for high, L for low, C for critical, or blank if normal)

Make the values related to the diagnosis: {case.get('diagnosis', case.get('expected_diagnosis', 'Unknown'))} as abnormal

Return a JSON object with exactly this format:
{{
  "results": [
    {{
      "test_name": "Test 1",
      "result": "value",
      "units": "units",
      "reference_range": "range",
      "flag": ""
    }},
    ...
  ],
  "interpretation": "Brief summary of results and clinical significance"
}}
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
            
            # Log the entire response for debugging
            logger.debug(f"Complete LLM response: {response.choices[0].message.content}")
            
            # Parse the generated results
            result_content = response.choices[0].message.content
            logger.info(f"Generated results: {result_content[:200]}...")
            generated_results = json.loads(result_content)
            
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
                "result_id": f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "source": "openai"
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
                "result_id": f"lab_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "source": "fallback"
            }
            
            return result_report
            
    def _structure_lab_results(self, generated_results: Dict[str, Any], 
                              reference_ranges: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Structure and validate the generated lab results.
        """
        structured_results = {"results": []}
        critical_values = []
        interpretation = "No interpretation provided."
        
        # Set default interpretation if provided in the response
        if "interpretation" in generated_results and generated_results["interpretation"]:
            interpretation = generated_results["interpretation"]
        
        # Check for results in different possible formats
        results_list = None
        if "results" in generated_results and isinstance(generated_results["results"], list):
            results_list = generated_results["results"]
        elif "lab_results" in generated_results and isinstance(generated_results["lab_results"], list):
            # Handle alternative format where results are under "lab_results" key
            results_list = generated_results["lab_results"]
            logger.info("Found lab results under 'lab_results' key instead of 'results'")
        
        if not results_list:
            logger.warning("Generated results missing valid results list, creating empty structure")
            structured_results["interpretation"] = interpretation
            structured_results["critical_values"] = []
            return structured_results
            
        for test_result in results_list:
            if not isinstance(test_result, dict):
                logger.warning(f"Skipping non-dict test result: {test_result}")
                continue
                
            # Handle different key names in the response
            test_name = test_result.get("test_name", "Unknown Test")
            
            # Try different field names for result value
            if "result" in test_result:
                value = test_result["result"]
            elif "result_value" in test_result:
                value = test_result["result_value"]
            else:
                value = "N/A"
                
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
                    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).replace('-', '', 1).isdigit()):
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
                        elif flag == "" and reference:
                            # Check if abnormal but not critical
                            try:
                                if "-" in reference:
                                    ref_min, ref_max = map(float, reference.split("-"))
                                    if numeric_value < ref_min:
                                        flag = "L"
                                    elif numeric_value > ref_max:
                                        flag = "H"
                            except (ValueError, TypeError):
                                pass
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
        
        # If critical values were provided directly, use those
        if "critical_values" in generated_results and isinstance(generated_results["critical_values"], list):
            # Don't completely override our calculated values, merge them
            existing_tests = set(cv["test"] for cv in critical_values)
            for cv in generated_results["critical_values"]:
                if isinstance(cv, dict) and "test" in cv and cv["test"] not in existing_tests:
                    critical_values.append(cv)
        
        # Add interpretation and critical values
        structured_results["interpretation"] = interpretation
        structured_results["critical_values"] = critical_values
        
        return structured_results
    
    def _generate_fallback_results(self, tests: List[str], 
                                  reference_ranges: Dict[str, Dict[str, Any]],
                                  case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate simple fallback results when LLM generation fails.
        """
        results = []
        
        diagnosis = case.get("diagnosis", case.get("expected_diagnosis", "Unknown"))
        
        # Map certain diagnoses to specific test abnormalities for more realistic results
        abnormal_patterns = {
            "Myocardial Infarction": {"Troponin I": 2.5, "CK-MB": 25.0, "Troponin T": 0.5},
            "Pneumonia": {"WBC": 15.0},
            "Diabetes": {"Glucose": 250},
            "Anemia": {"Hemoglobin": 8.0, "Hematocrit": 25},
            "Sepsis": {"WBC": 20.0, "Lactate": 4.0},
            "Liver Failure": {"AST": 500, "ALT": 450, "Total Bilirubin": 5.0},
            "Kidney Failure": {"Creatinine": 3.5, "BUN": 60},
            "Hyponatremia": {"Sodium": 128},
            "Hyperkalemia": {"Potassium": 6.2}
        }
        
        for test in tests:
            if test in reference_ranges:
                ref_data = reference_ranges[test]
                
                # Parse reference range into min and max
                try:
                    ref_range = ref_data["ref_range"]
                    
                    # Check if this test should be abnormal for this diagnosis
                    abnormal_value = None
                    for key_diagnosis, abnormal_tests in abnormal_patterns.items():
                        if key_diagnosis.lower() in diagnosis.lower() and test in abnormal_tests:
                            abnormal_value = abnormal_tests[test]
                            break
                    
                    if abnormal_value is not None:
                        # Use the predefined abnormal value
                        value = abnormal_value
                        flag = "H" if abnormal_value > float(ref_range.split("-")[1]) else "L"
                    elif "-" in ref_range:
                        # Generate a value in the normal range
                        min_val, max_val = map(float, ref_range.split("-"))
                        import random
                        value = round(min_val + (max_val - min_val) * random.random(), 1)
                        flag = ""
                    else:
                        value = ref_range
                        flag = ""
                except:
                    value = "N/A"
                    flag = ""
                
                results.append({
                    "test_name": test,
                    "result": value,
                    "units": ref_data.get("units", ""),
                    "reference_range": ref_data["ref_range"],
                    "flag": flag
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
    
    def generate_markdown_report(self, lab_results: dict) -> str:
        """
        Generate a markdown report from structured lab results with beautiful formatting.
        Returns the markdown string directly.
        """
        # Build the markdown content as a string
        markdown = "# Laboratory Results\n\n"
        markdown += f"**Case ID:** {lab_results.get('case_id', 'Unknown')}  \n"
        markdown += f"**Ordered By:** {lab_results.get('ordered_by', 'Unknown')}  \n"
        markdown += f"**Date/Time:** {lab_results.get('timestamp', 'Unknown')}  \n\n"
        
        # Add critical values if available
        critical_values = lab_results.get('critical_values', [])
        if critical_values:
            markdown += "## ⚠️ Critical Values\n\n"
            for crit in critical_values:
                markdown += f"**{crit['test']}:** {crit['value']} {crit['units']} (Threshold: {crit['threshold']})  \n"
            markdown += "\n"
        
        # Create a table for test results
        markdown += "## Test Results\n\n"
        markdown += "| Test | Result | Flag | Reference Range | Units |\n"
        markdown += "|------|--------|------|----------------|-------|\n"
        
        for result in lab_results.get("results", []):
            test_name = result.get("test_name", "Unknown")
            value = result.get("result", "N/A")
            flag = result.get("flag", "")
            reference = result.get("reference_range", "")
            units = result.get("units", "")
            
            # Emphasize abnormal values
            if flag:
                test_name = f"**{test_name}**"
                value = f"**{value}**"
                flag = f"**{flag}**"
            
            markdown += f"| {test_name} | {value} | {flag} | {reference} | {units} |\n"
        
        return markdown