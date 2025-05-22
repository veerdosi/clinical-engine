import React, { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';
import DiagnosisPanel from './DiagnosisPanel';
import TestOrderingPanel from './TestOrderingPanel';
import PhysicalExamPanel from './PhysicalExamPanel';
import CaseSelectionScreen from './CaseSelectionScreen';
import VitalSigns from './VitalSigns';
import NotesPanel from './NotesPanel';
import InactivityReminder from './InactivityReminder';
import LoginScreen from './LoginScreen';
import AuthTester from './AuthTester';
import StudentDashboard from './StudentDashboard';
import { isAuthenticated, getCurrentUser, logout } from './auth';
import './App.css';
import './Auth.css';

function App() {
  const [caseInfo, setCaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDiagnosisSubmitted, setIsDiagnosisSubmitted] = useState(false);
  const [isNewCase, setIsNewCase] = useState(false);
  const [showCaseSelection, setShowCaseSelection] = useState(true); // Start with case selection
  const [showExplicitCaseSelection, setShowExplicitCaseSelection] = useState(false); // For showing case selection from dashboard
  const [activeTab, setActiveTab] = useState('patient'); // Default to patient tab
  const [conversationHistory, setConversationHistory] = useState([]); // Add state for conversation history
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

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
    };

    checkAuth();
  }, []);

  // We'll keep this to handle case loading on initial visit, but we'll show the selection screen
  useEffect(() => {
    if (authenticated && !showCaseSelection) {
      fetchCurrentCase();
    } else if (authenticated) {
      setLoading(false); // No need to load case initially if we're showing selection screen
    }
  }, [showCaseSelection, authenticated]);

  // Log state changes for debugging
  useEffect(() => {
    console.log("State changed - showExplicitCaseSelection:", showExplicitCaseSelection);
  }, [showExplicitCaseSelection]);

  const fetchCurrentCase = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/current-case');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setCaseInfo(data);
      setError(null);
      setIsDiagnosisSubmitted(false);
    } catch (err) {
      console.error('Error fetching case:', err);
      setError('Unable to load patient case. Please try again later.');
      setShowCaseSelection(true);
    } finally {
      setLoading(false);
    }
  };

  const handleNewCase = async (specialty, difficulty) => {
    setLoading(true);
    try {
      const body = {};
      if (specialty) body.specialty = specialty;
      if (difficulty) body.difficulty = difficulty;

      const response = await fetch('/api/new-case', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setCaseInfo(data);
      setError(null);
      setIsDiagnosisSubmitted(false);
      setIsNewCase(true);

      // REMOVED: setNotes({}); // No longer managing 'notes' state here

      setConversationHistory([]);
      setShowCaseSelection(false);
      setShowExplicitCaseSelection(false);
      setActiveTab('patient');

      return true;
    } catch (err) {
      console.error('Error generating new case:', err);
      setError('Unable to generate a new patient case. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleCaseGenerated = (caseData) => {
    setCaseInfo(caseData);
    setIsNewCase(true);
    setShowCaseSelection(false);
    setShowExplicitCaseSelection(false);
    setActiveTab('patient');
    // REMOVED: setNotes({}); // No longer managing 'notes' state here
    setConversationHistory([]);
  };

  const handleDiagnosisSubmitted = () => {
    setIsDiagnosisSubmitted(true);
  };

  const handleNewCaseStarted = () => {
    setIsNewCase(false);
  };

  const handleReturnToSelection = () => {
    setShowCaseSelection(true);
    setShowExplicitCaseSelection(false);
    setIsDiagnosisSubmitted(false);
    setIsNewCase(false);
    // REMOVED: setNotes({}); // No longer managing 'notes' state here
    setConversationHistory([]);
  };

  // Handle notes update from NotesPanel (e.g., to save to backend)
  const handleNotesUpdate = (updatedNotes) => {

    if (caseInfo && caseInfo.id) {
      fetch('/api/save-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notes: updatedNotes, 
          case_id: caseInfo.id
        })
      }).catch(err => {
        console.error('Error saving notes to backend:', err);
      });
    }
  };

  const handleNewMessage = (message) => {
    setConversationHistory(prev => [...prev, message]);
  };

  const handleLoginSuccess = (userData) => {
    console.log("Login successful, userData:", userData);
    console.log("Token in localStorage:", localStorage.getItem('authToken'));

    setAuthenticated(true);
    setUser(userData);
    setShowCaseSelection(true);
    setLoading(false);
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setUser(null);
    setCaseInfo(null);
    // REMOVED: setNotes({});
    setConversationHistory([]);
    setIsDiagnosisSubmitted(false);
    // Potentially redirect to login or clear other states as needed
  };

  // Show login screen if not authenticated
  if (!authenticated) {
    if (window.location.search.includes('test-auth=true')) {
      return (
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
      );
    }
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  if (showExplicitCaseSelection) {
    console.log("App: showExplicitCaseSelection is true, showing CaseSelectionScreen with back button");
    return (
      <CaseSelectionScreen
        onCaseGenerated={handleCaseGenerated}
        onBackToDashboard={() => setShowExplicitCaseSelection(false)}
      />
    );
  }

  if (showCaseSelection) {
    if (window.location.search.includes('skip-dashboard=true')) {
      return <CaseSelectionScreen onCaseGenerated={handleCaseGenerated} />;
    }
    return (
      <StudentDashboard
        user={user}
        onStartNewCase={() => {
          console.log("App: onStartNewCase called, setting showExplicitCaseSelection=true");
          setShowExplicitCaseSelection(true);
        }}
        onResumeCaseClick={(caseId) => {
          console.log("Resuming case:", caseId);
          fetchCurrentCase(); // Assuming this fetches the specific case or current in-progress
          setShowCaseSelection(false);
        }}
      />
    );
  }

  if (loading && !caseInfo) {
    return (
      <div className="App loading">
        <div className="loading-spinner"></div>
        <p>Loading patient case...</p>
      </div>
    );
  }

  if (error && !caseInfo) {
    return (
      <div className="App error">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchCurrentCase}>Try Again</button>
          <button onClick={handleReturnToSelection}>Return to Case Selection</button>
        </div>
      </div>
    );
  }

  const getCaseUrgency = () => {
    if (!caseInfo) return 'medium';
    const difficulty = caseInfo.difficulty?.toLowerCase() || '';
    if (difficulty === 'hard') return 'high';
    if (difficulty === 'moderate') return 'medium';
    return 'low';
  };

  const getInactivityThreshold = () => {
    const urgency = getCaseUrgency();
    switch (urgency) {
      case 'high': return 60;
      case 'medium': return 120;
      case 'low': return 180;
      default: return 120;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo-section">
            <img src="/logo.svg" alt="Clinical Engine Logo" className="logo-img" />
            <h1>Clinical Engine</h1>
          </div>
          <div className="case-info">
            {user && (
              <div className="user-profile">
                {user.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
                <span className="user-name">{user.name}</span>
                <button className="logout-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}

            {caseInfo && (
              <>
                <div className="patient-badge">
                  <span className="badge-label">Patient:</span>
                  <span className="badge-value">{caseInfo.name}, {caseInfo.age}{caseInfo.gender === 'Male' ? 'M' : 'F'}</span>
                </div>
                <div className="case-badge">
                  <span className="badge-label">Difficulty:</span>
                  <span className="badge-value">{caseInfo.difficulty}</span>
                </div>
                <div className="specialty-badge">
                  <span className="badge-label">Specialty:</span>
                  <span className="badge-value">{caseInfo.specialty}</span>
                </div>
                <button
                  className="new-selection-btn"
                  onClick={handleReturnToSelection}
                  disabled={loading}
                >
                  New Case Selection
                </button>
              </>
            )}
          </div>
        </div>

        <div className="tab-navigation">
          <button className={`tab-button ${activeTab === 'patient' ? 'active' : ''}`} onClick={() => setActiveTab('patient')}>
            Patient Interaction
          </button>
          <button className={`tab-button ${activeTab === 'labs' ? 'active' : ''}`} onClick={() => setActiveTab('labs')}>
            Laboratory Tests
          </button>
          <button className={`tab-button ${activeTab === 'imaging' ? 'active' : ''}`} onClick={() => setActiveTab('imaging')}>
            Imaging Studies
          </button>
          <button className={`tab-button ${activeTab === 'procedures' ? 'active' : ''}`} onClick={() => setActiveTab('procedures')}>
            Procedures
          </button>
        </div>
      </header>

      <div className="tab-content">
        {activeTab === 'patient' && (
          <div className="patient-tab">
            <div className="vital-signs-container">
              <VitalSigns vitals={caseInfo?.vitals || {}} />
            </div>
            {caseInfo && !showCaseSelection && !isDiagnosisSubmitted && (
              <InactivityReminder inactivityThreshold={getInactivityThreshold()} />
            )}
            <div className="patient-grid-layout">
              <div className="chat-area">
                <ChatWindow
                  isDiagnosisSubmitted={isDiagnosisSubmitted}
                  isNewCase={isNewCase}
                  onNewCaseStart={handleNewCaseStarted}
                  conversationHistory={conversationHistory}
                  onNewMessage={handleNewMessage}
                />
              </div>
              <div className="controls-area">
                <PhysicalExamPanel isDisabled={isDiagnosisSubmitted} caseInfo={caseInfo} />
                <DiagnosisPanel
                  case_info={caseInfo}
                  onNewCase={handleNewCase}
                  onDiagnosisSubmitted={handleDiagnosisSubmitted}
                  onReturnToSelection={handleReturnToSelection}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'labs' && (
          <div className="labs-tab">
            <div className="tab-container">
              <h2>Laboratory Testing</h2>
              <p className="tab-description">Order laboratory tests and review results to aid in your diagnosis.</p>
              <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="lab" />
            </div>
          </div>
        )}

        {activeTab === 'imaging' && (
          <div className="imaging-tab">
            <div className="tab-container">
              <h2>Imaging Studies</h2>
              <p className="tab-description">Order imaging studies and review radiologic findings to support your diagnostic workup.</p>
              <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="imaging" />
            </div>
          </div>
        )}

        {activeTab === 'procedures' && (
          <div className="procedures-tab">
            <div className="tab-container">
              <h2>Investigative Procedures</h2>
              <p className="tab-description">Order specialized procedures to gather additional diagnostic information.</p>
              <div className="procedures-info">
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="procedure" />
              </div>
            </div>
          </div>
        )}
      </div>

      {caseInfo && (
        <NotesPanel
          caseInfo={caseInfo}
          isDisabled={isDiagnosisSubmitted}
          onNoteUpdate={handleNotesUpdate} 
        />
      )}

      {caseInfo && !isDiagnosisSubmitted && (
        <footer className="app-footer">
          <div className="footer-metrics">
            <div className="word-count">
              <span>Words: {conversationHistory.length > 0 ? conversationHistory.reduce((count, msg) =>
                count + (msg.content ? msg.content.split(/\s+/).length : 0), 0) : 0}</span>
            </div>
            <div className="save-status saved">
              <span>Auto-saved</span>
            </div>
            <div className="elapsed-time">
              <span>Session time: {Math.floor(Math.random() * 30) + 10} min</span>
            </div>
          </div>
          <div className="app-version">
            Clinical Engine v1.0.0
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;