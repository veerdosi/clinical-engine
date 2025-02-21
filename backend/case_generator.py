import json
import openai
from typing import Dict
from backend.config import MedicalSimConfig


class CaseParameters:
    def __init__(self, specialty: str, difficulty: str):
        self.specialty: str = specialty
        self.difficulty: str = difficulty
        self.complexity_map: dict[str, str] = {
            "easy": "common presentation with 1-2 classic symptoms",
            "moderate": "atypical presentation with comorbidities",
            "hard": "rare condition with multiple diagnostic red herrings"
    }

class CaseGenerator:
    def __init__(self, config: MedicalSimConfig):
        self.config = config

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
    
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create case: {params.specialty}, {params.difficulty}"}
            ],
            temperature=0.5 if params.difficulty == "hard" else 0.3
        )
        try:
            case = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON response: {response.choices[0].message.content}")
        case["specialty"] = params.specialty
        case["difficulty"] = params.difficulty
        return case