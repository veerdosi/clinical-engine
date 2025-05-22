// fetchInterceptor.js
// A utility to automatically add authentication headers to all fetch requests

// Store the original fetch function
const originalFetch = window.fetch;

// Create a wrapper function to intercept fetch calls
window.fetch = async function(url, options = {}) {
  console.log(`Fetch interceptor: ${url}`);

  // Skip interception for non-API or authentication endpoints
  if (!url.includes('/api/') ||
      url.includes('/api/auth/google') ||
      url.includes('/api/health')) {
    return originalFetch(url, options);
  }

  // Get the authentication token from localStorage
  const token = localStorage.getItem('authToken');

  // Create a new options object with authorization header if token exists
  if (token) {
    console.log(`Adding auth token to request: ${url}`);

    // Create new headers object by merging existing headers with authorization
    const newHeaders = {
      ...(options.headers || {}),
      'Authorization': `Bearer ${token}`
    };

    // Create new options with updated headers
    const newOptions = {
      ...options,
      headers: newHeaders
    };

    return originalFetch(url, newOptions);
  }

  // If no token exists, just pass through the original request
  return originalFetch(url, options);
};

console.log('Fetch interceptor installed. All API requests will include auth tokens.');

const fetchInterceptor = {}; // Export empty object to satisfy module system
export default fetchInterceptor;
