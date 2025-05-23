import logging
from flask import request, jsonify, Blueprint, g
from datetime import datetime
from PIL import Image
import requests
import io
import os
import time
from .auth import AuthService, login_required
from .user import User

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
        # Add Authentication Routes
        # Google Sign-In route
        @blueprint.route('/auth/google', methods=['POST'])
        def google_auth():
            try:
                data = request.get_json()
                if not data or 'token' not in data:
                    return jsonify({"error": "Invalid request"}), 400

                token = data.get('token')
                auth_service = AuthService()

                # Verify Google token
                user = auth_service.verify_google_token(token)
                if not user:
                    return jsonify({"error": "Invalid Google token"}), 401

                # Generate JWT token
                jwt_token = user.generate_auth_token()

                # Return user info and JWT token
                return jsonify({
                    "token": jwt_token,
                    "user": user.to_dict()
                })
            except Exception as e:
                logger.error(f"Error in Google authentication: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Authentication test endpoint
        @blueprint.route('/auth/test', methods=['GET'])
        @login_required
        def test_auth():
            """Simple endpoint to test if authentication is working"""
            return jsonify({
                "authenticated": True,
                "user": g.user.to_dict() if hasattr(g, 'user') else None
            })

        # User profile route (requires authentication)
        @blueprint.route('/user/profile', methods=['GET'])
        @login_required
        def get_user_profile():
            try:
                # User is already authenticated via @login_required
                user = g.user
                return jsonify({"user": user.to_dict()})
            except Exception as e:
                logger.error(f"Error getting user profile: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Validate token route
        @blueprint.route('/auth/validate', methods=['GET'])
        def validate_token():
            try:
                auth_service = AuthService()
                user = auth_service.authenticate_request()

                if user:
                    return jsonify({
                        "valid": True,
                        "user": user.to_dict()
                    })
                else:
                    return jsonify({"valid": False}), 401
            except Exception as e:
                logger.error(f"Error validating token: {str(e)}")
                return jsonify({"valid": False, "error": str(e)}), 500

        # Evaluation history endpoint
        @blueprint.route('/evaluations/history', methods=['GET'])
        @login_required
        def get_evaluation_history():
            try:
                from .db import mongo
                user = g.user

                # Get paginated evaluations for the user
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 10, type=int)

                # Calculate skip value for pagination
                skip = (page - 1) * per_page

                # Query MongoDB evaluations collection with all needed fields
                evaluations = list(mongo.db.evaluations.find(
                    {"user_id": user.user_id},
                    {
                        "case_info": 1,
                        "student_diagnosis": 1,
                        "evaluation_result.overall_clinical_score": 1,
                        "evaluation_result.diagnosis_correct": 1,
                        "evaluation_result.diagnosis_accuracy_score": 1,
                        "timestamp": 1,
                        "case_id": 1,
                        "session_data.timeline": 1
                    }
                ).sort("timestamp", -1).skip(skip).limit(per_page))

                # Count total evaluations for pagination
                total_evaluations = mongo.db.evaluations.count_documents({"user_id": user.user_id})

                # Format the results for frontend compatibility
                formatted_evaluations = []
                for eval_data in evaluations:
                    # Convert ObjectId to string for JSON serialization
                    eval_copy = eval_data.copy()
                    eval_copy['_id'] = str(eval_data['_id'])
                    eval_copy['id'] = str(eval_data['_id'])  # Add id field for frontend compatibility

                    # Map case_info to case_data for frontend compatibility
                    eval_copy['case_data'] = eval_data.get('case_info', {})

                    # Add is_correct field for frontend compatibility
                    eval_copy['is_correct'] = eval_data.get('evaluation_result', {}).get('diagnosis_correct', False)

                    # Add submission field for frontend compatibility
                    eval_copy['submission'] = {'diagnosis': eval_data.get('student_diagnosis', 'Unknown')}

                    # Calculate time_taken from session timeline if available
                    timeline = eval_data.get('session_data', {}).get('timeline', [])
                    time_taken_seconds = None
                    if timeline:
                        start_time = None
                        end_time = None
                        for event in timeline:
                            if event.get('action') == 'session_start':
                                start_time = event.get('timestamp')
                            elif event.get('action') == 'diagnosis_submitted':
                                end_time = event.get('timestamp')

                        if start_time and end_time:
                            try:
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                time_taken_seconds = (end_dt - start_dt).total_seconds()
                            except Exception as e:
                                logger.warning(f"Error calculating time taken: {str(e)}")

                    eval_copy['time_taken'] = time_taken_seconds
                    formatted_evaluations.append(eval_copy)

                return jsonify({
                    "evaluations": formatted_evaluations,
                    "pagination": {
                        "total": total_evaluations,
                        "page": page,
                        "per_page": per_page,
                        "pages": (total_evaluations + per_page - 1) // per_page  # Ceiling division
                    }
                })
            except Exception as e:
                logger.error(f"Error retrieving evaluation history: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Single evaluation details endpoint
        @blueprint.route('/evaluations/<evaluation_id>', methods=['GET'])
        @login_required
        def get_evaluation_details(evaluation_id):
            try:
                from .db import mongo
                from bson.objectid import ObjectId
                user = g.user

                # Query for the specific evaluation
                try:
                    evaluation = mongo.db.evaluations.find_one({
                        "_id": ObjectId(evaluation_id),
                        "user_id": user.user_id  # Ensure user can only access their own evaluations
                    })
                except Exception as e:
                    logger.error(f"Invalid evaluation ID format: {str(e)}")
                    return jsonify({"error": "Invalid evaluation ID"}), 400

                if not evaluation:
                    return jsonify({"error": "Evaluation not found or access denied"}), 404

                # Convert ObjectId to string for JSON serialization
                evaluation['_id'] = str(evaluation['_id'])

                return jsonify({"evaluation": evaluation})
            except Exception as e:
                logger.error(f"Error retrieving evaluation details: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # User sessions history endpoint
        @blueprint.route('/sessions/history', methods=['GET'])
        @login_required
        def get_session_history():
            try:
                from .db import mongo
                user = g.user

                # Get paginated sessions for the user
                page = request.args.get('page', 1, type=int)
                per_page = request.args.get('per_page', 10, type=int)

                # Calculate skip value for pagination
                skip = (page - 1) * per_page

                # Query MongoDB sessions collection
                sessions = list(mongo.db.sessions.find(
                    {"user_id": user.user_id},
                    {
                        "case_id": 1,
                        "timestamp": 1,
                        "session_start_time": 1,
                        "diagnosis_submission_time": 1,
                        "case_data": 1,
                        "status": 1,
                        "last_updated_at": 1,
                        "time_elapsed": 1
                    }
                ).sort("timestamp", -1).skip(skip).limit(per_page))

                # Count total sessions for pagination
                total_sessions = mongo.db.sessions.count_documents({"user_id": user.user_id})

                # Format the results
                formatted_sessions = []
                for session in sessions:
                    # Convert ObjectId to string for JSON serialization
                    session['_id'] = str(session['_id'])
                    session['id'] = str(session['_id'])  # Add id field for frontend compatibility

                    # Calculate duration if possible
                    if 'session_start_time' in session and 'diagnosis_submission_time' in session and session['diagnosis_submission_time']:
                        duration = (session['diagnosis_submission_time'] - session['session_start_time']).total_seconds()
                        session['duration_seconds'] = duration
                    formatted_sessions.append(session)

                return jsonify({
                    "sessions": formatted_sessions,
                    "pagination": {
                        "total": total_sessions,
                        "page": page,
                        "per_page": per_page,
                        "pages": (total_sessions + per_page - 1) // per_page  # Ceiling division
                    }
                })
            except Exception as e:
                logger.error(f"Error retrieving session history: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Dashboard data endpoint - combines all user dashboard data
        @blueprint.route('/dashboard', methods=['GET'])
        @login_required
        def get_dashboard_data():
            try:
                from .db import mongo
                user = g.user

                # Get evaluations for accuracy calculations
                evaluations = list(mongo.db.evaluations.find(
                    {"user_id": user.user_id},
                    {
                        "case_info": 1,
                        "evaluation_result.diagnosis_correct": 1,
                        "evaluation_result.overall_clinical_score": 1,
                        "timestamp": 1,
                        "case_id": 1,
                        "student_diagnosis": 1,
                        "session_data.timeline": 1
                    }
                ).sort("timestamp", -1))

                # Get sessions for in-progress cases
                sessions = list(mongo.db.sessions.find(
                    {"user_id": user.user_id},
                    {
                        "case_id": 1,
                        "timestamp": 1,
                        "case_data": 1,
                        "status": 1,
                        "last_updated_at": 1,
                        "time_elapsed": 1
                    }
                ).sort("timestamp", -1))

                # Calculate stats
                total_evaluations = len(evaluations)
                correct_evaluations = sum(1 for e in evaluations if e.get('evaluation_result', {}).get('diagnosis_correct', False))
                accuracy_rate = round((correct_evaluations / total_evaluations) * 100) if total_evaluations > 0 else 0

                # Get in-progress sessions count
                in_progress_sessions = [s for s in sessions if s.get('status') == 'in_progress']
                total_cases = total_evaluations + len(in_progress_sessions)

                # Format recent cases from evaluations
                recent_cases = []
                for eval_data in evaluations[:10]:  # Last 10 completed cases
                    case_info = eval_data.get('case_info', {})
                    timeline = eval_data.get('session_data', {}).get('timeline', [])
                    time_taken = None

                    # Calculate time taken from timeline
                    if timeline:
                        start_time = None
                        end_time = None
                        for event in timeline:
                            if event.get('action') == 'session_start':
                                start_time = event.get('timestamp')
                            elif event.get('action') == 'diagnosis_submitted':
                                end_time = event.get('timestamp')

                        if start_time and end_time:
                            try:
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                time_taken_seconds = (end_dt - start_dt).total_seconds()
                                time_taken = f"{int(time_taken_seconds // 60)} min"
                            except:
                                time_taken = "Unknown"

                    is_correct = eval_data.get('evaluation_result', {}).get('diagnosis_correct', False)
                    score = eval_data.get('evaluation_result', {}).get('overall_clinical_score', 0)

                    recent_cases.append({
                        'id': str(eval_data['_id']),
                        'name': case_info.get('name', 'Unknown Patient'),
                        'age': case_info.get('age', '??'),
                        'gender': case_info.get('gender', '?'),
                        'specialty': case_info.get('specialty', 'General'),
                        'difficulty': case_info.get('difficulty', 'Unknown'),
                        'status': 'Completed',
                        'completed': eval_data.get('timestamp', datetime.now()).strftime('%Y-%m-%d'),
                        'completedTimestamp': eval_data.get('timestamp', datetime.now()).isoformat(),
                        'diagnosisCorrect': is_correct,
                        'score': int(score) if score else (85 + (score % 15) if is_correct else 65 + (score % 15)),
                        'diagnosis': eval_data.get('student_diagnosis', 'Unknown'),
                        'timeTaken': time_taken or 'Unknown'
                    })

                # Add in-progress cases
                for session in in_progress_sessions[:5]:  # Last 5 in-progress
                    case_data = session.get('case_data', {})
                    recent_cases.append({
                        'id': str(session['_id']),
                        'name': case_data.get('name', 'Unknown Patient'),
                        'age': case_data.get('age', '??'),
                        'gender': case_data.get('gender', '?'),
                        'specialty': case_data.get('specialty', 'General'),
                        'difficulty': case_data.get('difficulty', 'Unknown'),
                        'status': 'In Progress',
                        'completed': 'In Progress',
                        'completedTimestamp': session.get('last_updated_at', datetime.now()).isoformat(),
                        'diagnosisCorrect': None,
                        'score': None,
                        'diagnosis': 'In Progress',
                        'timeTaken': f"{int((session.get('time_elapsed', 0)) // 60)} min" if session.get('time_elapsed') else 'Unknown'
                    })

                # Sort recent cases by timestamp
                recent_cases.sort(key=lambda x: x['completedTimestamp'], reverse=True)
                recent_cases = recent_cases[:10]  # Keep only top 10

                # Calculate specialty performance
                specialty_stats = {}
                for eval_data in evaluations:
                    specialty = eval_data.get('case_info', {}).get('specialty', 'Unknown')
                    is_correct = eval_data.get('evaluation_result', {}).get('diagnosis_correct', False)

                    if specialty not in specialty_stats:
                        specialty_stats[specialty] = {'total': 0, 'correct': 0}

                    specialty_stats[specialty]['total'] += 1
                    if is_correct:
                        specialty_stats[specialty]['correct'] += 1

                specialty_performance = []
                for specialty, stats in specialty_stats.items():
                    accuracy = round((stats['correct'] / stats['total']) * 100) if stats['total'] > 0 else 0
                    specialty_performance.append({
                        'specialty': specialty,
                        'accuracy': accuracy
                    })

                specialty_performance.sort(key=lambda x: x['accuracy'], reverse=True)

                # Format evaluations for frontend compatibility
                formatted_evaluations = []
                for eval_data in evaluations:
                    eval_copy = eval_data.copy()
                    eval_copy['id'] = str(eval_data['_id'])
                    eval_copy['case_data'] = eval_data.get('case_info', {})
                    eval_copy['is_correct'] = eval_data.get('evaluation_result', {}).get('diagnosis_correct', False)
                    eval_copy['submission'] = {'diagnosis': eval_data.get('student_diagnosis', 'Unknown')}

                    # Calculate time_taken from timeline if available
                    timeline = eval_data.get('session_data', {}).get('timeline', [])
                    time_taken_seconds = None
                    if timeline:
                        start_time = None
                        end_time = None
                        for event in timeline:
                            if event.get('action') == 'session_start':
                                start_time = event.get('timestamp')
                            elif event.get('action') == 'diagnosis_submitted':
                                end_time = event.get('timestamp')

                        if start_time and end_time:
                            try:
                                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                time_taken_seconds = (end_dt - start_dt).total_seconds()
                            except:
                                pass

                    eval_copy['time_taken'] = time_taken_seconds
                    formatted_evaluations.append(eval_copy)

                # Format sessions for frontend compatibility
                formatted_sessions = []
                for session in sessions:
                    session_copy = session.copy()
                    session_copy['id'] = str(session['_id'])
                    formatted_sessions.append(session_copy)

                return jsonify({
                    "stats": {
                        "totalCases": total_cases,
                        "completedCases": total_evaluations,
                        "accuracyRate": accuracy_rate
                    },
                    "recentCases": recent_cases,
                    "specialtyPerformance": specialty_performance,
                    "evaluations": formatted_evaluations,  # For compatibility with existing frontend logic
                    "sessions": formatted_sessions  # For compatibility with existing frontend logic
                })

            except Exception as e:
                logger.error(f"Error retrieving dashboard data: {str(e)}")
                return jsonify({"error": str(e)}), 500

        # Session-specific evaluations endpoint
        @blueprint.route('/sessions/<case_id>/evaluations', methods=['GET'])
        @login_required
        def get_session_evaluations(case_id):
            try:
                from .db import mongo
                user = g.user

                # Query MongoDB evaluations collection for evaluations related to this case
                evaluations = list(mongo.db.evaluations.find({
                    "user_id": user.user_id,
                    "case_id": case_id
                }).sort("timestamp", -1))

                # Format the results
                formatted_evaluations = []
                for eval in evaluations:
                    # Convert ObjectId to string for JSON serialization
                    eval['_id'] = str(eval['_id'])
                    formatted_evaluations.append(eval)

                return jsonify({"evaluations": formatted_evaluations})
            except Exception as e:
                logger.error(f"Error retrieving session evaluations: {str(e)}")
                return jsonify({"error": str(e)}), 500

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
        @login_required
        def create_new_case():
            try:
                logger.info("New case endpoint called")
                logger.info(f"User: {g.user.email if hasattr(g, 'user') and g.user else 'No user'}")

                data = request.get_json() or {}
                specialty = data.get('specialty')
                difficulty = data.get('difficulty')

                logger.info(f"Creating new case - Specialty: {specialty}, Difficulty: {difficulty}")

                new_case = self.case_manager.generate_new_case(specialty, difficulty)
                self.session_manager.reset_session(new_case.get("id"))

                # Associate the session with current user
                if hasattr(g, 'user') and g.user:
                    logger.info(f"Associating session with user {g.user.user_id}")
                    self.session_manager.set_user_id(g.user.user_id)
                else:
                    logger.warning("No user found in g object")

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
        @login_required
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

                # Store evaluation in MongoDB if user is authenticated
                if hasattr(g, 'user') and g.user:
                    from .db import mongo
                    current_case = self.case_manager.get_current_case()
                    evaluation_data = {
                        "user_id": g.user.user_id,
                        "case_id": current_case.get("id", "unknown"),
                        "case_info": {
                            "name": current_case.get("name", ""),
                            "age": current_case.get("age", ""),
                            "gender": current_case.get("gender", ""),
                            "specialty": current_case.get("specialty", ""),
                            "difficulty": current_case.get("difficulty", ""),
                            "diagnosis": current_case.get("diagnosis", ""),
                            "presenting_complaint": current_case.get("presenting_complaint", "")
                        },
                        "student_diagnosis": student_diagnosis,
                        "evaluation_result": evaluation_result,
                        "timestamp": datetime.now(),
                        "session_data": {
                            "ordered_tests": list(self.session_manager.get_ordered_tests()),
                            "ordered_imaging": list(self.session_manager.get_ordered_imaging()),
                            "notes": notes,
                            "timeline": timeline,
                            "efficiency_metrics": efficiency_metrics
                        }
                    }

                    # Save to MongoDB evaluations collection
                    mongo.db.evaluations.insert_one(evaluation_data)
                    logger.info(f"Evaluation stored for user {g.user.user_id} and case {current_case.get('id', 'unknown')}")

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
                    cwd = os.path.dirname(os.getcwd())
                    image_filename = f"{imaging_name.replace(' ', '_').lower()}_{int(time.time())}.png"
                    image_dir = os.path.join(cwd, 'static', 'generated_images')
                    os.makedirs(image_dir, exist_ok=True)
                    image_path = os.path.join(image_dir, image_filename)

                    # Generate and save the image
                    image_success = False
                    image_url = None
                    cloudinary_url = None

                    try:
                        # Call the image API and save the result
                        image = self.imaging_system.call_image_api(image_prompt, image_path)
                        if image:
                            image_success = True
                            # Create URL path for the image (relative to your static folder)
                            image_url = f"/static/generated_images/{image_filename}"

                            # Check if the image has a cloudinary_url attribute
                            if hasattr(image, 'cloudinary_url') and image.cloudinary_url:
                                cloudinary_url = image.cloudinary_url
                                logger.info(f"Cloudinary URL detected: {cloudinary_url}")
                    except Exception as img_err:
                        logger.error(f"Error generating image: {str(img_err)}")

                    return jsonify({
                        "success": True,
                        "message": f"Imaging study '{imaging_name}' ordered successfully",
                        "report": imaging_report,
                        "markdown": markdown_report,
                        "image_generated": image_success,
                        "image_url": cloudinary_url if cloudinary_url else image_url,
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
