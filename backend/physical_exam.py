import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import Client

logger = logging.getLogger(__name__)

class PerplexityPhysicalExamGenerator:
    """
    Uses Perplexity AI to generate medically accurate physical examination findings
    based on medical literature and clinical guidelines.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    async def generate_exam_findings_async(self, 
                                   case: Dict[str, Any], 
                                   system: str) -> Dict[str, Any]:
        """
        Generate medically accurate examination findings using Perplexity AI.
        
        Args:
            case: The patient case information
            system: The body system being examined
            
        Returns:
            Dict containing the generated examination findings
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        # Create a detailed prompt with all relevant medical information
        prompt = self._create_detailed_prompt(case, system)
        
        payload = {
            "model": "sonar",  # Using Perplexity's model with web search
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a clinical examination specialist generating physical examination findings for a medical simulation. "
                        "Create detailed, medically accurate findings based on the case information and system being examined. "
                        "Return a JSON object with the findings, ensuring all observations are consistent with current medical literature."
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
                    timeout=60  # Increased timeout for thorough search
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
                                exam_findings = json.loads(json_content)
                                
                                # Add additional metadata 
                                exam_findings["generated_by"] = "perplexity"
                                exam_findings["timestamp"] = datetime.now().isoformat()
                                exam_findings["references"] = exam_findings.get("references", [])
                                
                                return exam_findings
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
    
    def generate_exam_findings(self, case: Dict[str, Any], system: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for generate_exam_findings_async.
        
        Args:
            case: The patient case information
            system: The body system being examined
            
        Returns:
            Dict containing the generated examination findings
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
                self.generate_exam_findings_async(case, system)
            )
            return results
        except Exception as e:
            logger.error(f"Error in synchronous Perplexity generation: {str(e)}")
            return {"error": f"Perplexity generation error: {str(e)}"}
            
    def _create_detailed_prompt(self, case: Dict[str, Any], system: str) -> str:
        """
        Create a detailed prompt for Perplexity with all relevant medical information.
        
        Args:
            case: The patient case information
            system: The body system being examined
            
        Returns:
            Detailed prompt string for Perplexity
        """
        # Extract key case information
        diagnosis = case.get("diagnosis", 
                         case.get("expected_diagnosis", "Unknown"))
        
        age = case.get("age", "Unknown")
        gender = case.get("gender", "Unknown")
        presenting_complaint = case.get("presenting_complaint", "Unknown")
        
        # Extract symptoms and comorbidities
        symptoms = self._extract_symptoms(case)
        comorbidities = self._extract_comorbidities(case)
        
        # Build the system-specific prompt
        if system.lower() == 'cardiovascular' or system.lower() == 'cardiac':
            system_prompt = f"""Focus on heart sounds (S1, S2, murmurs, rubs, gallops), 
jugular venous pressure, carotid pulses, peripheral pulses, edema, and skin temperature.
For this {diagnosis} case, pay special attention to auscultation findings at standard cardiac landmarks."""
        elif system.lower() == 'respiratory' or system.lower() == 'pulmonary':
            system_prompt = f"""Focus on respiratory rate, pattern, effort, percussion notes, 
vocal fremitus, breath sounds (vesicular, bronchial, bronchovesicular), adventitious sounds (crackles, wheezes, rhonchi, rubs), 
and accessory muscle use. For this {diagnosis} case, include specific findings in all lung fields."""
        elif system.lower() == 'abdominal' or system.lower() == 'gastrointestinal':
            system_prompt = f"""Focus on inspection (contour, scars), auscultation (bowel sounds), 
percussion (tympany, dullness, fluid wave), and palpation (tenderness, masses, organomegaly, Murphy's sign, 
McBurney's point). For this {diagnosis} case, be specific about findings in all four quadrants."""
        elif system.lower() == 'neurological':
            system_prompt = f"""Focus on mental status, cranial nerves, motor function (strength, tone), 
sensory function, reflexes, coordination, and gait assessment. For this {diagnosis} case, 
include specific findings across all major neurological domains."""
        elif system.lower() == 'heent' or system.lower() == 'head':
            system_prompt = f"""Focus on head (inspection, palpation), eyes (visual acuity, fields, pupils, extraocular movements, fundi),
ears (external, tympanic membranes, hearing), nose (patency, septum, mucosa), and throat (oropharynx, tonsils). 
For this {diagnosis} case, include specific findings relevant to each component."""
        elif system.lower() == 'musculoskeletal':
            system_prompt = f"""Focus on joints (inspection, palpation, range of motion), muscles (strength, tone, bulk),
and special tests relevant to this {diagnosis}. Include findings across upper and lower extremities, spine, and any specific
areas of concern based on the symptoms."""
        elif system.lower() == 'skin':
            system_prompt = f"""Focus on skin color, texture, turgor, lesions (primary and secondary), 
rashes, and distribution patterns. For this {diagnosis} case, describe any dermatological findings 
with proper medical terminology and standard descriptors (color, shape, size, borders, etc.)."""
        else:
            system_prompt = f"Provide detailed physical examination findings for the {system} system."
        
        # Build the complete prompt
        prompt = f"""Generate physical examination findings for a {age}-year-old {gender} patient with {diagnosis}.

Patient Information:
- Presenting complaint: {presenting_complaint}
- Diagnosis: {diagnosis}
- Symptoms: {', '.join(symptoms) if symptoms else 'Not specified'}
- Comorbidities: {', '.join(comorbidities) if comorbidities else 'None'}

You are performing a {system} examination.

{system_prompt}

Create REALISTIC and MEDICALLY ACCURATE physical examination findings that would be expected in a patient with {diagnosis}. 
Include appropriate positive and negative findings that would be present in this case.
Be specific about which signs are present and which are absent.

Return the results in this JSON format:
{{
  "findings": {{
    "key_finding_1": "description",
    "key_finding_2": "description",
    ...
  }},
  "interpretation": "Brief clinical interpretation of findings",
  "references": [
    "Source 1: citation or URL",
    "Source 2: citation or URL",
    ...
  ]
}}

Use PubMed, medical journals, and clinical guidelines to ensure the physical examination findings are MEDICALLY ACCURATE and REALISTIC for this specific diagnosis.
"""
        return prompt
        
    def _extract_symptoms(self, case: Dict[str, Any]) -> list:
        """Extract symptoms from various possible formats in the case data"""
        symptoms = []
        
        # DEBUGGING: Log the case structure
        logger.info(f"Extracting symptoms from case structure")
        
        # Check for key_symptoms as a list
        if "key_symptoms" in case:
            logger.info(f"key_symptoms type: {type(case['key_symptoms'])}")
            if isinstance(case["key_symptoms"], list):
                for item in case["key_symptoms"]:
                    if isinstance(item, dict):
                        # Handle dictionary format (with system/symptom structure)
                        if "symptom" in item:
                            symptoms.append(item["symptom"])
                    elif isinstance(item, str):
                        # Handle simple string format
                        symptoms.append(item)
                    elif isinstance(item, int):
                        # Handle unexpected integer
                        logger.warning(f"Found integer in key_symptoms: {item}. Converting to string.")
                        symptoms.append(str(item))
            elif isinstance(case["key_symptoms"], dict):
                for system, symptom in case["key_symptoms"].items():
                    if symptom and symptom != "None":
                        if isinstance(symptom, str):
                            symptoms.append(f"{symptom}")
                        elif isinstance(symptom, int):
                            logger.warning(f"Found integer symptom for {system}: {symptom}. Converting to string.")
                            symptoms.append(str(symptom))
            elif isinstance(case["key_symptoms"], int):
                logger.warning(f"key_symptoms is an integer: {case['key_symptoms']}. Converting to string.")
                symptoms.append(str(case["key_symptoms"]))
        
        # Check for symptoms in presentation
        if "presentation" in case:
            presentation = case["presentation"]
            
            if isinstance(presentation, dict):
                if "classic_symptoms" in presentation:
                    if isinstance(presentation["classic_symptoms"], list):
                        for symptom in presentation["classic_symptoms"]:
                            if isinstance(symptom, str):
                                symptoms.append(symptom)
                            elif isinstance(symptom, int):
                                logger.warning(f"Found integer in classic_symptoms: {symptom}. Converting to string.")
                                symptoms.append(str(symptom))
                    elif isinstance(presentation["classic_symptoms"], str):
                        symptoms.append(presentation["classic_symptoms"])
                    elif isinstance(presentation["classic_symptoms"], int):
                        logger.warning(f"classic_symptoms is an integer: {presentation['classic_symptoms']}. Converting to string.")
                        symptoms.append(str(presentation["classic_symptoms"]))
                    
                if "description" in presentation and isinstance(presentation["description"], str):
                    symptoms.append(presentation["description"])
            elif isinstance(presentation, int):
                logger.warning(f"presentation is an integer: {presentation}. Converting to string.")
                symptoms.append(f"Presentation: {presentation}")
                    
        # Check for atypical_presentation
        if "atypical_presentation" in case:
            atypical = case["atypical_presentation"]
            if isinstance(atypical, dict):
                if "description" in atypical and isinstance(atypical["description"], str):
                    symptoms.append(atypical["description"])
            elif isinstance(atypical, int):
                logger.warning(f"atypical_presentation is an integer: {atypical}. Converting to string.")
                symptoms.append(f"Atypical presentation: {atypical}")
                    
        # Check condition description
        if "condition" in case:
            condition = case["condition"]
            if isinstance(condition, dict):
                if "description" in condition:
                    if isinstance(condition["description"], str):
                        symptoms.append(condition["description"])
                    elif isinstance(condition["description"], int):
                        logger.warning(f"condition description is an integer: {condition['description']}. Converting to string.")
                        symptoms.append(str(condition["description"]))
            elif isinstance(condition, int):
                logger.warning(f"condition is an integer: {condition}. Converting to string.")
                symptoms.append(f"Condition: {condition}")
                    
        # Check for symptoms as array directly in case
        if "symptoms" in case:
            if isinstance(case["symptoms"], list):
                for symptom in case["symptoms"]:
                    if isinstance(symptom, str):
                        symptoms.append(symptom)
                    elif isinstance(symptom, int):
                        logger.warning(f"Found integer in symptoms: {symptom}. Converting to string.")
                        symptoms.append(str(symptom))
            elif isinstance(case["symptoms"], str):
                symptoms.append(case["symptoms"])
            elif isinstance(case["symptoms"], int):
                logger.warning(f"symptoms is an integer: {case['symptoms']}. Converting to string.")
                symptoms.append(str(case["symptoms"]))
                
        # Check presenting_complaint
        if "presenting_complaint" in case:
            if isinstance(case["presenting_complaint"], str) and case["presenting_complaint"]:
                symptoms.append(case["presenting_complaint"])
            elif isinstance(case["presenting_complaint"], int):
                logger.warning(f"presenting_complaint is an integer: {case['presenting_complaint']}. Converting to string.")
                symptoms.append(f"Presenting complaint: {case['presenting_complaint']}")
                    
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

class PhysicalExamSystem:
    """
    Enhanced system for generating physical examination findings based on the patient case
    and verifying examination procedures. Now uses Perplexity AI when available for
    medically accurate findings based on current literature.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        # Initialize Perplexity client if API key is available
        self.perplexity_client = PerplexityPhysicalExamGenerator(config.perplexity_api_key) if hasattr(config, 'perplexity_api_key') and config.perplexity_api_key else None
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
        Now with enhanced medical accuracy using Perplexity AI when available.
        
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
            # Try using Perplexity AI if available
            if self.perplexity_client:
                try:
                    logger.info(f"Generating examination findings using Perplexity AI for: {system}")
                    
                    perplexity_results = self.perplexity_client.generate_exam_findings(case, system)
                    
                    # Check if we got valid results or an error
                    if "error" not in perplexity_results:
                        # Add timestamp if not present
                        if "timestamp" not in perplexity_results:
                            perplexity_results["timestamp"] = datetime.now().isoformat()
                            
                        # Cache the results
                        self.results_cache[cache_key] = perplexity_results
                        
                        return perplexity_results
                    else:
                        # Log the error but continue with OpenAI fallback
                        logger.warning(f"Perplexity generation failed: {perplexity_results.get('error')}")
                        logger.info("Falling back to OpenAI for examination findings generation")
                except Exception as e:
                    logger.error(f"Error using Perplexity for examination findings: {str(e)}")
                    logger.info("Falling back to OpenAI for examination findings generation")
            
            # Original OpenAI-based implementation (fallback)
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