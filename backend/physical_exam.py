import json
import logging
from typing import Dict, Any, Optional
from openai import Client
from datetime import datetime

logger = logging.getLogger(__name__)

class PhysicalExamSystem:
    """
    System for generating physical examination findings based on the patient case.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key= config.openai_api_key)
        self.results_cache = {}  # Cache to store generated results
        
    def _get_cache_key(self, case_id: str, system: str) -> str:
        """
        Generate a unique cache key for a case and examination.
        """
        return f"{case_id}:{system}"
    
    def perform_examination(self, case: Dict[str, Any], system: str) -> Dict[str, Any]:
        """
        Generate physical examination findings based on the case and selected body system.
        
        Args:
            case: The patient case information
            system: The body system to examine
            
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

Generate examination findings for body system: {system}

The findings should be consistent with the diagnosis and symptoms. Include both positive and negative findings
that would be discovered during a thorough physical examination.

Return a JSON object with:
1. "findings": Detailed observations as key-value pairs or paragraphs
2. "interpretation": Brief clinical interpretation of these findings (optional)

Make the findings detailed, specific, and medically accurate.
"""

            logger.info(f"Generating examination findings for system: {system}")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Perform physical examination of the {system} system"}
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