import json
import logging
from openai import Client
from typing import List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TimestampEvaluator:
    """
    Evaluates student performance based on timestamps and action sequence.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
    
    def evaluate_timestamps(self, 
                          timeline: List[Dict[str, Any]], 
                          efficiency_metrics: Dict[str, Any],
                          case_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the student's clinical workflow based on timestamps.
        
        Args:
            timeline: List of timestamped activities
            efficiency_metrics: Pre-calculated efficiency metrics
            case_info: Information about the current case
            
        Returns:
            Dict containing timestamp-based evaluation results
        """
        # Extract diagnosis and other case details
        diagnosis = case_info.get("diagnosis", case_info.get("expected_diagnosis", "Unknown"))
        specialty = case_info.get("specialty", "Unknown")
        urgency_level = self._determine_case_urgency(case_info)
        
        # Create a prompt for LLM evaluation
        system_prompt = f"""You are a medical education expert evaluating a student's clinical workflow efficiency based on their timestamp data.

Case Information:
- Diagnosis: {diagnosis}
- Specialty: {specialty}
- Urgency Level: {urgency_level}

The student's workflow timeline has been analyzed, and you have access to their activity sequence and timing metrics.

Evaluate the following aspects:
1. Workflow efficiency: Was time used effectively? Were there long idle periods?
2. Appropriate prioritization: Were urgent tests/exams performed first?
3. Logical progression: Did the workflow follow a sensible clinical approach?
4. Adherence to guidelines: Did the sequence align with standard clinical protocols?
5. Recognition of time-sensitivity: For urgent cases, was time managed appropriately?

Generate a comprehensive evaluation as a JSON object with:
- efficiency_score: int (1-10)
- prioritization_score: int (1-10) 
- logical_progression_score: int (1-10)
- guideline_adherence_score: int (1-10)
- time_sensitivity_score: int (1-10)
- overall_workflow_score: int (1-10)
- strengths: array of strings
- areas_for_improvement: array of strings
- feedback: string with assessment and advice
"""
        
        # Format timeline data for the prompt
        formatted_timeline = self._format_timeline_for_prompt(timeline)
        formatted_metrics = self._format_metrics_for_prompt(efficiency_metrics)
        
        try:
            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use appropriate model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Timeline data:\n{formatted_timeline}\n\nEfficiency metrics:\n{formatted_metrics}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Add raw metrics to the evaluation
            evaluation["timeline_data"] = timeline
            evaluation["efficiency_metrics_raw"] = efficiency_metrics
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in timestamp evaluation: {str(e)}")
            # Return a basic evaluation if LLM fails
            return {
                "efficiency_score": 5,
                "prioritization_score": 5,
                "logical_progression_score": 5,
                "guideline_adherence_score": 5,
                "time_sensitivity_score": 5,
                "overall_workflow_score": 5,
                "strengths": ["Unable to fully evaluate workflow due to technical error."],
                "areas_for_improvement": ["Unable to provide specific improvement areas due to evaluation error."],
                "feedback": "Due to a technical error, the system couldn't fully analyze your clinical workflow timing. General best practices include prioritizing critical tests, following a logical diagnostic sequence, and managing time efficiently based on case urgency.",
                "timeline_data": timeline,
                "efficiency_metrics_raw": efficiency_metrics
            }
    
    def _determine_case_urgency(self, case_info: Dict[str, Any]) -> str:
        """
        Determines the urgency level of a case based on diagnosis and symptoms.
        
        Args:
            case_info: Information about the case
            
        Returns:
            str: Urgency level (High, Medium, Low)
        """
        # List of conditions typically considered urgent or emergent
        urgent_conditions = [
            "myocardial infarction", "heart attack", "stroke", "pulmonary embolism",
            "aortic dissection", "sepsis", "meningitis", "appendicitis", "aneurysm",
            "tension pneumothorax", "cardiac arrest", "severe trauma", "hemorrhage",
            "overdose", "anaphylaxis", "status epilepticus", "diabetic ketoacidosis"
        ]
        
        # Get case details
        diagnosis = case_info.get("diagnosis", 
                             case_info.get("expected_diagnosis", "")).lower()
        
        # Get symptoms if available
        symptoms = []
        if "symptoms" in case_info and isinstance(case_info["symptoms"], list):
            symptoms = [s.lower() if isinstance(s, str) else "" for s in case_info["symptoms"]]
        
        # Check for urgent keywords in diagnosis
        for condition in urgent_conditions:
            if condition in diagnosis:
                return "High"
                
        # Check for urgent symptoms
        urgent_symptom_keywords = [
            "severe", "intense", "acute", "sudden", "extreme", "unbearable",
            "crushing", "worst", "cannot", "unable"
        ]
        
        for symptom in symptoms:
            for keyword in urgent_symptom_keywords:
                if keyword in symptom:
                    return "High"
        
        # Check for moderate urgency based on specialty and presenting complaint
        specialty = case_info.get("specialty", "").lower()
        presenting_complaint = case_info.get("presenting_complaint", "").lower()
        
        moderately_urgent_specialties = ["cardiology", "neurology", "emergency"]
        if any(spec in specialty for spec in moderately_urgent_specialties):
            return "Medium"
            
        # Default to low urgency if no urgent indicators found
        return "Low"
    
    def _format_timeline_for_prompt(self, timeline: List[Dict[str, Any]]) -> str:
        """
        Formats the timeline data into a readable string for the prompt.
        
        Args:
            timeline: List of timestamped activities
            
        Returns:
            str: Formatted timeline string
        """
        if not timeline:
            return "No timeline data available."
        
        formatted_entries = []
        for i, entry in enumerate(sorted(timeline, key=lambda x: x["timestamp"])):
            time_str = f"{entry.get('time_since_start', 0):.1f}s"
            activity = entry.get("activity_type", "unknown")
            description = entry.get("description", "")
            
            formatted_entries.append(f"{i+1}. [{time_str}] {activity.upper()}: {description}")
        
        return "\n".join(formatted_entries)
    
    def _format_metrics_for_prompt(self, metrics: Dict[str, Any]) -> str:
        """
        Formats the efficiency metrics into a readable string for the prompt.
        
        Args:
            metrics: Efficiency metrics dictionary
            
        Returns:
            str: Formatted metrics string
        """
        formatted_lines = []
        
        # Format durations
        for key, value in metrics.items():
            if key.endswith("_seconds") and value is not None:
                # Convert seconds to a more readable format
                minutes, seconds = divmod(int(value), 60)
                hours, minutes = divmod(minutes, 60)
                
                if hours > 0:
                    time_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    time_str = f"{minutes}m {seconds}s"
                else:
                    time_str = f"{seconds}s"
                
                # Format the key name to be more readable
                readable_key = key.replace("_seconds", "").replace("_", " ").title()
                formatted_lines.append(f"{readable_key}: {time_str}")
            elif key == "idle_periods_count":
                formatted_lines.append(f"Idle Periods: {value}")
            elif key == "critical_tests_ordered":
                formatted_lines.append(f"Critical Tests Ordered: {value}")
            elif key == "critical_test_ordering_sequence" and value:
                sequence = ", ".join([f"{item['test']} ({item['time_since_start']:.1f}s)" for item in value])
                formatted_lines.append(f"Critical Test Sequence: {sequence}")
        
        return "\n".join(formatted_lines)

