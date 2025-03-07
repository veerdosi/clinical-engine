import React, { useState, useEffect } from 'react';
import './PhysicalExamPanel.css';

const PhysicalExamPanel = ({ isDisabled, caseInfo }) => {
  // State for the exam procedure workflow
  const [examName, setExamName] = useState('');
  const [currentStep, setCurrentStep] = useState('');
  const [procedureSteps, setProcedureSteps] = useState([]);
  const [stepNumber, setStepNumber] = useState(1);
  const [procedureComplete, setProcedureComplete] = useState(false);
  const [vitalSigns, setVitalSigns] = useState(null);
  const [examResults, setExamResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Fetch vitals on initial load
  useEffect(() => {
    if (caseInfo && caseInfo.id) {
      fetchVitalSigns();
    }
  }, [caseInfo]);

  const fetchVitalSigns = async () => {
    try {
      const response = await fetch('/api/physical-exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ system: 'vital_signs' })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch vital signs');
      }
      
      const data = await response.json();
      setVitalSigns(data);
    } catch (err) {
      console.error('Error fetching vital signs:', err);
      // Don't show error for initial fetch
    }
  };

  const handleExamNameChange = (e) => {
    setExamName(e.target.value);
    // Reset other fields when exam name changes
    setProcedureSteps([]);
    setCurrentStep('');
    setProcedureComplete(false);
    setStepNumber(1);
    setExamResults(null);
    setError(null);
    setFeedback(null);
  };

  const handleStepInputChange = (e) => {
    setCurrentStep(e.target.value);
  };

  const addProcedureStep = () => {
    if (!currentStep.trim()) return;
    
    const newSteps = [...procedureSteps, { 
      number: stepNumber, 
      description: currentStep 
    }];
    
    setProcedureSteps(newSteps);
    setStepNumber(stepNumber + 1);
    setCurrentStep('');
  };

  const removeStep = (index) => {
    const newSteps = [...procedureSteps];
    newSteps.splice(index, 1);
    
    // Renumber remaining steps
    const renumberedSteps = newSteps.map((step, idx) => ({
      ...step,
      number: idx + 1
    }));
    
    setProcedureSteps(renumberedSteps);
    setStepNumber(renumberedSteps.length + 1);
  };

  const checkProcedure = async () => {
    if (!examName || procedureSteps.length === 0) {
      setError("Please enter an examination name and at least one procedure step.");
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      // Format the procedure steps into a single object
      const formattedProcedure = {
        exam_name: examName,
        steps: procedureSteps.map(step => step.description)
      };
      
      const response = await fetch('/api/verify-physical-exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formattedProcedure)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Error verifying procedure');
      }
      
      if (data.is_correct) {
        setFeedback({
          type: 'success',
          message: 'Procedure steps verified correctly. Now performing examination...'
        });
        setProcedureComplete(true);
        
        // Now that the procedure is verified, perform the actual examination
        await performExamination(examName);
      } else {
        setFeedback({
          type: 'error',
          message: data.feedback || 'Procedure steps are incorrect. Please review and try again.'
        });
      }
    } catch (err) {
      console.error('Error verifying physical exam procedure:', err);
      setError(err.message || 'Error verifying procedure');
    } finally {
      setIsLoading(false);
    }
  };

  const performExamination = async (systemToExamine) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/physical-exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          system: systemToExamine,
          procedure_verified: true // Tell backend this procedure was verified
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to perform examination');
      }
      
      const data = await response.json();
      setExamResults(data);
      
      // If it's vital signs, update those separately
      if (systemToExamine === 'vital_signs') {
        setVitalSigns(data);
      }
    } catch (err) {
      console.error('Error performing examination:', err);
      setError(err.message || 'Error performing examination');
    } finally {
      setIsLoading(false);
    }
  };

  const resetExam = () => {
    setExamName('');
    setCurrentStep('');
    setProcedureSteps([]);
    setStepNumber(1);
    setProcedureComplete(false);
    setExamResults(null);
    setError(null);
    setFeedback(null);
  };

  return (
    <div className="physical-exam-panel">
      <div className="panel-header">
        <h3>Physical Examination</h3>
        <p>Enter examination name and procedure steps in the correct order</p>
      </div>
      
      {vitalSigns && (
        <div className="vital-signs-display">
          <h4>Current Vital Signs</h4>
          <div className="vital-signs-grid">
            {Object.entries(vitalSigns.findings || {}).map(([key, value]) => (
              <div key={key} className="vital-sign-item">
                <span className="vital-label">{key}:</span>
                <span className="vital-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="exam-procedure-section">
        <div className="input-group">
          <label htmlFor="exam-name">Examination Name:</label>
          <input
            type="text"
            id="exam-name"
            value={examName}
            onChange={handleExamNameChange}
            placeholder="e.g., Cardiac Auscultation, Abdominal Examination"
            disabled={isDisabled || isLoading || procedureComplete}
          />
        </div>
        
        {procedureSteps.length > 0 && (
          <div className="procedure-steps-list">
            <h4>Procedure Steps:</h4>
            <ol>
              {procedureSteps.map((step, index) => (
                <li key={index}>
                  {step.description}
                  {!procedureComplete && (
                    <button 
                      className="remove-step-btn"
                      onClick={() => removeStep(index)}
                      disabled={isDisabled || isLoading}
                    >
                      ✕
                    </button>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}
        
        {!procedureComplete && (
          <div className="step-input-section">
            <div className="input-group">
              <label htmlFor="step-input">Step {stepNumber}:</label>
              <textarea
                id="step-input"
                value={currentStep}
                onChange={handleStepInputChange}
                placeholder="Describe the next procedure step in detail..."
                disabled={isDisabled || isLoading || !examName}
              />
            </div>
            
            <div className="step-buttons">
              <button 
                className="add-step-btn"
                onClick={addProcedureStep}
                disabled={isDisabled || isLoading || !currentStep.trim()}
              >
                Add Step
              </button>
              
              <button 
                className="check-procedure-btn"
                onClick={checkProcedure}
                disabled={isDisabled || isLoading || procedureSteps.length === 0}
              >
                {isLoading ? 'Processing...' : 'Verify & Perform Examination'}
              </button>
            </div>
          </div>
        )}
        
        {feedback && (
          <div className={`feedback-message ${feedback.type}`}>
            <p>{feedback.message}</p>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}
        
        {examResults && (
          <div className="exam-results">
            <div className="result-header">
              <h4>Examination Findings: {examName}</h4>
              <button 
                className="new-exam-btn"
                onClick={resetExam}
                disabled={isDisabled || isLoading}
              >
                New Examination
              </button>
            </div>
            
            <div className="exam-content">
              {examResults.findings ? (
                <div dangerouslySetInnerHTML={{ 
                  __html: typeof examResults.findings === 'string' 
                    ? examResults.findings.replace(/\n/g, '<br>') 
                    : Object.entries(examResults.findings)
                      .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
                      .join('')
                }} />
              ) : (
                <p>No significant findings.</p>
              )}
              
              {examResults.interpretation && (
                <div className="exam-interpretation">
                  <h5>Interpretation</h5>
                  <p>{examResults.interpretation}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PhysicalExamPanel;