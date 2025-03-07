import React, { useState, useEffect } from 'react';
import './PhysicalExamPanel.css';

const PhysicalExamPanel = ({ isDisabled, caseInfo }) => {
  const [selectedSystem, setSelectedSystem] = useState('');
  const [customExam, setCustomExam] = useState('');
  const [examResults, setExamResults] = useState(null);
  const [vitalSigns, setVitalSigns] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Body systems for examination
  const bodySystems = [
    { value: 'vital_signs', label: 'Vital Signs' },
    { value: 'general', label: 'General Appearance' },
    { value: 'heent', label: 'Head, Eyes, Ears, Nose & Throat' },
    { value: 'cardiovascular', label: 'Cardiovascular System' },
    { value: 'respiratory', label: 'Respiratory System' },
    { value: 'gastrointestinal', label: 'Gastrointestinal System' },
    { value: 'genitourinary', label: 'Genitourinary System' },
    { value: 'musculoskeletal', label: 'Musculoskeletal System' },
    { value: 'neurological', label: 'Neurological System' },
    { value: 'skin', label: 'Skin' },
    { value: 'lymphatic', label: 'Lymphatic System' },
    { value: 'psychiatric', label: 'Psychiatric Assessment' },
    { value: 'custom', label: 'Custom Examination...' }
  ];

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

  const handleSystemChange = (e) => {
    const value = e.target.value;
    setSelectedSystem(value);
    setShowCustomInput(value === 'custom');
    if (value !== 'custom') {
      setCustomExam('');
    }
    setExamResults(null);
    setError(null);
  };

  const handleCustomExamChange = (e) => {
    setCustomExam(e.target.value);
  };

  const performExamination = async () => {
    const systemToExamine = selectedSystem === 'custom' ? customExam : selectedSystem;
    
    if (!systemToExamine) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/physical-exam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ system: systemToExamine })
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
      
      // Reset after custom exam
      if (selectedSystem === 'custom') {
        setSelectedSystem('');
        setCustomExam('');
        setShowCustomInput(false);
      }
    } catch (err) {
      console.error('Error performing examination:', err);
      setError(err.message || 'Error performing examination');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="physical-exam-panel">
      <div className="panel-header">
        <h3>Physical Examination</h3>
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
      
      <div className="exam-selection">
        <label htmlFor="system-select">Select Body System to Examine:</label>
        <select 
          id="system-select" 
          value={selectedSystem} 
          onChange={handleSystemChange}
          disabled={isDisabled || isLoading}
        >
          <option value="">-- Select System --</option>
          {bodySystems.map(system => (
            <option key={system.value} value={system.value}>
              {system.label}
            </option>
          ))}
        </select>
        
        {showCustomInput && (
          <div className="custom-exam-input">
            <input
              type="text"
              placeholder="Describe specific examination to perform..."
              value={customExam}
              onChange={handleCustomExamChange}
              disabled={isDisabled || isLoading}
            />
            <div className="custom-exam-examples">
              <p>Examples: "Assess for Murphy's sign", "Check for Romberg's sign", "Palpate lymph nodes of the neck"</p>
            </div>
          </div>
        )}
        
        <button 
          className="perform-exam-btn"
          onClick={performExamination}
          disabled={isDisabled || isLoading || (!selectedSystem || (selectedSystem === 'custom' && !customExam))}
        >
          {isLoading ? 'Examining...' : 'Perform Examination'}
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {examResults && selectedSystem !== 'vital_signs' && (
        <div className="exam-results">
          <h4>Examination Findings: {bodySystems.find(s => s.value === selectedSystem)?.label || customExam}</h4>
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
  );
};

export default PhysicalExamPanel;