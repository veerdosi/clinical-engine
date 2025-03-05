import React, { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';
import DiagnosisPanel from './DiagnosisPanel';
import TestOrderingPanel from './TestOrderingPanel';
import PhysicalExamPanel from './PhysicalExamPanel';
import './App.css';

function App() {
  const [caseInfo, setCaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDiagnosisSubmitted, setIsDiagnosisSubmitted] = useState(false);
  const [isNewCase, setIsNewCase] = useState(false);

  // Fetch the current active case when the component mounts
  useEffect(() => {
    fetchCurrentCase();
  }, []);

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

  const handleNewCase = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/new-case', {
        method: 'POST'
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
      
      return true;
    } catch (err) {
      console.error('Error generating new case:', err);
      setError('Unable to generate a new patient case. Please try again.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnosisSubmitted = () => {
    setIsDiagnosisSubmitted(true);
  };

  const handleNewCaseStarted = () => {
    // Reset the new case flag once processed by child components
    setIsNewCase(false);
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
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Clinical Engine</h1>
        <div className="case-info">
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
            </>
          )}
        </div>
      </header>
      
      <div className="content-container">
        <div className="main-content">
          <div className="chat-container">
            <ChatWindow 
              isDiagnosisSubmitted={isDiagnosisSubmitted}
              isNewCase={isNewCase}
              onNewCaseStart={handleNewCaseStarted}
            />
          </div>
        </div>
        
        <div className="sidebar-content">
          <PhysicalExamPanel 
            isDisabled={isDiagnosisSubmitted}
            caseInfo={caseInfo}
          />
          
          <TestOrderingPanel isDisabled={isDiagnosisSubmitted} />
          
          <DiagnosisPanel 
            case_info={caseInfo} 
            onNewCase={handleNewCase}
            onDiagnosisSubmitted={handleDiagnosisSubmitted}
          />
        </div>
      </div>
    </div>
  );
}

export default App;