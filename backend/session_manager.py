import logging
from datetime import datetime, timedelta
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
        self.patient_notes = {}

        # Timing-related attributes
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.diagnosis_submission_time = None
        self.activity_timeline = []
        self.idle_periods = []
        self.critical_test_times = {}  # Map test names to timestamps
        
        # Record session start
        self._record_activity("session_start", "Session started")
    
    def reset_session(self, case_id=None):
        """
        Resets the session data for a new case.
        
        Args:
            case_id (str, optional): ID of the new case
        """
        # Save the previous session timing data if it exists
        if hasattr(self, 'case_id') and self.case_id:
            self._record_activity("session_end", "Session ended")

        self.case_id = case_id
        self.ordered_tests = set()
        self.ordered_imaging = set()
        self.physical_exams = []
        self.patient_interactions = []
        self.verified_exam_procedures = []
        self.patient_notes = {}  # Reset notes too

        # Reset timing-related attributes
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.diagnosis_submission_time = None
        self.activity_timeline = []
        self.idle_periods = []
        self.critical_test_times = {}

        # Record new session start
        self._record_activity("session_start", "Session started")
        logger.info(f"Session reset for case {case_id}")
    
    def _record_activity(self, activity_type: str, description: str, details: Dict = None):
        """
        Records an activity in the timeline.
        
        Args:
            activity_type: Type of activity (e.g., 'interaction', 'test_order')
            description: Brief description of the activity
            details: Additional details about the activity
        """
        timestamp = datetime.now()
        
        # Calculate idle time since last activity
        idle_duration = (timestamp - self.last_activity_time).total_seconds()
        if idle_duration > 60:  # More than 1 minute idle
            self.idle_periods.append({
                "start": self.last_activity_time,
                "end": timestamp,
                "duration_seconds": idle_duration
            })
        
        # Update last activity time
        self.last_activity_time = timestamp
        
        # Record the activity
        activity = {
            "timestamp": timestamp,
            "activity_type": activity_type,
            "description": description,
            "time_since_start": (timestamp - self.session_start_time).total_seconds()
        }
        
        if details:
            activity.update(details)
            
        self.activity_timeline.append(activity)

    def _check_for_inactivity(self, timeout_minutes: int = 5) -> bool:
        """
        Checks if there has been no activity for a specified period.
        
        Args:
            timeout_minutes: Threshold in minutes to consider inactivity
            
        Returns:
            bool: True if inactive beyond threshold, False otherwise
        """
        if not self.last_activity_time:
            return False
            
        idle_time = datetime.now() - self.last_activity_time
        return idle_time > timedelta(minutes=timeout_minutes)

    def add_patient_interaction(self, user_message, patient_response=None):
        """
        Records an interaction between the student and virtual patient.
        
        Args:
            user_message (str): Message sent by the student
            patient_response (str, optional): Response from the virtual patient
            
        Returns:
            dict: The recorded interaction
        """
        timestamp = datetime.now()
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message
        }
        
        if patient_response:
            interaction["patient_response"] = patient_response
            
        self.patient_interactions.append(interaction)

        # Record in timeline
        self._record_activity(
            "patient_interaction", 
            f"Patient interaction: {user_message[:30]}{'...' if len(user_message) > 30 else ''}",
            {"message_length": len(user_message)}
        )

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
        
        # Track notes changes
        if self.patient_notes != notes:
            old_word_count = sum(len(content.split()) for content in self.patient_notes.values() if content)
            new_word_count = sum(len(content.split()) for content in notes.values() if content)
            word_diff = new_word_count - old_word_count
            
            self._record_activity(
                "notes_update", 
                f"Notes updated ({'+' if word_diff >= 0 else ''}{word_diff} words)",
                {"old_word_count": old_word_count, "new_word_count": new_word_count}
            )

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

        # Record timeline entry with timestamp
        self._record_activity("test_order", f"Lab test ordered: {test_name}")
        
        # Check if this is a critical test and record the first time it was ordered
        if test_name.lower() in [t.lower() for t in self._get_critical_tests()]:
            if test_name not in self.critical_test_times:
                self.critical_test_times[test_name] = datetime.now()
        
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

        # Record timeline entry with timestamp
        self._record_activity("imaging_order", f"Imaging ordered: {imaging_name}")
        
        # Check if this is a critical imaging and record the first time it was ordered
        if imaging_name.lower() in [t.lower() for t in self._get_critical_tests()]:
            if imaging_name not in self.critical_test_times:
                self.critical_test_times[imaging_name] = datetime.now()
        
        logger.info(f"Imaging ordered: {imaging_name}")
        return True
    
    def _get_critical_tests(self):
        """
        Get list of critical tests from the case manager if available.
        """
        from backend.case_manager import CaseManager
        # This would need to be passed in or retrieved from a global store
        # For now, return an empty list
        return []
    
    def add_physical_exam(self, system, findings):
        """
        Records a physical examination performed by the student.
        
        Args:
            system (str): Body system examined
            findings (dict): Examination findings
            
        Returns:
            dict: The recorded examination
        """
        timestamp = datetime.now()
        exam = {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "findings": findings
        }
        
        self.physical_exams.append(exam)

        # Record in timeline
        self._record_activity("physical_exam", f"Physical exam: {system}")

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
        timestamp = datetime.now()
        procedure = {
            "timestamp": datetime.now().isoformat(),
            "exam_name": exam_name,
            "procedure_steps": procedure_steps,
            "procedure_score": score,
            "verified": True
        }
        
        self.verified_exam_procedures.append(procedure)

        # Record in timeline
        step_count = len(procedure_steps) if isinstance(procedure_steps, list) else 0
        self._record_activity(
            "verified_procedure", 
            f"Verified procedure: {exam_name}",
            {"score": score, "step_count": step_count}
        )

        logger.info(f"Verified exam procedure recorded: {exam_name}")
        return procedure
    
    def get_verified_exam_procedures(self):
        """
        Returns all verified physical examination procedures in this session.
        
        Returns:
            list: List of verified examination procedures
        """
        return self.verified_exam_procedures
    
    def record_diagnosis_submission(self, diagnosis):
        """
        Records the timestamp of diagnosis submission.
        
        Args:
            diagnosis (str): The submitted diagnosis
            
        Returns:
            dict: Diagnostic timing information
        """
        self.diagnosis_submission_time = datetime.now()
        time_to_diagnosis = (self.diagnosis_submission_time - self.session_start_time).total_seconds()
        
        # Record in timeline
        self._record_activity(
            "diagnosis_submission", 
            f"Diagnosis submitted: {diagnosis}",
            {"time_to_diagnosis_seconds": time_to_diagnosis}
        )
        
        return {
            "timestamp": self.diagnosis_submission_time.isoformat(),
            "time_to_diagnosis_seconds": time_to_diagnosis,
            "diagnosis": diagnosis
        }
    
    def get_efficiency_metrics(self):
        """
        Calculates efficiency metrics based on recorded timestamps.
        
        Returns:
            dict: Efficiency metrics with timing information
        """
        metrics = {
            "session_duration_seconds": (datetime.now() - self.session_start_time).total_seconds(),
            "time_to_diagnosis_seconds": None,
            "history_taking_time_seconds": None,
            "physical_exam_time_seconds": None,
            "idle_periods_count": len(self.idle_periods),
            "total_idle_time_seconds": sum(period["duration_seconds"] for period in self.idle_periods),
            "critical_tests_ordered": len(self.critical_test_times),
            "critical_test_ordering_sequence": [
                {"test": test, "time_since_start": (timestamp - self.session_start_time).total_seconds()}
                for test, timestamp in sorted(self.critical_test_times.items(), key=lambda x: x[1])
            ]
        }
        
        # Calculate time to diagnosis if diagnosis was submitted
        if self.diagnosis_submission_time:
            metrics["time_to_diagnosis_seconds"] = (
                self.diagnosis_submission_time - self.session_start_time
            ).total_seconds()
            
        # Calculate history taking time - from first to last patient interaction
        if self.patient_interactions:
            history_activities = [
                a for a in self.activity_timeline 
                if a["activity_type"] == "patient_interaction"
            ]
            if history_activities:
                first_interaction = min(history_activities, key=lambda x: x["timestamp"])
                last_interaction = max(history_activities, key=lambda x: x["timestamp"])
                metrics["history_taking_time_seconds"] = (
                    last_interaction["timestamp"] - first_interaction["timestamp"]
                ).total_seconds()
                
        # Calculate physical exam time - from first to last physical exam
        physical_exam_activities = [
            a for a in self.activity_timeline 
            if a["activity_type"] in ["physical_exam", "verified_procedure"]
        ]
        if physical_exam_activities:
            first_exam = min(physical_exam_activities, key=lambda x: x["timestamp"])
            last_exam = max(physical_exam_activities, key=lambda x: x["timestamp"])
            metrics["physical_exam_time_seconds"] = (
                last_exam["timestamp"] - first_exam["timestamp"]
            ).total_seconds()
        
        return metrics
    
    def get_session_timeline(self):
        """
        Returns the timeline of activities during the session.
        
        Returns:
            list: Chronological list of activities with timestamps
        """
        return sorted(self.activity_timeline, key=lambda x: x["timestamp"])
    
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
        
        # Calculate timing metrics
        current_time = datetime.now()
        session_duration = (current_time - self.session_start_time).total_seconds()
        
        # Time to complete key milestones
        milestones = {}
        for activity in self.activity_timeline:
            if activity["activity_type"] == "patient_interaction" and "first_interaction" not in milestones:
                milestones["first_interaction"] = activity["time_since_start"]
            elif activity["activity_type"] == "physical_exam" and "first_physical_exam" not in milestones:
                milestones["first_physical_exam"] = activity["time_since_start"]
            elif activity["activity_type"] == "test_order" and "first_test_order" not in milestones:
                milestones["first_test_order"] = activity["time_since_start"]
            elif activity["activity_type"] == "imaging_order" and "first_imaging_order" not in milestones:
                milestones["first_imaging_order"] = activity["time_since_start"]
            elif activity["activity_type"] == "diagnosis_submission":
                milestones["diagnosis_submission"] = activity["time_since_start"]
        
        return {
            "case_id": self.case_id,
            "session_duration": session_duration,
            "session_duration_formatted": self._format_duration(session_duration),
            "interaction_count": len(self.patient_interactions),
            "tests_ordered": list(self.ordered_tests),
            "imaging_ordered": list(self.ordered_imaging),
            "physical_exams_performed": len(self.physical_exams),
            "verified_exam_procedures": len(self.verified_exam_procedures),
            "notes_word_count": notes_word_count,
            "has_notes": notes_word_count > 0,
            "idle_periods_count": len(self.idle_periods),
            "total_idle_time": sum(period["duration_seconds"] for period in self.idle_periods),
            "milestones": milestones,
            "efficiency_metrics": self.get_efficiency_metrics()
        }
    
    def _format_duration(self, seconds):
        """Helper method to format duration in seconds to a readable string"""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

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