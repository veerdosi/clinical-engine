// Stable PhysicalExamPanel.js with proper fullscreen modal
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import './PhysicalExamPanel.css';

// This component handles the actual modal content and doesn't re-render when parent state changes
const ExamModal = ({ 
  onClose, 
  examName, setExamName,
  currentStep, setCurrentStep,
  procedureSteps, setProcedureSteps,
  stepNumber, setStepNumber,
  procedureComplete, setProcedureComplete,
  examResults, setExamResults,
  error, setError,
  isLoading, setIsLoading,
  feedback, setFeedback,
  isDisabled,
  resetExam,
  checkProcedure
}) => {
  // Setup body locking once when modal opens
  useEffect(() => {
    const originalStyle = window.getComputedStyle(document.body).overflow;
    const originalPosition = window.getComputedStyle(document.body).position;
    const scrollY = window.scrollY;
    
    // Lock body scroll
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = '100%';
    
    // Handle ESC key
    const handleEscKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleEscKey);
    
    // Clean up function
    return () => {
      // Restore original body styles and scroll position
      document.body.style.overflow = originalStyle;
      document.body.style.position = originalPosition;
      document.body.style.top = '';
      document.body.style.width = '';
      
      // Restore scroll position
      window.scrollTo(0, scrollY);
      window.removeEventListener('keydown', handleEscKey);
    };
  }, [onClose]);
  
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
  
  // Create a modal element that's attached to the body
  return ReactDOM.createPortal(
    <div className="exam-modal-overlay" onClick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div className="exam-modal-content">
        <button 
          className="exam-modal-close" 
          onClick={onClose}
          aria-label="Close dialog"
        >
          &times;
        </button>
        
        <div className="exam-modal-header">
          <h3>Physical Examination</h3>
        </div>
        
        <div className="exam-modal-body">
          <div className="exam-procedure-section">
            <div className="input-group">
              <label htmlFor="exam-name-modal">Examination Name:</label>
              <input
                type="text"
                id="exam-name-modal"
                value={examName}
                onChange={(e) => setExamName(e.target.value)}
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
                    onChange={(e) => setCurrentStep(e.target.value)}
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
        
        <div className="exam-modal-footer">
          <button className="close-modal-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

// Main component that manages state
const PhysicalExamPanel = ({ isDisabled, caseInfo }) => {
  // State for the exam procedure workflow
  const [examName, setExamName] = useState('');
  const [currentStep, setCurrentStep] = useState('');
  const [procedureSteps, setProcedureSteps] = useState([]);
  const [stepNumber, setStepNumber] = useState(1);
  const [procedureComplete, setProcedureComplete] = useState(false);
  const [examResults, setExamResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showModal, setShowModal] = useState(false);

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
    } catch (err) {
      console.error('Error performing examination:', err);
      setError(err.message || 'Error performing examination');
    } finally {
      setIsLoading(false);
    }
  };

  // Regular panel content (non-modal view)
  return (
    <div className="physical-exam-panel">
      <div className="panel-header">
        <h3>Physical Examination</h3>
        <div className="header-controls">
          <p>Enter examination name and procedure steps in the correct order</p>
          <button 
            className="expand-view-btn" 
            onClick={() => setShowModal(true)}
            title="Expand to full screen"
          >
            <span className="expand-icon">⛶</span>
          </button>
        </div>
      </div>

      {/* Show condensed content in the panel when not in fullscreen */}
      <div className="panel-summary">
        <div className="input-group">
          <label htmlFor="exam-name-summary">Examination Name:</label>
          <input
            type="text"
            id="exam-name-summary"
            value={examName}
            onChange={handleExamNameChange}
            placeholder="e.g., Cardiac Auscultation, Abdominal Examination"
            disabled={isDisabled || isLoading || procedureComplete}
          />
        </div>
        
        <div className="summary-content">
          {procedureSteps.length > 0 ? (
            <div className="procedure-steps-summary">
              <p>Steps added: {procedureSteps.length}</p>
            </div>
          ) : (
            <p>No procedure steps added yet</p>
          )}
          
          {examResults && (
            <div className="results-summary">
              <p><strong>Findings available for:</strong> {examName}</p>
            </div>
          )}
        </div>
        
        <button 
          className="fullscreen-btn" 
          onClick={() => setShowModal(true)}
        >
          Continue in Full Screen
        </button>
      </div>
      
      {/* Conditionally render the modal */}
      {showModal && (
        <ExamModal
          onClose={() => setShowModal(false)}
          examName={examName}
          setExamName={setExamName}
          currentStep={currentStep}
          setCurrentStep={setCurrentStep}
          procedureSteps={procedureSteps}
          setProcedureSteps={setProcedureSteps}
          stepNumber={stepNumber}
          setStepNumber={setStepNumber}
          procedureComplete={procedureComplete}
          setProcedureComplete={setProcedureComplete}
          examResults={examResults}
          setExamResults={setExamResults}
          error={error}
          setError={setError}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
          feedback={feedback}
          setFeedback={setFeedback}
          isDisabled={isDisabled}
          resetExam={resetExam}
          checkProcedure={checkProcedure}
        />
      )}
    </div>
  );
};

export default PhysicalExamPanel;