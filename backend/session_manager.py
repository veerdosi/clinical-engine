import logging
from datetime import datetime
from typing import List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages the student's session, including interactions and test orders.
    """
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.ordered_tests = set()
        self.ordered_imaging = set()
        self.physical_exams = []
        self.patient_interactions = []
        self.session_start_time = datetime.now()
        # Initialize verified_exam_procedures
        self.verified_exam_procedures = []
    
    def reset_session(self, case_id=None):
        """
        Resets the session data for a new case.
        
        Args:
            case_id (str, optional): ID of the new case
        """
        self.case_id = case_id
        self.ordered_tests = set()
        self.ordered_imaging = set()
        self.physical_exams = []
        self.patient_interactions = []
        self.verified_exam_procedures = []
        self.patient_notes = {}  # Reset notes too
        self.session_start_time = datetime.now()
        logger.info(f"Session reset for case {case_id}")
    
    def add_patient_interaction(self, user_message, patient_response=None):
        """
        Records an interaction between the student and virtual patient.
        
        Args:
            user_message (str): Message sent by the student
            patient_response (str, optional): Response from the virtual patient
            
        Returns:
            dict: The recorded interaction
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message
        }
        
        if patient_response:
            interaction["patient_response"] = patient_response
            
        self.patient_interactions.append(interaction)
        return interaction
    
    def update_patient_response(self, index, patient_response):
        """
        Updates an existing interaction with the patient's response.
        
        Args:
            index (int): Index of the interaction to update
            patient_response (str): Response from the virtual patient
        """
        if 0 <= index < len(self.patient_interactions):
            self.patient_interactions[index]["patient_response"] = patient_response
            return True
        return False
    
    def save_notes(self, notes):
        """
        Saves the patient notes for the current session.
        
        Args:
            notes (dict): Dictionary containing SOAP notes
            
        Returns:
            bool: True if notes were saved successfully
        """
        if not hasattr(self, 'patient_notes'):
            self.patient_notes = {}
        
        self.patient_notes = notes
        logger.info(f"Notes saved for case {self.case_id}")
        return True
    
    def get_notes(self):
        """
        Retrieves the current patient notes.
        
        Returns:
            dict: The current patient notes or empty dict if none exist
        """
        if not hasattr(self, 'patient_notes'):
            self.patient_notes = {}
        
        return self.patient_notes
    
    def order_test(self, test_name):
        """
        Records a lab test ordered by the student.
        
        Args:
            test_name (str): Name of the test ordered
            
        Returns:
            bool: True if the test was newly ordered, False if already ordered
        """
        if test_name in self.ordered_tests:
            return False
            
        self.ordered_tests.add(test_name)
        logger.info(f"Test ordered: {test_name}")
        return True
    
    def order_imaging(self, imaging_name):
        """
        Records an imaging study ordered by the student.
        
        Args:
            imaging_name (str): Name of the imaging study ordered
            
        Returns:
            bool: True if the imaging was newly ordered, False if already ordered
        """
        if imaging_name in self.ordered_imaging:
            return False
            
        self.ordered_imaging.add(imaging_name)
        logger.info(f"Imaging ordered: {imaging_name}")
        return True
    
    def add_physical_exam(self, system, findings):
        """
        Records a physical examination performed by the student.
        
        Args:
            system (str): Body system examined
            findings (dict): Examination findings
            
        Returns:
            dict: The recorded examination
        """
        exam = {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "findings": findings
        }
        
        self.physical_exams.append(exam)
        logger.info(f"Physical exam performed: {system}")
        return exam
    
    def add_verified_exam_procedure(self, exam_name, procedure_steps, score=0):
        """
        Records a verified physical examination procedure.
        
        Args:
            exam_name (str): Name of the examination
            procedure_steps (list): Steps of the procedure
            score (float): Score for the procedure (0-100)
            
        Returns:
            dict: The recorded examination procedure
        """
        procedure = {
            "timestamp": datetime.now().isoformat(),
            "exam_name": exam_name,
            "procedure_steps": procedure_steps,
            "procedure_score": score,
            "verified": True
        }
        
        self.verified_exam_procedures.append(procedure)
        logger.info(f"Verified exam procedure recorded: {exam_name}")
        return procedure
    
    def get_verified_exam_procedures(self):
        """
        Returns all verified physical examination procedures in this session.
        
        Returns:
            list: List of verified examination procedures
        """
        return self.verified_exam_procedures
    
    # Update get_session_summary to include notes status
    def get_session_summary(self):
        """
        Returns a summary of the current session.
        
        Returns:
            dict: Session summary information
        """
        notes_word_count = 0
        if hasattr(self, 'patient_notes'):
            for section, content in self.patient_notes.items():
                if content:
                    notes_word_count += len(content.split())
        
        return {
            "case_id": self.case_id,
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "interaction_count": len(self.patient_interactions),
            "tests_ordered": list(self.ordered_tests),
            "imaging_ordered": list(self.ordered_imaging),
            "physical_exams_performed": len(self.physical_exams),
            "verified_exam_procedures": len(self.verified_exam_procedures),
            "notes_word_count": notes_word_count,
            "has_notes": notes_word_count > 0
        }
    
    def get_ordered_tests(self):
        """
        Returns all tests ordered in this session.
        
        Returns:
            set: Set of ordered test names
        """
        return self.ordered_tests
    
    def get_ordered_imaging(self):
        """
        Returns all imaging studies ordered in this session.
        
        Returns:
            set: Set of ordered imaging names
        """
        return self.ordered_imaging
    
    def get_patient_interactions(self):
        """
        Returns all patient interactions in this session.
        
        Returns:
            list: List of patient interactions
        """
        return self.patient_interactions
    
    def get_physical_exams(self):
        """
        Returns all physical examinations performed in this session.
        
        Returns:
            list: List of physical examinations
        """
        return self.physical_exams