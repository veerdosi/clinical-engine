import React, { useState, useEffect, useCallback } from 'react'; 
import './NotesPanel.css';

const NotesPanel = ({ caseInfo, isDisabled, onNoteUpdate }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [notes, setNotes] = useState({
    subjective: '',
    objective: '',
    assessment: '',
    plan: ''
  });
  const [activeTab, setActiveTab] = useState('subjective');
  const [autoSaveStatus, setAutoSaveStatus] = useState('');

  useEffect(() => {
    if (caseInfo && caseInfo.id) {
      const savedNotes = sessionStorage.getItem(`notes_${caseInfo.id}`);
      if (savedNotes) {
        try {
          const parsedNotes = JSON.parse(savedNotes);
          setNotes(parsedNotes);
        } catch (e) {
          console.error('Error parsing saved notes:', e);
          // Optionally reset to default if parsing fails
          setNotes({ subjective: '', objective: '', assessment: '', plan: '' });
        }
      } else {
        // Reset notes if no saved notes for new caseId
        setNotes({ subjective: '', objective: '', assessment: '', plan: '' });
      }
    }
  }, [caseInfo]); // Runs when caseInfo changes

  const saveNotes = useCallback(() => {
    if (caseInfo && caseInfo.id) {
      sessionStorage.setItem(`notes_${caseInfo.id}`, JSON.stringify(notes));
      if (onNoteUpdate) {
        onNoteUpdate(notes);
      }
      setAutoSaveStatus('Saved');
      setTimeout(() => setAutoSaveStatus(''), 2000);
    }
  }, [caseInfo, notes, onNoteUpdate]); // Dependencies for saveNotes

  // Auto-save notes every 5 seconds if changed
  useEffect(() => {
    let autoSaveTimer;

    if (caseInfo && caseInfo.id && isExpanded) {
      autoSaveTimer = setInterval(() => {
        saveNotes(); // saveNotes is now memoized
      }, 5000);
    }

    return () => {
      if (autoSaveTimer) clearInterval(autoSaveTimer);
    };
  }, [caseInfo, isExpanded, saveNotes]); // Added saveNotes to dependencies

  const togglePanel = () => {
    setIsExpanded(!isExpanded);
  };

  const handleNoteChange = (section, value) => {
    setNotes(prev => ({ ...prev, [section]: value }));
    setAutoSaveStatus('Editing...');
  };

  // ... (rest of the component remains the same)
  const getSectionPlaceholder = (section) => {
    switch (section) {
      case 'subjective':
        return "Enter patient's history, symptoms, and concerns as reported by the patient...";
      case 'objective':
        return "Enter physical examination findings, vital signs, lab results, and other objective data...";
      case 'assessment':
        return "Enter your diagnostic assessment, differential diagnoses, and clinical reasoning...";
      case 'plan':
        return "Enter your treatment plan, interventions, further testing, and follow-up recommendations...";
      default:
        return "Enter notes...";
    }
  };

  const countTotalWords = () => {
    const allText = Object.values(notes).join(' ');
    return allText.split(/\s+/).filter(word => word.trim().length > 0).length;
  };

  return (
    <div className={`notes-panel-container ${isExpanded ? 'expanded' : ''}`}>
      {!isExpanded ? (
        <button
          className="notes-toggle-btn"
          onClick={togglePanel}
          title="SOAP Notes"
          disabled={isDisabled}
        >
          📝
          <span className="notes-count">{countTotalWords()}</span>
        </button>
      ) : (
        <div className="notes-panel">
          <div className="notes-header">
            <h3>Patient Notes (SOAP)</h3>
            <div className="notes-controls">
              <span className={`autosave-status ${autoSaveStatus ? 'active' : ''}`}>
                {autoSaveStatus}
              </span>
              <button className="notes-close-btn" onClick={togglePanel}>×</button>
            </div>
          </div>

          <div className="notes-tabs">
            <button
              className={`tab-btn ${activeTab === 'subjective' ? 'active' : ''}`}
              onClick={() => setActiveTab('subjective')}
            >
              Subjective
            </button>
            <button
              className={`tab-btn ${activeTab === 'objective' ? 'active' : ''}`}
              onClick={() => setActiveTab('objective')}
            >
              Objective
            </button>
            <button
              className={`tab-btn ${activeTab === 'assessment' ? 'active' : ''}`}
              onClick={() => setActiveTab('assessment')}
            >
              Assessment
            </button>
            <button
              className={`tab-btn ${activeTab === 'plan' ? 'active' : ''}`}
              onClick={() => setActiveTab('plan')}
            >
              Plan
            </button>
          </div>

          <div className="notes-content">
            <textarea
              className="notes-textarea"
              value={notes[activeTab]}
              onChange={(e) => handleNoteChange(activeTab, e.target.value)}
              placeholder={getSectionPlaceholder(activeTab)}
              disabled={isDisabled}
            />
          </div>

          <div className="notes-actions">
            <div className="notes-info">
              <span className="word-count">Words: {countTotalWords()}</span>
              <span className="patient-info">{caseInfo?.name}, {caseInfo?.age}{caseInfo?.gender === 'Male' ? 'M' : 'F'}</span>
            </div>
            <button
              className="save-btn"
              onClick={saveNotes}
              disabled={isDisabled}
            >
              Save Notes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default NotesPanel;