import asyncio
from dotenv import load_dotenv
from backend.config import MedicalSimConfig
from backend.enhanced_case_generator import EnhancedCaseGenerator, CaseParameters
import json
import os

# Load environment variables
load_dotenv()

# Get API key
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
print(f"API key present: {bool(perplexity_api_key)}")
print(f"API key length: {len(perplexity_api_key) if perplexity_api_key else 0}")

# Test if the API key is the default value
if perplexity_api_key == "your_perplexity_api_key_here":
    print("WARNING: Using default API key value")
config = MedicalSimConfig()
generator = EnhancedCaseGenerator(config)
params = CaseParameters("Cardiology", "moderate")
case = generator.generate_case(params)

print(json.dumps(case, indent=2))