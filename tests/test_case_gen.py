import json
from backend.case_generator import CaseParameters, CaseGenerator
from backend.config import MedicalSimConfig

def test_generate_case_live():
    # Ensure you have your actual API keys set in environment variables
    # or replace the placeholders below with your keys.
    config = MedicalSimConfig()
    
    # Define case parameters for the test
    params = CaseParameters("Emergency Medicine", "moderate")
    generator = CaseGenerator(config)
    
    # Generate a case using the actual API
    generated_case = generator.generate_case(params)
    
    # Print the generated case so you can inspect the actual response.
    print("Generated Case:")
    print(json.dumps(generated_case, indent=2))
    
    # Optionally, include assertions to verify expected structure
    assert "demographics" in generated_case, "The generated case should include a demographics field."
    assert "name" in generated_case["demographics"], "The generated demographics should include a name field."
    assert "age" in generated_case["demographics"], "The generated demographics should include an age field."
    assert "vital_signs" in generated_case, "The generated case should include vital signs."
