import openai
import json
from typing import Dict, List
import os
from dataclasses import dataclass, field
from datetime import datetime
import requests
from io import BytesIO
import replicate
from pprint import pprint  

class MedicalSimConfig:
    def __init__(self,
                 openai_key: str = None,
                 elevenlabs_key: str = None,
                 replicate_key: str = None,
                 default_voice_id: str = "EXAVITQu4vr4xnSDxMaL",
                 voice_settings: dict = None):
        """
        Initialize medical simulation configuration

        Args:
            openai_key: OpenAI API key
            elevenlabs_key: Eleven Labs API key
            default_voice_id: Default voice ID for text-to-speech
            voice_settings: Dictionary of voice parameters
                {
                    "stability": 0.5,       # (0-1) Lower = more expressive
                    "similarity_boost": 0.8 # (0-1) Higher = more consistent
                }
        """
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(
            api_key=openai_key or os.getenv("OPENAI_API_KEY")
        )

        # Configure Eleven Labs
        self.elevenlabs_key = elevenlabs_key or os.getenv("ELEVENLABS_API_KEY")
        self.default_voice_id = default_voice_id
        self.voice_settings = voice_settings or {
            "stability": 0.5,
            "similarity_boost": 0.8
        }

        self.replicate_key = replicate_key or os.getenv("REPLICATE_API_KEY")
        self._validate_replicate_key()  

        # Validate API keys
        self._validate_keys()

    def _validate_replicate_key(self):
        """Validate Replicate API key"""
        if not self.replicate_key:
            raise ValueError("Replicate API key is required")

        # Test Replicate connectivity
        try:
            replicate.Client(api_token=self.replicate_key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Replicate: {str(e)}")

    def _validate_keys(self):
        """Validate API credentials"""
        if not self.openai_client.api_key:
            raise ValueError("OpenAI API key is required")

        if not self.elevenlabs_key:
            raise ValueError("Eleven Labs API key is required")

        test_url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": self.elevenlabs_key}
        response = requests.get(test_url, headers=headers)
        if response.status_code != 200:
            raise ConnectionError("Failed to connect to Eleven Labs API")

    def set_voice(self, voice_id: str, settings: dict = None):
        """Update voice configuration"""
        self.default_voice_id = voice_id
        if settings:
            self.voice_settings.update(settings)

@dataclass
class CaseParameters:
    specialty: str
    difficulty: str
    complexity_map = {
        "easy": "common presentation with 1-2 classic symptoms",
        "moderate": "atypical presentation with comorbidities",
        "hard": "rare condition with multiple diagnostic red herrings"
    }

class CaseGenerator:
    def __init__(self, config: MedicalSimConfig):
        self.client = config.openai_client

    def generate_case(self, params: CaseParameters) -> Dict:
        system_prompt = f"""Generate a {params.difficulty} {params.specialty} case with:
        - Demographics: name, age, gender, height(cm), weight(kg), blood type
        - {params.complexity_map[params.difficulty]}
        - Vital signs (BP, HR, RR, Temp)
        - 3-5 key symptoms across body systems
        - 2-3 relevant past medical conditions
        - Medication allergies
        - 1-2 relevant negative findings
        - Expected correct diagnosis
        Format as JSON with all these fields."""
    
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create case: {params.specialty}, {params.difficulty}"}
            ],
            temperature=0.7 if params.difficulty == "hard" else 0.5,
            response_format={"type": "json_object"}
        )
        case = json.loads(response.choices[0].message.content)
        return {**case, "difficulty": params.difficulty, "specialty": params.specialty}

