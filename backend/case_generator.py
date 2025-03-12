import json
import re
from openai import Client  # Using the new client-based interface
from typing import Dict
from backend.config import MedicalSimConfig

class CaseParameters:
    def __init__(self, specialty: str, difficulty: str, avoid_conditions: list = None):
        self.specialty: str = specialty
        self.difficulty: str = difficulty
        self.avoid_conditions: list = avoid_conditions or []
        self.complexity_map: dict[str, str] = {
            "Easy": "common presentation with 1-2 classic symptoms",
            "Moderate": "atypical presentation with comorbidities",
            "Hard": "rare condition with multiple diagnostic red herrings"
        }

class CaseGenerator:
    def __init__(self, config: MedicalSimConfig):
        self.config = config
        # Pass the API key to the new Client
        self.client = Client(api_key=config.openai_api_key)
    
    def _clean_json_response(self, content: str) -> str:
        """
        Clean up potentially malformed JSON from the API response.
        
        This fixes common issues:
        1. Removes code blocks markers
        2. Fixes unquoted strings
        3. Handles other common formatting issues
        """
        # Remove code block markers if present
        if content.startswith("```"):
            # Find the end of the opening code block marker line
            first_newline = content.find('\n')
            if first_newline != -1:
                # Find the closing code block marker
                last_backticks = content.rfind("```")
                if last_backticks > first_newline:
                    # Extract content between the markers
                    content = content[first_newline+1:last_backticks].strip()
        
        # Fix numeric values with attached strings (e.g., "HR": 110 bpm)
        pattern = r':\s*(\d+)\s+([a-zA-Z/°]+)'
        content = re.sub(pattern, r': "\1 \2"', content)
        
        # Fix degree symbols and other special characters
        content = content.replace("°C", " °C")
        content = content.replace("°F", " °F")
        
        return content
    
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
Format as JSON with all these fields.

IMPORTANT: Ensure all string values are properly quoted, including values like "110 bpm" or "22 breaths/min".
Format vital signs values like BP as "120/80 mmHg", HR as "80 bpm", etc."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create case: {params.specialty}, {params.difficulty}"}
                ],
                temperature=0.5 if params.difficulty == "hard" else 0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            
            # Clean up the response to fix common formatting issues
            content = self._clean_json_response(content)
            
            try:
                case = json.loads(content)
            except json.JSONDecodeError as e:
                # If still failing, make one more attempt with a more aggressive cleanup
                content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
                try:
                    case = json.loads(content)
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse JSON response: {response.choices[0].message.content}")
            
            case["specialty"] = params.specialty
            case["difficulty"] = params.difficulty
            return case
        except Exception as e:
            # Log the error and rethrow
            print(f"Error generating case: {str(e)}")
            raise