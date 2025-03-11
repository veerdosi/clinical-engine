# populate_synthea.py

import os
import sys
import json
import subprocess
import glob
from dotenv import load_dotenv
from backend.synthea_repository import SyntheaRepository

load_dotenv()

def main():
    synthea_path = os.getenv("SYNTHEA_PATH")
    db_path = os.getenv("SYNTHEA_DB_PATH", "synthea_patients.db")
    
    if not synthea_path:
        print("Error: SYNTHEA_PATH environment variable not set")
        sys.exit(1)
    
    synthea_jar = os.path.join(synthea_path, "build", "libs", "synthea-with-dependencies.jar")
    if not os.path.exists(synthea_jar):
        print(f"Error: Synthea JAR not found at {synthea_jar}")
        sys.exit(1)
    
    repo = SyntheaRepository(db_path)
    
    # Define specialties and module mappings
    specialty_modules = {
        "Cardiology": "heart",
        "Pulmonology": "lung_cancer",
        "Neurology": "stroke",
        "Internal Medicine": "metabolic_syndrome_care",
        "Emergency Medicine": "appendicitis"
    }
    
    # Generate patients for each specialty
    for specialty, module in specialty_modules.items():
        for difficulty in ["easy", "moderate", "hard"]:
            count = 3  # Generate 3 patients per specialty/difficulty
            
            print(f"Generating {count} {difficulty} {specialty} patients with module {module}")
            
            # Build Synthea command
            cmd = ["java", "-jar", synthea_jar, 
                  "-p", str(count),
                  "-m", module,
                  "--exporter.fhir.export", "true",
                  "--exporter.hospital.fhir.export", "false",
                  "--exporter.practitioner.fhir.export", "false"]
            
            # Add difficulty modifiers
            if difficulty == "easy":
                cmd.extend(["-a", "30-50"])  # Younger patients
            elif difficulty == "moderate":
                cmd.extend(["-a", "50-70"])  # Middle-aged
            else:  # hard
                cmd.extend(["-a", "70-90"])  # Elderly with likely comorbidities
            
            # Run Synthea
            subprocess.run(cmd, cwd=synthea_path)
            
            # Import generated patients
            output_dir = os.path.join(synthea_path, "output", "fhir")
            for file_path in glob.glob(os.path.join(output_dir, "*.json")):
                with open(file_path, 'r') as f:
                    try:
                        patient_data = json.load(f)
                        patient_id = repo.import_patient(patient_data, specialty, difficulty)
                        print(f"Imported patient {patient_id}")
                    except json.JSONDecodeError:
                        print(f"Error parsing {file_path}")
                        
                # Remove file after processing
                os.remove(file_path)
    
    print(f"Repository now contains {len(repo.get_all_patient_ids())} patients")

if __name__ == "__main__":
    main()