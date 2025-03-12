// Complete App.js with tabbed navigation, VitalSigns, and NotesPanel integration
import React, { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';
import DiagnosisPanel from './DiagnosisPanel';
import TestOrderingPanel from './TestOrderingPanel';
import PhysicalExamPanel from './PhysicalExamPanel';
import CaseSelectionScreen from './CaseSelectionScreen';
import VitalSigns from './VitalSigns';
import NotesPanel from './NotesPanel'; // Import the NotesPanel component
import './App.css';

function App() {
  const [caseInfo, setCaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDiagnosisSubmitted, setIsDiagnosisSubmitted] = useState(false);
  const [isNewCase, setIsNewCase] = useState(false);
  const [showCaseSelection, setShowCaseSelection] = useState(true); // Start with case selection
  const [activeTab, setActiveTab] = useState('patient'); // Default to patient tab
  const [notes, setNotes] = useState({}); // Add state for notes

  // We'll keep this to handle case loading on initial visit, but we'll show the selection screen
  useEffect(() => {
    if (!showCaseSelection) {
      fetchCurrentCase();
    } else {
      setLoading(false); // No need to load case initially if we're showing selection screen
    }
  }, [showCaseSelection]);

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
      
      // Hide case selection screen when we have a case
      setShowCaseSelection(false);
      
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
    setActiveTab('patient'); // Reset to the patient tab
    setNotes({}); // Reset notes
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
    setIsDiagnosisSubmitted(false);
    setIsNewCase(false);
    setNotes({});
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

  // Show case selection screen if the flag is true
  if (showCaseSelection) {
    return <CaseSelectionScreen onCaseGenerated={handleCaseGenerated} />;
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
            
            <div className="patient-grid-layout">
              {/* Left column: Chat */}
              <div className="chat-area">
                <ChatWindow 
                  isDiagnosisSubmitted={isDiagnosisSubmitted}
                  isNewCase={isNewCase}
                  onNewCaseStart={handleNewCaseStarted}
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