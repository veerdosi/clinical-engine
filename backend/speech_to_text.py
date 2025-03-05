import os
import openai
from openai import Client
from backend.config import MedicalSimConfig

class SpeechProcessor:
    def __init__(self, config: MedicalSimConfig):
        self.config = config
        self.client = Client(api_key = config.openai_api_key)

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio to text using OpenAI's Whisper model
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1"
                )
            return transcript.text
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")