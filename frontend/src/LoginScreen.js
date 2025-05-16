import React, { useState, useEffect } from 'react';
import './LoginScreen.css';

const LoginScreen = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load Google's OAuth script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    // Set up callback for Google OAuth
    window.handleGoogleSignIn = async (response) => {
      setLoading(true);
      setError(null);

      try {
        console.log("Google sign-in response received:", response.credential ? "Token received" : "No token");

        // Exchange Google token for our JWT token
        const result = await fetch('/api/auth/google', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: response.credential }),
        });

        if (!result.ok) {
          console.error("Authentication failed with status:", result.status);
          throw new Error('Authentication failed');
        }

        const data = await result.json();
        console.log("Auth response:", data.token ? "Token received" : "No token", data.user ? "User data received" : "No user data");

        // Store the token and user info in localStorage
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));

        console.log("Token stored in localStorage:", data.token.substring(0, 10) + "...");

        // Call the parent component's success handler
        if (onLoginSuccess) {
          onLoginSuccess(data.user);
        }
      } catch (err) {
        console.error('Login error:', err);
        setError('Authentication failed. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    // Clean up
    return () => {
      delete window.handleGoogleSignIn;
      const scriptElement = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (scriptElement) {
        document.body.removeChild(scriptElement);
      }
    };
  }, [onLoginSuccess]);

  useEffect(() => {
    // Initialize Google Sign-In button after script loads
    const intervalId = setInterval(() => {
      if (window.google && document.getElementById('google-signin-button')) {
        clearInterval(intervalId);

        window.google.accounts.id.initialize({
          client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || '123456789-your-client-id-here.apps.googleusercontent.com',
          callback: window.handleGoogleSignIn,
          auto_select: false,
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            theme: 'outline',
            size: 'large',
            type: 'standard',
            text: 'signin_with',
            shape: 'rectangular',
            logo_alignment: 'left',
            width: 280
          }
        );
      }
    }, 100);

    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="login-screen">
      <div className="login-container">
        <div className="login-header">
          <h1>Clinical Engine</h1>
          <h2>Medical Training Simulator</h2>
        </div>

        <div className="login-content">
          <p>Please sign in to continue</p>

          {error && <div className="login-error">{error}</div>}

          <div id="google-signin-button" className="google-signin-button"></div>

          {loading && (
            <div className="login-loading">
              <div className="loading-spinner"></div>
              <p>Signing in...</p>
            </div>
          )}
        </div>

        <div className="login-footer">
          <p>© {new Date().getFullYear()} Clinical Engine</p>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
