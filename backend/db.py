import os
import logging
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logger = logging.getLogger(__name__)

# MongoDB instance
mongo = PyMongo()

def init_db(app):
    """
    Initialize MongoDB connection

    Args:
        app: Flask application instance

    Returns:
        PyMongo instance or None if connection fails
    """
    # Get MongoDB URI from environment variable or use default for local development
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/clinical_engine")

    # Configure Flask app for MongoDB
    app.config["MONGO_URI"] = mongodb_uri

    try:
        # Initialize PyMongo with the app
        mongo.init_app(app)

        # Test connection
        mongo.db.command('ping')

        logger.info("MongoDB connection established successfully")

        # Create indices for better query performance
        create_indices()

        return mongo

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

def create_indices():
    """Create indices for collections for better query performance"""
    try:
        # Create index on users collection
        mongo.db.users.create_index("email", unique=True)

        # Create index on sessions collection (by user_id and timestamp)
        mongo.db.sessions.create_index([("user_id", 1), ("timestamp", -1)])

        # Create index on evaluations collection (by user_id and case_id)
        mongo.db.evaluations.create_index([("user_id", 1), ("case_id", 1)])

        logger.info("Database indices created successfully")

    except Exception as e:
        logger.error(f"Error creating indices: {str(e)}")
