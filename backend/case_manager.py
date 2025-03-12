import json
import logging
import random
from datetime import datetime
from backend.case_generator import CaseParameters, CaseGenerator
from backend.virtual_patient import VirtualPatientAgent
from backend.evaluation import DiagnosisEvaluator
from backend.enhanced_case_generator import EnhancedCaseGenerator

logger = logging.getLogger(__name__)

class CaseManager:
    """
    Manages the creation, storage, and lifecycle of patient cases.
    """
    def __init__(self, config):
        self.config = config
        self.current_case = None
        self.current_patient_agent = None
        self.diagnosis_evaluator = None
        self.specialties = ["Internal Medicine", "Cardiology", "Neurology", "Pulmonology", "Orthopedic"]
        self.difficulties = ["Easy", "Moderate", "Hard"]
        
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
            
            # Get list of previously generated diagnoses to avoid repetition
            avoid_conditions = []
            if hasattr(self, 'previous_diagnoses'):
                avoid_conditions = self.previous_diagnoses[-5:] if len(self.previous_diagnoses) > 5 else self.previous_diagnoses
            
            params = CaseParameters(selected_specialty, selected_difficulty, avoid_conditions)
            case_gen = EnhancedCaseGenerator(self.config)
            case_dict = case_gen.generate_case(params)

            # Log the case for debugging
            logger.info(f"Generated case: {json.dumps(case_dict, indent=2)}")
            
            # Store the diagnosis to avoid repetition in future cases
            if not hasattr(self, 'previous_diagnoses'):
                self.previous_diagnoses = []
            if "diagnosis" in case_dict and case_dict["diagnosis"]:
                self.previous_diagnoses.append(case_dict["diagnosis"])
            elif "expected_diagnosis" in case_dict and case_dict["expected_diagnosis"]:
                self.previous_diagnoses.append(case_dict["expected_diagnosis"])
            
            # Ensure diagnosis is present
            if "expected_diagnosis" not in case_dict or not case_dict["expected_diagnosis"]:
                case_dict["expected_diagnosis"] = "Unspecified illness"
                logger.warning("Generated case missing diagnosis, adding default value")

            # Add a unique ID and timestamp to the case
            case_dict["id"] = f"case_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            case_dict["created_at"] = datetime.now().isoformat()

            # Map demographics to individual fields
            if "demographics" in case_dict:
                demographics = case_dict["demographics"]
                for key, value in demographics.items():
                    if key not in case_dict:
                        case_dict[key] = value
            
            # Add required fields for evaluation if not present
            if "key_findings" not in case_dict:
                symptoms = case_dict.get("symptoms", [])
                # Extract 2-3 most important symptoms as key findings
                case_dict["key_findings"] = symptoms[:min(3, len(symptoms))]
                if not case_dict["key_findings"]:
                    case_dict["key_findings"] = ["Unspecified symptoms"]
            
            if "critical_tests" not in case_dict:
                # Add some default critical tests based on specialty
                if selected_specialty == "Cardiology":
                    case_dict["critical_tests"] = ["ECG", "Cardiac Enzymes", "Echocardiogram"]
                elif selected_specialty == "Pulmonology":
                    case_dict["critical_tests"] = ["CXR", "ABG", "PFTs"]
                elif selected_specialty == "Neurology":
                    case_dict["critical_tests"] = ["CT Head", "MRI Brain", "Lumbar Puncture"]
                else:
                    case_dict["critical_tests"] = ["CBC", "CMP", "Urinalysis"]
            
            # Set the voice based on the patient's gender (if provided)
            if "gender" in case_dict and case_dict["gender"].lower() in ["male", "female"]:
                self.config.set_voice_by_gender(case_dict["gender"])

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