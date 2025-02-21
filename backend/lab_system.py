import json
import openai
from backend.simulation_session import SimulationSession

class LabSystem:
    def __init__(self, config):
        self.config = config

    def validate_test_order(self, tests: list, session: SimulationSession) -> bool:
        required_tests = {
            "ABG": ["CXR"],
            "Troponin": ["ECG"],
        }
        for test in tests:
            if test in required_tests:
                for required in required_tests[test]:
                    if required not in session.ordered_tests and required not in session.ordered_imaging:
                        raise ValueError(f"{test} requires {required} to be ordered first")
        return True

    def generate_report(self, case: dict, tests: list) -> str:
        system_prompt = f"""Generate lab results based on:
- Patient: {json.dumps(case)}
- Tests: {', '.join(tests)}
Include:
- 2-3 abnormal values related to likely diagnosis
- Test name, result, units, reference range
- Automated interpretation
Format in markdown."""
    
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate formatted lab report"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content