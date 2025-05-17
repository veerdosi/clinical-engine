import datetime
import logging
import jwt
from flask import current_app
from .db import mongo

# Configure logging
logger = logging.getLogger(__name__)

class User:
    """User model for authentication and user management"""

    def __init__(self, email=None, name=None, picture=None, google_id=None,
                 user_id=None, created_at=None, last_login=None):
        self.email = email
        self.name = name
        self.picture = picture  # Profile picture URL
        self.google_id = google_id
        self.user_id = user_id  # MongoDB _id
        self.created_at = created_at or datetime.datetime.utcnow()
        self.last_login = last_login

    @staticmethod
    def find_by_email(email):
        """Find a user by email address"""
        if not email:
            return None

        user_data = mongo.db.users.find_one({"email": email})
        if not user_data:
            return None

        return User(
            email=user_data.get('email'),
            name=user_data.get('name'),
            picture=user_data.get('picture'),
            google_id=user_data.get('google_id'),
            user_id=str(user_data.get('_id')),
            created_at=user_data.get('created_at'),
            last_login=user_data.get('last_login')
        )

    @staticmethod
    def find_by_id(user_id):
        """Find a user by MongoDB ID"""
        if not user_id:
            return None

        from bson.objectid import ObjectId
        try:
            user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if not user_data:
                return None

            return User(
                email=user_data.get('email'),
                name=user_data.get('name'),
                picture=user_data.get('picture'),
                google_id=user_data.get('google_id'),
                user_id=str(user_data.get('_id')),
                created_at=user_data.get('created_at'),
                last_login=user_data.get('last_login')
            )
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None

    @staticmethod
    def create_or_update_from_google_data(google_data):
        """Create or update a user from Google OAuth data"""
        email = google_data.get('email')
        if not email:
            logger.error("No email provided in Google data")
            return None

        # Check if user already exists
        existing_user = User.find_by_email(email)

        if existing_user:
            # Update existing user
            update_data = {
                "name": google_data.get('name'),
                "picture": google_data.get('picture'),
                "google_id": google_data.get('sub'),
                "last_login": datetime.datetime.utcnow()
            }

            mongo.db.users.update_one(
                {"email": email},
                {"$set": update_data}
            )

            # Refresh user data after update
            return User.find_by_email(email)
        else:
            # Create new user
            new_user = {
                "email": email,
                "name": google_data.get('name'),
                "picture": google_data.get('picture'),
                "google_id": google_data.get('sub'),
                "created_at": datetime.datetime.utcnow(),
                "last_login": datetime.datetime.utcnow()
            }

            result = mongo.db.users.insert_one(new_user)
            new_user['user_id'] = str(result.inserted_id)

            return User(
                email=new_user.get('email'),
                name=new_user.get('name'),
                picture=new_user.get('picture'),
                google_id=new_user.get('google_id'),
                user_id=new_user.get('user_id'),
                created_at=new_user.get('created_at'),
                last_login=new_user.get('last_login')
            )

    def generate_auth_token(self, expiration=86400):
        """Generate a JWT authentication token for the user"""
        try:
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')

            payload = {
                'user_id': self.user_id,
                'email': self.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration)
            }

            # Import PyJWT directly to avoid confusion with any other jwt module
            import jwt
            token = jwt.encode(payload, secret_key, algorithm='HS256')

            # PyJWT might return bytes or string depending on version
            if isinstance(token, bytes):
                token = token.decode('utf-8')

            return token

        except Exception as e:
            logger.error(f"Error generating auth token: {str(e)}")
            return None

    @staticmethod
    def verify_auth_token(token):
        """Verify and decode a JWT authentication token"""
        if not token:
            return None

        try:
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
            logger.info(f"Verifying token with secret key: {secret_key[:5]}...")

            # Import jwt directly
            import jwt

            # Debug: print token format
            token_parts = token.split('.')
            if len(token_parts) != 3:
                logger.warning(f"Invalid token format - not a standard JWT (parts: {len(token_parts)})")

            # Handle jwt exceptions explicitly
            try:
                logger.info("Attempting to decode token...")
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                logger.info(f"Token decoded successfully. User ID: {payload.get('user_id')}")
                user = User.find_by_id(payload.get('user_id'))
                if user:
                    logger.info(f"User found: {user.email}")
                else:
                    logger.warning(f"No user found with ID: {payload.get('user_id')}")
                return user
            except jwt.exceptions.ExpiredSignatureError:
                logger.warning("Expired token")
                return None
            except jwt.exceptions.InvalidTokenError as e:
                logger.warning(f"Invalid token: {str(e)}")
                return None
            except Exception as e:
                logger.warning(f"Error decoding token: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error verifying auth token: {str(e)}")
            return None

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'picture': self.picture,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
