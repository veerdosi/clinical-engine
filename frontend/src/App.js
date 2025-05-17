// Complete App.js with tabbed navigation, VitalSigns, NotesPanel integration,
// and conversation history persistence
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
  const [notes, setNotes] = useState({}); // Add state for notes
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
      // If we can't fetch a case, go back to case selection screen
      setShowCaseSelection(true);
    } finally {
      setLoading(false);
    }
  };

  const handleNewCase = async (specialty, difficulty) => {
    setLoading(true);
    try {
      // Optional parameters for specialty and difficulty if passed
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

      // Signal to child components that we have a new case
      setIsNewCase(true);

      // Reset notes for new case
      setNotes({});

      // Reset conversation history
      setConversationHistory([]);

      // Hide case selection screen when we have a case
      setShowCaseSelection(false);
      setShowExplicitCaseSelection(false);

      // Reset to the patient tab
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
    setActiveTab('patient'); // Reset to the patient tab
    setNotes({}); // Reset notes
    setConversationHistory([]); // Reset conversation history
  };

  const handleDiagnosisSubmitted = () => {
    setIsDiagnosisSubmitted(true);
  };

  const handleNewCaseStarted = () => {
    // Reset the new case flag once processed by child components
    setIsNewCase(false);
  };

  const handleReturnToSelection = () => {
    setShowCaseSelection(true);
    setShowExplicitCaseSelection(false);
    setIsDiagnosisSubmitted(false);
    setIsNewCase(false);
    setNotes({});
    setConversationHistory([]);
  };

  // Handle notes update
  const handleNotesUpdate = (updatedNotes) => {
    setNotes(updatedNotes);

    // If we want to save to the backend as well
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

  // Handle new messages in conversation
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
    setNotes({});
    setConversationHistory([]);
    setIsDiagnosisSubmitted(false);
  };

  // Show login screen if not authenticated
  if (!authenticated) {
    // Show auth tester if URL has ?test-auth=true
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

  // IMPORTANT: Check for explicit case selection first
  // Handle showing case selection screen when requested from dashboard
  if (showExplicitCaseSelection) {
    console.log("App: showExplicitCaseSelection is true, showing CaseSelectionScreen with back button");
    return (
      <CaseSelectionScreen
        onCaseGenerated={handleCaseGenerated}
        onBackToDashboard={() => setShowExplicitCaseSelection(false)}
      />
    );
  }

  // Then handle the regular dashboard view
  if (showCaseSelection) {
    // If it's explicitly marked as showing case selection, render it
    if (window.location.search.includes('skip-dashboard=true')) {
      return <CaseSelectionScreen onCaseGenerated={handleCaseGenerated} />;
    }

    // Otherwise, show the student dashboard as the main landing screen
    return (
      <StudentDashboard
        user={user}
        onStartNewCase={() => {
          // Show case selection screen but keep showCaseSelection as true
          // so we can return to dashboard afterward
          console.log("App: onStartNewCase called, setting showExplicitCaseSelection=true");
          setShowExplicitCaseSelection(true);
        }}
        onResumeCaseClick={(caseId) => {
          // Handle resuming a specific case
          // In a real implementation, this would load the specified case
          console.log("Resuming case:", caseId);
          fetchCurrentCase();
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
    if (difficulty === 'hard') {
      return 'high';
    } else if (difficulty === 'moderate') {
      return 'medium';
    }

    return 'low';
  };

  const getInactivityThreshold = () => {
    const urgency = getCaseUrgency();
    switch (urgency) {
      case 'high':
        return 60; // 1 minute for urgent cases
      case 'medium':
        return 120; // 2 minutes for moderate cases
      case 'low':
        return 180; // 3 minutes for low urgency cases
      default:
        return 120; // Default to 2 minutes
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Clinical Engine</h1>
        <div className="case-info">
          {user && (
            <div className="user-profile">
              {user.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
              <span className="user-name">{user.name}</span>
              <button
                className="logout-btn"
                onClick={handleLogout}
              >
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
              {/* Added a button to return to case selection */}
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

        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === 'patient' ? 'active' : ''}`}
            onClick={() => setActiveTab('patient')}
          >
            Patient Interaction
          </button>
          <button
            className={`tab-button ${activeTab === 'labs' ? 'active' : ''}`}
            onClick={() => setActiveTab('labs')}
          >
            Laboratory Tests
          </button>
          <button
            className={`tab-button ${activeTab === 'imaging' ? 'active' : ''}`}
            onClick={() => setActiveTab('imaging')}
          >
            Imaging Studies
          </button>
          <button
            className={`tab-button ${activeTab === 'procedures' ? 'active' : ''}`}
            onClick={() => setActiveTab('procedures')}
          >
            Procedures
          </button>
        </div>
      </header>

      <div className="tab-content">
        {activeTab === 'patient' && (
          <div className="patient-tab">
            {/* Add vital signs monitor at the top */}
            <div className="vital-signs-container">
              <VitalSigns vitals={caseInfo?.vitals || {}} />
            </div>

          {/* Add the InactivityReminder component only when a case is active */}
          {caseInfo && !showCaseSelection && !isDiagnosisSubmitted && (
        <InactivityReminder inactivityThreshold={getInactivityThreshold()} />
          )}

            <div className="patient-grid-layout">
              {/* Left column: Chat */}
              <div className="chat-area">
                <ChatWindow
                  isDiagnosisSubmitted={isDiagnosisSubmitted}
                  isNewCase={isNewCase}
                  onNewCaseStart={handleNewCaseStarted}
                  conversationHistory={conversationHistory}
                  onNewMessage={handleNewMessage}
                />
              </div>

              {/* Right column: Physical exam & diagnosis stacked */}
              <div className="controls-area">
                <PhysicalExamPanel
                  isDisabled={isDiagnosisSubmitted}
                  caseInfo={caseInfo}
                />

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
              <TestOrderingPanel
                isDisabled={isDiagnosisSubmitted}
                forceTabType="lab"
              />
            </div>
          </div>
        )}

        {activeTab === 'imaging' && (
          <div className="imaging-tab">
            <div className="tab-container">
              <h2>Imaging Studies</h2>
              <p className="tab-description">Order imaging studies and review radiologic findings to support your diagnostic workup.</p>
              <TestOrderingPanel
                isDisabled={isDiagnosisSubmitted}
                forceTabType="imaging"
              />
            </div>
          </div>
        )}

        {activeTab === 'procedures' && (
          <div className="procedures-tab">
            <div className="tab-container">
              <h2>Investigative Procedures</h2>
              <p className="tab-description">Order specialized procedures to gather additional diagnostic information.</p>
              <div className="procedures-info">
                <TestOrderingPanel
                  isDisabled={isDiagnosisSubmitted}
                  forceTabType="procedure"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add NotesPanel - always visible across all tabs */}
      {caseInfo && (
        <NotesPanel
          caseInfo={caseInfo}
          isDisabled={isDiagnosisSubmitted}
          onNoteUpdate={handleNotesUpdate}
        />
      )}
    </div>
  );
}

export default App;