class InteractionEvaluator:
    """
    Evaluates the quality of student-patient interactions, focusing on communication skills,
    empathy, and interview technique.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
        
    def evaluate_interactions(self, interactions: List[Dict[str, str]], case_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates the quality of student-patient interactions.
        
        Args:
            interactions: List of interaction records between student and patient
            case_info: Information about the current case for context
            
        Returns:
            Dict containing evaluation results focused on communication skills
        """
        if not interactions:
            return {
                "communication_score": 0,
                "empathy_score": 0,
                "interview_technique_score": 0,
                "overall_interaction_score": 0,
                "strengths": [],
                "areas_for_improvement": [],
                "feedback": "No patient interactions recorded."
            }
        
        try:
            # Format interactions for evaluation
            formatted_interactions = []
            for i, interaction in enumerate(interactions, 1):
                formatted_interactions.append({
                    "number": i,
                    "student_message": interaction.get("user_message", ""),
                    "patient_response": interaction.get("patient_response", "")
                })
            
            # Create a context-appropriate prompt
            system_prompt = f"""You are a medical education expert evaluating a medical student's communication skills.
            
Case context: {case_info.get('presenting_complaint', 'Unknown complaint')}, {case_info.get('difficulty', 'moderate')} difficulty.

You have access to the transcript of the student's interactions with a virtual patient. Evaluate the following aspects:
1. Communication skills (clarity, listening, question quality)
2. Empathy and rapport building
3. Medical interview technique (organization, thoroughness, efficiency)

Rate each area on a scale of 1-10.
Identify specific strengths and areas for improvement with examples from the transcript.
Provide actionable feedback to help the student improve.

Return a JSON object with these fields:
- communication_score: int (1-10)
- empathy_score: int (1-10)
- interview_technique_score: int (1-10)
- overall_interaction_score: int (1-10)
- strengths: array of strings
- areas_for_improvement: array of strings
- feedback: string with overall assessment and advice
"""

            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Evaluate these interactions: {json.dumps(formatted_interactions[-10:], indent=2)}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Ensure all expected fields are present
            expected_fields = [
                "communication_score", "empathy_score", "interview_technique_score",
                "overall_interaction_score", "strengths", "areas_for_improvement", "feedback"
            ]
            
            for field in expected_fields:
                if field not in evaluation:
                    if field.endswith("_score"):
                        evaluation[field] = 5  # Default middle score
                    elif field in ["strengths", "areas_for_improvement"]:
                        evaluation[field] = []
                    else:
                        evaluation[field] = "No evaluation available."
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in interaction evaluation: {str(e)}")
            return {
                "communication_score": 5,
                "empathy_score": 5,
                "interview_technique_score": 5,
                "overall_interaction_score": 5,
                "strengths": [],
                "areas_for_improvement": ["Unable to evaluate interactions due to a technical error."],
                "feedback": f"An error occurred during evaluation. Please try again."
            }

