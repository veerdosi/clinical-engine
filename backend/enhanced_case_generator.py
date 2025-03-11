import json
import re
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import Client  # Using the new client-based interface
from backend.config import MedicalSimConfig
from backend.case_generator import CaseParameters, CaseGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerplexityClient:
    """
    Client for interacting with Perplexity AI's API to retrieve medically accurate information.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def search_async(self, query: str, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        Perform an asynchronous search using Perplexity AI.
        
        Args:
            query: The search query
            max_tokens: Maximum number of tokens in the response
            
        Returns:
            Dict containing the search response
        """
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": "sonar",  # Using a supported model with web search capability
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a medical research assistant that retrieves detailed, accurate medical information. "
                        "When providing information, include specific details about symptoms, presentations, vital signs, "
                        "physical examination findings, lab values, and diagnostic criteria. "
                        "Always cite authoritative medical sources like guidelines, textbooks, or journal articles. "
                        "Format information in clear sections with headings for easy parsing."
                    )
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "options": {
                "search_focus": "internet"
            },
            "max_tokens": max_tokens
        }
        
        logger.debug(f"Perplexity API request payload: {json.dumps(payload)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, 
                    headers=self.headers,
                    json=payload,
                    timeout=60  # Increased timeout for thorough search
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"Perplexity API response status: {response.status}")
                    
                    if response.status != 200:
                        logger.error(f"Perplexity API error: {response.status} - {response_text[:500]}")
                        return {"error": f"Perplexity API error: {response.status}"}
                    
                    result = json.loads(response_text)
                    
                    # Extract the content from Perplexity's response
                    perplexity_content = ""
                    if "choices" in result:
                        for choice in result["choices"]:
                            msg = choice.get("message", {})
                            perplexity_content += msg.get("content", "")
                    
                    logger.info("Successfully retrieved information from Perplexity")
                    
                    return {
                        "raw_content": perplexity_content,
                        "result_found": bool(perplexity_content.strip()),
                        "query": query
                    }
        except Exception as e:
            logger.error(f"Error in Perplexity search: {str(e)}")
            return {"error": str(e)}
            
    def search(self, query: str, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        Perform a synchronous search using Perplexity AI by running the async method in an event loop.
        
        Args:
            query: The search query
            max_tokens: Maximum number of tokens in the response
            
        Returns:
            Dict containing the search response
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there is no event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        try:
            return loop.run_until_complete(self.search_async(query, max_tokens))
        except Exception as e:
            logger.error(f"Error in synchronous Perplexity search: {str(e)}")
            return {"error": str(e)}


class EnhancedCaseGenerator(CaseGenerator):
    """
    Enhanced version of CaseGenerator that uses Perplexity AI to gather medically
    accurate information before using OpenAI to structure the final case.
    """
    def __init__(self, config: MedicalSimConfig):
        super().__init__(config)
        self.perplexity_client = PerplexityClient(config.perplexity_api_key)
    
    def _generate_perplexity_query(self, params: CaseParameters) -> str:
        """
        Generate a query for Perplexity based on the case parameters.
        
        Args:
            params: The case parameters
            
        Returns:
            A query string to send to Perplexity
        """
        difficulty_descriptions = {
            "easy": "common condition with typical presentation",
            "moderate": "condition with atypical presentation or comorbidities",
            "hard": "rare condition or one with confounding factors"
        }
        
        difficulty_desc = difficulty_descriptions.get(params.difficulty, "condition")
        
        # Create a specialized prompt based on specialty
        if params.specialty == "Cardiology":
            query = f"""
I need detailed medical information for creating a realistic cardiac patient case for medical education. 
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide information about a {difficulty_desc} in the field of cardiology.

Specifically, include:
1. The specific cardiac diagnosis
2. 3-5 key cardiac and associated symptoms (including character, location, duration, precipitating/alleviating factors)
3. Expected vital signs (HR, BP, RR, O2 sat, temperature)
4. Pertinent physical examination findings (heart sounds, murmurs, lung sounds, edema, etc.)
5. Relevant past medical history and risk factors
6. Key ECG findings
7. Important cardiac biomarkers and their expected values
8. Expected findings on echocardiogram or other cardiac imaging
9. 1-2 red herring symptoms that might confuse diagnosis
10. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite cardiology guidelines or literature.
Format your response in a clear, structured manner that separates each category of information.
"""
        elif params.specialty == "Neurology":
            query = f"""
I need detailed medical information for creating a realistic neurology patient case for medical education. 
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide information about a {difficulty_desc} in the field of neurology.

Specifically, include:
1. The specific neurological diagnosis
2. 3-5 key neurological symptoms (including onset, progression, character, location)
3. Expected vital signs
4. Pertinent neurological examination findings (mental status, cranial nerves, motor/sensory function, reflexes, coordination, gait)
5. Relevant past medical history and risk factors
6. Key findings on neuroimaging (CT, MRI)
7. Important lab values if relevant (CSF analysis, etc.)
8. 1-2 red herring symptoms that might confuse diagnosis
9. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite neurology guidelines or literature.
Format your response in a clear, structured manner that separates each category of information.
"""
        elif params.specialty == "Pulmonology":
            query = f"""
I need detailed medical information for creating a realistic pulmonology patient case for medical education. 
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide information about a {difficulty_desc} in the field of pulmonology.

Specifically, include:
1. The specific pulmonary diagnosis
2. 3-5 key respiratory symptoms (including character of cough, sputum, dyspnea, chest pain)
3. Expected vital signs with emphasis on respiratory rate and oxygen saturation
4. Pertinent physical examination findings (respiratory inspection, palpation, percussion, auscultation)
5. Relevant past medical history and risk factors (smoking history, occupational exposures)
6. Key findings on chest X-ray or CT
7. Important pulmonary function test results
8. Arterial blood gas values if relevant
9. 1-2 red herring symptoms that might confuse diagnosis
10. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite pulmonology guidelines or literature.
Format your response in a clear, structured manner that separates each category of information.
"""
        elif params.specialty == "Emergency Medicine":
            query = f"""
I need detailed medical information for creating a realistic emergency medicine patient case for medical education.
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide information about a {difficulty_desc} commonly seen in emergency departments.

Specifically, include:
1. The specific emergency diagnosis
2. 3-5 key symptoms and their presentation (onset, progression, severity)
3. Expected vital signs (HR, BP, RR, O2 sat, temperature) and how they might change during the emergency
4. Pertinent physical examination findings
5. Relevant past medical history and risk factors
6. Key laboratory findings and point-of-care test results
7. Important imaging findings if applicable
8. Expected clinical course and time-sensitive aspects of management
9. 1-2 red herring symptoms or findings that might confuse diagnosis
10. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite emergency medicine guidelines or literature.
Format your response in a clear, structured manner that separates each category of information.
"""
        elif params.specialty == "Internal Medicine":
            query = f"""
I need detailed medical information for creating a realistic internal medicine patient case for medical education.
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide information about a {difficulty_desc} in general internal medicine.

Specifically, include:
1. The specific medical diagnosis
2. 3-5 key symptoms and their presentation (character, duration, exacerbating/alleviating factors)
3. Expected vital signs
4. Pertinent physical examination findings across relevant body systems
5. Relevant past medical history, medications, and risk factors
6. Key laboratory findings and their expected values
7. Important imaging or diagnostic test findings if applicable
8. Differential diagnoses that should be considered
9. 1-2 red herring symptoms or findings that might confuse diagnosis
10. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite internal medicine guidelines or literature.
Format your response in a clear, structured manner that separates each category of information.
"""
        else:
            # Generic query for other specialties
            query = f"""
I need detailed medical information for creating a realistic patient case for medical education in {params.specialty}. 
The case should be of {params.difficulty} difficulty ({difficulty_desc}).

Please provide:

1. A {difficulty_desc} presentation of a condition in {params.specialty} field, including:
   - The specific condition/diagnosis
   - 3-5 key symptoms and their typical presentation in patients
   - Typical vital sign abnormalities for this condition
   - Key physical examination findings
   - 2-3 relevant comorbidities or past medical history that might accompany this condition
   - Any medication allergies that would be relevant to treatment
   - Important negative findings (symptoms typically asked about but not present in this condition)

2. Realistic lab values and imaging findings that would be expected

3. Demographics where this condition is commonly found (age range, gender predisposition if any)

Please cite reputable medical sources or guidelines in your response.
Format your response in a clear, structured manner that separates each category of information.
"""
        
        return query
    
    def _parse_perplexity_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the response from Perplexity AI.
        
        Args:
            response: The Perplexity API response
            
        Returns:
            Dict containing extracted medical information
        """
        extracted_info = {}
        
        try:
            if "error" in response:
                logger.error(f"Error in Perplexity response: {response['error']}")
                return {"error": response["error"]}
                
            content = response.get("raw_content", "")
            if not content:
                logger.error("No content in Perplexity response")
                return {"error": "No content in Perplexity response"}
            
            # Extract diagnosis
            diagnosis_match = re.search(r"(?:diagnosis|condition):\s*(.*?)(?:\n|$)", content, re.IGNORECASE)
            if diagnosis_match:
                extracted_info["diagnosis"] = diagnosis_match.group(1).strip()
            
            # Extract symptoms
            symptoms = []
            symptoms_section = re.search(r"(?:symptoms|key symptoms):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            if symptoms_section:
                symptom_text = symptoms_section.group(1)
                # Look for bullet points or numbered symptoms
                symptom_matches = re.findall(r"(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?:\n|$)", symptom_text)
                if symptom_matches:
                    symptoms.extend([s.strip() for s in symptom_matches if s.strip()])
                else:
                    # If no bullets found, try to split on commas or newlines
                    symptom_parts = re.split(r",|\n", symptom_text)
                    symptoms.extend([s.strip() for s in symptom_parts if s.strip()])
            
            extracted_info["symptoms"] = symptoms
            
            # Extract vital signs
            vitals = {}
            vitals_section = re.search(r"(?:vital signs|vitals):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            if vitals_section:
                vitals_text = vitals_section.group(1)
                
                # Extract BP
                bp_match = re.search(r"(?:BP|blood pressure):\s*(\d+/\d+)(?:\s*mmHg)?", vitals_text, re.IGNORECASE)
                if bp_match:
                    vitals["BP"] = f"{bp_match.group(1)} mmHg"
                
                # Extract HR
                hr_match = re.search(r"(?:HR|heart rate|pulse):\s*(\d+)(?:\s*bpm)?", vitals_text, re.IGNORECASE)
                if hr_match:
                    vitals["HR"] = f"{hr_match.group(1)} bpm"
                
                # Extract RR
                rr_match = re.search(r"(?:RR|respiratory rate):\s*(\d+)(?:\s*breaths/min)?", vitals_text, re.IGNORECASE)
                if rr_match:
                    vitals["RR"] = f"{rr_match.group(1)} breaths/min"
                
                # Extract Temp
                temp_match = re.search(r"(?:temperature|temp):\s*([\d\.]+)(?:\s*[°C|°F])?", vitals_text, re.IGNORECASE)
                if temp_match:
                    # Assume Celsius if not specified
                    vitals["Temp"] = f"{temp_match.group(1)} °C"
                
                # Extract SpO2
                spo2_match = re.search(r"(?:SpO2|O2 sat|oxygen saturation):\s*(\d+)(?:\s*%)?", vitals_text, re.IGNORECASE)
                if spo2_match:
                    vitals["SpO2"] = f"{spo2_match.group(1)}%"
            
            extracted_info["vitals"] = vitals
            
            # Extract demographics
            demo_section = re.search(r"(?:demographics|patient profile):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            demographics = {}
            
            if demo_section:
                demo_text = demo_section.group(1)
                
                # Extract age
                age_match = re.search(r"(?:age|aged):\s*(\d+)(?:\s*years)?", demo_text, re.IGNORECASE)
                if age_match:
                    demographics["age"] = age_match.group(1)
                else:
                    # Try to find age range and pick a value
                    age_range_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)(?:\s*years)?", demo_text, re.IGNORECASE)
                    if age_range_match:
                        min_age = int(age_range_match.group(1))
                        max_age = int(age_range_match.group(2))
                        import random
                        demographics["age"] = str(random.randint(min_age, max_age))
                
                # Extract gender
                gender_match = re.search(r"(?:gender|sex):\s*(male|female)", demo_text, re.IGNORECASE)
                if gender_match:
                    demographics["gender"] = gender_match.group(1).capitalize()
            
            extracted_info["demographics"] = demographics
            
            # Extract past medical history/comorbidities
            pmh = []
            pmh_section = re.search(r"(?:past medical history|comorbidities):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            if pmh_section:
                pmh_text = pmh_section.group(1)
                # Look for bullet points or numbered items
                pmh_matches = re.findall(r"(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?:\n|$)", pmh_text)
                if pmh_matches:
                    pmh.extend([p.strip() for p in pmh_matches if p.strip()])
                else:
                    # If no bullets found, try to split on commas or newlines
                    pmh_parts = re.split(r",|\n", pmh_text)
                    pmh.extend([p.strip() for p in pmh_parts if p.strip()])
            
            extracted_info["past_medical_conditions"] = pmh
            
            # Extract physical exam findings
            exam_findings = {}
            exam_section = re.search(r"(?:physical examination|examination findings):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            if exam_section:
                exam_text = exam_section.group(1)
                # Check for common exam systems
                systems = ["cardiovascular", "respiratory", "neurological", "abdominal", "musculoskeletal", "heent"]
                for system in systems:
                    system_match = re.search(f"{system}[^\n]*:(.*?)(?:\n(?:[A-Za-z]+[^\n]*:|\d)|\Z)", exam_text, re.IGNORECASE | re.DOTALL)
                    if system_match:
                        exam_findings[system] = system_match.group(1).strip()
            
            extracted_info["examination_findings"] = exam_findings
            
            # Extract lab/imaging findings for critical tests
            critical_tests = []
            tests_section = re.search(r"(?:lab values|lab tests|laboratory findings|imaging findings):(.*?)(?:\n\d|\n[A-Z])", content, re.IGNORECASE | re.DOTALL)
            if tests_section:
                tests_text = tests_section.group(1)
                
                # Look for common test types
                test_patterns = [
                    r"(?:CBC|complete blood count)",
                    r"(?:CMP|comprehensive metabolic panel)",
                    r"(?:BMP|basic metabolic panel)",
                    r"(?:Troponin|cardiac enzymes)",
                    r"(?:ECG|EKG|electrocardiogram)",
                    r"(?:CXR|chest x-ray)",
                    r"(?:CT|computed tomography)",
                    r"(?:MRI|magnetic resonance imaging)"
                ]
                
                for pattern in test_patterns:
                    if re.search(pattern, tests_text, re.IGNORECASE):
                        test_name = re.search(pattern, tests_text, re.IGNORECASE).group(0)
                        critical_tests.append(test_name)
            
            extracted_info["critical_tests"] = critical_tests
            
            # Extract citations/sources if available
            citations = []
            citations_match = re.findall(r"(?:references|sources|citations):(.*?)(?:\n\d|\n[A-Z]|\Z)", content, re.IGNORECASE | re.DOTALL)
            if citations_match:
                citations_text = citations_match[0]
                citation_lines = re.findall(r"(?:^|\n)(?:\d+\.|\*|\-)\s*(.*?)(?:\n|$)", citations_text)
                if citation_lines:
                    citations.extend([c.strip() for c in citation_lines if c.strip()])
            
            extracted_info["sources"] = citations

            # Store the raw Perplexity content for reference
            extracted_info["raw_perplexity_content"] = content
            
        except Exception as e:
            logger.error(f"Error parsing Perplexity response: {str(e)}")
            logger.debug(f"Response content: {response}")
            return {"error": f"Error parsing response: {str(e)}"}
        
        return extracted_info
    
    def generate_case(self, params: CaseParameters) -> Dict:
        """
        Generates a case using Perplexity AI for medical information and GPT for formatting.
        
        Args:
            params: Parameters for case generation
            
        Returns:
            Dict representing the generated case
        """
        try:
            logger.info(f"Generating {params.difficulty} case for {params.specialty}")
            
            # Step 1: Generate query for Perplexity based on parameters
            perplexity_query = self._generate_perplexity_query(params)
            logger.info("Querying Perplexity AI for medical information")
            
            # Step 2: Get information from Perplexity
            perplexity_response = self.perplexity_client.search(perplexity_query)
            
            # Step 3: Parse the Perplexity response to extract structured medical info
            medical_info = self._parse_perplexity_response(perplexity_response)
            
            # If there was an error in the Perplexity response, log and fall back to original generator
            if "error" in medical_info:
                logger.error(f"Error from Perplexity: {medical_info['error']}")
                logger.info("Falling back to original case generator")
                return super().generate_case(params)
                
            logger.info(f"Extracted medical information for: {medical_info.get('diagnosis', 'Unknown diagnosis')}")
            
            # Step 4: Use OpenAI to structure the final case based on Perplexity data
            medical_info_json = json.dumps(medical_info, indent=2)
            system_prompt = f"""You are a medical case generator. Create a {params.difficulty} {params.specialty} case based on the provided medical information.

Format the case as a JSON object with these fields:
- name: Generate a realistic patient name
- age: Use the provided age or generate appropriate age if not provided
- gender: Use the provided gender or generate appropriate gender if not provided
- diagnosis: Use the exact diagnosis provided
- presenting_complaint: A brief statement of why the patient is seeking care
- symptoms: An array of symptoms reported by the patient
- vitals: Object with BP, HR, RR, Temp, SpO2
- past_medical_conditions: Array of previous conditions
- medication_allergies: Array of medication allergies (can be generated if not provided)
- negative_findings: Array of important negative findings
- critical_tests: Array of tests that should be ordered to diagnose this condition
- key_findings: Array of the most important symptoms/signs for diagnosis

The JSON must be properly formatted with no trailing commas. Format all string values with proper quotes, especially values like "110 bpm" or "22 breaths/min".
"""
            
            try:
                logger.info("Sending structured medical info to OpenAI for case formatting")
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create a detailed case based on this medical information: {medical_info_json}"}
                    ],
                    temperature=0.5 if params.difficulty == "hard" else 0.3,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content.strip()
                
                # Clean up the response
                content = self._clean_json_response(content)
                
                try:
                    case = json.loads(content)
                except json.JSONDecodeError as e:
                    # If still failing, make one more attempt with a more aggressive cleanup
                    content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
                    try:
                        case = json.loads(content)
                    except json.JSONDecodeError:
                        raise ValueError(f"Failed to parse JSON response: {content}")
                
                # Add specialty and difficulty to the case
                case["specialty"] = params.specialty
                case["difficulty"] = params.difficulty
                
                # Add information about the sources if available
                if "sources" in medical_info and medical_info["sources"]:
                    case["medical_sources"] = medical_info["sources"]
                
                return case
                
            except Exception as e:
                logger.error(f"Error in OpenAI case formatting: {str(e)}")
                
                # Fallback to the original case generator if OpenAI formatting fails
                logger.info("Falling back to original case generator")
                return super().generate_case(params)
                
        except Exception as e:
            logger.error(f"Error in enhanced case generation: {str(e)}")
            
            # Fallback to the original case generator if Perplexity fails
            logger.info("Falling back to original case generator due to Perplexity error")
            return super().generate_case(params)


# Update the MedicalSimConfig class to include Perplexity API key
def update_config_class():
    """
    Updates the MedicalSimConfig class definition to include Perplexity API key.
    This is a patch that should be applied to config.py.
    """
    config_update = """
class MedicalSimConfig:
    def __init__(self,
                 openai_key: str = None,
                 elevenlabs_key: str = None,
                 replicate_key: str = None,
                 perplexity_key: str = None,
                 default_voice_id: str = "EXAVITQu4vr4xnSDxMaL",
                 voice_settings: dict = None):
        \"\"\"
        Initialize medical simulation configuration.
        \"\"\"
        # Validate and set OpenAI API key
        self.openai_api_key = openai_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.openai_api_key

        # Validate Eleven Labs API key
        self.elevenlabs_key = elevenlabs_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.elevenlabs_key:
            raise ValueError("Eleven Labs API key is required")
        self.default_voice_id = default_voice_id
        self.voice_settings = voice_settings or {
            "stability": 0.5,
            "similarity_boost": 0.8
        }

        # Validate Replicate API key
        self.replicate_key = replicate_key or os.getenv("REPLICATE_API_KEY")
        self._validate_replicate_key()
        self._validate_elevenlabs_key()
        
        # Set Perplexity API key
        self.perplexity_api_key = perplexity_key or os.getenv("PERPLEXITY_API_KEY")
"""
    
    return config_update


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Example implementation
    config = MedicalSimConfig()
    generator = EnhancedCaseGenerator(config)
    params = CaseParameters("Cardiology", "moderate")
    case = generator.generate_case(params)
    
    print(json.dumps(case, indent=2))