class VirtualPatientAgent:
    def __init__(self, case: Dict, config: MedicalSimConfig):
        self.case = case
        self.config = config
        self.conversation = []
        self.critical_decisions = []

        self.system_prompt = f"""You are a patient experiencing {case.get('presenting_complaint', 'an issue')}.
        Follow these rules:
        1. Speak naturally like a real patient
        2. Reveal {case.get('hidden_findings', 'additional details')} only when asked directly
        3. Never use medical terms
        4. If asked about non-relevant systems, say 'I don't understand'
        5. Base your responses on: {json.dumps(case.get('history', {}))}"""

    def text_to_speech(self, text: str, voice_id: str = None) -> BytesIO:
        """Convert text to speech using Eleven Labs API"""
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
        # Store interaction
        self.conversation.append({"role": "user", "content": user_input})
    
        # Get patient response
        response = self.config.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.conversation[-6:]  # Keeping last few messages for context
            ],
            temperature=0.4
        )
        answer = response.choices[0].message.content
        self.conversation.append({"role": "assistant", "content": answer})
    
        # Convert to speech using Eleven Labs
        audio_buffer = self.text_to_speech(answer)
    
        return {
            "text": answer,
            "audio": audio_buffer,
            "timestamp": datetime.now().isoformat()
        }

@dataclass
class SimulationSession:
    """
    Tracks the state of a clinical simulation session.
    """
    case: Dict  # The patient case being simulated
    config: MedicalSimConfig  # Configuration for APIs
    start_time: datetime = field(default_factory=datetime.now)
    interactions: List[Dict] = field(default_factory=list)  # Conversation history
    ordered_tests: List[str] = field(default_factory=list)  # Lab tests ordered
    ordered_imaging: List[str] = field(default_factory=list)  # Imaging studies ordered
    diagnoses: List[str] = field(default_factory=list)  # Differential diagnoses
    critical_actions: List[str] = field(default_factory=list)  # Key clinical decisions
    elapsed_time: int = 0  # Time elapsed in minutes
    
    def add_interaction(self, user_input: str, patient_response: str):
        """Log an interaction between the user and the virtual patient."""
        self.interactions.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "patient_response": patient_response
        })
        self.elapsed_time += 1  # Increment time by 1 minute per interaction
    
    def add_test_order(self, test: str):
        """Log a lab test order."""
        if test not in self.ordered_tests:
            self.ordered_tests.append(test)
            self.elapsed_time += 5  # Simulate time for test processing
    
    def add_imaging_order(self, imaging_study: str):
        """Log an imaging study order."""
        if imaging_study not in self.ordered_imaging:
            self.ordered_imaging.append(imaging_study)
            self.elapsed_time += 10  # Simulate time for imaging
    
    def add_diagnosis(self, diagnosis: str):
        """Log a diagnosis made by the user."""
        if diagnosis not in self.diagnoses:
            self.diagnoses.append(diagnosis)
    
    def add_critical_action(self, action: str):
        """Log a critical clinical action (e.g., starting antibiotics)."""
        if action not in self.critical_actions:
            self.critical_actions.append(action)
    
    def get_summary(self) -> Dict:
        """Generate a summary of the simulation session."""
        return {
            "case_id": self.case.get("id", "unknown"),
            "start_time": self.start_time.isoformat(),
            "elapsed_time": self.elapsed_time,
            "interaction_count": len(self.interactions),
            "tests_ordered": self.ordered_tests,
            "imaging_ordered": self.ordered_imaging,
            "diagnoses_made": self.diagnoses,
            "critical_actions": self.critical_actions
        }

class LabSystem:
    def __init__(self, config: MedicalSimConfig):
        self.client = config.openai_client
        self.required_tests = {
            "ABG": ["CXR"],  # ABG requires a CXR
            "Troponin": ["ECG"],  # Troponin requires an ECG
        }
    
    def validate_test_order(self, tests: List[str], session: SimulationSession) -> bool:
        for test in tests:
            if test in self.required_tests:
                for required in self.required_tests[test]:
                    if required not in session.ordered_tests and required not in session.ordered_imaging:
                        raise ValueError(f"{test} requires {required} to be ordered first")
        return True
    
    def generate_report(self, case: Dict, tests: List[str]) -> str:
        template = """**LABORATORY REPORT**
        Patient: {name} | DOB: {dob}
        Collection Date: {date}
    
        {results}
    
        Interpretation: {interpretation}"""
    
        system_prompt = f"""Generate lab results based on:
        - Patient: {json.dumps(case)}
        - Tests: {', '.join(tests)}
        Include:
        - 2-3 abnormal values related to likely diagnosis
        - Test name, result, units, reference range
        - Automated interpretation
        Format in markdown."""
    
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate formatted lab report"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content

