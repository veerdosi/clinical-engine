import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser, logout } from './auth';

// Import all page components
import LoginScreen from './LoginScreen';
import AuthTester from './AuthTester';
import StudentDashboard from './StudentDashboard';
import CaseSelectionScreen from './CaseSelectionScreen';
import CaseView from './CaseView';
import NotFound from './NotFound';
import LoadingScreen from './LoadingScreen';

// Import styles
import './App.css';
import './Auth.css';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication status when the component mounts
  useEffect(() => {
    const checkAuth = () => {
      const auth = isAuthenticated();
      setAuthenticated(auth);

      if (auth) {
        setUser(getCurrentUser());
      } else {
        setUser(null);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLoginSuccess = (userData) => {
    console.log("Login successful, userData:", userData);
    console.log("Token in localStorage:", localStorage.getItem('authToken'));

    setAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return <LoadingScreen message="Initializing application..." />;
  }

  return (
    <Router>
      <div className="App">
        {!authenticated ? (
          <Routes>
            <Route path="/test-auth" element={
              <div>
                <div style={{ padding: '15px', backgroundColor: '#f8d7da', marginBottom: '20px', textAlign: 'center' }}>
                  <p style={{ margin: 0, color: '#721c24' }}>
                    <strong>Authentication Test Mode</strong> - You are not logged in.
                    <a href="/" style={{ marginLeft: '10px', color: '#721c24', textDecoration: 'underline' }}>
                      Return to Login
                    </a>
                  </p>
                </div>
                <AuthTester />
              </div>
            } />
            <Route path="*" element={<LoginScreen onLoginSuccess={handleLoginSuccess} />} />
          </Routes>
        ) : (
          <Routes>
            {/* Dashboard - default route */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<StudentDashboard user={user} />} />

            {/* Case selection screen */}
            <Route path="/case-selection" element={
              <div>
                <header className="global-header">
                  <div className="header-content">
                    <div className="logo-section">
                      <img src="/logo.png" alt="Clinical Engine Logo" className="logo-img" />
                      <h1>Clinical Engine</h1>
                    </div>
                    {user && (
                      <div className="user-profile">
                        {user.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
                        <span className="user-name">{user.name}</span>
                        <button className="logout-btn" onClick={handleLogout}>
                          Logout
                        </button>
                      </div>
                    )}
                  </div>
                </header>
                <CaseSelectionScreen />
              </div>
            } />

            {/* Case view - both new cases and resume with ID, with nested tab routes */}
            <Route path="/case/*" element={<CaseView />} />
            <Route path="/case/:caseId/*" element={<CaseView />} />

            {/* Fallback for any other routes */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        )}
      </div>
    </Router>
  );
}

export default App;
