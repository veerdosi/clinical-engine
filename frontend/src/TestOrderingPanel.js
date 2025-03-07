import React, { useState } from 'react';
import './TestOrderingPanel.css';

const TestOrderingPanel = ({ isDisabled }) => {
  const [selectedTab, setSelectedTab] = useState('lab');
  const [isOrdering, setIsOrdering] = useState(false);
  const [selectedTest, setSelectedTest] = useState('');
  const [customTest, setCustomTest] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [error, setError] = useState(null);
  const [showCustomInput, setShowCustomInput] = useState(false);

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

  // Current options based on selected tab
  const currentOptions = selectedTab === 'lab' ? labTestOptions : imagingOptions;

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
      const endpoint = selectedTab === 'lab' ? '/api/order-lab' : '/api/order-imaging';
      const requestBody = selectedTab === 'lab' 
        ? { test: testToOrder }
        : { imaging: testToOrder };
      
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

  return (
    <div className="test-ordering-panel">
      <div className="panel-header">
        <h3>Order Tests & Imaging</h3>
      </div>
      
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
      
      <div className="test-selection">
        <label htmlFor="test-select">
          Select {selectedTab === 'lab' ? 'Lab Test' : 'Imaging Study/Procedure'}:
        </label>
        <select 
          id="test-select" 
          value={selectedTest} 
          onChange={handleTestSelection}
          disabled={isDisabled || isOrdering}
        >
          <option value="">
            -- Select {selectedTab === 'lab' ? 'Test' : 'Study/Procedure'} --
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
              placeholder={`Enter custom ${selectedTab === 'lab' ? 'lab test' : 'imaging/procedure'} name`}
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
          {isOrdering ? 'Ordering...' : `Order ${selectedTab === 'lab' ? 'Test' : 'Study/Procedure'}`}
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