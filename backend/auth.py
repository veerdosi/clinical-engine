import os
import logging
import functools
import json
from flask import request, jsonify, current_app, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .user import User

# Configure logging
logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for handling Google Auth and JWT tokens"""

    def __init__(self):
        # Get Google OAuth client ID from environment
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not self.google_client_id:
            logger.warning("GOOGLE_CLIENT_ID is not set in environment variables")

    def verify_google_token(self, token):
        """
        Verify the Google OAuth ID token

        Args:
            token: The Google ID token to verify

        Returns:
            User object if verified successfully, None otherwise
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.google_client_id
            )

            # Check if the token is valid
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.warning("Invalid token issuer")
                return None

            # Create or update user
            user = User.create_or_update_from_google_data(idinfo)
            return user

        except ValueError as e:
            # Invalid token
            logger.error(f"Invalid token: {str(e)}")
            return None

    def authenticate_request(self):
        """
        Authenticate a request using the JWT token in the Authorization header

        Returns:
            The authenticated user or None
        """
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.debug("No valid Authorization header")
            return None

        # Get the token part
        token = auth_header.split(' ')[1]
        logger.info(f"Authenticating request with token: {token[:10]}...")

        # Verify the token
        user = User.verify_auth_token(token)
        if user:
            logger.info(f"Successfully authenticated user: {user.email}")
        else:
            logger.warning("Token verification failed")
        return user


# Decorator for routes requiring authentication
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Authentication required for route: {request.path}")

        # Print all request headers for debugging
        logger.info("Request headers:")
        for header, value in request.headers.items():
            if header.lower() != 'authorization':  # Don't log the full token
                logger.info(f"  {header}: {value}")
            else:
                auth_value = value[:15] + "..." if value else "None"
                logger.info(f"  {header}: {auth_value}")

        # Create auth service
        auth_service = AuthService()

        # Authenticate the request
        user = auth_service.authenticate_request()

        # Check if authentication failed
        if not user:
            logger.warning(f"Authentication failed for route: {request.path}")
            return jsonify({"error": "Authentication required"}), 401

        # Store user in Flask's g object for the current request
        g.user = user
        logger.info(f"Authentication successful for user: {user.email}, route: {request.path}")

        # Call the original function
        return f(*args, **kwargs)

    return decorated_function


