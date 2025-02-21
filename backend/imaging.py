import json
import openai
from backend.config import MedicalSimConfig
import replicate

def generate_imaging_prompt(case: dict, modality: str, config: MedicalSimConfig, findings: str = None) -> dict:
    """
    Generates both natural language prompt for radiologists and technical parameters for image generation.
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
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": findings or "Generate standard imaging study"}
        ],
        temperature=0.4
    )
    try:
        imaging_data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse JSON response: {response.choices[0].message.content}")
    return imaging_data

class FluxImagingGenerator:
    def __init__(self, config: MedicalSimConfig):
        self.config = config
        self.model = "black-forest-labs/flux-pro"
    
    def generate_image(self, parameters: Dict) -> Dict:
        """
        Generate a medical image using Replicate's Flux model.
        """
        try:
            input_data = {
                "prompt": parameters.get("findings_description", "Normal anatomy"),
                "width": parameters.get("width", 1024),
                "height": parameters.get("height", 1024),
                "negative_prompt": "artifacts, blurry, low quality",
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 50
            }
            client = replicate.Client(api_token=self.config.replicate_key)
            output = client.run(
                self.model,
                input=input_data
            )
            image_url = output[0] if output else None
            return {
                "image_url": image_url,
                "findings_report": parameters.get("findings_description"),
                "metadata": input_data
            }
        except Exception as e:
            raise Exception(f"Replicate API Error: {str(e)}")
