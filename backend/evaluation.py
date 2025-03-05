import json
import logging
from openai import Client
from typing import List, Set, Dict, Any, Optional

logger = logging.getLogger(__name__)

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
        case_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates the student's physical examination approach.
        
        Args:
            physical_exams: List of physical examinations performed by the student
            case_info: Information about the current case
            
        Returns:
            Dict containing evaluation of physical examination skills
        """
        if not physical_exams:
            return {
                "thoroughness_score": 0,
                "relevance_score": 0,
                "efficiency_score": 0,
                "overall_exam_score": 0,
                "strengths": [],
                "areas_for_improvement": ["No physical examinations were performed."],
                "feedback": "You did not perform any physical examinations. Physical examination is a critical part of clinical assessment."
            }
        
        try:
            # Extract performed exam systems
            performed_systems = [exam.get("system", "") for exam in physical_exams]
            
            # Determine which exams should have been performed based on case
            expected_systems = self._determine_expected_exams(case_info)
            
            # Format for evaluation
            formatted_exams = []
            for exam in physical_exams:
                formatted_exams.append({
                    "system": exam.get("system", "Unknown"),
                    "timestamp": exam.get("timestamp", "Unknown")
                })
            
            # Create a prompt for evaluation
            system_prompt = f"""You are a medical education expert evaluating a medical student's physical examination skills.

Case Information:
- Diagnosis: {case_info.get('diagnosis', 'Unknown')}
- Key symptoms: {json.dumps(case_info.get('symptoms', []))}
- Expected physical exams: {json.dumps(expected_systems)}

Student's physical examinations:
{json.dumps(formatted_exams, indent=2)}

Evaluate the following aspects:
1. Thoroughness (Did they perform all necessary examinations?)
2. Relevance (Were the examinations chosen relevant to the case?)
3. Efficiency (Did they avoid unnecessary examinations?)
4. Sequence (Did they perform examinations in a logical order?)

Rate each area on a scale of 1-10.
Identify specific strengths and areas for improvement.
Provide actionable feedback to help the student improve.

Return a JSON object with these fields:
- thoroughness_score: int (1-10)
- relevance_score: int (1-10)
- efficiency_score: int (1-10)
- sequence_score: int (1-10)
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
            
            # Ensure all expected fields are present
            expected_fields = [
                "thoroughness_score", "relevance_score", "efficiency_score", "sequence_score",
                "overall_exam_score", "strengths", "areas_for_improvement", 
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
    
    def evaluate(
        self, 
        student_diagnosis: str,
        ordered_tests: Set[str],
        ordered_imaging: Set[str],
        interactions: List[Dict[str, str]],
        physical_exams: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Performs a comprehensive evaluation of the student's performance.
        
        Args:
            student_diagnosis: The diagnosis provided by the student
            ordered_tests: Tests ordered by the student
            ordered_imaging: Imaging studies ordered by the student
            interactions: List of student-patient interactions
            physical_exams: List of physical examinations performed by the student
            
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
            logger.warning("Case missing diagnosis for evaluation")
            # Set a default diagnosis if missing
            actual_diagnosis = "Unspecified illness"
            self.case["diagnosis"] = actual_diagnosis
        
        # Use empty list if physical_exams is None
        if physical_exams is None:
            physical_exams = []
        
        # Get interaction evaluation
        interaction_eval = self.interaction_evaluator.evaluate_interactions(
            interactions, self.case
        )
        
        # Get physical exam evaluation
        physical_eval = self.physical_exam_evaluator.evaluate_physical_exams(
            physical_exams, self.case
        )
        
        # Get clinical decision evaluation
        clinical_eval = self.clinical_evaluator.evaluate_clinical_decisions(
            student_diagnosis, ordered_tests, ordered_imaging, physical_exams, self.case
        )
        
        # Combine evaluations
        combined_eval = {
            # Overall correctness from clinical evaluation
            "correct": clinical_eval.get("diagnosis_correct", False),
            "actual_diagnosis": clinical_eval.get("actual_diagnosis", "Unknown"),
            
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
                
                # Clinical decision making
                "diagnosis_accuracy": clinical_eval.get("diagnosis_accuracy_score", 0),
                "test_selection": clinical_eval.get("test_selection_score", 0),
                "clinical_reasoning": clinical_eval.get("clinical_reasoning_score", 0),
                "resource_efficiency": clinical_eval.get("efficiency_score", 0),
            },
            
            # Overall scores for major categories
            "overall_interaction_score": interaction_eval.get("overall_interaction_score", 0),
            "overall_physical_exam_score": physical_eval.get("overall_exam_score", 0),
            "overall_clinical_score": clinical_eval.get("overall_clinical_score", 0),
            
            # Specific feedback elements
            "interaction_strengths": interaction_eval.get("strengths", []),
            "interaction_improvements": interaction_eval.get("areas_for_improvement", []),
            
            "physical_exam_strengths": physical_eval.get("strengths", []),
            "physical_exam_improvements": physical_eval.get("areas_for_improvement", []),
            "missed_key_exams": physical_eval.get("missed_key_exams", []),
            "unnecessary_exams": physical_eval.get("unnecessary_exams", []),
            
            "missed_critical_tests": clinical_eval.get("missed_critical_tests", []),
            "unnecessary_tests": clinical_eval.get("unnecessary_tests", []),
            
            # Category feedback
            "interaction_feedback": interaction_eval.get("feedback", ""),
            "physical_exam_feedback": physical_eval.get("feedback", ""),
            "clinical_feedback": clinical_eval.get("feedback", ""),
            
            # Combined feedback
            "feedback": self._generate_combined_feedback(interaction_eval, physical_eval, clinical_eval)
        }
        
        return combined_eval
    
    def _generate_combined_feedback(
        self, 
        interaction_eval: Dict[str, Any],
        physical_eval: Dict[str, Any],
        clinical_eval: Dict[str, Any]
    ) -> str:
        """
        Generates combined feedback from all three evaluations.
        
        Args:
            interaction_eval: Results of interaction evaluation
            physical_eval: Results of physical examination evaluation
            clinical_eval: Results of clinical decision evaluation
            
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
        
        # Combine all feedback
        combined = f"{diagnosis_feedback}{communication_feedback}{physical_feedback}{clinical_feedback}\n\n"
        
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
        
        unnecessary = clinical_eval.get("unnecessary_tests", [])
        if unnecessary:
            combined += "\nUnnecessary tests that could have been avoided:\n"
            for test in unnecessary[:3]:  # Limit to top 3
                combined += f"- {test}\n"
        
        return combined