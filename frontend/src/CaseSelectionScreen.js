// src/CaseSelectionScreen.js
import React, { useState } from 'react';
import './CaseSelectionScreen.css';

const CaseSelectionScreen = ({ onCaseGenerated }) => {
  const [specialty, setSpecialty] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // These should match the options in the backend CaseManager.specialties and CaseManager.difficulties
  const specialties = [
    { value: "random", label: "Feeling Lucky? (Random Specialty)" },
    { value: "Internal Medicine", label: "Internal Medicine" },
    { value: "Cardiology", label: "Cardiology" },
    { value: "Neurology", label: "Neurology" },
    { value: "Pulmonology", label: "Pulmonology" },
    { value: "Orthopedic", label: "Orthopedic" }
  ];

  const difficulties = [
    { value: "Random", label: "Feeling Lucky? (Random Difficulty)" },
    { value: "Easy", label: "Easy - common presentation with classic symptoms" },
    { value: "Moderate", label: "Moderate - atypical presentation with comorbidities" },
    { value: "Hard", label: "Hard - rare condition with diagnostic red herrings" }
  ];

  const handleGenerateCase = async () => {
    if (!specialty || !difficulty) {
      setError("Please select both a specialty and difficulty level");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Only include non-random values in the request body
      const requestBody = {};
      if (specialty !== "random") requestBody.specialty = specialty;
      if (difficulty !== "random") requestBody.difficulty = difficulty;

      const response = await fetch('/api/new-case', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const caseData = await response.json();
      onCaseGenerated(caseData);
    } catch (err) {
      console.error('Error generating case:', err);
      setError('Unable to generate case. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="case-selection-screen">
      <div className="selection-container">
        <h1>Clinical Engine</h1>
        <h2>Select Case Parameters</h2>

        <div className="selection-form">
          <div className="form-group">
            <label>Medical Specialty:</label>
            <select
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              disabled={isLoading}
            >
              <option value="">-- Select Specialty --</option>
              {specialties.map((spec) => (
                <option key={spec.value} value={spec.value}>{spec.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Difficulty Level:</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              disabled={isLoading}
            >
              <option value="">-- Select Difficulty --</option>
              {difficulties.map((diff) => (
                <option key={diff.value} value={diff.value}>{diff.label}</option>
              ))}
            </select>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            className="generate-btn"
            onClick={handleGenerateCase}
            disabled={isLoading}
          >
            <span className={isLoading ? 'loading' : ''}></span>
            {isLoading ? 'Generating...' : 'Generate Case'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CaseSelectionScreen;
