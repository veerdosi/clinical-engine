import React, { useState } from 'react';
import './DiagnosisPanel.css';
import TimelineVisualization from './TimelineVisualization';

const DiagnosisPanel = ({ case_info, onNewCase, onDiagnosisSubmitted, onReturnToSelection }) => {
  const [diagnosis, setDiagnosis] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);

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
        headers: {
          'Content-Type': 'application/json',
        },
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
      // Pass the result data to allow parent to access timeline data
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
    await onNewCase();
  };
  
  const toggleTimeline = () => {
    setShowTimeline(!showTimeline);
  };

  return (
    <div className="diagnosis-panel">
      <div className="diagnosis-header">
        <h3>Medical Diagnosis</h3>
        <p>Submit your final diagnosis based on your evaluation</p>
      </div>

      {!isSubmitted ? (
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
      ) : (
        <div className={`diagnosis-result ${result.correct ? 'correct' : 'incorrect'}`}>
          <h4>{result.correct ? '✅ Correct Diagnosis!' : '❌ Incorrect Diagnosis'}</h4>
          
          <div className="diagnosis-details">
            <p><strong>Your diagnosis:</strong> {diagnosis}</p>
            <p><strong>Correct diagnosis:</strong> {result.actual_diagnosis}</p>
          </div>
          
          <div className="feedback">
            <h5>Feedback:</h5>
            <p>{result.feedback}</p>
          </div>
          
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
          
          <div className="evaluation-summary">
            <h5>Performance Summary:</h5>
            <ul>
              {/* Original evaluation items */}
              {result.key_findings_identified && (
                <li className="positive">Identified key findings</li>
              )}
              {result.missed_key_findings && result.missed_key_findings.length > 0 && (
                <li className="negative">Missed important symptoms: {result.missed_key_findings.join(', ')}</li>
              )}
              {result.unnecessary_tests && result.unnecessary_tests.length > 0 && (
                <li className="negative">Ordered unnecessary tests: {result.unnecessary_tests.join(', ')}</li>
              )}
              {result.critical_tests_ordered && (
                <li className="positive">Ordered all critical tests</li>
              )}
              {result.missed_critical_tests && result.missed_critical_tests.length > 0 && (
                <li className="negative">Failed to order critical tests: {result.missed_critical_tests.join(', ')}</li>
              )}
              
              {/* Add notes evaluation items */}
              {result.notes_strengths && result.notes_strengths.length > 0 && (
                <li className="positive">Documentation strength: {result.notes_strengths[0]}</li>
              )}
              {result.notes_improvements && result.notes_improvements.length > 0 && (
                <li className="negative">Documentation needs improvement: {result.notes_improvements[0]}</li>
              )}
              {result.overall_notes_score > 0 ? (
                <li className={result.overall_notes_score >= 7 ? "positive" : "negative"}>
                  Documentation score: {result.overall_notes_score}/10
                </li>
              ) : (
                <li className="negative">No patient notes created</li>
              )}
              
              {/* Add workflow evaluation items */}
              {result.workflow_strengths && result.workflow_strengths.length > 0 && (
                <li className="positive">Workflow strength: {result.workflow_strengths[0]}</li>
              )}
              {result.workflow_improvements && result.workflow_improvements.length > 0 && (
                <li className="negative">Workflow needs improvement: {result.workflow_improvements[0]}</li>
              )}
              {result.overall_workflow_score > 0 ? (
                <li className={result.overall_workflow_score >= 7 ? "positive" : "negative"}>
                  Clinical workflow score: {result.overall_workflow_score}/10
                </li>
              ) : null}
            </ul>
          </div>
          
          <div className="button-group">
            <button className="new-case-btn" onClick={handleNewCase}>
              Start New Case
            </button>
            
            {/* Add this button if onReturnToSelection prop is provided */}
            {onReturnToSelection && (
              <button className="selection-btn" onClick={onReturnToSelection}>
                Return to Case Selection
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DiagnosisPanel;