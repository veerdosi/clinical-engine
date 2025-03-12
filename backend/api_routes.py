import logging
from flask import request, jsonify, Blueprint
from datetime import datetime
from PIL import Image
import requests
import io
import os
import time

logger = logging.getLogger(__name__)

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

class APIRoutes:
    """
    Defines and manages API routes for the application.
    """
    def __init__(self, case_manager, session_manager, chat_handler, 
                lab_system=None, imaging_system=None, physical_exam_system=None):
        self.case_manager = case_manager
        self.session_manager = session_manager
        self.chat_handler = chat_handler
        self.lab_system = lab_system
        self.imaging_system = imaging_system
        self.physical_exam_system = physical_exam_system
        
    def register_routes(self, blueprint):
        """
        Registers all API routes with the provided blueprint.
        
        Args:
            blueprint: Flask Blueprint to register routes on
        """
        # Health check endpoint
        @blueprint.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy"})
        
        # Current case endpoint
        @blueprint.route('/current-case', methods=['GET'])
        def get_current_case():
            try:
                sanitized_case = self.case_manager.get_sanitized_case()
                if sanitized_case:
                    return jsonify(sanitized_case)
                else:
                    return jsonify({"error": "No active case"}), 404
            except Exception as e:
                logger.error(f"Error getting current case: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # New case endpoint
        @blueprint.route('/new-case', methods=['POST'])
        def create_new_case():
            try:
                data = request.get_json() or {}
                specialty = data.get('specialty')
                difficulty = data.get('difficulty')
                
                new_case = self.case_manager.generate_new_case(specialty, difficulty)
                self.session_manager.reset_session(new_case.get("id"))
                
                return jsonify(self.case_manager.get_sanitized_case())
            except Exception as e:
                logger.error(f"Error creating new case: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @blueprint.route('/session-timeline', methods=['GET'])
        def get_session_timeline():
            try:
                # Get timeline data from session manager
                timeline = self.session_manager.get_session_timeline()
                efficiency_metrics = self.session_manager.get_efficiency_metrics()
                
                # Return the data
                return jsonify({
                    "timeline": timeline,
                    "efficiency_metrics": efficiency_metrics
                })
            except Exception as e:
                logger.error(f"Error getting session timeline: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Notes API endpoints
        @blueprint.route('/save-notes', methods=['POST'])
        def save_notes():
            try:
                data = request.get_json()
                if not data or 'notes' not in data:
                    return jsonify({"error": "No notes provided"}), 400
                    
                notes = data.get('notes', {})
                case_id = data.get('case_id', 'current')
                
                # Store notes in session manager
                self.session_manager.save_notes(notes)
                
                return jsonify({"success": True, "message": "Notes saved successfully"})
            except Exception as e:
                logger.error(f"Error saving notes: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @blueprint.route('/evaluate-notes', methods=['POST'])
        def evaluate_notes():
            try:
                data = request.get_json()
                case_id = data.get('case_id', 'current')
                
                # Get the current case
                current_case = self.case_manager.get_current_case()
                if not current_case:
                    return jsonify({"error": "No active case"}), 404
                    
                # Get the notes from session manager
                notes = self.session_manager.get_notes()
                
                if not notes or not any(notes.values()):
                    return jsonify({"error": "No notes to evaluate"}), 400
                
                # Get the evaluator
                from backend.evaluation import NotesEvaluator
                notes_evaluator = NotesEvaluator(self.case_manager.config)
                
                # Evaluate the notes
                evaluation_result = notes_evaluator.evaluate_notes(notes, current_case)
                
                return jsonify(evaluation_result)
            except Exception as e:
                logger.error(f"Error evaluating notes: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @blueprint.route('/submit-diagnosis', methods=['POST'])
        def evaluate_diagnosis():
            try:
                data = request.get_json()
                if not data or 'diagnosis' not in data:
                    return jsonify({"error": "No diagnosis provided"}), 400
                    
                student_diagnosis = data.get('diagnosis', '').strip()
                case_id = data.get('case_id', 'current')
                
                # Get notes from the request or session manager
                notes = data.get('notes', None) or self.session_manager.get_notes()
                
                logger.info(f"Evaluating diagnosis: {student_diagnosis} for case {case_id}")
                
                if not student_diagnosis:
                    return jsonify({"error": "Diagnosis cannot be empty"}), 400
                    
                # Get the evaluator
                evaluator = self.case_manager.get_diagnosis_evaluator()
                if not evaluator:
                    return jsonify({"error": "No active case for evaluation"}), 400
                
                # Get verified procedures from session manager with fallback
                try:
                    verified_procedures = self.session_manager.get_verified_exam_procedures()
                except AttributeError:
                    logger.warning("Session manager missing get_verified_exam_procedures method. Using empty list.")
                    verified_procedures = []
                
                # Record diagnosis submission timestamp
                self.session_manager.record_diagnosis_submission(student_diagnosis)
                
                # Get timestamp data for evaluation
                timeline = self.session_manager.get_session_timeline()
                efficiency_metrics = self.session_manager.get_efficiency_metrics()
                timestamp_data = {
                    "timeline": timeline,
                    "efficiency_metrics": efficiency_metrics
                }
                
                # Evaluate the diagnosis with all available data
                evaluation_result = evaluator.evaluate(
                    student_diagnosis,
                    self.session_manager.get_ordered_tests(),
                    self.session_manager.get_ordered_imaging(),
                    self.session_manager.get_patient_interactions(),
                    self.session_manager.get_physical_exams(),
                    verified_procedures,
                    notes,
                    timestamp_data  # New parameter
                )
                
                return jsonify(evaluation_result)
            except Exception as e:
                logger.error(f"Error evaluating diagnosis: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Order lab tests endpoint
        @blueprint.route('/order-lab', methods=['POST'])
        def order_lab_test():
            try:
                data = request.get_json()
                if not data or 'test' not in data:
                    return jsonify({"error": "No test specified"}), 400
                    
                test_name = data.get('test', '').strip()
                if not test_name:
                    return jsonify({"error": "Test name cannot be empty"}), 400
                
                # Record the test order
                result = self.session_manager.order_test(test_name)
                
                # Generate lab results if lab system available
                if self.lab_system:
                    current_case = self.case_manager.get_current_case()
                    
                    # Validate the test order
                    is_valid, error_msg = self.lab_system.validate_test_order(
                        [test_name],
                        self.session_manager.get_ordered_tests(),
                        self.session_manager.get_ordered_imaging()
                    )
                    
                    if not is_valid:
                        return jsonify({"success": False, "message": error_msg}), 400
                    
                    # Generate report
                    lab_results = self.lab_system.generate_report(current_case, [test_name])
                    
                    # Generate markdown report for display
                    markdown_report = self.lab_system.generate_markdown_report(lab_results)
                    
                    return jsonify({
                        "message": f"Test '{test_name}' ordered successfully",
                        "markdown": markdown_report
                    })
                else:
                    # Basic response if lab system not available
                    return jsonify({
                        "message": f"Test '{test_name}' ordered successfully",
                        "results": None
                    })
            except Exception as e:
                logger.error(f"Error ordering lab test: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @blueprint.route('/order-imaging', methods=['POST'])
        def order_imaging():
            try:
                data = request.get_json()
                if not data or 'imaging' not in data:
                    return jsonify({"error": "No imaging study specified"}), 400
                    
                imaging_name = data.get('imaging', '').strip()
                if not imaging_name:
                    return jsonify({"error": "Imaging study name cannot be empty"}), 400
                
                # Record the imaging order
                result = self.session_manager.order_imaging(imaging_name)
                
                # Generate report if imaging system available
                if self.imaging_system:
                    current_case = self.case_manager.get_current_case()
                    imaging_report = self.imaging_system.generate_report(current_case, imaging_name)

                    # Generate markdown report for display
                    markdown_report = self.imaging_system.generate_markdown_report(imaging_report)
                    
                    # Generate image prompt
                    image_prompt = self.imaging_system.generate_image_prompt(current_case, imaging_name)
                    
                    # Define path to save the generated image
                    image_filename = f"{imaging_name.replace(' ', '_').lower()}_{int(time.time())}.png"
                    image_dir = os.path.join("static", "generated_images")
                    os.makedirs(image_dir, exist_ok=True)
                    image_path = os.path.join(image_dir, image_filename)
                    
                    # Generate and save the image
                    image_success = False
                    image_url = None
                    
                    try:
                        # Call the image API and save the result
                        image = self.imaging_system.call_image_api(image_prompt, image_path)
                        if image:
                            image_success = True
                            # Create URL path for the image (relative to your static folder)
                            image_url = f"/static/generated_images/{image_filename}"
                    except Exception as img_err:
                        logger.error(f"Error generating image: {str(img_err)}")
                    
                    return jsonify({
                        "success": True,
                        "message": f"Imaging study '{imaging_name}' ordered successfully",
                        "report": imaging_report,
                        "markdown": markdown_report,
                        "image_generated": image_success,
                        "image_url": image_url,
                        # "image_prompt": image_prompt  # Optional: include the prompt for debugging
                    })
                else:
                    # Basic response if imaging system not available
                    return jsonify({
                        "success": True,
                        "message": f"Imaging study '{imaging_name}' ordered successfully",
                        "report": None
                    })
            except Exception as e:
                logger.error(f"Error ordering imaging: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Physical examination endpoint
        @blueprint.route('/physical-exam', methods=['POST'])
        def perform_physical_exam():
            try:
                data = request.get_json()
                if not data or 'system' not in data:
                    return jsonify({"error": "No body system specified"}), 400
                    
                system = data.get('system', '').strip()
                procedure_verified = data.get('procedure_verified', False)
                
                if not system:
                    return jsonify({"error": "Body system cannot be empty"}), 400
                
                # Perform examination if physical exam system available
                if self.physical_exam_system:
                    current_case = self.case_manager.get_current_case()
                    exam_results = self.physical_exam_system.perform_examination(
                        current_case, 
                        system,
                        procedure_verified
                    )
                    
                    # Only track verified examinations or vital signs in the session manager
                    if procedure_verified or system.lower() == 'vital_signs':
                        self.session_manager.add_physical_exam(system, exam_results.get("findings", {}))
                    
                    return jsonify(exam_results)
                else:
                    # Basic response if physical exam system not available
                    return jsonify({
                        "findings": "Physical examination system not available",
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error performing physical examination: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        @blueprint.route('/verify-physical-exam', methods=['POST'])
        def verify_physical_exam():
            try:
                data = request.get_json()
                if not data or 'exam_name' not in data or 'steps' not in data:
                    return jsonify({"error": "Missing exam name or steps"}), 400
                    
                exam_name = data.get('exam_name', '').strip()
                procedure_steps = data.get('steps', [])
                
                if not exam_name:
                    return jsonify({"error": "Exam name cannot be empty"}), 400
                
                if not procedure_steps or not isinstance(procedure_steps, list):
                    return jsonify({"error": "Procedure steps must be a non-empty list"}), 400
                
                # Verify the procedure steps using the physical exam system
                current_case = self.case_manager.get_current_case()
                if not current_case:
                    return jsonify({"error": "No active case"}), 404
                    
                verification_result = self.physical_exam_system.verify_procedure(
                    current_case, 
                    exam_name, 
                    procedure_steps
                )
                
                # If procedure is correct, track it in the session manager
                if verification_result.get("is_correct", False):
                    # Use add_verified_exam_procedure from the session manager
                    self.session_manager.add_verified_exam_procedure(
                        exam_name, 
                        procedure_steps, 
                        verification_result.get("score", 0)
                    )
                
                return jsonify(verification_result)
            except Exception as e:
                logger.error(f"Error verifying physical examination procedure: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Get lab history endpoint
        @blueprint.route('/lab-history', methods=['GET'])
        def get_lab_history():
            try:
                if not self.lab_system:
                    return jsonify({"error": "Lab system not available"}), 404
                
                test_name = request.args.get('test')
                current_case = self.case_manager.get_current_case()
                
                if not current_case:
                    return jsonify({"error": "No active case"}), 404
                
                history = self.lab_system.get_test_history(current_case.get("id"), test_name)
                return jsonify({"history": history})
            except Exception as e:
                logger.error(f"Error getting lab history: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Evaluate interactions separately endpoint
        @blueprint.route('/evaluate-interactions', methods=['POST'])
        def evaluate_interactions():
            try:
                # Get the current case
                current_case = self.case_manager.get_current_case()
                if not current_case:
                    return jsonify({"error": "No active case"}), 404
                
                # Create an interaction evaluator
                from backend.evaluation import InteractionEvaluator
                interaction_evaluator = InteractionEvaluator(self.case_manager.config)
                
                # Get interactions from session manager
                interactions = self.session_manager.get_patient_interactions()
                
                # Evaluate interactions
                evaluation = interaction_evaluator.evaluate_interactions(interactions, current_case)
                
                return jsonify(evaluation)
            except Exception as e:
                logger.error(f"Error evaluating interactions: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Text chat endpoint
        @blueprint.route('/chat', methods=['POST'])
        def chat():
            try:
                data = request.get_json()
                user_message = data.get("message", "")
                include_voice_response = data.get("includeVoiceResponse", True)
                
                response_data, status_code = self.chat_handler.process_text_chat(
                    user_message,
                    include_voice_response
                )
                
                return jsonify(response_data), status_code
            except Exception as e:
                logger.error(f"Error in chat endpoint: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Voice chat endpoint
        @blueprint.route('/voice-chat', methods=['POST'])
        def voice_chat():
            try:
                include_voice_response_str = request.form.get('includeVoiceResponse', 'true')
                include_voice_response = include_voice_response_str.lower() == 'true'
                is_text_input = request.form.get('isTextInput', 'false').lower() == 'true'
                
                # Check if this is actually a text message sent via voice endpoint
                if is_text_input:
                    text_message = request.form.get('message', '')
                    response_data, status_code = self.chat_handler.process_voice_chat(
                        None,
                        include_voice_response,
                        is_text_input,
                        text_message
                    )
                else:
                    # Regular voice input
                    if 'audio' not in request.files:
                        return jsonify({"error": "No audio file provided"}), 400
                    
                    audio_file = request.files['audio']
                    response_data, status_code = self.chat_handler.process_voice_chat(
                        audio_file,
                        include_voice_response
                    )
                
                return jsonify(response_data), status_code
            except Exception as e:
                logger.error(f"Error in voice chat endpoint: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        # Session summary endpoint
        @blueprint.route('/session-summary', methods=['GET'])
        def session_summary():
            try:
                summary = self.session_manager.get_session_summary()
                return jsonify(summary)
            except Exception as e:
                logger.error(f"Error getting session summary: {str(e)}")
                return jsonify({"error": str(e)}), 500
        
        logger.info("All API routes registered successfully")
        return blueprint