class NotesEvaluator:
    """
    Evaluates the quality of student-created SOAP notes, focusing on structure,
    completeness, accuracy, and medical terminology.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
    
    def evaluate_notes(self, notes: Dict[str, str], case_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates SOAP notes created by a student.
        
        Args:
            notes: Dictionary containing SOAP notes (subjective, objective, assessment, plan)
            case_info: Information about the current case for context
            
        Returns:
            Dict containing evaluation results for the notes
        """
        if not notes or not any(notes.values()):
            return {
                "completeness_score": 0,
                "organization_score": 0,
                "accuracy_score": 0,
                "terminology_score": 0,
                "assessment_plan_score": 0,
                "overall_notes_score": 0,
                "strengths": [],
                "areas_for_improvement": ["No notes were created."],
                "feedback": "No patient notes were recorded. Creating detailed SOAP notes is an essential part of clinical practice."
            }
        
        try:
            # Format notes for evaluation
            formatted_notes = {
                "subjective": notes.get("subjective", ""),
                "objective": notes.get("objective", ""),
                "assessment": notes.get("assessment", ""),
                "plan": notes.get("plan", "")
            }
            
            # Extract key case information for evaluation context
            diagnosis = case_info.get("diagnosis", 
                                 case_info.get("expected_diagnosis", "Unknown"))
            symptoms = []
            if "symptoms" in case_info and isinstance(case_info["symptoms"], list):
                symptoms = case_info["symptoms"]
            
            vitals = {}
            if "vitals" in case_info and isinstance(case_info["vitals"], dict):
                vitals = case_info["vitals"]
            
            # Create a context-appropriate prompt
            system_prompt = f"""You are a medical education expert evaluating a medical student's SOAP notes.
            
Case context:
- Patient: {case_info.get('name', 'Unknown')}, {case_info.get('age', 'Unknown')} {case_info.get('gender', 'Unknown')}
- Presenting complaint: {case_info.get('presenting_complaint', 'Unknown complaint')}
- Correct diagnosis: {diagnosis}
- Relevant symptoms: {json.dumps(symptoms)}
- Vital signs: {json.dumps(vitals)}

You have access to the student's SOAP notes. Evaluate the following aspects:
1. Completeness (1-10): Inclusion of all relevant findings and information
2. Organization and structure (1-10): Proper use of SOAP format with information in correct sections
3. Accuracy (1-10): Correctness of recorded information compared to the case details
4. Medical terminology (1-10): Appropriate use of medical language and terminology
5. Assessment and plan (1-10): Logical assessment and plan based on findings, identification of key clinical issues

Rate each area on a scale of 1-10.
Identify specific strengths and areas for improvement with examples from the notes.
Provide actionable feedback to help the student improve.

Return a JSON object with these fields:
- completeness_score: int (1-10)
- organization_score: int (1-10)
- accuracy_score: int (1-10)
- terminology_score: int (1-10)
- assessment_plan_score: int (1-10)
- overall_notes_score: int (1-10)
- strengths: array of strings
- areas_for_improvement: array of strings
- feedback: string with overall assessment and advice
"""

            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Evaluate these SOAP notes: {json.dumps(formatted_notes, indent=2)}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Ensure all expected fields are present
            expected_fields = [
                "completeness_score", "organization_score", "accuracy_score", 
                "terminology_score", "assessment_plan_score", "overall_notes_score",
                "strengths", "areas_for_improvement", "feedback"
            ]
            
            for field in expected_fields:
                if field not in evaluation:
                    if field.endswith("_score"):
                        evaluation[field] = 5  # Default middle score
                    elif field in ["strengths", "areas_for_improvement"]:
                        evaluation[field] = []
                    else:
                        evaluation[field] = "No evaluation available."
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in notes evaluation: {str(e)}")
            return {
                "completeness_score": 5,
                "organization_score": 5,
                "accuracy_score": 5,
                "terminology_score": 5,
                "assessment_plan_score": 5,
                "overall_notes_score": 5,
                "strengths": [],
                "areas_for_improvement": ["Unable to evaluate notes due to a technical error."],
                "feedback": f"An error occurred during evaluation. Please try again."
            }

