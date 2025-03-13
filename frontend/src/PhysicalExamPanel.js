// Revised PhysicalExamPanel.js with persistent modal fix
import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import './PhysicalExamPanel.css';

// Modal component implemented as a class to avoid unnecessary re-renders
class ExamModal extends React.Component {
  constructor(props) {
    super(props);
    // Local state for the modal component
    this.state = {
      localCurrentStep: props.currentStep || '',
    };
    
    // Bind methods
    this.handleStepChange = this.handleStepChange.bind(this);
    this.addProcedureStep = this.addProcedureStep.bind(this);
    this.removeStep = this.removeStep.bind(this);
  }
  
  componentDidMount() {
    // Lock body scroll when modal opens
    const scrollY = window.scrollY;
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = '100%';
    document.body.style.overflow = 'hidden';
    
    // Add ESC key handler
    window.addEventListener('keydown', this.handleEscKey);
  }
  
  componentWillUnmount() {
    // Restore scroll position when modal closes
    const scrollY = document.body.style.top;
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.width = '';
    document.body.style.overflow = '';
    
    if (scrollY) {
      window.scrollTo(0, parseInt(scrollY || '0', 10) * -1);
    }
    
    // Remove ESC key handler
    window.removeEventListener('keydown', this.handleEscKey);
  }
  
  // Update local state when props change
  static getDerivedStateFromProps(props, state) {
    // Only update if props.currentStep is different from what was used to initialize state.localCurrentStep
    if (props.currentStep !== state.prevPropsCurrentStep) {
      return {
        localCurrentStep: props.currentStep,
        prevPropsCurrentStep: props.currentStep
      };
    }
    return null;
  }
  
  // Handle ESC key
  handleEscKey = (event) => {
    if (event.key === 'Escape') {
      this.props.onClose();
    }
  };
  
  // Update local state when input changes
  handleStepChange(e) {
    this.setState({ localCurrentStep: e.target.value });
    this.props.setCurrentStep(e.target.value);
  }
  
  // Add a procedure step without closing the modal
  addProcedureStep() {
    const { localCurrentStep } = this.state;
    const { procedureSteps, stepNumber, setProcedureSteps, setStepNumber } = this.props;
    
    if (!localCurrentStep.trim()) return;
    
    const newSteps = [...procedureSteps, { 
      number: stepNumber, 
      description: localCurrentStep 
    }];
    
    setProcedureSteps(newSteps);
    setStepNumber(stepNumber + 1);
    
    // Clear only the local state, this avoids re-rendering the parent
    this.setState({ localCurrentStep: '' });
    this.props.setCurrentStep('');
  }
  
  // Remove a step without closing the modal
  removeStep(index) {
    const { procedureSteps, setProcedureSteps, setStepNumber } = this.props;
    
    const newSteps = [...procedureSteps];
    newSteps.splice(index, 1);
    
    // Renumber remaining steps
    const renumberedSteps = newSteps.map((step, idx) => ({
      ...step,
      number: idx + 1
    }));
    
    setProcedureSteps(renumberedSteps);
    setStepNumber(renumberedSteps.length + 1);
  }
  
  render() {
    const { 
      onClose, examName, setExamName,
      procedureSteps, procedureComplete, examResults,
      error, isLoading, feedback, isDisabled,
      resetExam, checkProcedure, stepNumber
    } = this.props;
    
    const { localCurrentStep } = this.state;
    
    return ReactDOM.createPortal(
      <div className="exam-modal-overlay" onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}>
        <div className="exam-modal-content" onClick={e => e.stopPropagation()}>
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
                      <li key={`step-${index}-${step.number}`}>
                        {step.description}
                        {!procedureComplete && (
                          <button 
                            className="remove-step-btn"
                            onClick={() => this.removeStep(index)}
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
                      value={localCurrentStep}
                      onChange={this.handleStepChange}
                      placeholder="Describe the next procedure step in detail..."
                      disabled={isDisabled || isLoading || !examName}
                    />
                  </div>
                  
                  <div className="step-buttons">
                    <button 
                      className="add-step-btn"
                      onClick={this.addProcedureStep}
                      disabled={isDisabled || isLoading || !localCurrentStep.trim()}
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
  }
}

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

  // Use useCallback to prevent recreating these functions on every render
  const handleExamNameChange = useCallback((e) => {
    setExamName(e.target.value);
    // Don't reset other fields here - this helps maintain modal state
  }, []);
  
  const resetExam = useCallback(() => {
    setExamName('');
    setCurrentStep('');
    setProcedureSteps([]);
    setStepNumber(1);
    setProcedureComplete(false);
    setExamResults(null);
    setError(null);
    setFeedback(null);
    // Importantly, don't change modal visibility
  }, []);

  const checkProcedure = useCallback(async () => {
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
  }, [examName, procedureSteps]);

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

  const openModal = useCallback(() => {
    setShowModal(true);
  }, []);
  
  const closeModal = useCallback(() => {
    setShowModal(false);
  }, []);

  // Regular panel content (non-modal view)
  return (
    <div className="physical-exam-panel">
      <div className="panel-header">
        <h3>Physical Examination</h3>
        <div className="header-controls">
          <p>Enter examination name and procedure steps in the correct order</p>
          <button 
            className="expand-view-btn" 
            onClick={openModal}
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
          onClick={openModal}
        >
          Continue in Full Screen
        </button>
      </div>
      
      {/* Conditionally render the modal */}
      {showModal && (
        <ExamModal
          onClose={closeModal}
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