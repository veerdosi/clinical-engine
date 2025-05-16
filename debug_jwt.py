#!/usr/bin/env python
"""
JWT Token Debugging Script for Clinical Engine

This script tests JWT token generation and validation to help diagnose
authentication issues. It uses the same libraries and configuration as
the main application.
"""

import os
import jwt
import datetime
import time

def generate_token(payload, secret_key):
    """Generate a JWT token with the given payload and secret key"""
    print(f"Generating token with secret key: {secret_key[:5]}...")

    try:
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        print(f"Token generated successfully: {token[:10]}...")
        return token
    except Exception as e:
        print(f"❌ Error generating token: {str(e)}")
        return None

def verify_token(token, secret_key):
    """Verify a JWT token with the given secret key"""
    print(f"Verifying token: {token[:10]}...")

    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"✅ Token verified successfully!")
        print(f"Payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error verifying token: {str(e)}")
        return None

def test_token_expiration(secret_key):
    """Test token expiration by creating a token that expires in 2 seconds"""
    print("\n=== Testing Token Expiration ===")

    # Create payload with short expiration
    payload = {
        'user_id': 'test_user',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
    }

    # Generate token
    token = generate_token(payload, secret_key)

    # Verify token before expiration
    print("\nVerifying token before expiration...")
    verify_token(token, secret_key)

    # Wait for token to expire
    print("\nWaiting 3 seconds for token to expire...")
    time.sleep(3)

    # Verify token after expiration
    print("\nVerifying token after expiration...")
    verify_token(token, secret_key)

def main():
    print("=== JWT Token Debugging Script ===")

    # Try to get secret key from environment variable
    secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
    print(f"Using secret key: {secret_key[:5]}...")

    # Create a test payload
    test_payload = {
        'user_id': 'test_user',
        'email': 'test@example.com',
        'role': 'student',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }

    # Generate a token
    print("\n=== Token Generation Test ===")
    token = generate_token(test_payload, secret_key)

    if token:
        # Verify the token
        print("\n=== Token Verification Test ===")
        verify_token(token, secret_key)

        # Try verifying with wrong secret key
        print("\n=== Wrong Secret Key Test ===")
        verify_token(token, 'wrong-secret-key')

    # Test token expiration
    test_token_expiration(secret_key)

    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