class ClinicalDecisionEvaluator:
    """
    Evaluates the clinical decisions made by the student, including test ordering,
    diagnosis accuracy, and clinical reasoning.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
    
    def evaluate_clinical_decisions(
        self, 
        student_diagnosis: str,
        ordered_tests: Set[str],
        ordered_imaging: Set[str],
        physical_exams: List[Dict[str, Any]],
        case_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates the student's clinical decisions.
        
        Args:
            student_diagnosis: The diagnosis provided by the student
            ordered_tests: Tests ordered by the student
            ordered_imaging: Imaging studies ordered by the student
            physical_exams: Physical examinations performed by the student
            case_info: Information about the current case
            
        Returns:
            Dict containing evaluation of clinical decision-making
        """
        try:
            # Extract correct diagnosis and key information
            correct_diagnosis = case_info.get("diagnosis", "Unknown")
            key_findings = case_info.get("key_findings", [])
            critical_tests = case_info.get("critical_tests", [])
            
            # Extract relevant physical exam systems based on the case
            expected_exams = self._determine_expected_exams(case_info)
            performed_exams = [exam.get("system", "") for exam in physical_exams]
            
            # Create a prompt for clinical evaluation
            system_prompt = f"""You are a medical education expert evaluating a medical student's clinical decision-making.

Case Information:
- Presenting complaint: {case_info.get('presenting_complaint', 'Unknown')}
- Key symptoms: {json.dumps(case_info.get('symptoms', []))}
- Correct diagnosis: {correct_diagnosis}
- Critical tests needed: {json.dumps(critical_tests)}
- Expected physical exams: {json.dumps(expected_exams)}

Student's actions:
- Final diagnosis: "{student_diagnosis}"
- Tests ordered: {json.dumps(list(ordered_tests))}
- Imaging ordered: {json.dumps(list(ordered_imaging))}
- Physical exams performed: {json.dumps(performed_exams)}

Evaluate the following:
1. Diagnostic accuracy (Is the diagnosis correct or close? Consider semantic similarity.)
2. Test selection (Were appropriate tests ordered? Any unnecessary ones?)
3. Physical examination thoroughness (Did they examine relevant body systems?)
4. Resource utilization (Was testing efficient or excessive?)
5. Clinical reasoning (Based on the diagnosis, exams, and tests ordered)

Return a JSON object with:
- diagnosis_correct: boolean
- diagnosis_accuracy_score: int (1-10)
- test_selection_score: int (1-10)
- physical_exam_score: int (1-10)
- efficiency_score: int (1-10)
- clinical_reasoning_score: int (1-10)
- overall_clinical_score: int (1-10)
- missed_critical_tests: array of strings
- unnecessary_tests: array of strings
- missed_physical_exams: array of strings
- feedback: string with assessment and recommendations
"""

            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Evaluate clinical decisions for diagnosis: \"{student_diagnosis}\""}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Add additional fields
            evaluation["actual_diagnosis"] = correct_diagnosis
            
            # Basic string matching fallback
            if not evaluation.get("diagnosis_correct", False):
                similarity = self._calculate_similarity(student_diagnosis, correct_diagnosis)
                if similarity > 0.8:
                    evaluation["diagnosis_correct"] = True
                    evaluation["feedback"] = f"Your diagnosis is essentially correct, with minor terminology differences. {evaluation.get('feedback', '')}"
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in clinical decision evaluation: {str(e)}")
            return {
                "diagnosis_correct": self._calculate_similarity(student_diagnosis, case_info.get("diagnosis", "")) > 0.8,
                "diagnosis_accuracy_score": 5,
                "test_selection_score": 5,
                "physical_exam_score": 5,
                "efficiency_score": 5,
                "clinical_reasoning_score": 5,
                "overall_clinical_score": 5,
                "missed_critical_tests": [],
                "unnecessary_tests": [],
                "missed_physical_exams": [],
                "actual_diagnosis": case_info.get("diagnosis", "Unknown"),
                "feedback": "An error occurred during evaluation. Please try again."
            }
    
    def _determine_expected_exams(self, case_info: Dict[str, Any]) -> List[str]:
        """
        Determine which physical examinations should be performed based on the case.
        
        Args:
            case_info: Information about the current case
            
        Returns:
            List of expected physical examination systems
        """
        # Default exams that should always be performed
        default_exams = ["vital_signs", "general"]
        
        # Extract relevant symptoms to determine which body systems should be examined
        symptoms = case_info.get("symptoms", [])
        if isinstance(symptoms, dict):
            # Handle symptoms in system-based format
            symptom_systems = symptoms.keys()
        else:
            # Try to infer systems from symptom descriptions
            symptom_systems = []
            system_keywords = {
                "cardiovascular": ["chest", "heart", "palpitation", "edema", "swelling", "pressure"],
                "respiratory": ["breath", "cough", "lung", "wheeze", "respiratory", "dyspnea", "chest"],
                "gastrointestinal": ["abdom", "stomach", "nausea", "vomit", "diarrhea", "bowel", "digest"],
                "neurological": ["head", "dizz", "numbness", "tingling", "vision", "speech", "balance", "consciousness"],
                "musculoskeletal": ["joint", "muscle", "pain", "weak", "back", "bone", "movement"],
                "skin": ["rash", "itch", "lesion", "skin", "color"],
                "heent": ["head", "eye", "ear", "nose", "throat", "face", "vision", "hearing"]
            }
            
            # Check each symptom for keywords
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                for system, keywords in system_keywords.items():
                    if any(keyword in symptom_lower for keyword in keywords):
                        symptom_systems.append(system)
        
        # Add relevant systems to expected exams
        expected_exams = default_exams.copy()
        expected_exams.extend(list(set(symptom_systems)))
        
        # Convert to unique list
        return list(set(expected_exams))
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity for basic matching.
        """
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Check for direct substring
        if s1 in s2 or s2 in s1:
            return 0.9
            
        # Check for word overlap
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


class PhysicalExamEvaluator:
    """
    Evaluates the student's physical examination approach and technique.
    """
    def __init__(self, config):
        self.config = config
        self.client = Client(api_key=config.openai_api_key)
    
    def evaluate_physical_exams(
        self,
        physical_exams: List[Dict[str, Any]],
        verified_procedures: List[Dict[str, Any]],  # Added parameter for procedure verification
        case_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates the student's physical examination approach.
        
        Args:
            physical_exams: List of physical examinations performed by the student
            verified_procedures: List of verified examination procedures
            case_info: Information about the current case
            
        Returns:
            Dict containing evaluation of physical examination skills
        """
        if not physical_exams and not verified_procedures:
            return {
                "thoroughness_score": 0,
                "relevance_score": 0,
                "efficiency_score": 0,
                "procedural_score": 0,
                "sequence_score": 0,
                "overall_exam_score": 0,
                "strengths": [],
                "areas_for_improvement": ["No physical examinations were performed."],
                "missed_key_exams": [],
                "unnecessary_exams": [],
                "feedback": "You did not perform any physical examinations. Physical examination is a critical part of clinical assessment."
            }
        
        try:
            # Extract performed exam systems
            performed_systems = [exam.get("system", "") for exam in physical_exams]
            
            # Extract verified procedures
            performed_procedures = [proc.get("exam_name", "") for proc in verified_procedures]
            procedure_scores = [proc.get("procedure_score", 0) for proc in verified_procedures]
            
            # Calculate average procedure score if available
            avg_procedure_score = sum(procedure_scores) / len(procedure_scores) if procedure_scores else 0
            
            # Determine which exams should have been performed based on case
            expected_systems = self._determine_expected_exams(case_info)
            
            # Format for evaluation
            formatted_exams = []
            for exam in physical_exams:
                formatted_exams.append({
                    "system": exam.get("system", "Unknown"),
                    "timestamp": exam.get("timestamp", "Unknown")
                })
            
            formatted_procedures = []
            for proc in verified_procedures:
                formatted_procedures.append({
                    "exam_name": proc.get("exam_name", "Unknown"),
                    "procedure_score": proc.get("procedure_score", 0),
                    "timestamp": proc.get("timestamp", "Unknown")
                })
            
            # Create a prompt for evaluation
            system_prompt = f"""You are a medical education expert evaluating a medical student's physical examination skills.

Case Information:
- Diagnosis: {case_info.get('diagnosis', case_info.get('expected_diagnosis', 'Unknown'))}
- Key symptoms: {json.dumps(case_info.get('symptoms', []))}
- Expected physical exams: {json.dumps(expected_systems)}

Student's physical examinations:
{json.dumps(formatted_exams, indent=2)}

Student's verified examination procedures:
{json.dumps(formatted_procedures, indent=2)}

Evaluate the following aspects:
1. Thoroughness (Did they perform all necessary examinations?)
2. Relevance (Were the examinations chosen relevant to the case?)
3. Efficiency (Did they avoid unnecessary examinations?)
4. Sequence (Did they perform examinations in a logical order?)
5. Procedural skill (Did they demonstrate knowledge of proper examination techniques?)

Rate each area on a scale of 1-10.
Identify specific strengths and areas for improvement.
Provide actionable feedback to help the student improve.

Return a JSON object with these fields:
- thoroughness_score: int (1-10)
- relevance_score: int (1-10)
- efficiency_score: int (1-10)
- sequence_score: int (1-10)
- procedural_score: int (1-10) - based on their demonstrated knowledge of procedures
- overall_exam_score: int (1-10)
- strengths: array of strings
- areas_for_improvement: array of strings
- missed_key_exams: array of strings (important exams they should have done)
- unnecessary_exams: array of strings (exams that weren't needed)
- feedback: string with overall assessment and advice
"""

            # Call LLM for evaluation
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Evaluate the student's physical examination approach"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Include procedure score if we have verified procedures
            if verified_procedures:
                if "procedural_score" not in evaluation:
                    evaluation["procedural_score"] = int(min(10, avg_procedure_score / 10))
            else:
                evaluation["procedural_score"] = 0
                if "areas_for_improvement" not in evaluation:
                    evaluation["areas_for_improvement"] = []
                evaluation["areas_for_improvement"].append(
                    "No properly verified examination procedures were performed. Demonstrating procedural knowledge is important."
                )
            
            # Ensure all expected fields are present
            expected_fields = [
                "thoroughness_score", "relevance_score", "efficiency_score", "sequence_score",
                "procedural_score", "overall_exam_score", "strengths", "areas_for_improvement", 
                "missed_key_exams", "unnecessary_exams", "feedback"
            ]
            
            for field in expected_fields:
                if field not in evaluation:
                    if field.endswith("_score"):
                        evaluation[field] = 5  # Default middle score
                    elif field in ["strengths", "areas_for_improvement", "missed_key_exams", "unnecessary_exams"]:
                        evaluation[field] = []
                    else:
                        evaluation[field] = "No evaluation available."
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error in physical exam evaluation: {str(e)}")
            return {
                "thoroughness_score": 5,
                "relevance_score": 5,
                "efficiency_score": 5,
                "sequence_score": 5,
                "procedural_score": 0 if not verified_procedures else int(min(10, avg_procedure_score / 10)),
                "overall_exam_score": 5,
                "strengths": [],
                "areas_for_improvement": ["Unable to evaluate physical examinations due to a technical error."],
                "missed_key_exams": [],
                "unnecessary_exams": [],
                "feedback": "An error occurred during evaluation. Please try again."
            }
    
    def _determine_expected_exams(self, case_info: Dict[str, Any]) -> List[str]:
        """
        Determine which physical examinations should be performed based on the case.
        
        Args:
            case_info: Information about the current case
            
        Returns:
            List of expected physical examination systems
        """
        # Default exams that should always be performed
        default_exams = ["vital_signs", "general"]
        
        # Extract relevant symptoms to determine which body systems should be examined
        symptoms = case_info.get("symptoms", [])
        if isinstance(symptoms, dict):
            # Handle symptoms in system-based format
            symptom_systems = symptoms.keys()
        else:
            # Try to infer systems from symptom descriptions
            symptom_systems = []
            system_keywords = {
                "cardiovascular": ["chest", "heart", "palpitation", "edema", "swelling", "pressure"],
                "respiratory": ["breath", "cough", "lung", "wheeze", "respiratory", "dyspnea", "chest"],
                "gastrointestinal": ["abdom", "stomach", "nausea", "vomit", "diarrhea", "bowel", "digest"],
                "neurological": ["head", "dizz", "numbness", "tingling", "vision", "speech", "balance", "consciousness"],
                "musculoskeletal": ["joint", "muscle", "pain", "weak", "back", "bone", "movement"],
                "skin": ["rash", "itch", "lesion", "skin", "color"],
                "heent": ["head", "eye", "ear", "nose", "throat", "face", "vision", "hearing"]
            }
            
            # Check each symptom for keywords
            if isinstance(symptoms, list):
                for symptom in symptoms:
                    if isinstance(symptom, str):
                        symptom_lower = symptom.lower()
                        for system, keywords in system_keywords.items():
                            if any(keyword in symptom_lower for keyword in keywords):
                                symptom_systems.append(system)
            
            # Also check presenting complaint
            if "presenting_complaint" in case_info and isinstance(case_info["presenting_complaint"], str):
                complaint = case_info["presenting_complaint"].lower()
                for system, keywords in system_keywords.items():
                    if any(keyword in complaint for keyword in keywords):
                        symptom_systems.append(system)
        
        # Also examine based on specialty
        specialty = case_info.get("specialty", "").lower()
        if "cardio" in specialty:
            symptom_systems.append("cardiovascular")
        elif "neuro" in specialty:
            symptom_systems.append("neurological")
        elif "pulmon" in specialty or "respiratory" in specialty:
            symptom_systems.append("respiratory")
        elif "gastro" in specialty:
            symptom_systems.append("gastrointestinal")
        elif "ortho" in specialty:
            symptom_systems.append("musculoskeletal")
        elif "derma" in specialty:
            symptom_systems.append("skin")
        
        # Add relevant systems to expected exams
        expected_exams = default_exams.copy()
        expected_exams.extend(list(set(symptom_systems)))
        
        # Convert to unique list
        return list(set(expected_exams))


