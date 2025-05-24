import logging
import traceback
import os
from flask import Flask
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
from backend.db import init_db
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
    #app = Flask(__name__, static_folder='static')
    app = Flask(__name__)
    CORS(app, supports_credentials=True, expose_headers=['Authorization'], allow_headers=['Content-Type', 'Authorization'])

    # Set a strong secret key for session and token signing
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

    # Initialize configuration with API keys
    try:
        logger.info("Initializing application configuration...")
        config = MedicalSimConfig()

        # Initialize MongoDB database
        logger.info("Initializing MongoDB connection...")
        mongo = init_db(app)
        app.mongo = mongo
        if not mongo:
            logger.warning("MongoDB connection failed. Some features may not work correctly.")

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
            physical_exam_system=physical_exam_system
        )

        # Register routes
        api_routes.register_routes(api_bp)
        app.register_blueprint(api_bp)

        logger.info("Application initialization complete!")

    except Exception as e:
        logger.error(f"Error during application initialization: {str(e)}")
        traceback.print_exc()
        raise

    return app

# if __name__ == '__main__':
app = create_app()
    # logger.info("Starting Flask server...")
    # app.run(debug=True, host="127.0.0.1", port=5000)
