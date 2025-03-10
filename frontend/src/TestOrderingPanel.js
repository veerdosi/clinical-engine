import React, { useState, useEffect } from 'react';
import './TestOrderingPanel.css';

const TestOrderingPanel = ({ isDisabled, forceTabType = null }) => {
  const [selectedTab, setSelectedTab] = useState('lab');
  const [isOrdering, setIsOrdering] = useState(false);
  const [selectedTest, setSelectedTest] = useState('');
  const [customTest, setCustomTest] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [error, setError] = useState(null);
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Effect to set the tab based on forceTabType prop
  useEffect(() => {
    if (forceTabType && ['lab', 'imaging', 'procedure'].includes(forceTabType)) {
      setSelectedTab(forceTabType);
      // Reset state when tab is forced to change
      setSelectedTest('');
      setCustomTest('');
      setShowCustomInput(false);
      setTestResults(null);
      setError(null);
    }
  }, [forceTabType]);

  // Common lab test options
  const labTestOptions = [
    { value: 'CBC', label: 'Complete Blood Count (CBC)' },
    { value: 'BMP', label: 'Basic Metabolic Panel (BMP)' },
    { value: 'CMP', label: 'Comprehensive Metabolic Panel (CMP)' },
    { value: 'LFT', label: 'Liver Function Tests (LFT)' },
    { value: 'Lipid Panel', label: 'Lipid Panel' },
    { value: 'Cardiac Enzymes', label: 'Cardiac Enzymes' },
    { value: 'Troponin', label: 'Troponin' },
    { value: 'BNP', label: 'BNP' },
    { value: 'Coagulation', label: 'Coagulation Studies' },
    { value: 'ABG', label: 'Arterial Blood Gas (ABG)' },
    { value: 'Urinalysis', label: 'Urinalysis' },
    { value: 'HbA1c', label: 'HbA1c' },
    { value: 'TSH', label: 'Thyroid Function Tests' },
    { value: 'Blood Culture', label: 'Blood Culture' },
    { value: 'D-dimer', label: 'D-dimer' },
    { value: 'custom', label: 'Order Custom Lab Test...' }
  ];

  // Common imaging options
  const imagingOptions = [
    { value: 'CXR', label: 'Chest X-ray (CXR)' },
    { value: 'X-ray', label: 'X-ray (specify region)' },
    { value: 'CT Chest', label: 'CT Chest' },
    { value: 'CT Abdomen/Pelvis', label: 'CT Abdomen/Pelvis' },
    { value: 'CT Head', label: 'CT Head' },
    { value: 'MRI Brain', label: 'MRI Brain' },
    { value: 'MRI Spine', label: 'MRI Spine' },
    { value: 'Ultrasound Abdomen', label: 'Ultrasound Abdomen' },
    { value: 'Echocardiogram', label: 'Echocardiogram' },
    { value: 'ECG', label: 'Electrocardiogram (ECG)' },
    { value: 'custom', label: 'Order Custom Imaging/Procedure...' }
  ];

  // Procedure options
  const procedureOptions = [
    { value: 'ECG', label: 'Standard 12-Lead ECG' },
    { value: 'Exercise Stress Test', label: 'Exercise Stress Test' },
    { value: 'Echocardiogram', label: 'Echocardiogram' },
    { value: 'Pulmonary Function Test', label: 'Pulmonary Function Test (PFT)' },
    { value: 'Upper Endoscopy', label: 'Upper Endoscopy (EGD)' },
    { value: 'Colonoscopy', label: 'Colonoscopy' },
    { value: 'Bronchoscopy', label: 'Bronchoscopy' },
    { value: 'Lumbar Puncture', label: 'Lumbar Puncture' },
    { value: 'Paracentesis', label: 'Paracentesis' },
    { value: 'Thoracentesis', label: 'Thoracentesis' },
    { value: 'custom', label: 'Order Custom Procedure...' }
  ];

  // Get current options based on selected tab
  const getOptions = () => {
    switch (selectedTab) {
      case 'lab':
        return labTestOptions;
      case 'imaging':
        return imagingOptions;
      case 'procedure':
        return procedureOptions;
      default:
        return labTestOptions;
    }
  };

  const currentOptions = getOptions();

  const handleTestSelection = (e) => {
    const value = e.target.value;
    setSelectedTest(value);
    setShowCustomInput(value === 'custom');
    if (value !== 'custom') {
      setCustomTest('');
    }
    setTestResults(null);
    setError(null);
  };

  const handleCustomTestChange = (e) => {
    setCustomTest(e.target.value);
    setError(null);
  };

  const handleOrderTest = async () => {
    const testToOrder = selectedTest === 'custom' ? customTest : selectedTest;
    
    if (!testToOrder) return;

    setIsOrdering(true);
    setError(null);
    
    try {
      let endpoint, requestBody;
      
      // Determine endpoint and request body based on tab
      if (selectedTab === 'lab') {
        endpoint = '/api/order-lab';
        requestBody = { test: testToOrder };
      } else if (selectedTab === 'imaging') {
        endpoint = '/api/order-imaging';
        requestBody = { imaging: testToOrder };
      } else if (selectedTab === 'procedure') {
        // For procedures, use the imaging endpoint but mark it as a procedure
        endpoint = '/api/order-imaging';
        requestBody = { imaging: testToOrder, type: 'procedure' };
      }
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Error ordering test');
      }
      
      setTestResults(data);
      
      // Reset after successful order
      if (selectedTest === 'custom') {
        setSelectedTest('');
        setCustomTest('');
        setShowCustomInput(false);
      }
    } catch (err) {
      console.error(`Error ordering ${selectedTab}:`, err);
      setError(err.message || `Failed to order ${selectedTab} test`);
    } finally {
      setIsOrdering(false);
    }
  };

  // Get appropriate labels based on the tab
  const getLabels = () => {
    switch (selectedTab) {
      case 'lab':
        return {
          title: 'Laboratory Tests',
          selectLabel: 'Select Lab Test:',
          buttonText: 'Order Lab Test',
          customPlaceholder: 'Enter custom lab test name'
        };
      case 'imaging':
        return {
          title: 'Imaging Studies',
          selectLabel: 'Select Imaging Study:',
          buttonText: 'Order Imaging',
          customPlaceholder: 'Enter custom imaging study name'
        };
      case 'procedure':
        return {
          title: 'Investigative Procedures',
          selectLabel: 'Select Procedure:',
          buttonText: 'Order Procedure',
          customPlaceholder: 'Enter custom procedure name'
        };
      default:
        return {
          title: 'Order Tests',
          selectLabel: 'Select Test:',
          buttonText: 'Order Test',
          customPlaceholder: 'Enter custom test name'
        };
    }
  };

  const labels = getLabels();

  // Don't render tab buttons if tab type is forced
  const renderTabButtons = !forceTabType && (
    <div className="tabs">
      <button 
        className={`tab-btn ${selectedTab === 'lab' ? 'active' : ''}`}
        onClick={() => {
          setSelectedTab('lab');
          setSelectedTest('');
          setCustomTest('');
          setShowCustomInput(false);
          setTestResults(null);
        }}
        disabled={isDisabled}
      >
        Lab Tests
      </button>
      <button 
        className={`tab-btn ${selectedTab === 'imaging' ? 'active' : ''}`}
        onClick={() => {
          setSelectedTab('imaging');
          setSelectedTest('');
          setCustomTest('');
          setShowCustomInput(false);
          setTestResults(null);
        }}
        disabled={isDisabled}
      >
        Imaging & Procedures
      </button>
    </div>
  );

  return (
    <div className={`test-ordering-panel ${forceTabType ? 'full-width' : ''}`}>
      {!forceTabType && (
        <div className="panel-header">
          <h3>Order Tests & Imaging</h3>
        </div>
      )}
      
      {renderTabButtons}
      
      <div className="test-selection">
        <label htmlFor="test-select">
          {labels.selectLabel}
        </label>
        <select 
          id="test-select" 
          value={selectedTest} 
          onChange={handleTestSelection}
          disabled={isDisabled || isOrdering}
        >
          <option value="">
            -- Select {selectedTab === 'lab' ? 'Test' : selectedTab === 'imaging' ? 'Study' : 'Procedure'} --
          </option>
          {currentOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        
        {showCustomInput && (
          <div className="custom-test-input">
            <input
              type="text"
              placeholder={labels.customPlaceholder}
              value={customTest}
              onChange={handleCustomTestChange}
              disabled={isDisabled || isOrdering}
            />
            {selectedTab === 'imaging' && (
              <div className="custom-test-note">
                <p><strong>Note:</strong> Specialized procedures will provide text reports only.</p>
              </div>
            )}
          </div>
        )}
        
        <button 
          className="order-btn"
          onClick={handleOrderTest}
          disabled={isDisabled || isOrdering || (!selectedTest || (selectedTest === 'custom' && !customTest))}
        >
          {isOrdering ? 'Ordering...' : labels.buttonText}
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {testResults && (
        <div className="test-results">
          <h4>Results:</h4>
          <div 
            className="result-content"
            dangerouslySetInnerHTML={{ 
              __html: testResults.markdown ? 
                testResults.markdown.replace(/\n/g, '<br>') : 
                `<p>${testResults.message || 'Test results received.'}</p>` 
            }} 
          />
        </div>
      )}
    </div>
  );
};

export default TestOrderingPanel;