class DiagnosisEvaluator:
    """
    Main evaluator that combines interaction, clinical decision, and physical exam evaluation
    to provide comprehensive feedback.
    """
    def __init__(self, case: Dict[str, Any], config):
        self.case = case
        self.config = config
        self.interaction_evaluator = InteractionEvaluator(config)
        self.clinical_evaluator = ClinicalDecisionEvaluator(config)
        self.physical_exam_evaluator = PhysicalExamEvaluator(config)
    
    # Modified evaluate method for DiagnosisEvaluator class in evaluation.py

    def evaluate(self, 
            student_diagnosis: str,
            ordered_tests: Set[str],
            ordered_imaging: Set[str],
            interactions: List[Dict[str, str]],
            physical_exams: List[Dict[str, Any]] = None,
            verified_procedures: List[Dict[str, Any]] = None,
            notes: Dict[str, str] = None,
            timestamp_data: Dict[str, Any] = None  # New parameter
        ) -> Dict[str, Any]:
        """
        Performs a comprehensive evaluation of the student's performance.
        
        Args:
            student_diagnosis: The diagnosis provided by the student
            ordered_tests: Tests ordered by the student
            ordered_imaging: Imaging studies ordered by the student
            interactions: List of student-patient interactions
            physical_exams: List of physical examinations performed by the student
            verified_procedures: List of verified examination procedures
            notes: SOAP notes created by the student
            timestamp_data: Timestamp and workflow data for time-based evaluation
            
        Returns:
            Dict containing comprehensive evaluation results
        """
        # Validate case data first
        if not self.case or not isinstance(self.case, dict):
            logger.error("Invalid case data for evaluation")
            return {
                "correct": False,
                "actual_diagnosis": "Unknown - Case data error",
                "feedback": "Error: The case data is not properly initialized. Please start a new case."
            }
            
        # Ensure diagnosis exists in the case
        actual_diagnosis = self.case.get("diagnosis")
        if not actual_diagnosis:
            # Try different keys used in the case generation
            actual_diagnosis = self.case.get("expected_diagnosis")
            if not actual_diagnosis:
                actual_diagnosis = self.case.get("expected_correct_diagnosis", "Unspecified illness")
            # Store it back in the standard field
            self.case["diagnosis"] = actual_diagnosis
        
        # Use empty lists if parameters are None
        if physical_exams is None:
            physical_exams = []
            
        if verified_procedures is None:
            verified_procedures = []
        
        if notes is None:
            notes = {}
        
        # Get interaction evaluation
        interaction_eval = self.interaction_evaluator.evaluate_interactions(
            interactions, self.case
        )
        
        # Get physical exam evaluation with verified procedures
        physical_eval = self.physical_exam_evaluator.evaluate_physical_exams(
            physical_exams, verified_procedures, self.case
        )
        
        # Get clinical decision evaluation
        clinical_eval = self.clinical_evaluator.evaluate_clinical_decisions(
            student_diagnosis, ordered_tests, ordered_imaging, physical_exams, self.case
        )
        
        # Get notes evaluation if notes are provided
        notes_eval = {}
        if notes and any(notes.values()):
            notes_evaluator = NotesEvaluator(self.config)
            notes_eval = notes_evaluator.evaluate_notes(notes, self.case)
        else:
            notes_eval = {
                "completeness_score": 0,
                "organization_score": 0,
                "accuracy_score": 0,
                "terminology_score": 0,
                "assessment_plan_score": 0,
                "overall_notes_score": 0,
                "strengths": [],
                "areas_for_improvement": ["No notes were created."],
                "feedback": "No patient notes were recorded. Creating detailed SOAP notes is an essential part of clinical practice."
            }
        
        # Get timestamp evaluation if timestamp data is provided
        timestamp_eval = {}
        if timestamp_data and timestamp_data.get("timeline") and timestamp_data.get("efficiency_metrics"):
            timestamp_evaluator = TimestampEvaluator(self.config)
            timestamp_eval = timestamp_evaluator.evaluate_timestamps(
                timestamp_data["timeline"],
                timestamp_data["efficiency_metrics"],
                self.case
            )
        else:
            timestamp_eval = {
                "efficiency_score": 0,
                "prioritization_score": 0,
                "logical_progression_score": 0,
                "guideline_adherence_score": 0,
                "time_sensitivity_score": 0,
                "overall_workflow_score": 0,
                "strengths": [],
                "areas_for_improvement": ["Timestamp data not available for evaluation."],
                "feedback": "No timestamp data was available for workflow evaluation."
            }
        
        # Determine correctness based on exact match or close match
        diagnosis_correct = clinical_eval.get("diagnosis_correct", False)
        
        # Add basic exact matching as a fallback
        if not diagnosis_correct:
            # Clean and normalize diagnoses for comparison
            student_diag_clean = student_diagnosis.lower().strip()
            actual_diag_clean = actual_diagnosis.lower().strip()
            
            # Check for exact match or substring match
            if student_diag_clean == actual_diag_clean or \
            student_diag_clean in actual_diag_clean or \
            actual_diag_clean in student_diag_clean:
                diagnosis_correct = True
        
        # Combine evaluations
        combined_eval = {
            # Overall correctness from clinical evaluation
            "correct": diagnosis_correct,
            "actual_diagnosis": actual_diagnosis,
            
            # Detailed scores
            "scores": {
                # Communication skills
                "communication": interaction_eval.get("communication_score", 0),
                "empathy": interaction_eval.get("empathy_score", 0),
                "interview_technique": interaction_eval.get("interview_technique_score", 0),
                
                # Physical examination
                "exam_thoroughness": physical_eval.get("thoroughness_score", 0),
                "exam_relevance": physical_eval.get("relevance_score", 0),
                "exam_efficiency": physical_eval.get("efficiency_score", 0),
                "procedural_skill": physical_eval.get("procedural_score", 0),
                
                # Clinical decision making
                "diagnosis_accuracy": clinical_eval.get("diagnosis_accuracy_score", 0),
                "test_selection": clinical_eval.get("test_selection_score", 0),
                "clinical_reasoning": clinical_eval.get("clinical_reasoning_score", 0),
                "resource_efficiency": clinical_eval.get("efficiency_score", 0),
                
                # Notes evaluation
                "notes_completeness": notes_eval.get("completeness_score", 0),
                "notes_organization": notes_eval.get("organization_score", 0),
                "notes_accuracy": notes_eval.get("accuracy_score", 0),
                "notes_terminology": notes_eval.get("terminology_score", 0),
                "notes_assessment": notes_eval.get("assessment_plan_score", 0),
                
                # Timestamp evaluation 
                "workflow_efficiency": timestamp_eval.get("efficiency_score", 0),
                "test_prioritization": timestamp_eval.get("prioritization_score", 0),
                "logical_progression": timestamp_eval.get("logical_progression_score", 0),
                "guideline_adherence": timestamp_eval.get("guideline_adherence_score", 0),
                "time_sensitivity": timestamp_eval.get("time_sensitivity_score", 0)
            },
            
            # Overall scores for major categories
            "overall_interaction_score": interaction_eval.get("overall_interaction_score", 0),
            "overall_physical_exam_score": physical_eval.get("overall_exam_score", 0),
            "overall_clinical_score": clinical_eval.get("overall_clinical_score", 0),
            "overall_notes_score": notes_eval.get("overall_notes_score", 0),
            "overall_workflow_score": timestamp_eval.get("overall_workflow_score", 0),
            
            # Specific feedback elements
            "interaction_strengths": interaction_eval.get("strengths", []),
            "interaction_improvements": interaction_eval.get("areas_for_improvement", []),
            
            "physical_exam_strengths": physical_eval.get("strengths", []),
            "physical_exam_improvements": physical_eval.get("areas_for_improvement", []),
            "missed_key_exams": physical_eval.get("missed_key_exams", []),
            "unnecessary_exams": physical_eval.get("unnecessary_exams", []),
            
            "missed_critical_tests": clinical_eval.get("missed_critical_tests", []),
            "unnecessary_tests": clinical_eval.get("unnecessary_tests", []),
            
            "notes_strengths": notes_eval.get("strengths", []),
            "notes_improvements": notes_eval.get("areas_for_improvement", []),
            
            "workflow_strengths": timestamp_eval.get("strengths", []),
            "workflow_improvements": timestamp_eval.get("areas_for_improvement", []),
            
            # Add timeline data for visualization
            "timeline_data": timestamp_data.get("timeline", []) if timestamp_data else [],
            "efficiency_metrics": timestamp_data.get("efficiency_metrics", {}) if timestamp_data else {},
            
            # Category feedback
            "interaction_feedback": interaction_eval.get("feedback", ""),
            "physical_exam_feedback": physical_eval.get("feedback", ""),
            "clinical_feedback": clinical_eval.get("feedback", ""),
            "notes_feedback": notes_eval.get("feedback", ""),
            "workflow_feedback": timestamp_eval.get("feedback", ""),
            
            # Combined feedback
            "feedback": self._generate_combined_feedback(
                interaction_eval, physical_eval, clinical_eval, notes_eval, timestamp_eval
            )
        }
        
        return combined_eval
    
    def _generate_combined_feedback(
    self, 
    interaction_eval: Dict[str, Any],
    physical_eval: Dict[str, Any],
    clinical_eval: Dict[str, Any],
    notes_eval: Dict[str, Any],
    timestamp_eval: Dict[str, Any]  # New parameter
) -> str:
        """
        Generates combined feedback from all evaluations.
        
        Args:
            interaction_eval: Results of interaction evaluation
            physical_eval: Results of physical examination evaluation
            clinical_eval: Results of clinical decision evaluation
            notes_eval: Results of notes evaluation
            timestamp_eval: Results of timestamp evaluation
            
        Returns:
            String containing combined feedback
        """
        # Diagnosis correctness assessment
        if clinical_eval.get("diagnosis_correct", False):
            diagnosis_feedback = "Your diagnosis was correct. "
        else:
            diagnosis_feedback = f"Your diagnosis was incorrect. The correct diagnosis is {clinical_eval.get('actual_diagnosis', 'unknown')}. "
        
        # Communication assessment
        interaction_score = interaction_eval.get("overall_interaction_score", 0)
        if interaction_score >= 8:
            communication_feedback = "Your communication with the patient was excellent. "
        elif interaction_score >= 6:
            communication_feedback = "Your communication with the patient was good, but has room for improvement. "
        else:
            communication_feedback = "Your communication with the patient needs significant improvement. "
        
        # Physical examination assessment
        physical_score = physical_eval.get("overall_exam_score", 0)
        if physical_score >= 8:
            physical_feedback = "Your physical examination approach was thorough and appropriate. "
        elif physical_score >= 6:
            physical_feedback = "Your physical examination was adequate but could be improved. "
        elif physical_score > 0:  # Only include if they did some exams
            physical_feedback = "Your physical examination approach needs significant improvement. "
        else:
            physical_feedback = "You did not perform physical examinations, which is a critical omission. "
        
        # Clinical reasoning assessment
        clinical_score = clinical_eval.get("overall_clinical_score", 0)
        if clinical_score >= 8:
            clinical_feedback = "Your clinical reasoning was very strong. "
        elif clinical_score >= 6:
            clinical_feedback = "Your clinical reasoning was adequate but could be improved. "
        else:
            clinical_feedback = "Your clinical reasoning needs significant improvement. "
        
        # Notes assessment
        notes_score = notes_eval.get("overall_notes_score", 0)
        if notes_score >= 8:
            notes_feedback = "Your patient documentation was comprehensive and well-structured. "
        elif notes_score >= 6:
            notes_feedback = "Your patient notes were adequate but could be improved. "
        elif notes_score > 0:  # Only include if they created notes
            notes_feedback = "Your patient documentation needs significant improvement. "
        else:
            notes_feedback = "You did not create patient notes, which is an essential part of clinical practice. "
        
        # Workflow timing assessment (new)
        workflow_score = timestamp_eval.get("overall_workflow_score", 0)
        if workflow_score >= 8:
            workflow_feedback = "Your clinical workflow was highly efficient and well-prioritized. "
        elif workflow_score >= 6:
            workflow_feedback = "Your clinical workflow was reasonably efficient with appropriate prioritization of tasks. "
        elif workflow_score > 0:  # Only include if there is a score
            workflow_feedback = "Your clinical workflow efficiency needs significant improvement. "
        else:
            workflow_feedback = ""
        
        # Combine all feedback
        combined = f"{diagnosis_feedback}{communication_feedback}{physical_feedback}{clinical_feedback}{notes_feedback}{workflow_feedback}\n\n"
        
        # Add specific points from each evaluation
        combined += "Key observations:\n"
        
        # Add interaction strengths
        strengths = interaction_eval.get("strengths", [])
        if strengths:
            combined += "\nStrengths in patient interaction:\n"
            for strength in strengths[:3]:  # Limit to top 3
                combined += f"- {strength}\n"
        
        # Add interaction improvement areas
        improvements = interaction_eval.get("areas_for_improvement", [])
        if improvements:
            combined += "\nAreas to improve in patient interaction:\n"
            for improvement in improvements[:3]:  # Limit to top 3
                combined += f"- {improvement}\n"
        
        # Add physical exam feedback
        missed_exams = physical_eval.get("missed_key_exams", [])
        if missed_exams:
            combined += "\nMissed important physical examinations:\n"
            for exam in missed_exams:
                combined += f"- {exam}\n"
        
        # Add clinical feedback
        missed_tests = clinical_eval.get("missed_critical_tests", [])
        if missed_tests:
            combined += "\nMissed critical tests/studies:\n"
            for test in missed_tests:
                combined += f"- {test}\n"
        
        # Add notes feedback
        notes_strengths = notes_eval.get("strengths", [])
        if notes_strengths:
            combined += "\nStrengths in patient documentation:\n"
            for strength in notes_strengths[:2]:  # Limit to top 2
                combined += f"- {strength}\n"
                
        notes_improvements = notes_eval.get("areas_for_improvement", [])
        if notes_improvements:
            combined += "\nAreas to improve in patient documentation:\n"
            for improvement in notes_improvements[:3]:  # Limit to top 3
                combined += f"- {improvement}\n"
        
        # Add workflow feedback (new)
        workflow_strengths = timestamp_eval.get("strengths", [])
        if workflow_strengths:
            combined += "\nStrengths in clinical workflow:\n"
            for strength in workflow_strengths[:2]:  # Limit to top 2
                combined += f"- {strength}\n"
                
        workflow_improvements = timestamp_eval.get("areas_for_improvement", [])
        if workflow_improvements:
            combined += "\nAreas to improve in clinical workflow:\n"
            for improvement in workflow_improvements[:3]:  # Limit to top 3
                combined += f"- {improvement}\n"
        
        return combined