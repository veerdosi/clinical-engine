import json
import openai
import requests
from io import BytesIO
from datetime import datetime
from backend.config import MedicalSimConfig

class VirtualPatientAgent:
    def __init__(self, case: dict, config: MedicalSimConfig):
        self.case = case
        self.config = config
        self.conversation = []
        # removed the unused self.critical_decision list, couldn't find any use
        self.system_prompt = f"""You are a patient experiencing {case.get('presenting_complaint', 'an issue')}.
Follow these rules:
1. Speak naturally like a real patient
2. Reveal {case.get('hidden_findings', 'additional details')} only when asked directly
3. Never use medical terms
4. If asked about non-relevant systems, say 'I don't understand'
5. Base your responses on: {json.dumps(case.get('history', {}))}"""

    def text_to_speech(self, text: str, voice_id: str = None) -> BytesIO:
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
    
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Eleven Labs API Error: {response.text}")
    
        return BytesIO(response.content)
    
    def process_interaction(self, user_input: str) -> dict:
        self.conversation.append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation[-6:]
            ],
            temperature=0.4
        )
        answer = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": answer})
        audio_buffer = self.text_to_speech(answer)
    
        return {
            "text": answer,
            "audio": audio_buffer,
            "timestamp": datetime.now().isoformat()
        }