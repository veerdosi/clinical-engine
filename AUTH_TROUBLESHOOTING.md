# Authentication Troubleshooting Guide

This guide helps you diagnose and fix authentication issues with the Clinical Engine application.

## Common Issues and Solutions

### 1. JWT Token Not Being Sent

**Symptoms:**
- 401 Unauthorized errors
- Authentication required messages
- Missing Authorization header in logs

**Solutions:**
- Check that the token is stored in localStorage correctly
- Verify that the Authorization header is properly formatted (`Bearer [token]`)
- Make sure CORS settings allow the Authorization header

### 2. JWT Token Not Being Verified

**Symptoms:**
- Invalid token errors
- Token verification failed messages
- Signature verification failed logs

**Solutions:**
- Ensure the same SECRET_KEY is used for both token creation and verification
- Check that the token format is correct (three parts separated by periods)
- Verify that the token hasn't expired

### 3. MongoDB Connection Issues

**Symptoms:**
- Database connection errors
- Failed to connect to MongoDB messages
- User data not being stored or retrieved

**Solutions:**
- Verify MongoDB is running (`mongod --dbpath ~/mongodb/data`)
- Check that the connection string is correct in .env
- Ensure database permissions allow read/write access

## Debugging Steps

### 1. Test Authentication Flow

```bash
# Run the JWT debugging script
python debug_jwt.py

# Access the authentication tester in the browser
# Visit: http://localhost:3000/?test-auth=true
```

### 2. Check Browser Console

Look for:
- Token storage logs
- Request header logs
- Authentication error messages

### 3. Check Backend Logs

Look for:
- Headers received from the frontend
- Token verification attempts
- Authentication results

### 4. Test with Curl

```bash
# Get a valid token from localStorage in the browser
# Then use it in this curl command

curl -X POST http://localhost:5000/api/new-case \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"specialty":"Cardiology","difficulty":"Easy"}'
```

## Quick Fixes

### Fix 1: Clear Local Storage

```javascript
// In browser console
localStorage.clear()
// Then log in again
```

### Fix 2: Restart Backend with Debug Mode

```bash
# Set logging to debug level
export FLASK_DEBUG=1
python -m backend.main
```

### Fix 3: Test with a Hardcoded Token

Add this temporary code to the backend for testing:

```python
# In backend/auth.py
# In the login_required decorator, add this temporary bypass
if 'testing' in request.args:
    # Set a dummy user for testing
    from .user import User
    g.user = User(email="test@example.com", user_id="test123", role="student")
    return f(*args, **kwargs)
```

## Environment Setup

Make sure you have a `.env` file in your project root with:

```
MONGODB_URI=mongodb://localhost:27017/clinical_engine
SECRET_KEY=YourSuperSecretKeyForJWTTokens123456789012
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
```

And a `.env` file in your frontend directory with:

```
REACT_APP_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
```
