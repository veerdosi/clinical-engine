import json
import logging
from typing import Dict, Any, List, Optional
from openai import Client
from datetime import datetime

logger = logging.getLogger(__name__)

class PhysicalExamSystem:
    """
    Enhanced system for generating physical examination findings based on the patient case
    and verifying examination procedures.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        self.results_cache = {}  # Cache to store generated results
        self.procedure_cache = {}  # Cache to store procedure verification
        
    def _get_cache_key(self, case_id: str, system: str) -> str:
        """
        Generate a unique cache key for a case and examination.
        """
        return f"{case_id}:{system}"
    
    def perform_examination(self, case: Dict[str, Any], system: str, procedure_verified=False) -> Dict[str, Any]:
        """
        Generate physical examination findings based on the case and selected body system.
        
        Args:
            case: The patient case information
            system: The body system to examine
            procedure_verified: Whether the procedure steps were verified
            
        Returns:
            Dict containing the examination findings
        """
        # Check cache first
        cache_key = self._get_cache_key(case.get("id", "unknown"), system)
        if cache_key in self.results_cache:
            logger.info(f"Using cached examination results for {cache_key}")
            cached_result = self.results_cache[cache_key].copy()
            return cached_result
        
        # Handle vital signs separately - extract directly from the case
        if system.lower() == 'vital_signs':
            return self._extract_vital_signs(case)
        
        # If procedure verification is required but not done, return limited information
        if not procedure_verified:
            return {
                "findings": "Examination findings are only available after proper verification of the examination procedure.",
                "error": "Procedure not verified",
                "timestamp": datetime.now().isoformat(),
                "requires_verification": True
            }
        
        try:
            # Extract key case info for context
            diagnosis = case.get("diagnosis", 
                             case.get("expected_diagnosis", 
                                   case.get("expected_correct_diagnosis", "Unknown")))
            symptoms = self._extract_symptoms(case)
            comorbidities = self._extract_comorbidities(case)
            
            # Generate results using LLM
            system_prompt = f"""Generate realistic physical examination findings for a patient case.

Patient information:
- Age: {case.get('age', case.get('demographics', {}).get('age', 'Unknown'))}
- Gender: {case.get('gender', case.get('demographics', {}).get('gender', 'Unknown'))}
- Presenting symptoms: {json.dumps(symptoms)}
- Comorbidities: {json.dumps(comorbidities)}
- Diagnosis: {diagnosis} (use to guide findings)

Generate examination findings for: {system}

The findings should be consistent with the diagnosis and symptoms. Include both positive and negative findings
that would be discovered during a thorough physical examination.

Return a JSON object with:
1. "findings": Detailed observations as key-value pairs or paragraphs
2. "interpretation": Brief clinical interpretation of these findings (optional)

