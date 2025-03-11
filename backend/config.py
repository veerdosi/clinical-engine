import os
import requests
import replicate
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MedicalSimConfig:
    def __init__(self,
                 openai_key: str = None,
                 elevenlabs_key: str = None,
                 replicate_key: str = None,
                 perplexity_key: str = None,
                 default_voice_id: str = "EXAVITQu4vr4xnSDxMaL",
                 voice_settings: dict = None):
        """
        Initialize medical simulation configuration.
        """
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
        self.perplexity_api_key = perplexity_key or os.getenv("PERPLEXITY_API_KEY")

    def _validate_replicate_key(self):
        if not self.replicate_key:
            raise ValueError("Replicate API key is required")
        try:
            replicate.Client(api_token=self.replicate_key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Replicate: {str(e)}")

    def _validate_elevenlabs_key(self):
        test_url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": self.elevenlabs_key}
        response = requests.get(test_url, headers=headers)
        if response.status_code != 200:
            raise ConnectionError("Failed to connect to Eleven Labs API")

    def set_voice(self, voice_id: str, settings: dict = None):
        """
        Manually set the voice by voice ID.
        """
        self.default_voice_id = voice_id
        if settings:
            self.voice_settings.update(settings)

    def set_voice_by_gender(self, gender: str, settings: dict = None):
        """
        Set the default voice based on the specified gender.
        :param gender: 'male' or 'female'
        :param settings: Additional voice settings to update
        """
        if gender.lower() == "female":
            # Set to a female voice id (assumed)
            self.default_voice_id = "EXAVITQu4vr4xnSDxMaL"
        elif gender.lower() == "male":
            # Set to a male voice id (assumed)
            self.default_voice_id = "TxGEqnHWrfWFTfGW9XjX"
        else:
            raise ValueError("Gender must be either 'male' or 'female'")
        if settings:
            self.voice_settings.update(settings)