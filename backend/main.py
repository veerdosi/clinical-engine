import logging
import traceback
import os
import tempfile
from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.config import MedicalSimConfig
from backend.case_manager import CaseManager
from backend.session_manager import SessionManager
from backend.chat_handler import ChatHandler
from backend.api_routes import APIRoutes, api_bp
from backend.speech_to_text import SpeechProcessor
from backend.lab_system import LabSystem
from backend.imaging import ImagingSystem
from backend.physical_exam import PhysicalExamSystem
from backend.evaluation import DiagnosisEvaluator, InteractionEvaluator, ClinicalDecisionEvaluator
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure the Flask application
    """
    app = Flask(__name__)
    CORS(app)
    
    # Initialize configuration with API keys
    try:
        logger.info("Initializing application configuration...")
        config = MedicalSimConfig()
        
        # Create a temporary directory for PDF reports
        app.config['REPORT_FOLDER'] = tempfile.mkdtemp()
        os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)
        logger.info(f"Report folder created at: {app.config['REPORT_FOLDER']}")
        
        # Add a route to serve PDF files
        @app.route('/reports/<path:filename>')
        def serve_report(filename):
            return send_from_directory(app.config['REPORT_FOLDER'], filename)
        
        # Initialize components
        logger.info("Initializing application components...")
        
        # Create speech processor
        speech_processor = SpeechProcessor(config)
        
        # Create lab, imaging, and physical exam systems
        lab_system = LabSystem(config)
        imaging_system = ImagingSystem(config)
        physical_exam_system = PhysicalExamSystem(config)
        
        # Create case manager and generate initial case
        case_manager = CaseManager(config)
        
        # Create session manager
        session_manager = SessionManager()
        
        # Create chat handler
        chat_handler = ChatHandler(case_manager, session_manager, speech_processor)
        
        # Set up API routes with additional systems
        logger.info("Setting up API routes...")
        api_routes = APIRoutes(
            case_manager=case_manager, 
            session_manager=session_manager, 
            chat_handler=chat_handler,
            lab_system=lab_system,
            imaging_system=imaging_system,
            physical_exam_system=physical_exam_system,
            app=app  # Pass the app reference to APIRoutes
        )
        
        # Register routes
        blueprint = api_routes.register_routes(api_bp)
        app.register_blueprint(blueprint)
        
        logger.info("Application initialization complete!")
        
    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        traceback.print_exc()
        raise
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting Flask server...")
    app.run(debug=True, host="127.0.0.1", port=5000)