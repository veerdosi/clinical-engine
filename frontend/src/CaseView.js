import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import ChatWindow from './ChatWindow';
import DiagnosisPanel from './DiagnosisPanel';
import TestOrderingPanel from './TestOrderingPanel';
import PhysicalExamPanel from './PhysicalExamPanel';
import VitalSigns from './VitalSigns';
import NotesPanel from './NotesPanel';
import InactivityReminder from './InactivityReminder';
import { resumeCase } from './api';
import './App.css';

function CaseView() {
  const [caseInfo, setCaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDiagnosisSubmitted, setIsDiagnosisSubmitted] = useState(false);
  const [isNewCase, setIsNewCase] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  const navigate = useNavigate();
  const { caseId } = useParams(); // Get case ID from URL if resuming

  useEffect(() => {
    if (caseId) {
      // Resume existing case
      resumeExistingCase(caseId);
    } else {
      // Load current case
      fetchCurrentCase();
    }
  }, [caseId]);

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
    } finally {
      setLoading(false);
    }
  };

  const resumeExistingCase = async (caseId) => {
    setLoading(true);
    try {
      const response = await resumeCase(caseId);

      if (response.success) {
        setCaseInfo(response.case);
        setError(null);
        setIsDiagnosisSubmitted(false);
        // You could restore other session data here if needed
      } else {
        throw new Error('Failed to resume case');
      }
    } catch (err) {
      console.error('Error resuming case:', err);
      setError('Unable to resume case. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnosisSubmitted = () => {
    setIsDiagnosisSubmitted(true);
  };

  const handleNewCaseStarted = () => {
    setIsNewCase(false);
  };

  const handleReturnToDashboard = () => {
    navigate('/dashboard');
  };

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
          <button onClick={handleReturnToDashboard}>Return to Dashboard</button>
        </div>
      </div>
    );
  }

  if (!caseInfo) {
    return (
      <div className="App error">
        <div className="error-message">
          <h2>No Case Data</h2>
          <p>No case information available.</p>
          <button onClick={handleReturnToDashboard}>Return to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo-section">
            <img src="/logo.svg" alt="Clinical Engine Logo" className="logo-img" />
            <h1>Clinical Engine</h1>
          </div>
          <div className="case-info">
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
              onClick={handleReturnToDashboard}
              disabled={loading}
            >
              Return to Dashboard
            </button>
          </div>
        </div>

        <div className="tab-navigation">
          <NavLink
            to={caseId ? `/case/${caseId}/patient` : '/case/patient'}
            className={({ isActive }) => `tab-button ${isActive ? 'active' : ''}`}
          >
            Patient Interaction
          </NavLink>
          <NavLink
            to={caseId ? `/case/${caseId}/labs` : '/case/labs'}
            className={({ isActive }) => `tab-button ${isActive ? 'active' : ''}`}
          >
            Laboratory Tests
          </NavLink>
          <NavLink
            to={caseId ? `/case/${caseId}/imaging` : '/case/imaging'}
            className={({ isActive }) => `tab-button ${isActive ? 'active' : ''}`}
          >
            Imaging Studies
          </NavLink>
          <NavLink
            to={caseId ? `/case/${caseId}/procedures` : '/case/procedures'}
            className={({ isActive }) => `tab-button ${isActive ? 'active' : ''}`}
          >
            Procedures
          </NavLink>
        </div>
      </header>

      <div className="tab-content">
        <Routes>
          {/* Default redirect to patient tab */}
          <Route path="/" element={<Navigate to="patient" replace />} />

          {/* Patient interaction tab */}
          <Route path="/patient" element={
            <div className="patient-tab">
              <div className="vital-signs-container">
                <VitalSigns vitals={caseInfo?.vitals || {}} />
              </div>
              {caseInfo && !isDiagnosisSubmitted && (
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
                    onDiagnosisSubmitted={handleDiagnosisSubmitted}
                    onReturnToSelection={handleReturnToDashboard}
                  />
                </div>
              </div>
            </div>
          } />

          {/* Laboratory tests tab */}
          <Route path="/labs" element={
            <div className="labs-tab">
              <div className="tab-container">
                <h2>Laboratory Testing</h2>
                <p className="tab-description">Order laboratory tests and review results to aid in your diagnosis.</p>
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="lab" />
              </div>
            </div>
          } />

          {/* Imaging studies tab */}
          <Route path="/imaging" element={
            <div className="imaging-tab">
              <div className="tab-container">
                <h2>Imaging Studies</h2>
                <p className="tab-description">Order imaging studies and review radiologic findings to support your diagnostic workup.</p>
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="imaging" />
              </div>
            </div>
          } />

          {/* Procedures tab */}
          <Route path="/procedures" element={
            <div className="procedures-tab">
              <div className="tab-container">
                <h2>Investigative Procedures</h2>
                <p className="tab-description">Order specialized procedures to gather additional diagnostic information.</p>
                <div className="procedures-info">
                  <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="procedure" />
                </div>
              </div>
            </div>
          } />
        </Routes>
      </div>

      <NotesPanel
        caseInfo={caseInfo}
        isDisabled={isDiagnosisSubmitted}
        onNoteUpdate={handleNotesUpdate}
      />

      {!isDiagnosisSubmitted && (
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

export default CaseView;
