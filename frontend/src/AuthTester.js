import React, { useState, useEffect } from 'react';
import { isAuthenticated, getCurrentUser } from './auth';
import { testAuth } from './api';

const AuthTester = () => {
  const [authStatus, setAuthStatus] = useState({ checking: true });
  const [token, setToken] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Check if authenticated according to local state
      const isAuth = isAuthenticated();
      console.log("isAuthenticated() result:", isAuth);

      // Get the current token
      const storedToken = localStorage.getItem('authToken');
      setToken(storedToken ? `${storedToken.substring(0, 15)}...` : 'No token found');

      // Get the current user
      const user = getCurrentUser();
      console.log("getCurrentUser() result:", user);

      // Call the test endpoint
      const testResult = await testAuth();
      console.log("testAuth() result:", testResult);

      setAuthStatus({
        checking: false,
        localAuth: isAuth,
        user: user,
        serverAuth: testResult.authenticated === true,
        serverResponse: testResult
      });
    } catch (error) {
      console.error("Error checking auth:", error);
      setAuthStatus({
        checking: false,
        error: error.message
      });
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Authentication Tester</h2>

      {authStatus.checking ? (
        <div>Checking authentication status...</div>
      ) : (
        <div>
          <h3>Authentication Status</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px', fontWeight: 'bold' }}>Token in localStorage:</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{token}</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px', fontWeight: 'bold' }}>Client-side Auth:</td>
                <td style={{ border: '1px solid #ddd', padding: '8px', color: authStatus.localAuth ? 'green' : 'red' }}>
                  {authStatus.localAuth ? 'Authenticated' : 'Not Authenticated'}
                </td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px', fontWeight: 'bold' }}>Server-side Auth:</td>
                <td style={{ border: '1px solid #ddd', padding: '8px', color: authStatus.serverAuth ? 'green' : 'red' }}>
                  {authStatus.serverAuth ? 'Authenticated' : 'Not Authenticated'}
                </td>
              </tr>
              {authStatus.user && (
                <tr>
                  <td style={{ border: '1px solid #ddd', padding: '8px', fontWeight: 'bold' }}>User:</td>
                  <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                    {authStatus.user.name} ({authStatus.user.email})
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {authStatus.error && (
            <div style={{ color: 'red', marginTop: '15px' }}>
              <strong>Error:</strong> {authStatus.error}
            </div>
          )}

          <div style={{ marginTop: '20px' }}>
            <button
              onClick={checkAuth}
              style={{
                padding: '8px 15px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Refresh Status
            </button>
          </div>

          <div style={{ marginTop: '30px' }}>
            <h3>Server Response</h3>
            <pre style={{
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '5px',
              overflow: 'auto'
            }}>
              {JSON.stringify(authStatus.serverResponse, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuthTester;
