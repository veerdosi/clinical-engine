import json
import logging
import random
from openai import Client
from datetime import datetime
from backend.case_generator import CaseParameters, CaseGenerator
from backend.virtual_patient import VirtualPatientAgent
from backend.evaluation import DiagnosisEvaluator
from backend.synthea_repository import SyntheaRepository

logger = logging.getLogger(__name__)

class CaseManager:
    """
    Manages the creation, storage, and lifecycle of patient cases.
    """
    def __init__(self, config):
        self.config = config
        self.current_case = None
        self.current_patient_agent = None
        self.client = Client(api_key=config.openai_api_key)
        self.diagnosis_evaluator = None
        self.specialties = ["Internal Medicine", "Emergency Medicine", "Cardiology", "Neurology", "Pulmonology"]
        self.difficulties = ["easy", "moderate", "hard"]
        # Initialize Synthea repository
        self.synthea_repo = SyntheaRepository(config.synthea_db_path)
        self.case_generator = CaseGenerator(config)

    def generate_new_case(self, specialty=None, difficulty=None):
        """
        Generates a new patient case, either with specified parameters or randomly.
        
        Args:
            specialty (str, optional): Medical specialty for the case
            difficulty (str, optional): Difficulty level for the case
            
        Returns:
            dict: The generated case information
        """
        try:
            logger.info("Generating new case...")
            
            # Use provided parameters or choose randomly
            selected_specialty = specialty if specialty and specialty.strip() else random.choice(self.specialties)
            selected_difficulty = difficulty if difficulty and difficulty.strip() else random.choice(self.difficulties)
            
            # Try to get a matching patient from Synthea repository
            synthea_patient = self.synthea_repo.find_matching_patient(
                specialty=selected_specialty,
                difficulty=selected_difficulty
            )

            if synthea_patient:
                logger.info(f"Found matching Synthea patient for {selected_specialty}, {selected_difficulty}")
                
                # Convert Synthea data to our case format
                case_dict = self._convert_synthea_to_case_format(synthea_patient)
                
                # Optionally enhance with GPT for narrative elements
                if self.config.enhance_with_gpt:
                    params = CaseParameters(selected_specialty, selected_difficulty)
                    case_dict = self._enhance_with_gpt(case_dict, params)
            else:
                logger.info(f"No matching Synthea patient found, using GPT to generate case")

                params = CaseParameters(selected_specialty, selected_difficulty)
                case_dict = self.case_generator.generate_case(params)

             # Add a unique ID and timestamp to the case
            case_dict["id"] = f"case_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            case_dict["created_at"] = datetime.now().isoformat()
            case_dict["specialty"] = selected_specialty
            case_dict["difficulty"] = selected_difficulty

            # Store the case
            self.current_case = case_dict
            
            # Create a new patient agent
            case_json = json.dumps(case_dict)
            self.current_patient_agent = VirtualPatientAgent(case_json, self.config)
            
            # Initialize evaluator for this case
            self.diagnosis_evaluator = DiagnosisEvaluator(self.current_case, self.config)
            
            logger.info(f"New case generated: {selected_specialty}, {selected_difficulty}")
            return self.current_case
            
        except Exception as e:
            logger.error(f"Error generating new case: {str(e)}")
            raise
    
    def _convert_synthea_to_case_format(self, synthea_patient):
        """Convert a Synthea patient record to our case format"""
        raw_data = synthea_patient.get('raw_data', {})
        
        # Basic case structure
        case = {
            "name": synthea_patient.get("name", "Unknown Patient"),
            "age": synthea_patient.get("age", 35),
            "gender": synthea_patient.get("gender", "Unknown"),
            "specialty": synthea_patient.get("specialty", "General Medicine"),
            "difficulty": synthea_patient.get("difficulty", "moderate"),
            "diagnosis": synthea_patient.get("primary_diagnosis", "Unknown"),
            "expected_diagnosis": synthea_patient.get("primary_diagnosis", "Unknown"),
            "presenting_complaint": synthea_patient.get("presenting_complaint", "General illness"),
            "symptoms": [],
            "past_medical_conditions": [],
            "key_findings": [],
            "vitals": {
                "BP": "120/80 mmHg",
                "HR": "72 bpm",
                "RR": "16 breaths/min",
                "Temp": "37.0 °C"
            }
        }
        
        # Add default fallbacks if we can't extract proper data
        if not raw_data or not isinstance(raw_data, dict):
            logger.warning(f"No raw Synthea data available for patient {synthea_patient.get('id', 'unknown')}")
            return case
        
        # Extract patient information
        try:
            # Get full patient record
            patient = None
            for entry in raw_data.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Patient':
                    patient = resource
                    break
            
            if patient:
                # Extract name
                if 'name' in patient and len(patient['name']) > 0:
                    given = patient['name'][0].get('given', ['Unknown'])
                    family = patient['name'][0].get('family', 'Patient')
                    case['name'] = f"{given[0]} {family}"
                
                # Extract gender
                if 'gender' in patient:
                    case['gender'] = patient['gender']
                
                # Calculate age from birthDate
                if 'birthDate' in patient:
                    try:
                        from datetime import datetime
                        birth_date = datetime.strptime(patient['birthDate'], '%Y-%m-%d')
                        today = datetime.now()
                        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                        case['age'] = age
                    except Exception as e:
                        logger.error(f"Error calculating age: {str(e)}")
            
            # Extract conditions for symptoms and medical history
            active_conditions = []
            past_conditions = []
            
            for entry in raw_data.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Condition':
                    condition_text = resource.get('code', {}).get('text', '')
                    if condition_text:
                        # Check if condition is active or historical
                        if resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '') == 'active':
                            active_conditions.append(condition_text)
                        else:
                            past_conditions.append(condition_text)
            
            if active_conditions:
                case['symptoms'] = active_conditions
                case['key_findings'] = active_conditions[:3]  # Use top 3 as key findings
            
            if past_conditions:
                case['past_medical_conditions'] = past_conditions
            
            # Extract vital signs
            vitals = {}
            for entry in raw_data.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Observation':
                    code = resource.get('code', {}).get('coding', [{}])[0].get('code', '')
                    # Map LOINC codes to vital sign names
                    vital_map = {
                        '8867-4': 'HR',  # Heart rate
                        '8480-6': 'BP',  # Systolic blood pressure
                        '8462-4': 'BP',  # Diastolic blood pressure (will need special handling)
                        '9279-1': 'RR',  # Respiratory rate
                        '8310-5': 'Temp'  # Body temperature
                    }
                    
                    if code in vital_map:
                        name = vital_map[code]
                        value = resource.get('valueQuantity', {}).get('value', '')
                        unit = resource.get('valueQuantity', {}).get('unit', '')
                        
                        # Special handling for blood pressure
                        if name == 'BP' and code == '8480-6' and value:  # Systolic
                            # Find the matching diastolic reading
                            diastolic = None
                            for dentry in raw_data.get('entry', []):
                                dres = dentry.get('resource', {})
                                if dres.get('resourceType') == 'Observation' and dres.get('code', {}).get('coding', [{}])[0].get('code', '') == '8462-4':
                                    diastolic = dres.get('valueQuantity', {}).get('value', '')
                                    break
                            
                            if diastolic:
                                vitals[name] = f"{value}/{diastolic} mmHg"
                        elif name != 'BP' or code != '8462-4':  # Skip diastolic as individual entry
                            vitals[name] = f"{value} {unit}"
            
            # Update vitals if we found any
            if vitals:
                case['vitals'] = vitals
            
            # Generate a presenting complaint from primary diagnosis
            if case['diagnosis'] and case['diagnosis'] != "Unknown":
                common_symptoms = {
                    "heart attack": "chest pain",
                    "myocardial infarction": "chest pain",
                    "pneumonia": "cough and fever",
                    "stroke": "sudden weakness",
                    "diabetes": "increased thirst and urination",
                    "hypertension": "headache",
                    "asthma": "shortness of breath",
                    "copd": "difficulty breathing",
                    "fracture": "pain and swelling",
                    "depression": "persistent sadness",
                    "anxiety": "excessive worry"
                }
                
                diagnosis_lower = case['diagnosis'].lower()
                complaint = "general illness"
                
                for key, symptom in common_symptoms.items():
                    if key in diagnosis_lower:
                        complaint = symptom
                        break
                
                case['presenting_complaint'] = f"Patient presenting with {complaint}"
            
        except Exception as e:
            logger.error(f"Error converting Synthea data: {str(e)}")
        
        return case
        
    def _enhance_with_gpt(self, case_dict, params):
        """Enhance a Synthea-generated case with GPT for narrative elements"""
        try:
            # Create a prompt that asks GPT to enhance the existing case
            system_prompt = f"""Enhance this medical case with detailed narrative elements.
    The underlying medical facts should not be changed, but add:
    - More detailed symptoms descriptions
    - Patient history narrative
    - More natural language for the presenting complaint
    - Any realistic negative findings that would be relevant

    Original case: {json.dumps(case_dict)}

    Return the enhanced case as JSON with all original fields preserved plus any enhancements.
    """
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Enhance this {params.difficulty} {params.specialty} case"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            enhanced_case = json.loads(response.choices[0].message.content)
            return enhanced_case
            
        except Exception as e:
            logger.error(f"Error enhancing case with GPT: {str(e)}")
            # Return original case if enhancement fails
            return case_dict

    def get_current_case(self):
        """
        Returns the current active case.
        
        Returns:
            dict: Current case or None if no case is active
        """
        return self.current_case
    
    def get_sanitized_case(self):
        """
        Returns a sanitized version of the current case with sensitive information removed.
        
        Returns:
            dict: Sanitized case information suitable for frontend display
        """
        if not self.current_case:
            return None
            
        return {
            "id": self.current_case.get("id", "unknown"),
            "specialty": self.current_case.get("specialty", "General Medicine"),
            "difficulty": self.current_case.get("difficulty", "moderate"),
            "name": self.current_case.get("name", "Unknown Patient"),
            "age": self.current_case.get("age", "Unknown"),
            "gender": self.current_case.get("gender", "Unknown"),
            "created_at": self.current_case.get("created_at"),
            "presenting_complaint": self.current_case.get("presenting_complaint", "Unknown"),
            "vitals": self.current_case.get("vitals", {})
        }
    
    def get_patient_agent(self):
        """
        Returns the current virtual patient agent.
        
        Returns:
            VirtualPatientAgent: The current patient agent
        """
        return self.current_patient_agent
    
    def get_diagnosis_evaluator(self):
        """
        Returns the diagnosis evaluator for the current case.
        
        Returns:
            DiagnosisEvaluator: The diagnosis evaluator
        """
        return self.diagnosis_evaluator