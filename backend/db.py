import os
import logging
from flask_pymongo import PyMongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logger = logging.getLogger(__name__)

def init_db(app):
    """
    Initialize MongoDB connection

    Args:
        app: Flask application instance

    Returns:
        PyMongo instance or None if connection fails
    """
    # Get MongoDB URI from environment variable or use default for local development
    mongodb_uri = os.getenv("MONGODB_URI")

    # Configure Flask app for MongoDB
    app.config["MONGO_URI"] = mongodb_uri

    try:
        # Initialize new PyMongo instance with the app
        mongo = PyMongo(app)

        # Test connection
        if not mongo.db:
            logger.error("mongo.db is None — check MONGODB_URI and MongoDB status")
            return None

        mongo.db.command('ping')

        logger.info("MongoDB connection established successfully")

        # Create indices for better query performance
        create_indices(mongo)

        return mongo

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

def create_indices(mongo):
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