def generate_imaging_prompt(case: Dict, modality: str, config: MedicalSimConfig, findings: str = None) -> Dict:
    """
    Generates both natural language prompt for radiologists
    and technical parameters for Replicate image generation
    """
    system_prompt = f"""You are a radiologist assistant. Create imaging prompts for:
    Patient Case: {json.dumps(case)}
    Modality: {modality}
    Required:
    1. Natural language description of findings
    2. Technical parameters for {modality} simulation
    3. Differential diagnosis hints
    
    Example JSON output:
    {{
        "clinical_indication": "45yo male with chest pain",
        "findings_description": "PA chest X-ray showing left lower lobe consolidation",
        "replicate_parameters": {{
            "width": 1024,
            "height": 1024,
            "prompt": "Chest X-ray showing left lower lobe consolidation with air bronchograms",
            "negative_prompt": "artifacts, blurry, low quality"
        }},
        "diagnostic_hints": ["Pneumonia", "Pulmonary edema"]
    }}"""
    
    response = config.openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": findings or "Generate standard imaging study"}
        ],
        temperature=0.4,
        response_format={"type": "json_object"}
    )
    
    imaging_data = json.loads(response.choices[0].message.content)
    return imaging_data

class FluxImagingGenerator:
    def __init__(self, config: MedicalSimConfig):
        self.config = config
        self.model = "black-forest-labs/flux-pro"
    
    def generate_image(self, parameters: Dict) -> Dict:
        """
        Generate medical image using Replicate's Flux model
        Args:
            parameters: Dictionary containing:
                - prompt: Description of findings
                - width: Image width (default 1024)
                - height: Image height (default 1024)
        Returns:
            Dictionary with image URL and findings
        """
    
        try:
            # Prepare input for Replicate
            input_data = {
                "prompt": parameters.get("findings_description", "Normal anatomy"),
                "width": parameters.get("width", 1024),
                "height": parameters.get("height", 1024),
                "negative_prompt": "artifacts, blurry, low quality",  # Improve image quality
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
    
            # Generate image
            client = replicate.Client(api_token=self.config.replicate_key)
            output = client.run(
                self.model,
                input=input_data
            )
    
            # Replicate returns a list of URLs
            image_url = output[0]
            return {
                "image_url": image_url,
                "findings_report": parameters.get("findings_description"),
                "metadata": input_data  # Include generation parameters
            }
    
        except Exception as e:
            raise Exception(f"Replicate API Error: {str(e)}")

class PerformanceEvaluator:
    def __init__(self, case: Dict):
        self.case = case
        self.evaluation_criteria = {}  # Initialize evaluation criteria
        # Added imaging evaluation criteria
        self.evaluation_criteria["imaging_interpretation"] = [
            "Appropriate modality selection",
            "Findings recognition",
            "Clinical correlation"
        ]
    
    def _assess_imaging_choices(self, ordered_studies: List[str]) -> Dict:
        """
        Evaluate appropriateness of imaging orders based on clinical guidelines.
        Returns detailed scoring and feedback.
        """
        imaging_guidelines = {
            "pneumonia": {
                "first_line": ["xray"],
                "alternatives": ["ct"],
                "contraindications": ["mri"],
                "scoring": {
                    "xray": 10,
                    "ct": 7,
                    "mri": 1
                },
                "feedback": {
                    "xray": "Chest X-ray is the first-line imaging for suspected pneumonia.",
                    "ct": "CT is indicated if X-ray is inconclusive or complications are suspected.",
                    "mri": "MRI is not routinely used for pneumonia diagnosis."
                }
            },
            "stroke": {
                "first_line": ["ct"],
                "alternatives": ["mri"],
                "contraindications": ["xray"],
                "scoring": {
                    "ct": 10,
                    "mri": 8,
                    "xray": 0
                },
                "feedback": {
                    "ct": "Non-contrast CT is first-line for acute stroke evaluation.",
                    "mri": "MRI is preferred for subacute or posterior circulation strokes.",
                    "xray": "Chest X-ray is not indicated for stroke evaluation."
                }
            },
            "appendicitis": {
                "first_line": ["us"],
                "alternatives": ["ct"],
                "contraindications": ["mri"],
                "scoring": {
                    "us": 9,
                    "ct": 10,
                    "mri": 5
                },
                "feedback": {
                    "us": "Ultrasound is first-line for children and pregnant women.",
                    "ct": "CT is first-line for adults due to higher sensitivity.",
                    "mri": "MRI is used if CT is contraindicated (e.g., pregnancy)."
                }
            }
        }
    
        diagnosis = self.case["expected_diagnosis"].lower()
        results = {
            "ordered_studies": ordered_studies,
            "appropriateness_score": 0,
            "feedback": [],
            "expected_modality": imaging_guidelines.get(diagnosis, {}).get("first_line", []),
            "alternatives": imaging_guidelines.get(diagnosis, {}).get("alternatives", []),
            "contraindications": imaging_guidelines.get(diagnosis, {}).get("contraindications", [])
        }
    
        for study in ordered_studies:
            study = study.lower()
            if study in imaging_guidelines.get(diagnosis, {}).get("first_line", []):
                results["appropriateness_score"] += 10
                results["feedback"].append(f"✅ {imaging_guidelines[diagnosis]['feedback'][study]}")
            elif study in imaging_guidelines.get(diagnosis, {}).get("alternatives", []):
                results["appropriateness_score"] += 7
                results["feedback"].append(f"⚠️ {imaging_guidelines[diagnosis]['feedback'][study]}")
            elif study in imaging_guidelines.get(diagnosis, {}).get("contraindications", []):
                results["appropriateness_score"] -= 5
                results["feedback"].append(f"❌ {imaging_guidelines[diagnosis]['feedback'][study]}")
            else:
                results["appropriateness_score"] -= 3
                results["feedback"].append(f"❓ {study} is not typically indicated for {diagnosis}.")
    
        max_score = 10 * len(imaging_guidelines.get(diagnosis, {}).get("first_line", []))
        results["appropriateness_score"] = max(0, min(100, (results["appropriateness_score"] / max_score) * 100))
    
        return results

if __name__ == "__main__":
    # Initialize config
    config = MedicalSimConfig(
        openai_key="your-openai-key",
        elevenlabs_key="your-elevenlabs-key",
        replicate_key="your-replicate-key"
    )
    
    # Generate case
    case_generator = CaseGenerator(config)
    case = case_generator.generate_case(CaseParameters("Emergency Medicine", "moderate"))
    
    # Initialize session
    session = SimulationSession(case=case, config=config)
    
    # Initialize agents
    patient = VirtualPatientAgent(case, config)
    lab_system = LabSystem(config)
    imaging_generator = FluxImagingGenerator(config)
    
    # Simulate interaction
    user_input = "What brings you in today?"
    response = patient.process_interaction(user_input)
    session.add_interaction(user_input, response["text"])
    
    # Order tests
    session.add_test_order("CBC")
    session.add_test_order("CMP")
    lab_report = lab_system.generate_report(case, session.ordered_tests)  # Fixed argument count
    
    # Order imaging
    session.add_imaging_order("Chest X-ray")
    imaging_prompt = generate_imaging_prompt(case, "Chest X-ray", config)  # Pass config
    imaging_result = imaging_generator.generate_image(imaging_prompt["replicate_parameters"])
    
    # Add diagnosis and critical action
    session.add_diagnosis("Community-acquired pneumonia")
    session.add_critical_action("Started antibiotics")
    
    # Print session summary
    print("Session Summary:")
    pprint(session.get_summary())