Make the findings detailed, specific, and medically accurate.
"""

            logger.info(f"Generating examination findings for: {system}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Perform physical examination: {system}"}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            # Parse the generated results
            try:
                result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Handle non-JSON responses
                text_content = response.choices[0].message.content.strip()
                result = {
                    "findings": text_content,
                    "interpretation": "Unable to structure findings. Please review the text."
                }
                
            # Add timestamp
            result["timestamp"] = datetime.now().isoformat()
            
            # Cache the result
            self.results_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating examination findings: {str(e)}")
            return {
                "findings": f"Unable to perform {system} examination: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_vital_signs(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract vital signs directly from the case data.
        """
        result = {"timestamp": datetime.now().isoformat()}
        
        # Check for vital_signs object
        if "vital_signs" in case and isinstance(case["vital_signs"], dict):
            result["findings"] = case["vital_signs"]
            return result
            
        # Check alternative formats
        vitals = {}
        
        # Check for individual vital fields
        vital_fields = ["BP", "HR", "RR", "Temp", "SpO2", "Glucose", "Pain"]
        for field in vital_fields:
            if field in case:
                vitals[field] = case[field]
        
        # If nothing found, return a generic message
        if not vitals:
            vital_lookup = {
                "BP": "120/80 mmHg",
                "HR": "72 bpm",
                "RR": "16 breaths/min",
                "Temp": "37.0 °C (98.6 °F)",
                "SpO2": "98% on room air"
            }
            # Add note that these are generic values
            result["findings"] = vital_lookup
            result["interpretation"] = "Note: These are default values as specific vital signs were not found in the case."
            return result
            
        result["findings"] = vitals
        return result

    def _extract_symptoms(self, case: Dict[str, Any]) -> list:
        """Extract symptoms from various possible formats in the case data"""
        symptoms = []
        
        # Check for key_symptoms as a list
        if "key_symptoms" in case and isinstance(case["key_symptoms"], list):
            symptoms.extend(case["key_symptoms"])
        
        # Check for key_symptoms as a dictionary
        elif "key_symptoms" in case and isinstance(case["key_symptoms"], dict):
            for system, symptom in case["key_symptoms"].items():
                if symptom and symptom != "None":
                    symptoms.append(f"{symptom}")
        
        # Check for symptoms in presentation
        if "presentation" in case:
            presentation = case["presentation"]
            
            if "classic_symptoms" in presentation and isinstance(presentation["classic_symptoms"], list):
                symptoms.extend(presentation["classic_symptoms"])
                
            if "description" in presentation and isinstance(presentation["description"], str):
                symptoms.append(presentation["description"])
                
        # Check for atypical_presentation
        if "atypical_presentation" in case:
            atypical = case["atypical_presentation"]
            if "description" in atypical and isinstance(atypical["description"], str):
                symptoms.append(atypical["description"])
                
        # Check condition description
        if "condition" in case and isinstance(case["condition"], dict):
            if "description" in case["condition"]:
                symptoms.append(case["condition"]["description"])
                
        # Check for symptoms as array directly in case
        if "symptoms" in case and isinstance(case["symptoms"], list):
            symptoms.extend(case["symptoms"])
            
        # Check presenting_complaint
        if "presenting_complaint" in case and case["presenting_complaint"]:
            symptoms.append(case["presenting_complaint"])
                
        # Deduplicate symptoms
        return list(set(symptoms))

    def _extract_comorbidities(self, case: Dict[str, Any]) -> list:
        """Extract comorbidities from various possible formats in the case data"""
        comorbidities = []
        
        # Check for comorbidities as a list
        if "comorbidities" in case and isinstance(case["comorbidities"], list):
            comorbidities.extend(case["comorbidities"])
            
        # Check for comorbidities in atypical_presentation
        if "atypical_presentation" in case and isinstance(case["atypical_presentation"], dict):
            if "comorbidities" in case["atypical_presentation"] and isinstance(case["atypical_presentation"]["comorbidities"], list):
                comorbidities.extend(case["atypical_presentation"]["comorbidities"])
                
        # Check for past_medical_conditions
        if "past_medical_conditions" in case and isinstance(case["past_medical_conditions"], list):
            comorbidities.extend(case["past_medical_conditions"])
            
        # Deduplicate comorbidities
        return list(set(comorbidities))

    def verify_procedure(self, 
                        case: Dict[str, Any], 
                        exam_name: str, 
                        procedure_steps: List[str]) -> Dict[str, Any]:
        """
        Verifies if a physical examination procedure is correctly described.
        
        Args:
            case: The patient case information
            exam_name: Name of the examination procedure
            procedure_steps: List of procedure steps in order
            
        Returns:
            Dict containing verification results
        """
        # Check cache for this procedure
        cache_key = f"{case.get('id', 'unknown')}:{exam_name}"
        if cache_key in self.procedure_cache:
            logger.info(f"Using cached procedure verification for {cache_key}")
            return self.procedure_cache[cache_key]
            
        # Check if this exam is appropriate for the case
        is_appropriate = self._check_exam_relevance(case, exam_name)
        
        # Extract key case info for context
        diagnosis = case.get("diagnosis", 
                         case.get("expected_diagnosis", 
                               case.get("expected_correct_diagnosis", "Unknown")))
        symptoms = self._extract_symptoms(case)
        
        try:
            # Generate verification using LLM
            system_prompt = f"""You are an expert medical educator verifying a medical student's physical examination procedure.

Patient information:
- Presenting symptoms: {json.dumps(symptoms)}
- Diagnosis: {diagnosis}

The student wants to perform: {exam_name}

They have provided these procedure steps in order:
{json.dumps(procedure_steps, indent=2)}

Your task is to:
1. Verify if the exam is appropriate for this case
2. Verify if the steps are correct and in the right order
3. Check for any missing critical steps or incorrect procedures

Return a JSON object with:
1. "is_correct": Boolean indicating if the procedure is correctly described
2. "is_appropriate": Boolean indicating if this exam is appropriate for the case
3. "feedback": Specific feedback about the procedure (what's good, what's missing, what's in wrong order)
4. "score": A score from 0-100 evaluating the procedure
5. "correct_steps": A list of the expected steps in correct order (if the student's steps are incorrect)
6. "penalties": A list of specific issues that would lead to evaluation penalties

If the procedure is generally correct but has minor issues, still mark it as correct but provide feedback.
"""

            logger.info(f"Verifying procedure for: {exam_name}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Verify this {exam_name} procedure for appropriateness and correctness."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the generated results
            result = json.loads(response.choices[0].message.content)
            
            # Add timestamp
            result["timestamp"] = datetime.now().isoformat()
            
            # Add appropriate flag from our initial check as a fallback
            if "is_appropriate" not in result:
                result["is_appropriate"] = is_appropriate
                
            # Ensure all required fields are present
            if "is_correct" not in result:
                result["is_correct"] = False
            if "feedback" not in result:
                result["feedback"] = "Unable to properly verify the procedure."
            if "score" not in result:
                result["score"] = 0
                
            # Cache the result
            self.procedure_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying examination procedure: {str(e)}")
            return {
                "is_correct": False,
                "is_appropriate": is_appropriate,
                "feedback": f"Error verifying procedure: {str(e)}",
                "score": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _check_exam_relevance(self, case: Dict[str, Any], exam_name: str) -> bool:
        """
        Determines if an examination is appropriate for the given case.
        
        Args:
            case: The patient case information
            exam_name: Name of the examination
            
        Returns:
            Boolean indicating if the examination is appropriate
        """
        try:
            # Extract symptoms and diagnosis
            diagnosis = case.get("diagnosis", 
                             case.get("expected_diagnosis", 
                                   case.get("expected_correct_diagnosis", "Unknown")))
            symptoms = self._extract_symptoms(case)
            specialty = case.get("specialty", "General Medicine")
            
            # Quick check for vital signs - always appropriate
            if "vital" in exam_name.lower():
                return True
                
            # Quick check for general assessment - always appropriate
            if "general" in exam_name.lower() or "assessment" in exam_name.lower():
                return True
                
            # Use LLM to determine relevance
            system_prompt = f"""You are an expert in medical education. Determine if a specific physical examination is appropriate for a given patient case.

Patient information:
- Specialty: {specialty}
- Presenting symptoms: {json.dumps(symptoms)}
- Diagnosis: {diagnosis}

Physical examination: {exam_name}

Answer with a simple "true" if the examination is relevant and appropriate for this case, or "false" if it's not relevant.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Is {exam_name} appropriate for this case?"}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result_text = response.choices[0].message.content.strip().lower()
            return "true" in result_text or "yes" in result_text
            
        except Exception as e:
            logger.error(f"Error checking exam relevance: {str(e)}")
            # Default to true in case of error
            return True