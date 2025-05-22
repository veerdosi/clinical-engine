/**
 * Authentication service to manage tokens and user state
 */

// Base API URL configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Check if user is already authenticated
export const isAuthenticated = () => {
  const token = localStorage.getItem('authToken');
  const user = localStorage.getItem('user');

  if (!token || !user) {
    return false;
  }

  // Check if token is expired
  try {
    const tokenData = parseJwt(token);
    const expiry = tokenData.exp ? tokenData.exp * 1000 : 0; // Convert seconds to milliseconds

    if (expiry < Date.now()) {
      // Token is expired, clear localStorage
      logout();
      return false;
    }

    return true;
  } catch (error) {
    console.error('Error parsing JWT token:', error);
    return false;
  }
};

// Get current user data
export const getCurrentUser = () => {
  if (!isAuthenticated()) {
    return null;
  }

  const userStr = localStorage.getItem('user');
  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error('Error parsing user data:', error);
    return null;
  }
};

// Get authentication token
export const getToken = () => {
  if (!isAuthenticated()) {
    return null;
  }

  return localStorage.getItem('authToken');
};

// Logout user by clearing local storage
export const logout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
};

// Validate token with the server
export const validateToken = async () => {
  if (!isAuthenticated()) {
    return false;
  }

  try {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/api/auth/validate`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Token validation failed');
    }

    const data = await response.json();
    return data.valid;
  } catch (error) {
    console.error('Token validation error:', error);
    return false;
  }
};

// Helper function to parse JWT token
const parseJwt = (token) => {
  try {
    // Split the token and get the payload part
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );

    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing JWT:', error);
    return {};
  }
};

// Fetch wrapper with authentication
export const authFetch = async (url, options = {}) => {
  console.log(`Calling authFetch for URL: ${url}`);

  if (!isAuthenticated()) {
    console.error('Authentication check failed - not authenticated');
    throw new Error('Not authenticated');
  }

  const token = getToken();
  console.log(`Token retrieved: ${token ? token.substring(0, 10) + '...' : 'None'}`);

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  console.log('Request headers:', headers);

  try {
    console.log(`Making authenticated request to ${url}`);
    const finalUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    const response = await fetch(finalUrl, {
      ...options,
      headers
    });

    console.log(`Response status: ${response.status}`);

    // If we get a 401 Unauthorized, the token might be expired
    if (response.status === 401) {
      console.error('Got 401 Unauthorized, checking token validity');
      // Check if the token is still valid
      const isValid = await validateToken();

      if (!isValid) {
        console.error('Token validated as invalid, logging out');
        // Token is invalid, log out the user
        logout();
        throw new Error('Authentication expired. Please log in again.');
      }
    }

    return response;
  } catch (error) {
    console.error(`Error in authFetch: ${error.message}`);
    throw error;
  }
};
