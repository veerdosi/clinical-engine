import json
from backend.case_generator import CaseParameters, CaseGenerator
from backend.virtual_patient import VirtualPatientAgent
from backend.config import MedicalSimConfig

def test_case_generation_and_virtual_patient_workflow():
    # Initialize configuration with your actual API keys (or set via environment variables)
    config = MedicalSimConfig()
    
    # Generate a patient case using the case generator
    params = CaseParameters("General Medicine", "moderate")
    case_gen = CaseGenerator(config)
    case_dict = case_gen.generate_case(params)
    case_json = json.dumps(case_dict)
    
    # Pass the generated case JSON into the VirtualPatientAgent
    vp_agent = VirtualPatientAgent(case_json, config)
    result = vp_agent.process_interaction("How are you feeling today?")
    
    # For printing, replace the non-serializable audio field with a placeholder.
    result_printable = result.copy()
    result_printable["audio"] = "<BytesIO object>"
    print("Integrated Workflow Result:")
    print(json.dumps(result_printable, indent=2))
    
    # Basic assertion: the response should contain non-empty text.
    assert "text" in result and result["text"], "The integrated workflow should produce a valid text response."
