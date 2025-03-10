import React, { useState } from 'react';
import './DiagnosisPanel.css';

const DiagnosisPanel = ({ case_info, onNewCase, onDiagnosisSubmitted, onReturnToSelection }) => {
  const [diagnosis, setDiagnosis] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!diagnosis.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/submit-diagnosis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          diagnosis: diagnosis.trim(),
          case_id: case_info.id || 'current',
        }),
      });

      const data = await response.json();
      setResult(data);
      setIsSubmitted(true);
      
      // Notify parent component that diagnosis has been submitted
      if (onDiagnosisSubmitted) {
        onDiagnosisSubmitted();
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
    await onNewCase();
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
          
          <div className="evaluation-summary">
            <h5>Performance Summary:</h5>
            <ul>
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