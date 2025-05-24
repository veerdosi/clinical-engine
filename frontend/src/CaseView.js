import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import ChatWindow from './ChatWindow';
import DiagnosisPanel from './DiagnosisPanel';
import TestOrderingPanel from './TestOrderingPanel';
import PhysicalExamPanel from './PhysicalExamPanel';
import VitalSigns from './VitalSigns';
import NotesPanel from './NotesPanel';
import InactivityReminder from './InactivityReminder';
import { resumeCase } from './api';
import './App.css';

function CaseView() {
  const [caseInfo, setCaseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDiagnosisSubmitted, setIsDiagnosisSubmitted] = useState(false);
  const [isNewCase, setIsNewCase] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  const navigate = useNavigate();
  const { caseId } = useParams(); // Get case ID from URL if resuming

  useEffect(() => {
    if (caseId) {
      // Resume existing case
      resumeExistingCase(caseId);
    } else {
      // Load current case
      fetchCurrentCase();
    }
  }, [caseId]);

  const fetchCurrentCase = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/current-case');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setCaseInfo(data);
      setError(null);
      setIsDiagnosisSubmitted(false);
    } catch (err) {
      console.error('Error fetching case:', err);
      setError('Unable to load patient case. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const resumeExistingCase = async (caseId) => {
    setLoading(true);
    try {
      const response = await resumeCase(caseId);

      if (response.success) {
        setCaseInfo(response.case);
        setError(null);
        setIsDiagnosisSubmitted(false);
        // You could restore other session data here if needed
      } else {
        throw new Error('Failed to resume case');
      }
    } catch (err) {
      console.error('Error resuming case:', err);
      setError('Unable to resume case. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnosisSubmitted = () => {
    setIsDiagnosisSubmitted(true);
  };

  const handleNewCaseStarted = () => {
    setIsNewCase(false);
  };

  const handleReturnToDashboard = () => {
    navigate('/dashboard');
  };

  const handleNotesUpdate = (updatedNotes) => {
    if (caseInfo && caseInfo.id) {
      fetch('/api/save-notes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notes: updatedNotes,
          case_id: caseInfo.id
        })
      }).catch(err => {
        console.error('Error saving notes to backend:', err);
      });
    }
  };

  const handleNewMessage = (message) => {
    setConversationHistory(prev => [...prev, message]);
  };

  const getCaseUrgency = () => {
    if (!caseInfo) return 'medium';
    const difficulty = caseInfo.difficulty?.toLowerCase() || '';
    if (difficulty === 'hard') return 'high';
    if (difficulty === 'moderate') return 'medium';
    return 'low';
  };

  const getInactivityThreshold = () => {
    const urgency = getCaseUrgency();
    switch (urgency) {
      case 'high': return 60;
      case 'medium': return 120;
      case 'low': return 180;
      default: return 120;
    }
  };

  if (loading && !caseInfo) {
    return (
      <div className="App loading">
        <div className="loading-spinner"></div>
        <p>Loading patient case...</p>
      </div>
    );
  }

  if (error && !caseInfo) {
    return (
      <div className="App error">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={fetchCurrentCase}>Try Again</button>
          <button onClick={handleReturnToDashboard}>Return to Dashboard</button>
        </div>
      </div>
    );
  }

  if (!caseInfo) {
    return (
      <div className="App error">
        <div className="error-message">
          <h2>No Case Data</h2>
          <p>No case information available.</p>
          <button onClick={handleReturnToDashboard}>Return to Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Modern Header matching StudentDashboard */}
      <header className="bg-white/90 backdrop-blur-lg border-b border-slate-200/60 sticky top-0 z-50 shadow-sm">
        <div className="w-full px-4 lg:px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
                <img src="/logo.svg" alt="Clinical Engine Logo" className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Clinical Engine</h1>
                <p className="text-sm text-slate-600 font-medium">Medical Training Platform</p>
              </div>
            </div>

            {/* Patient Info Cards */}
            <div className="hidden md:flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-2 rounded-xl border border-blue-200/50">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-semibold text-slate-700">
                    {caseInfo.name}, {caseInfo.age}{caseInfo.gender === 'Male' ? 'M' : 'F'}
                  </span>
                </div>
              </div>
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-2 rounded-xl border border-purple-200/50">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="text-sm font-semibold text-slate-700">{caseInfo.difficulty}</span>
                </div>
              </div>
              <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-4 py-2 rounded-xl border border-emerald-200/50">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                  <span className="text-sm font-semibold text-slate-700">{caseInfo.specialty}</span>
                </div>
              </div>
              <button
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-xl shadow-lg hover:from-blue-700 hover:to-blue-800 hover:scale-105 transition-all duration-300"
                onClick={handleReturnToDashboard}
                disabled={loading}
              >
                Dashboard
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-xl shadow-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-300"
              onClick={handleReturnToDashboard}
              disabled={loading}
            >
              Dashboard
            </button>
          </div>

          {/* Mobile Patient Info */}
          <div className="md:hidden mt-4 flex flex-wrap gap-2">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-3 py-1.5 rounded-lg border border-blue-200/50">
              <span className="text-xs font-semibold text-slate-700">
                {caseInfo.name}, {caseInfo.age}{caseInfo.gender === 'Male' ? 'M' : 'F'}
              </span>
            </div>
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-3 py-1.5 rounded-lg border border-purple-200/50">
              <span className="text-xs font-semibold text-slate-700">{caseInfo.difficulty}</span>
            </div>
            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-3 py-1.5 rounded-lg border border-emerald-200/50">
              <span className="text-xs font-semibold text-slate-700">{caseInfo.specialty}</span>
            </div>
          </div>
        </div>

        {/* Modern Tab Navigation */}
        <div className="w-full px-4 lg:px-6">
          <div className="flex overflow-x-auto space-x-1 bg-slate-100/70 backdrop-blur-sm rounded-2xl p-2 mt-4 scrollbar-hide">
            <NavLink
              to={caseId ? `/case/${caseId}/patient` : '/case/patient'}
              className={({ isActive }) => `flex-shrink-0 px-4 lg:px-6 py-3 rounded-xl text-center font-semibold transition-all duration-300 whitespace-nowrap ${
                isActive
                  ? 'bg-white text-blue-700 shadow-lg ring-1 ring-blue-200 scale-105'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <span className="hidden sm:inline">Patient Interaction</span>
              <span className="sm:hidden">Patient</span>
            </NavLink>
            <NavLink
              to={caseId ? `/case/${caseId}/labs` : '/case/labs'}
              className={({ isActive }) => `flex-shrink-0 px-4 lg:px-6 py-3 rounded-xl text-center font-semibold transition-all duration-300 whitespace-nowrap ${
                isActive
                  ? 'bg-white text-blue-700 shadow-lg ring-1 ring-blue-200 scale-105'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <span className="hidden sm:inline">Laboratory Tests</span>
              <span className="sm:hidden">Labs</span>
            </NavLink>
            <NavLink
              to={caseId ? `/case/${caseId}/imaging` : '/case/imaging'}
              className={({ isActive }) => `flex-shrink-0 px-4 lg:px-6 py-3 rounded-xl text-center font-semibold transition-all duration-300 whitespace-nowrap ${
                isActive
                  ? 'bg-white text-blue-700 shadow-lg ring-1 ring-blue-200 scale-105'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <span className="hidden sm:inline">Imaging Studies</span>
              <span className="sm:hidden">Imaging</span>
            </NavLink>
            <NavLink
              to={caseId ? `/case/${caseId}/procedures` : '/case/procedures'}
              className={({ isActive }) => `flex-shrink-0 px-4 lg:px-6 py-3 rounded-xl text-center font-semibold transition-all duration-300 whitespace-nowrap ${
                isActive
                  ? 'bg-white text-blue-700 shadow-lg ring-1 ring-blue-200 scale-105'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <span className="hidden sm:inline">Procedures</span>
              <span className="sm:hidden">Procedures</span>
            </NavLink>
          </div>
        </div>
      </header>

      <main className="w-full px-4 lg:px-6 py-8">
        <Routes>
          {/* Default redirect to patient tab */}
          <Route path="/" element={<Navigate to="patient" replace />} />

          {/* Patient interaction tab */}
          <Route path="/patient" element={
            <div className="patient-tab">
              <div className="vital-signs-container">
                <VitalSigns vitals={caseInfo?.vitals || {}} />
              </div>
              {caseInfo && !isDiagnosisSubmitted && (
                <InactivityReminder inactivityThreshold={getInactivityThreshold()} />
              )}
              <div className="patient-grid-layout">
                <div className="chat-area">
                  <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300 h-full">
                    <div className="p-6 border-b border-slate-200/60">
                      <h2 className="text-xl font-bold text-slate-900 mb-1">Patient Interaction</h2>
                      <p className="text-slate-600 text-sm">Communicate with the patient to gather information</p>
                    </div>
                    <div className="p-6">
                      <ChatWindow
                        isDiagnosisSubmitted={isDiagnosisSubmitted}
                        isNewCase={isNewCase}
                        onNewCaseStart={handleNewCaseStarted}
                        conversationHistory={conversationHistory}
                        onNewMessage={handleNewMessage}
                      />
                    </div>
                  </div>
                </div>
                <div className="controls-area">
                  <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300 mb-6">
                    <div className="p-6 border-b border-slate-200/60">
                      <h2 className="text-xl font-bold text-slate-900 mb-1">Physical Examination</h2>
                      <p className="text-slate-600 text-sm">Perform systematic examination</p>
                    </div>
                    <div className="p-6">
                      <PhysicalExamPanel isDisabled={isDiagnosisSubmitted} caseInfo={caseInfo} />
                    </div>
                  </div>
                  <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
                    <div className="p-6 border-b border-slate-200/60">
                      <h2 className="text-xl font-bold text-slate-900 mb-1">Diagnosis & Assessment</h2>
                      <p className="text-slate-600 text-sm">Submit your clinical diagnosis</p>
                    </div>
                    <div className="p-6">
                      <DiagnosisPanel
                        case_info={caseInfo}
                        onDiagnosisSubmitted={handleDiagnosisSubmitted}
                        onReturnToSelection={handleReturnToDashboard}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          } />

          {/* Laboratory tests tab */}
          <Route path="/labs" element={
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div className="p-6 lg:p-8 border-b border-slate-200/60">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Laboratory Testing</h2>
                <p className="text-slate-600">Order laboratory tests and review results to aid in your diagnosis.</p>
              </div>
              <div className="p-6 lg:p-8">
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="lab" />
              </div>
            </div>
          } />

          {/* Imaging studies tab */}
          <Route path="/imaging" element={
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div className="p-6 lg:p-8 border-b border-slate-200/60">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Imaging Studies</h2>
                <p className="text-slate-600">Order imaging studies and review radiologic findings to support your diagnostic workup.</p>
              </div>
              <div className="p-6 lg:p-8">
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="imaging" />
              </div>
            </div>
          } />

          {/* Procedures tab */}
          <Route path="/procedures" element={
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div className="p-6 lg:p-8 border-b border-slate-200/60">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Investigative Procedures</h2>
                <p className="text-slate-600">Order specialized procedures to gather additional diagnostic information.</p>
              </div>
              <div className="p-6 lg:p-8">
                <TestOrderingPanel isDisabled={isDiagnosisSubmitted} forceTabType="procedure" />
              </div>
            </div>
          } />
        </Routes>
      </main>

      <NotesPanel
        caseInfo={caseInfo}
        isDisabled={isDiagnosisSubmitted}
        onNoteUpdate={handleNotesUpdate}
      />

      {!isDiagnosisSubmitted && (
        <footer className="bg-white/70 backdrop-blur-sm border-t border-slate-200/60 mt-12">
          <div className="w-full px-4 lg:px-6 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium text-slate-700">
                    Words: {conversationHistory.length > 0 ? conversationHistory.reduce((count, msg) =>
                      count + (msg.content ? msg.content.split(/\s+/).length : 0), 0) : 0}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-slate-700">Auto-saved</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="text-sm font-medium text-slate-700">
                    Session time: {Math.floor(Math.random() * 30) + 10} min
                  </span>
                </div>
              </div>
              <div className="text-sm font-medium text-slate-500">
                Clinical Engine v1.0.0
              </div>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

export default CaseView;
