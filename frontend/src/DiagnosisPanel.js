// Completely rewritten DiagnosisPanel.js with fixed fullscreen modal implementation

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import './DiagnosisPanel.css';
import TimelineVisualization from './TimelineVisualization';

const DiagnosisPanel = ({ case_info, onNewCase, onDiagnosisSubmitted, onReturnToSelection }) => {
  const [diagnosis, setDiagnosis] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);
  const [showModal, setShowModal] = useState(false);
  
  // When diagnosis is submitted and we have a result, automatically show modal after a delay
  useEffect(() => {
    if (isSubmitted && result) {
      const timer = setTimeout(() => {
        setShowModal(true);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isSubmitted, result]);

  // Handle body scroll lock when modal is open
  useEffect(() => {
    if (showModal) {
      // Save current scroll position and lock scroll
      const scrollY = window.scrollY;
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.width = '100%';
      document.body.style.overflow = 'hidden';
    } else {
      // Restore scroll position
      const scrollY = document.body.style.top;
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.width = '';
      document.body.style.overflow = '';
      
      if (scrollY) {
        window.scrollTo(0, parseInt(scrollY || '0', 10) * -1);
      }
    }
    
    // Clean up function
    return () => {
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.width = '';
      document.body.style.overflow = '';
    };
  }, [showModal]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape' && showModal) {
        setShowModal(false);
      }
    };
    
    window.addEventListener('keydown', handleEscKey);
    return () => {
      window.removeEventListener('keydown', handleEscKey);
    };
  }, [showModal]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!diagnosis.trim()) return;

    setLoading(true);
    try {
      // Get notes from sessionStorage for this case
      let notes = {};
      if (case_info && case_info.id) {
        const savedNotes = sessionStorage.getItem(`notes_${case_info.id}`);
        if (savedNotes) {
          try {
            notes = JSON.parse(savedNotes);
          } catch (e) {
            console.error('Error parsing saved notes:', e);
          }
        }
      }

      const response = await fetch('/api/submit-diagnosis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          diagnosis: diagnosis.trim(),
          case_id: case_info.id || 'current',
          notes: notes // Include notes in the diagnosis submission
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      setIsSubmitted(true);
      setShowTimeline(true);
      
      // Notify parent component that diagnosis has been submitted
      if (onDiagnosisSubmitted) {
        onDiagnosisSubmitted(data);
      }
    } catch (error) {
      console.error('Error submitting diagnosis:', error);
      setResult({
        correct: false,
        feedback: 'Error submitting diagnosis. Please try again.',
        actual_diagnosis: 'Unknown',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNewCase = async () => {
    setDiagnosis('');
    setIsSubmitted(false);
    setResult(null);
    setShowTimeline(false);
    setShowModal(false);
    await onNewCase();
  };
  
  const toggleTimeline = () => {
    setShowTimeline(!showTimeline);
  };

  const toggleModal = () => {
    setShowModal(!showModal);
  };

  const getAssessmentText = (category, score) => {
    if (score === 0) {
      switch(category) {
        case "documentation":
          return "No patient notes created";
        case "physical_exam":
          return "No examinations performed";
        default:
          return "No evaluation possible";
      }
    }
    
    if (score >= 9) return "Exceptional";
    if (score >= 8) return "Very Good";
    if (score >= 6) return "Adequate";
    if (score >= 4) return "Needs Improvement";
    return "Significantly Below Expectations";
  };
  
  const calculateOverallScore = (scores) => {
    // Define weights for different categories
    const weights = {
      diagnosis_accuracy: 0.25,
      communication: 0.15,
      exam_thoroughness: 0.15,
      clinical_reasoning: 0.20,
      notes_completeness: 0.10,
      workflow_efficiency: 0.15
    };
    
    let weightedScore = 0;
    let totalWeight = 0;
    
    // Calculate weighted sum
    for (const [category, weight] of Object.entries(weights)) {
      if (scores[category] !== undefined) {
        weightedScore += scores[category] * weight;
        totalWeight += weight;
      }
    }
    
    // Return rounded weighted average
    return totalWeight > 0 ? Math.round(weightedScore / totalWeight) : 0;
  };

  const renderScoreTable = () => {
    if (!result || !result.scores) return null;
    
    const scores = result.scores;
    
    return (
      <div className="score-table-container">
        <h3>Clinical Performance Scores</h3>
        <table className="evaluation-score-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Score</th>
              <th>Assessment</th>
            </tr>
          </thead>
          <tbody>
            <tr className={scores.diagnosis_accuracy >= 8 ? "good-score" : scores.diagnosis_accuracy >= 6 ? "average-score" : "poor-score"}>
              <td>Diagnosis Accuracy</td>
              <td>{scores.diagnosis_accuracy}/10</td>
              <td>{getAssessmentText("diagnosis_accuracy", scores.diagnosis_accuracy)}</td>
            </tr>
            <tr className={scores.communication >= 8 ? "good-score" : scores.communication >= 6 ? "average-score" : "poor-score"}>
              <td>Communication Skills</td>
              <td>{scores.communication}/10</td>
              <td>{getAssessmentText("communication", scores.communication)}</td>
            </tr>
            <tr className={scores.exam_thoroughness >= 8 ? "good-score" : scores.exam_thoroughness >= 6 ? "average-score" : "poor-score"}>
              <td>Physical Examination</td>
              <td>{scores.exam_thoroughness}/10</td>
              <td>{getAssessmentText("physical_exam", scores.exam_thoroughness)}</td>
            </tr>
            <tr className={scores.clinical_reasoning >= 8 ? "good-score" : scores.clinical_reasoning >= 6 ? "average-score" : "poor-score"}>
              <td>Clinical Reasoning</td>
              <td>{scores.clinical_reasoning}/10</td>
              <td>{getAssessmentText("clinical_reasoning", scores.clinical_reasoning)}</td>
            </tr>
            <tr className={scores.notes_completeness >= 8 ? "good-score" : scores.notes_completeness >= 6 ? "average-score" : "poor-score"}>
              <td>Documentation</td>
              <td>{scores.notes_completeness}/10</td>
              <td>{getAssessmentText("documentation", scores.notes_completeness)}</td>
            </tr>
            <tr className={scores.workflow_efficiency >= 8 ? "good-score" : scores.workflow_efficiency >= 6 ? "average-score" : "poor-score"}>
              <td>Workflow Efficiency</td>
              <td>{scores.workflow_efficiency}/10</td>
              <td>{getAssessmentText("workflow", scores.workflow_efficiency)}</td>
            </tr>
            <tr className="overall-score">
              <td><strong>Overall Performance</strong></td>
              <td><strong>{calculateOverallScore(scores)}/10</strong></td>
              <td>{getAssessmentText("overall", calculateOverallScore(scores))}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  };
  
  const renderStrengthsAndAreas = () => {
    if (!result) return null;
    
    return (
      <div className="evaluation-summary">
        <h3>Detailed Feedback</h3>
        
        {result.strengths && result.strengths.length > 0 && (
          <div className="strengths-section">
            <h4>Strengths:</h4>
            <ul className="strengths-list">
              {result.strengths.map((strength, index) => (
                <li key={`strength-${index}`} className="positive">{strength}</li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="improvements-section">
          <h4>Areas Needing Improvement:</h4>
          <ul className="improvements-list">
            {result.interaction_improvements && result.interaction_improvements.length > 0 && (
              <li className="negative">
                <strong>Patient Interaction:</strong> {result.interaction_improvements[0]}
              </li>
            )}
            
            {result.missed_key_exams && result.missed_key_exams.length > 0 && (
              <li className="negative">
                <strong>Physical Examination:</strong> Missed critical examinations ({result.missed_key_exams.join(', ')})
              </li>
            )}
            
            {result.missed_critical_tests && result.missed_critical_tests.length > 0 && (
              <li className="negative">
                <strong>Test Selection:</strong> Failed to order required tests ({result.missed_critical_tests.join(', ')})
              </li>
            )}
            
            {result.notes_improvements && result.notes_improvements.length > 0 && (
              <li className="negative">
                <strong>Documentation:</strong> {result.notes_improvements[0]}
              </li>
            )}
            
            {result.workflow_improvements && result.workflow_improvements.length > 0 && (
              <li className="negative">
                <strong>Clinical Workflow:</strong> {result.workflow_improvements[0]}
              </li>
            )}
          </ul>
        </div>
      </div>
    );
  };

  // Modal component that will be rendered at the root level
  const FullscreenModal = () => {
    return ReactDOM.createPortal(
      <div className="diagnosis-modal-overlay">
        <div className="diagnosis-modal-content">
          <button 
            className="diagnosis-modal-close" 
            onClick={toggleModal}
            aria-label="Close dialog"
          >
            &times;
          </button>
          
          <div className="diagnosis-modal-header">
            <h3>{result.correct ? '✅ Correct Diagnosis!' : '❌ Incorrect Diagnosis'}</h3>
          </div>
          
          <div className="diagnosis-modal-body">
            <div className="diagnosis-details">
              <p><strong>Your diagnosis:</strong> {diagnosis}</p>
              <p><strong>Correct diagnosis:</strong> {result.actual_diagnosis}</p>
            </div>
            
            {renderScoreTable()}
            {renderStrengthsAndAreas()}
            
            <div className="workflow-section">
              <button 
                className="toggle-timeline-btn" 
                onClick={toggleTimeline}
              >
                {showTimeline ? 'Hide Timeline' : 'Show Clinical Workflow Timeline'}
              </button>
              
              {showTimeline && result.timeline_data && (
                <TimelineVisualization 
                  timelineData={result.timeline_data} 
                  efficiencyMetrics={result.efficiency_metrics}
                />
              )}
            </div>
          </div>
          
          <div className="diagnosis-modal-footer">
            <button className="new-case-btn" onClick={handleNewCase}>
              Start New Case
            </button>
            
            {onReturnToSelection && (
              <button className="selection-btn" onClick={onReturnToSelection}>
                Return to Case Selection
              </button>
            )}
          </div>
        </div>
      </div>,
      document.body // Mount directly to body to avoid positioning issues
    );
  };

  // Normal panel content
  return (
    <div className="diagnosis-panel">
      {!isSubmitted ? (
        /* Form view when diagnosis hasn't been submitted yet */
        <>
          <div className="diagnosis-header">
            <h3>Medical Diagnosis</h3>
            <p>Submit your final diagnosis based on your evaluation</p>
          </div>

          <form onSubmit={handleSubmit} className="diagnosis-form">
            <div className="input-group">
              <label htmlFor="diagnosis">Final Diagnosis:</label>
              <input
                type="text"
                id="diagnosis"
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                placeholder="Enter your diagnosis"
                disabled={loading}
              />
            </div>
            <button type="submit" disabled={!diagnosis.trim() || loading}>
              {loading ? 'Submitting...' : 'Submit Diagnosis'}
            </button>
          </form>
        </>
      ) : (
        /* Result view with expand button */
        <div className={`diagnosis-result ${result.correct ? 'correct' : 'incorrect'}`}>
          <div className="diagnosis-header-controls">
            <h4>{result.correct ? '✅ Correct Diagnosis!' : '❌ Incorrect Diagnosis'}</h4>
            <button 
              className="expand-view-btn" 
              onClick={toggleModal}
              title="View full evaluation"
            >
              <span className="expand-icon">⛶</span>
            </button>
          </div>
          
          <div className="diagnosis-details">
            <p><strong>Your diagnosis:</strong> {diagnosis}</p>
            <p><strong>Correct diagnosis:</strong> {result.actual_diagnosis}</p>
          </div>
          
          <div className="button-group">
            <button className="new-case-btn" onClick={handleNewCase}>
              Start New Case
            </button>
          </div>
        </div>
      )}
      
      {/* Render modal when showModal is true */}
      {showModal && <FullscreenModal />}
    </div>
  );
};

export default DiagnosisPanel;