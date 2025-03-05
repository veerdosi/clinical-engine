import json
import logging
from openai import Client
import requests
from io import BytesIO
from datetime import datetime
from backend.config import MedicalSimConfig

logger = logging.getLogger(__name__)

class VirtualPatientAgent:
    def __init__(self, case_json: str, config: MedicalSimConfig):
        try:
            self.case = json.loads(case_json)
            logger.info(f"Initializing virtual patient with case ID: {self.case.get('id', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input for case: {e}")
            raise ValueError("Invalid JSON input for case") from e
        
        self.config = config
        self.conversation = []
        
        # Process and extract key symptoms in a standardized format
        self.symptoms = self._extract_symptoms()
        logger.info(f"Extracted symptoms: {self.symptoms}")
        
        # Extract demographics in a standardized format
        self.demographics = self._extract_demographics()
        logger.info(f"Extracted demographics: {self.demographics}")
        
        # Build a comprehensive system prompt with all available case information
        self.system_prompt = self._build_system_prompt()
        logger.debug(f"System prompt: {self.system_prompt}")
        
        self.client = Client(api_key=config.openai_api_key)

    def _extract_symptoms(self):
        """Extract symptoms from various possible formats in the case data"""
        symptoms = []
    
        # Check for key_symptoms as a list
        if "key_symptoms" in self.case and isinstance(self.case["key_symptoms"], list):
            for item in self.case["key_symptoms"]:
                if isinstance(item, dict):
                    # Handle dictionary format (with system/symptom structure)
                    if "symptom" in item:
                        symptoms.append(item["symptom"])
                else:
                    # Handle simple string format
                    symptoms.append(item)
        
        # Check for key_symptoms as a dictionary
        elif "key_symptoms" in self.case and isinstance(self.case["key_symptoms"], dict):
            for system, symptom in self.case["key_symptoms"].items():
                if symptom and symptom != "None":
                    symptoms.append(f"{symptom}")
        
        # Check for symptoms in presentation
        if "presentation" in self.case:
            presentation = self.case["presentation"]
            
            if "classic_symptoms" in presentation and isinstance(presentation["classic_symptoms"], list):
                symptoms.extend(presentation["classic_symptoms"])
                
            if "description" in presentation and isinstance(presentation["description"], str):
                symptoms.append(presentation["description"])
                
        # Check for atypical_presentation
        if "atypical_presentation" in self.case:
            atypical = self.case["atypical_presentation"]
            if "description" in atypical and isinstance(atypical["description"], str):
                symptoms.append(atypical["description"])
                
        # Deduplicate symptoms
        unique_symptoms = []
        for symptom in symptoms:
            if isinstance(symptom, str) and symptom not in unique_symptoms:
                unique_symptoms.append(symptom)
                
        return unique_symptoms

    def _extract_demographics(self):
        """Extract demographics from various possible formats in the case data"""
        demo = {}
        
        # Direct demographics fields
        direct_fields = ["name", "age", "gender", "height_cm", "weight_kg", "blood_type"]
        for field in direct_fields:
            if field in self.case:
                demo[field] = self.case[field]
        
        # Check for nested demographics
        if "demographics" in self.case and isinstance(self.case["demographics"], dict):
            for field, value in self.case["demographics"].items():
                if field not in demo:  # Don't overwrite direct fields
                    demo[field] = value
                    
        return demo

    def _build_system_prompt(self):
        """Build a comprehensive system prompt with all available case information"""
        # Basic patient information
        age = self.demographics.get("age", "unknown age")
        gender = self.demographics.get("gender", "unknown gender")
        name = self.demographics.get("name", "a patient")
        
        # Start with basic identity and presenting complaint
        prompt = f"""You are {name}, a {age}-year-old {gender} patient. 
        
You are visiting a doctor for the following health concerns:
"""

        # Add symptoms
        for symptom in self.symptoms:
            prompt += f"- {symptom}\n"
            
        # Add vital signs if present
        if "vital_signs" in self.case:
            prompt += "\nYour vital signs are:\n"
            vitals = self.case["vital_signs"]
            if isinstance(vitals, dict):
                for key, value in vitals.items():
                    prompt += f"- {key}: {value}\n"
                    
        # Add past medical history
        if "past_medical_conditions" in self.case and isinstance(self.case["past_medical_conditions"], list):
            prompt += "\nYour medical history includes:\n"
            for condition in self.case["past_medical_conditions"]:
                prompt += f"- {condition}\n"
                
        # Add comorbidities if present
        if "comorbidities" in self.case and isinstance(self.case["comorbidities"], list):
            prompt += "\nYou also have these chronic conditions:\n"
            for condition in self.case["comorbidities"]:
                prompt += f"- {condition}\n"
                
        # Add medication allergies
        if "medication_allergies" in self.case and isinstance(self.case["medication_allergies"], list):
            prompt += "\nYou have allergies to these medications:\n"
            for allergy in self.case["medication_allergies"]:
                prompt += f"- {allergy}\n"
                
        # Add negative findings
        if "negative_findings" in self.case and isinstance(self.case["negative_findings"], list):
            prompt += "\nImportant negative findings to mention if asked:\n"
            for finding in self.case["negative_findings"]:
                prompt += f"- {finding}\n"
        
        # Add behavioral instructions
        prompt += """
Follow these rules during the conversation:
1. Speak naturally like a real patient would
2. Do not use medical terminology unless the doctor uses it first
3. Only reveal medical details when asked directly relevant questions
4. If asked about symptoms you don't have, simply say you don't have those symptoms
5. If asked about symptoms you do have, describe them in detail
6. Stay consistent with your medical history and symptoms throughout the conversation
7. If asked about systems unrelated to your symptoms, say you haven't noticed any issues with those
8. Act as if you're meeting this doctor for the first time"""

        return prompt

    def text_to_speech(self, text: str, voice_id: str = None) -> BytesIO:
        """
        Converts text to speech using Eleven Labs API
        """
        voice_id = voice_id or self.config.default_voice_id
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.config.elevenlabs_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": self.config.voice_settings
        }
    
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"Eleven Labs API Error: {str(e)}")
            raise Exception(f"Eleven Labs API Error: {str(e)}")
    
    def process_interaction(self, user_input: str, include_voice: bool = True) -> dict:
        """
        Process user input and generate patient response
        
        Args:
            user_input (str): The message from the user
            include_voice (bool): Whether to generate voice response
            
        Returns:
            dict: Contains text response and optionally audio
        """
        try:
            # Add the user message to conversation history
            self.conversation.append({"role": "user", "content": user_input})
            
            # Get conversation context (limited to last few messages for context window)
            conversation_context = self.conversation[-10:]  # Only use last 10 messages
            
            # Create messages for the API call
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            messages.extend(conversation_context)
            
            logger.info(f"Sending interaction to LLM: '{user_input[:50]}...' (truncated)")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7  # Slightly higher temperature for more natural responses
            )
            
            # Extract the response text
            answer = response.choices[0].message.content
            logger.info(f"Received response from LLM: '{answer[:50]}...' (truncated)")
            
            # Add to conversation history
            self.conversation.append({"role": "assistant", "content": answer})
            
            # Create result dictionary
            result = {
                "text": answer,
                "timestamp": datetime.now().isoformat()
            }
            
            # Only generate audio if requested
            if include_voice:
                try:
                    audio_buffer = self.text_to_speech(answer)
                    result["audio"] = audio_buffer
                except Exception as e:
                    logger.error(f"Error generating audio: {str(e)}")
                    # Continue without audio if it fails
        
            return result
            
        except Exception as e:
            logger.error(f"Error in process_interaction: {str(e)}")
            return {
                "text": "I'm sorry, I'm not feeling well and need a moment. Could you repeat that?",
                "timestamp": datetime.now().isoformat()
            }