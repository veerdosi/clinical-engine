import json
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from backend.config import MedicalSimConfig
from backend.case_generator import CaseParameters, CaseGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_safe_type(value, expected_type, default_value=None, name=None):
    """
    Utility function to ensure a value is of the expected type.
    
    Args:
        value: The value to check
        expected_type: The expected type (list, dict, etc.)
        default_value: The default value to use if conversion fails
        name: Name of the field for logging purposes
        
    Returns:
        The value converted to the expected type, or the default value
    """
    field_name = name or "value"
    
    # If value is already the expected type, return it
    if isinstance(value, expected_type):
        return value
        
    # If value is None, return default
    if value is None:
        return default_value
        
    # Try to convert based on expected type
    try:
        if expected_type == list:
            if isinstance(value, str):
                return [value]
            elif isinstance(value, dict):
                return [f"{k}: {v}" for k, v in value.items()]
            elif isinstance(value, int):
                logger.warning(f"{field_name} is an integer: {value}. Converting to string in list.")
                return [str(value)]
            else:
                return list(value)  # Attempt to convert to list
        elif expected_type == dict:
            if isinstance(value, str):
                return {value: True}
            elif isinstance(value, int):
                logger.warning(f"{field_name} is an integer: {value}. Converting to empty dict.")
                return {}
            else:
                return dict(value)  # Attempt to convert to dict
        elif expected_type == str:
            return str(value)
        elif expected_type == int:
            return int(value)
        else:
            logger.warning(f"Unsupported conversion to {expected_type.__name__} for {field_name}")
            return default_value
    except Exception as e:
        logger.warning(f"Error converting {field_name} to {expected_type.__name__}: {str(e)}")
        return default_value

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
            "model": "sonar",  # Using a supported model with web search
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a medical case generator assistant. Your task is to create a realistic medical case based on the specialty and difficulty provided."
                        "Search for medical information and return a JSON object with the precise structure defined below."
                        "\n\nEXTREMELY IMPORTANT: Respond ONLY with a valid JSON object and nothing else. Do NOT include any text before or after the JSON."
                        "Do NOT use markdown formatting, explanations, or other text. The response must start with '{' and end with '}'."
                        "The response must be parseable by JSON.parse() with no modifications needed."
                        "\n\nJSON structure:\n"
                        "{\n"
                        "  \"name\": \"string (realistic patient name)\",\n"
                        "  \"age\": number (appropriate for the condition),\n"
                        "  \"gender\": \"string (Male or Female)\",\n"
                        "  \"diagnosis\": \"string (medical diagnosis based on your search)\",\n"
                        "  \"presenting_complaint\": \"string (brief statement of chief complaint)\",\n"
                        "  \"symptoms\": [\"array\", \"of\", \"symptom\", \"strings\"],\n"
                        "  \"vitals\": {\n"
                        "    \"BP\": \"string (e.g., 120/80 mmHg)\",\n"
                        "    \"HR\": \"string (e.g., 72 bpm)\",\n"
                        "    \"RR\": \"string (e.g., 16 breaths/min)\",\n"
                        "    \"Temp\": \"string (e.g., 37.0 °C or 98.6 °F)\",\n"
                        "    \"SpO2\": \"string (e.g., 98%)\"\n"
                        "  },\n"
                        "  \"vitals_range\": {\n"
                        "    \"BP_systolic\": { \"min\": number, \"max\": number },\n"
                        "    \"BP_diastolic\": { \"min\": number, \"max\": number },\n"
                        "    \"HR\": { \"min\": number, \"max\": number },\n"
                        "    \"RR\": { \"min\": number, \"max\": number },\n"
                        "    \"Temp\": { \"min\": number, \"max\": number },\n"
                        "    \"SpO2\": { \"min\": number, \"max\": number }\n"
                        "  },\n"
                        "  \"past_medical_conditions\": [\"array\", \"of\", \"condition\", \"strings\"],\n"
                        "  \"medication_allergies\": [\"array\", \"of\", \"allergy\", \"strings\"],\n"
                        "  \"negative_findings\": [\"array\", \"of\", \"string\"],\n"
                        "  \"critical_tests\": [\"array\", \"of\", \"necessary\", \"test\", \"strings\"],\n"
                        "  \"key_findings\": [\"array\", \"of\", \"important\", \"clinical\", \"findings\"],\n"
                        "  \"sources\": [\"array\", \"of\", \"medical\", \"sources\", \"referenced\"]\n"
                        "}"
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
            "max_tokens": max_tokens,
            "temperature": 0.5  # Use higher temperature for more variety in cases
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
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logger.info("Successfully retrieved information from Perplexity")
                        logger.debug(f"Raw content: {content[:500]}...")
                        
                        try:
                            # Find JSON in the response if there's any text surrounding it
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            
                            if json_start >= 0 and json_end > json_start:
                                json_content = content[json_start:json_end]
                                logger.debug(f"Extracted JSON: {json_content[:500]}...")
                                case_data = json.loads(json_content)
                                return case_data
                            else:
                                # If no JSON found, log the full content and return error
                                logger.error(f"No valid JSON found in response. Content: {content}")
                                return {"error": "No valid JSON found in response"}
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON from Perplexity: {str(e)}")
                            logger.debug(f"Raw content: {content}")
                            return {"error": f"Invalid JSON in response: {str(e)}"}
                    else:
                        logger.error("No content in Perplexity response")
                        return {"error": "No content in Perplexity response"}
        except Exception as e:
            error_details = str(e)
            logger.error(f"Error in Perplexity search: {error_details}")
            return {"error": f"Perplexity API error: {error_details}"}
            

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
            result = loop.run_until_complete(self.search_async(query, max_tokens))
            
            # DEBUGGING: Add these lines to inspect the result format
            logger.info(f"Perplexity result type: {type(result)}")
            if isinstance(result, dict):
                for key, value in result.items():
                    logger.info(f"Result field '{key}' is type: {type(value)}")
                    
                    # Check for problematic integer values
                    if isinstance(value, int) and key not in ['age']: # Age can be an integer
                        logger.warning(f"Integer value found in field '{key}': {value}")
            
            # Make sure we always return a dictionary, even if we get something unexpected
            if not isinstance(result, dict):
                logger.warning(f"Unexpected result type from Perplexity: {type(result)}. Converting to dict.")
                try:
                    if isinstance(result, str):
                        # Try to parse string as JSON
                        import json
                        return json.loads(result)
                    elif isinstance(result, list):
                        # If it's a list, convert to a dict with standard fields
                        return {"diagnosis": "Unknown", "symptoms": result}
                    elif isinstance(result, int):
                        logger.warning(f"Received integer result from Perplexity: {result}. Converting to dict.")
                        return {"diagnosis": f"Unknown condition (error code: {result})", 
                                "symptoms": [], 
                                "vitals": {}, 
                                "past_medical_conditions": [],
                                "medication_allergies": [],
                                "negative_findings": [],
                                "critical_tests": []}
                    else:
                        # For any other type, return a default case structure
                        return {"diagnosis": f"Unknown condition (unexpected result type)", 
                            "symptoms": [], 
                            "vitals": {}, 
                            "past_medical_conditions": [],
                            "medication_allergies": [],
                            "negative_findings": [],
                            "critical_tests": []}
                except Exception as e:
                    logger.error(f"Error converting Perplexity result: {str(e)}")
                    return {"error": f"Perplexity result conversion error: {str(e)}"}
            
            # Sanitize and validate results
            for key, value in list(result.items()):
                # Handle integer values in most fields
                if isinstance(value, int) and key not in ['age']:
                    logger.warning(f"Integer value found in field '{key}': {value}. Converting to string.")
                    result[key] = str(value)
                    
            # Ensure critical fields exist and have correct types
            result['symptoms'] = ensure_safe_type(result.get('symptoms', []), list, [], 'symptoms')
            result['past_medical_conditions'] = ensure_safe_type(result.get('past_medical_conditions', []), list, [], 'past_medical_conditions')
            result['medication_allergies'] = ensure_safe_type(result.get('medication_allergies', []), list, [], 'medication_allergies')
            result['negative_findings'] = ensure_safe_type(result.get('negative_findings', []), list, [], 'negative_findings')
            result['critical_tests'] = ensure_safe_type(result.get('critical_tests', []), list, [], 'critical_tests')
            result['key_findings'] = ensure_safe_type(result.get('key_findings', []), list, [], 'key_findings')
            result['vitals'] = ensure_safe_type(result.get('vitals', {}), dict, {}, 'vitals')
            
            return result
        except Exception as e:
            error_details = str(e)
            logger.error(f"Error in synchronous Perplexity search: {error_details}")
            return {"error": f"Perplexity API error: {error_details}"}

