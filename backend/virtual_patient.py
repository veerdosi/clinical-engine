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
                
        # Check for symptoms as array directly in case
        if "symptoms" in self.case and isinstance(self.case["symptoms"], list):
            symptoms.extend(self.case["symptoms"])
            
        # Check presenting_complaint
        if "presenting_complaint" in self.case and self.case["presenting_complaint"]:
            symptoms.append(self.case["presenting_complaint"])
                
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
        """Build a comprehensive system prompt with all available case information and natural patient behaviors"""
        # Basic patient information
        age = self.demographics.get("age", "unknown age")
        gender = self.demographics.get("gender", "unknown gender")
        name = self.demographics.get("name", "a patient")
        
        # Construct patient personality and background based on case
        presenting_complaint = self.case.get("presenting_complaint", "health concerns")
        
        # Start with strong identity and context guidance
        prompt = f"""You are embodying {name}, a {age}-year-old {gender} patient speaking with a doctor today. 
This is a medical simulation for training doctors, so respond as authentically as you can.

CONTEXT AND DISPOSITION:
You're visiting the doctor for {presenting_complaint}. You're talking to a medical student or doctor who you're meeting for the first time. You're generally cooperative but naturally concerned about your health. Your attitude is {self._determine_patient_attitude()}.

YOUR MEDICAL INFORMATION:
"""

        # Add symptoms with experienced details, not just listing them
        prompt += "Your current symptoms and experiences:\n"
        for symptom in self.symptoms:
            prompt += f"- {symptom}\n"
        
        # Add vital signs if present
        if "vital_signs" in self.case or "vitals" in self.case:
            vitals = self.case.get("vital_signs", self.case.get("vitals", {}))
            if isinstance(vitals, dict) and vitals:
                prompt += "\nThe doctor previously recorded these vital signs, but you're not aware of these measurements yourself:\n"
                for key, value in vitals.items():
                    prompt += f"- {key}: {value}\n"
                    
        # Add past medical history
        if "past_medical_conditions" in self.case and isinstance(self.case["past_medical_conditions"], list):
            prompt += "\nYour medical history includes:\n"
            for condition in self.case["past_medical_conditions"]:
                prompt += f"- {condition}\n"
                
        # Add comorbidities if present
        if "comorbidities" in self.case and isinstance(self.case["comorbidities"], list):
            prompt += "\nYou also have these ongoing health conditions:\n"
            for condition in self.case["comorbidities"]:
                prompt += f"- {condition}\n"
                
        # Add medication allergies
        if "medication_allergies" in self.case and isinstance(self.case["medication_allergies"], list):
            if self.case["medication_allergies"]:
                prompt += "\nYou're allergic to these medications:\n"
                for allergy in self.case["medication_allergies"]:
                    prompt += f"- {allergy}\n"
            else:
                prompt += "\nYou have no known medication allergies.\n"
                
        # Add negative findings - things patient does NOT have
        if "negative_findings" in self.case and isinstance(self.case["negative_findings"], list):
            prompt += "\nImportant: If directly asked, you do NOT have these symptoms/conditions:\n"
            for finding in self.case["negative_findings"]:
                prompt += f"- {finding}\n"
                
        # Add social history if available
        social_history = self._extract_social_history()
        if social_history:
            prompt += "\nYour personal and social background:\n"
            for detail in social_history:
                prompt += f"- {detail}\n"
        
        # Add detailed behavioral instructions
        prompt += """
BEHAVIOR AND COMMUNICATION GUIDELINES:

1. NATURAL SPEECH: Speak naturally like a real patient, not a medical professional. Use plain language, not medical terminology. For example, say "my stomach hurts" rather than "I'm experiencing epigastric pain."

2. KNOWLEDGE LEVEL: You have an average person's understanding of medicine. You know basic terms like "blood pressure" but wouldn't know what "hypertension" means unless your doctor has diagnosed you with it previously.

3. ANSWER STYLE:
   - Give appropriately detailed answers to open-ended questions
   - Give brief answers to yes/no questions
   - If asked about a symptom you have, describe it naturally (location, severity, duration, what makes it better/worse)
   - If asked about a symptom you don't have, simply say you don't have it
   - Never list symptoms unless specifically asked about each one

4. EMOTIONAL AUTHENTICITY: Express appropriate concern about your symptoms. Show relief when reassured. React naturally if the doctor says something concerning.

5. CONSISTENCY: Never contradict information about your symptoms or history that you've already shared. If you're unsure about something, say so rather than making up new details.

6. CONVERSATIONAL FLOW: Let the doctor lead the interview but respond as a real person would:
   - Ask occasional clarifying questions if you don't understand something
   - Express natural concerns about serious symptoms
   - Don't volunteer all information at once - wait to be asked specific questions

Remember: You're a real person with concerns, not just a collection of symptoms. Respond with authentic human reactions to questions about your health.
"""
        return prompt

    def _determine_patient_attitude(self):
        """Determine a realistic patient attitude based on the case details"""
        # Check for emergency/urgent conditions
        urgent_keywords = ["severe", "extreme", "worst", "unbearable", "crushing", "can't breathe", 
                          "chest pain", "stroke", "hemorrhage", "bleeding", "unconscious"]
        
        symptoms_text = " ".join(self.symptoms).lower()
        
        # Check severity from symptoms
        if any(keyword in symptoms_text for keyword in urgent_keywords):
            return "anxious and distressed due to the severity of your symptoms"
        
        # Check for chronic conditions
        chronic_conditions = []
        if "past_medical_conditions" in self.case:
            chronic_conditions = self.case["past_medical_conditions"]
        
        chronic_keywords = ["chronic", "ongoing", "years", "diabetes", "hypertension", "arthritis"]
        conditions_text = " ".join(str(c) for c in chronic_conditions).lower()
        
        if any(keyword in conditions_text for keyword in chronic_keywords) or any(keyword in symptoms_text for keyword in ["chronic", "ongoing", "years"]):
            return "somewhat frustrated as you've been dealing with this problem for a while"
        
        # Default moderate concern
        return "moderately concerned about your symptoms but calm and cooperative"

    def _extract_social_history(self):
        """Extract or generate basic social history context from case data"""
        social_history = []
        
        # Extract explicitly defined social history if available
        if "social_history" in self.case:
            social_data = self.case["social_history"]
            if isinstance(social_data, dict):
                for key, value in social_data.items():
                    social_history.append(f"{key}: {value}")
            elif isinstance(social_data, list):
                social_history.extend(social_data)
            elif isinstance(social_data, str):
                social_history.append(social_data)
        
        # Add occupation if available
        if "occupation" in self.case:
            social_history.append(f"You work as a {self.case['occupation']}")
        
        # Add living situation if available
        if "living_situation" in self.case:
            social_history.append(self.case["living_situation"])
            
        return social_history

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