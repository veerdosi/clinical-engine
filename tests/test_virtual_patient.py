import json
from io import BytesIO
from backend.virtual_patient import VirtualPatientAgent
from backend.config import MedicalSimConfig

def test_virtual_patient_json_live():
    # Initialize configuration with your actual API keys (or set via environment variables)
    config = MedicalSimConfig()
    
    # Create a dummy case as a Python dict and convert it to JSON
    case = {
        "presenting_complaint": "headache",
        "hidden_findings": "none",
        "history": {"allergies": "none"}
    }
    case_json = json.dumps(case)
    
    # Instantiate the VirtualPatientAgent with the JSON case
    patient_agent = VirtualPatientAgent(case_json, config)
    
    # Simulate a user interaction
    result = patient_agent.process_interaction("How are you feeling today?")
    
    # For printing purposes, we cannot directly serialize BytesIO; so we replace it.
    result_printable = result.copy()
    result_printable["audio"] = "<BytesIO object>"
    print("Virtual Patient Response (JSON test):")
    print(json.dumps(result_printable, indent=2))
    
    # Assertions to ensure the response contains expected keys
    assert "text" in result, "Response should include a text field."
    assert result["text"], "Response text should not be empty."
    assert "audio" in result, "Response should include an audio field."
    assert isinstance(result["audio"], BytesIO), "Audio field should be a BytesIO object."