class EnhancedCaseGenerator(CaseGenerator):
    """
    Enhanced version of CaseGenerator that uses Perplexity AI to gather medically
    accurate information and return a structured JSON case directly.
    """
    def __init__(self, config: MedicalSimConfig):
        super().__init__(config)
        self.perplexity_client = PerplexityClient(config.perplexity_api_key)

    def _process_vitals_ranges(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process vitals range data to ensure it's properly formatted.
        
        Args:
            case_data: The case data from Perplexity
            
        Returns:
            The updated case data with properly formatted vitals ranges
        """
        logger.info("Processing vitals ranges")
        
        # Check if vitals_range exists and is a valid type
        if "vitals_range" in case_data:
            case_data["vitals_range"] = ensure_safe_type(case_data["vitals_range"], dict, {}, 'vitals_range')
            
            # Process each field to ensure it's properly formatted
            for key, value in list(case_data["vitals_range"].items()):
                if isinstance(value, int):
                    logger.warning(f"vitals_range.{key} is an integer: {value}. Converting to dict.")
                    case_data["vitals_range"][key] = {"min": value-10, "max": value+10}
                elif not isinstance(value, dict):
                    logger.warning(f"Unexpected vitals_range.{key} type: {type(value)}. Removing.")
                    case_data["vitals_range"].pop(key, None)
        
        # Ensure "vitals" is a dictionary, not an integer
        if "vitals" in case_data:
            case_data["vitals"] = ensure_safe_type(case_data["vitals"], dict, {
                "HR": "70 bpm",
                "BP": "120/80 mmHg",
                "RR": "16 breaths/min",
                "Temp": "37.0 °C",
                "SpO2": "98%"
            }, 'vitals')
            
            # Ensure vital fields are strings, not integers
            for key, value in list(case_data["vitals"].items()):
                if isinstance(value, int):
                    logger.warning(f"vitals.{key} is an integer: {value}. Converting to string.")
                    if key == "HR":
                        case_data["vitals"][key] = f"{value} bpm"
                    elif key == "BP":
                        case_data["vitals"][key] = f"{value}/80 mmHg"  # Default diastolic
                    elif key == "RR":
                        case_data["vitals"][key] = f"{value} breaths/min"
                    elif key == "Temp":
                        case_data["vitals"][key] = f"{value} °C"
                    elif key == "SpO2":
                        case_data["vitals"][key] = f"{value}%"
                    elif key == "Pain":
                        case_data["vitals"][key] = f"{value}/10"
                    else:
                        case_data["vitals"][key] = str(value)
        
        return case_data
    
    def _generate_perplexity_query(self, params: CaseParameters) -> str:
        """
        Generate a query for Perplexity based on the case parameters.
        
        Args:
            params: The case parameters
            
        Returns:
            A query string to send to Perplexity
        """
        # Add a timestamp to ensure uniqueness in each query
        import time
        timestamp = time.time()
        seed = int(timestamp % 10000)  # Create a seed from current timestamp
        difficulty_descriptions = {
            "easy": "common condition with typical presentation",
            "moderate": "condition with atypical presentation or comorbidities",
            "hard": "rare condition or one with confounding factors"
        }
        
        difficulty_desc = difficulty_descriptions.get(params.difficulty, "condition")
        
        query = f"""
    Generate a realistic patient case for medical education in {params.specialty}. 
    The case should be of {params.difficulty} difficulty ({difficulty_desc}).
    Use randomization seed: {seed} (This is to ensure a unique case is generated each time).

    Create a {difficulty_desc} in the {params.specialty} field. The case should include appropriate:
    - Specific diagnosis within this specialty
    - Key symptoms and their presentation 
    - Vital signs with realistic RANGES for this condition (not just single values)
    - Pertinent physical examination findings
    - Relevant past medical history and risk factors
    - Critical tests and expected findings
    - Demographics appropriate for this condition

    IMPORTANT: For vital signs, provide realistic ranges that would be seen in this condition:
    - Heart rate range (formatted as MIN_HR-MAX_HR bpm, appropriate for this condition)
    - Blood pressure range (formatted as MIN_SYSTOLIC-MAX_SYSTOLIC/MIN_DIASTOLIC-MAX_DIASTOLIC mmHg, appropriate for this condition)
    - Respiratory rate range (formatetd as MIN_RR-MAX_RR breaths/min, appropriate for this condition)
    - Temperature range (formatted as MIN_TEMP-MAX_TEMP °C, appropriate for this condition)
    - Oxygen saturation range (formatted as MIN_SPO2-MAX_SPO2%, appropriate for this condition)

    IMPORTANT: Include a "Pain" field directly in the vitals object with a value on a scale of 0-10 representing the patient's self-reported pain level for this condition.

    IMPORTANT: Include a "pain_description" field in the main case object with details about the character, location, and pattern of pain relevant to this specialty condition.

    IMPORTANT: Include a "recommended_physical_exams" field with an array of specific physical examinations that are indicated for this case. 
    For each examination, provide:
    - Name of the examination (specific type of assessment relevant to the specialty)
    - Clinical significance (why this exam is important for this case)
    - Expected findings (what a clinician would likely observe in this patient)

    Be sure to include "Pain Assessment" as one of the recommended physical exams, using the 0-10 Numeric Rating Scale and including details appropriate to this specialty.

    Using these ranges will enable dynamic visualization of the patient's status over time.

    Base your case on evidence-based medical information and include citations from relevant medical literature.
    Return ONLY a valid JSON object as specified, nothing else.
    """
        # If we have conditions to avoid, add them to the query
        if hasattr(params, 'avoid_conditions') and params.avoid_conditions:
            avoid_str = ", ".join(params.avoid_conditions)
            query += f"\n\nIMPORTANT: Do NOT generate any of these diagnoses: {avoid_str}"
        
        return query

    def generate_case(self, params: CaseParameters) -> Dict:
        """
        Generates a case using Perplexity AI for medical information in JSON format.
        
        Args:
            params: Parameters for case generation
            
        Returns:
            Dict representing the generated case
        """
        # Add variation by supporting a list of conditions to avoid
        avoid_conditions = getattr(params, 'avoid_conditions', [])
        try:
            logger.info(f"Generating {params.difficulty} case for {params.specialty}")
            
            # Verify API key is set
            if not self.perplexity_client.api_key:
                logger.error("Perplexity API key not set")
                return super().generate_case(params)
                
            # Generate query for Perplexity based on parameters
            perplexity_query = self._generate_perplexity_query(params)
            
            # If we have conditions to avoid, add them to the query
            if avoid_conditions:
                avoid_str = ", ".join(avoid_conditions)
                perplexity_query += f"\n\nIMPORTANT: Do NOT generate any of these diagnoses: {avoid_str}"
                
            logger.info("Querying Perplexity AI for medical information")
            
            # Get information from Perplexity in JSON format
            case_data = self.perplexity_client.search(perplexity_query)
            
            # If there was an error in the Perplexity response, log and fall back to original generator
            if "error" in case_data:
                logger.error(f"Error from Perplexity: {case_data['error']}")
                logger.info("Falling back to original case generator")
                return super().generate_case(params)
            
            # Add required specialty and difficulty to the case
            case_data["specialty"] = params.specialty
            case_data["difficulty"] = params.difficulty
            
            # Add some standard expected fields if missing
            if "id" not in case_data:
                case_data["id"] = f"case_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
            if "created_at" not in case_data:
                case_data["created_at"] = datetime.now().isoformat()
                
            # Set the expected_diagnosis field for compatibility
            if "diagnosis" in case_data and "expected_diagnosis" not in case_data:
                case_data["expected_diagnosis"] = case_data["diagnosis"]
                
            # Update vitals format for compatibility with original format
            if "vitals_range" in case_data:
                case_data["vital_signs"] = case_data.get("vitals", {})
            
            # Process pain information
            import re
            
            # 1. Ensure pain score is in vitals
            if "vitals" in case_data and "Pain" not in case_data["vitals"] and "pain_description" in case_data:
                # Try to extract numeric pain score from description
                pain_match = re.search(r'(\d+)/10', case_data["pain_description"])
                if pain_match:
                    case_data["vitals"]["Pain"] = f"{pain_match.group(1)}/10"
                    # Also add to vital_signs for compatibility
                    if "vital_signs" in case_data:
                        case_data["vital_signs"]["Pain"] = f"{pain_match.group(1)}/10"
            
            # Process vitals ranges to ensure proper format
            case_data = self._process_vitals_ranges(case_data)
            
            # Ensure all list fields have correct types
            list_fields = ["symptoms", "past_medical_conditions", "medication_allergies", 
                        "negative_findings", "critical_tests", "key_findings"]
                        
            for field in list_fields:
                default_value = []
                case_data[field] = ensure_safe_type(case_data.get(field, default_value), list, default_value, field)
            
            # 2. Make sure pain is in symptoms if it's significant (>3/10)
            if "vitals" in case_data and "Pain" in case_data["vitals"]:
                pain_score = 0
                try:
                    # Extract just the numeric value
                    pain_text = case_data["vitals"]["Pain"]
                    pain_match = re.search(r'(\d+)', pain_text)
                    if pain_match:
                        pain_score = int(pain_match.group(1))
                except Exception as e:
                    logger.warning(f"Error parsing pain score: {str(e)}")
                    
                # If pain is significant and not already in symptoms, add it
                if pain_score > 3 and "symptoms" in case_data:
                    pain_description = case_data.get("pain_description", "Pain")
                    has_pain_symptom = False
                    
                    # Check if pain is already listed in symptoms
                    for symptom in case_data["symptoms"]:
                        if isinstance(symptom, str) and "pain" in symptom.lower():
                            has_pain_symptom = True
                            break
                            
                    if not has_pain_symptom:
                        # Add a simplified version of the pain description to symptoms
                        simple_pain = "Pain"
                        if "pain_description" in case_data:
                            # Try to extract a simpler version (first part only)
                            parts = case_data["pain_description"].split(',', 1)
                            if parts:
                                simple_pain = parts[0]
                        case_data["symptoms"].append(simple_pain)
            
            # Make sure vital signs are properly formatted
            if "vitals" in case_data:
                vitals = case_data["vitals"]
                
                # Ensure BP has mmHg
                if "BP" in vitals and isinstance(vitals["BP"], str) and "mmHg" not in vitals["BP"]:
                    vitals["BP"] = f"{vitals['BP']} mmHg"
                
                # Ensure HR has bpm
                if "HR" in vitals and isinstance(vitals["HR"], str) and "bpm" not in vitals["HR"]:
                    vitals["HR"] = f"{vitals['HR']} bpm"
                
                # Ensure RR has breaths/min
                if "RR" in vitals and isinstance(vitals["RR"], str) and "breaths" not in vitals["RR"]:
                    vitals["RR"] = f"{vitals['RR']} breaths/min"
                
                # Ensure Temp has °C or °F
                if "Temp" in vitals and isinstance(vitals["Temp"], str) and "°" not in vitals["Temp"]:
                    # Assume Celsius if value is low, Fahrenheit if high
                    temp_value = 0
                    try:
                        temp_value = float(vitals["Temp"].replace("°C", "").replace("°F", "").strip())
                    except (ValueError, TypeError):
                        # If conversion fails, use a default temperature
                        temp_value = 37.0
                        
                    if temp_value < 50:  # Likely Celsius
                        vitals["Temp"] = f"{temp_value} °C"
                    else:  # Likely Fahrenheit
                        vitals["Temp"] = f"{temp_value} °F"
                        
                # Ensure SpO2 has %
                if "SpO2" in vitals and isinstance(vitals["SpO2"], str) and "%" not in vitals["SpO2"]:
                    vitals["SpO2"] = f"{vitals['SpO2']}%"
                
                # Ensure Pain has /10 format if present
                if "Pain" in vitals and isinstance(vitals["Pain"], str) and "/10" not in vitals["Pain"]:
                    vitals["Pain"] = f"{vitals['Pain']}/10"
                
            logger.info(f"Successfully generated case: {case_data.get('diagnosis', 'Unknown diagnosis')}")
            return case_data
                
        except Exception as e:
            logger.error(f"Error in enhanced case generation: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to the original case generator if Perplexity fails
            logger.info("Falling back to original case generator due to error")
            return super().generate_case(params)