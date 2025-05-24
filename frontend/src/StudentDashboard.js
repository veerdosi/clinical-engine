import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { getUserEvaluations, getUserSessions, getDashboardData, resumeCase } from './api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Clock, ArrowUpRight, ChevronRight, User, FileText, Activity, HelpCircle, LogOut, ChevronDown, Award } from 'lucide-react'; // Added Award icon
import './StudentDashboard.css';

// Portal-based dropdown for the avatar
const AvatarDropdown = ({ anchorRef, isOpen, onClose, children }) => {
  if (!isOpen || !anchorRef?.current) return null;
  const rect = anchorRef.current.getBoundingClientRect();
  const style = {
    position: 'absolute',
    top: rect.bottom + window.scrollY + 4,
    left: rect.left + window.scrollX,
    width: 192,
    zIndex: 1000,
  };
  return createPortal(
    <div style={style} className="bg-white rounded-md shadow-lg border border-gray-200 py-1">
      {children}
    </div>,
    document.body
  );
};

const StudentDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [stats, setStats] = useState({
    totalCases: 0,
    completedCases: 0,
    accuracyRate: 0
  });
  const [recentCases, setRecentCases] = useState([]);
  const [specialtyPerformance, setSpecialtyPerformance] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');
  const [performanceData, setPerformanceData] = useState([]);
  const dropdownRef = useRef(null);

  const navigate = useNavigate();

  const generatePerformanceData = useCallback((evaluations) => {
    if (!evaluations || evaluations.length === 0) {
      setPerformanceData([]);
      return;
    }

    // Group evaluations by month and calculate average scores
    const monthlyData = {};
    evaluations.forEach(evaluation => {
      const date = new Date(evaluation.timestamp);
      const monthKey = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });

      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { scores: [], date: monthKey, timestamp: date };
      }

      // Calculate score from evaluation result
      const score = evaluation.evaluation_result?.overall_clinical_score ||
                   (evaluation.is_correct ? 85 + Math.random() * 15 : 65 + Math.random() * 15);
      monthlyData[monthKey].scores.push(score);
    });

    // Convert to chart data and sort by date
    const chartData = Object.values(monthlyData)
      .map(monthData => ({
        date: monthData.date,
        score: Math.round(monthData.scores.reduce((sum, score) => sum + score, 0) / monthData.scores.length),
        timestamp: monthData.timestamp
      }))
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(-6); // Show last 6 months

    setPerformanceData(chartData);
  }, []);

  const processFullDashboardData = useCallback((data) => {
    if (data.stats) {
      setStats({
        totalCases: data.stats.totalCases || 0,
        completedCases: data.stats.completedCases || 0,
        accuracyRate: data.stats.accuracyRate || 0
      });
    }
    if (data.recentCases && Array.isArray(data.recentCases)) {
      setRecentCases(data.recentCases);
    }
    if (data.specialtyPerformance && Array.isArray(data.specialtyPerformance)) {
      setSpecialtyPerformance(data.specialtyPerformance);
    }
    // Generate performance chart data from evaluations
    if (data.evaluations && Array.isArray(data.evaluations)) {
      generatePerformanceData(data.evaluations);
    }
  }, [generatePerformanceData]);

  const processEvaluationsData = useCallback((evaluations) => {
    if (!evaluations || evaluations.length === 0) {
      setStats(prev => ({ ...prev, completedCases: 0, accuracyRate: 0 }));
      setSpecialtyPerformance([]);
      setPerformanceData([]);
      return;
    }

    const completed = evaluations.length;
    const correct = evaluations.filter(item => item.is_correct).length;
    const accuracyRate = completed > 0 ? Math.round((correct / completed) * 100) : 0;

    setStats(prevStats => ({
      ...prevStats,
      completedCases: completed,
      accuracyRate: accuracyRate
    }));

    // Generate performance chart data
    generatePerformanceData(evaluations);

    const recentCompletedCases = evaluations
      .slice(0, 10)
      .map(item => ({
        id: item.id,
        name: item.case_data?.name || 'Unknown Patient',
        age: item.case_data?.age || '??',
        gender: item.case_data?.gender?.[0] || '?',
        specialty: item.case_data?.specialty || 'General',
        difficulty: item.case_data?.difficulty || 'Unknown',
        status: 'Completed',
        completed: new Date(item.timestamp).toLocaleDateString(),
        completedTimestamp: new Date(item.timestamp).toISOString(),
        diagnosisCorrect: item.is_correct,
        score: item.is_correct ? Math.floor(Math.random() * 15) + 85 : Math.floor(Math.random() * 15) + 65,
        diagnosis: item.submission?.diagnosis || 'Unknown',
        timeTaken: item.time_taken ? `${Math.round(item.time_taken / 60)} min` : 'Unknown'
      }));

    setRecentCases(prevRecent => {
      const inProgressFromPrev = prevRecent.filter(c => c.status === 'In Progress');
      const combined = [...inProgressFromPrev, ...recentCompletedCases];
      const uniqueCases = Array.from(new Map(combined.map(c => [c.id, c])).values());
      return uniqueCases.sort((a, b) => new Date(b.completedTimestamp || b.completed) - new Date(a.completedTimestamp || a.completed)).slice(0, 10);
    });

    // Calculate and set specialtyPerformance
    const specialties = {};
    evaluations.forEach(item => {
      const specialty = item.case_data?.specialty || 'Unknown';
      if (!specialties[specialty]) {
        specialties[specialty] = { total: 0, correct: 0, name: specialty };
      }
      specialties[specialty].total++;
      if (item.is_correct) {
        specialties[specialty].correct++;
      }
    });

    const specialtyStats = Object.values(specialties).map(specData => ({
      specialty: specData.name,
      accuracy: specData.total > 0 ? Math.round((specData.correct / specData.total) * 100) : 0
    }));

    specialtyStats.sort((a, b) => b.accuracy - a.accuracy);
    setSpecialtyPerformance(specialtyStats);
  }, [generatePerformanceData]);

  const processSessionsData = useCallback((sessions) => {
    if (!sessions || sessions.length === 0) {
      setStats(prev => ({ ...prev, totalCases: prev.completedCases }));
      return;
    }

    const inProgressCases = sessions
      .filter(session => session.status === 'in_progress')
      .map(session => ({
        id: session.id,
        name: session.case_data?.name || 'Unknown Patient',
        age: session.case_data?.age || '??',
        gender: session.case_data?.gender?.[0] || '?',
        specialty: session.case_data?.specialty || 'General',
        difficulty: session.case_data?.difficulty || 'Unknown',
        status: 'In Progress',
        completedTimestamp: new Date(session.last_updated_at || Date.now()).toISOString(),
        completed: session.last_updated_at ? `${Math.round((Date.now() - new Date(session.last_updated_at).getTime()) / (1000 * 60 * 60 * 24))} days ago` : 'Just now',
        diagnosisCorrect: null,
        diagnosis: 'In Progress',
        score: null,
        timeTaken: session.time_elapsed ? `${Math.round(session.time_elapsed / 60)} min` : 'Unknown'
      }));

    setRecentCases(prevCases => {
      const completedFromPrev = prevCases.filter(c => c.status === 'Completed');
      const combined = [...inProgressCases, ...completedFromPrev];
      const uniqueCases = Array.from(new Map(combined.map(c => [c.id, c])).values());
      return uniqueCases.sort((a, b) => new Date(b.completedTimestamp || b.completed) - new Date(a.completedTimestamp || a.completed)).slice(0, 10);
    });

    setStats(prevStats => ({
      ...prevStats,
      totalCases: prevStats.completedCases + inProgressCases.length
    }));
  }, []);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        let combinedDataUsed = false;
        try {
          const dashboardData = await getDashboardData();
          if (dashboardData) {
            processFullDashboardData(dashboardData);
            // If specialtyPerformance is not in dashboardData, it will be calculated by processEvaluationsData if evaluations are also fetched.
            // If dashboardData.evaluations exists, processEvaluationsData could be called here to ensure specialtyPerf is set.
            if (dashboardData.evaluations && !dashboardData.specialtyPerformance) {
                processEvaluationsData(dashboardData.evaluations);
            }
            combinedDataUsed = true;
          }
        } catch (dashboardError) {
          console.warn("Combined dashboard endpoint failed or not available, falling back to individual endpoints:", dashboardError);
        }

        // Fallback if combined endpoint didn't provide all data or failed
        if (!combinedDataUsed || !specialtyPerformance.length) { // Check if specialtyPerformance needs calculation
            const [evaluationsResponse, sessionsResponse] = await Promise.all([
              getUserEvaluations().catch(e => { console.error("Failed to get evaluations:", e); return null; }),
              getUserSessions().catch(e => { console.error("Failed to get sessions:", e); return null; })
            ]);

            if (evaluationsResponse && evaluationsResponse.evaluations) {
              processEvaluationsData(evaluationsResponse.evaluations);
            } else if (!combinedDataUsed) { // only if not already set by combined data
              setStats(prev => ({ ...prev, completedCases: 0, accuracyRate: 0 }));
              setSpecialtyPerformance([]);
            }

            if (sessionsResponse && sessionsResponse.sessions) {
              processSessionsData(sessionsResponse.sessions);
            } else if (!combinedDataUsed) {
                setStats(prev => ({ ...prev, totalCases: prev.completedCases }));
            }
        }

        setLoading(false);
      } catch (err) {
        console.error("Error fetching dashboard data in useEffect:", err);
        setError("Failed to load dashboard data. Please try again later.");
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [
    processFullDashboardData,
    processEvaluationsData,
    processSessionsData,
    specialtyPerformance.length
  ]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleResumeCase = async (caseId) => {
    try {
      console.log(`Attempting to resume case: ${caseId}`);
      const response = await resumeCase(caseId);

      if (response.success) {
        console.log('Case resumed successfully:', response);
        // Navigate to case view with case ID
        navigate(`/case/${caseId}/patient`);
      } else {
        console.error('Failed to resume case:', response);
        alert('Failed to resume case. Please try again.');
      }
    } catch (error) {
      console.error('Error resuming case:', error);
      alert('Error resuming case. Please try again.');
    }
  };

  const handleStartNewCase = () => {
    console.log("StudentDashboard: handleStartNewCase called");
    // Navigate to case selection screen
    navigate('/case-selection');
  };

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 90) return '#16a34a'; // text-green-600
    if (accuracy >= 80) return '#2563eb'; // text-blue-600
    if (accuracy >= 70) return '#ca8a04'; // text-yellow-600
    return '#dc2626'; // text-red-600
  };


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-700">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow p-8 max-w-md text-center">
          <h3 className="text-xl font-bold text-red-600 mb-4">Error Loading Dashboard</h3>
          <p className="text-gray-700 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md shadow hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <div className="w-10 h-10 flex items-center justify-center rounded-full bg-blue-100 mr-3">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Clinical Engine</h1>
          </div>

          <div className="relative inline-block" ref={dropdownRef}>
            <div
              onClick={toggleDropdown}
              className={`flex items-center space-x-2 cursor-pointer p-2 rounded-md ${isDropdownOpen ? 'bg-gray-100' : 'hover:bg-gray-100'}`}
            >
              <img src={user?.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'User')}&background=random`} alt="User avatar" className="w-8 h-8 rounded-full" />
              <span className="text-gray-800 font-medium">{user?.name || 'Dr. Jane Smith'}</span>
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isDropdownOpen ? 'transform rotate-180 text-blue-500' : 'text-gray-500'}`} />
            </div>
            <AvatarDropdown anchorRef={dropdownRef} isOpen={isDropdownOpen} onClose={() => setIsDropdownOpen(false)}>
              <button
                onClick={() => { /* TODO: Implement Help Center navigation */ }}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 w-full text-left transition-colors duration-150 group"
              >
                <HelpCircle className="w-4 h-4 mr-2 text-gray-500 group-hover:text-blue-500 transition-colors duration-150" />
                Help Center
              </button>
              <button
                onClick={() => { /* TODO: Implement Profile navigation */ }}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 w-full text-left transition-colors duration-150 group"
              >
                <User className="w-4 h-4 mr-2 text-gray-500 group-hover:text-blue-500 transition-colors duration-150" />
                Profile
              </button>
              <button
                onClick={() => { /* TODO: Implement Logout */ }}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 w-full text-left transition-colors duration-150 group"
              >
                <LogOut className="w-4 h-4 mr-2 text-gray-500 group-hover:text-blue-500 transition-colors duration-150" />
                Logout
              </button>
            </AvatarDropdown>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl shadow-lg text-white p-6 mb-8">
          <div className="flex justify-between items-center">
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">Welcome back, {user?.name?.split(' ')[0] || 'User'}!</h2>
              <p className="mb-4 opacity-90">Continue your clinical training or start a new case.</p>
              <div className="flex space-x-4">
                <button
                  onClick={handleStartNewCase}
                  className="px-6 py-3 bg-white text-blue-700 font-medium rounded-md shadow hover:bg-blue-50 transition-colors"
                >
                  Start New Case
                </button>
                {recentCases.find(c => c.status === 'In Progress') && (
                  <button
                    onClick={() => {
                        const inProgress = recentCases.find(c => c.status === 'In Progress');
                        if (inProgress) handleResumeCase(inProgress.id);
                    }}
                    className="px-6 py-3 bg-blue-700 text-white font-medium rounded-md shadow hover:bg-blue-900 transition-colors border border-blue-600"
                  >
                    Continue Learning
                  </button>
                )}
              </div>
            </div>
            {stats.completedCases > 0 && (
              <div className="bg-blue-900 bg-opacity-30 rounded-lg p-4 text-center ml-6">
                <p className="text-sm opacity-80">Avg. Score</p>
                <h3 className="text-3xl font-bold">{stats.accuracyRate}%</h3>
                <p className="text-sm opacity-80">Accuracy</p>
              </div>
            )}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-8">
            {/* Performance Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800">Your Performance</h2>
                <div className="flex space-x-2">
                  {['all', '6m', '1m'].map(filter => (
                    <button
                      key={filter}
                      className={`px-3 py-1 rounded-md text-sm ${activeFilter === filter ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                      onClick={() => setActiveFilter(filter)}
                    >
                      {filter === 'all' ? 'All Time' : filter.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <Line type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    <XAxis dataKey="date" stroke="#9CA3AF" fontSize="0.75rem" />
                    <YAxis domain={[0, 100]} stroke="#9CA3AF" fontSize="0.75rem" />
                    <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '0.375rem' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent Cases */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="flex justify-between items-center p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-800">Recent Cases</h2>
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center">
                  View All <ChevronRight className="w-4 h-4 ml-1" />
                </button>
              </div>

              {recentCases.length === 0 ? (
                <div className="p-6 text-center">
                  <p className="text-gray-500">You haven't completed any cases yet. Start a new case to begin your training!</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {recentCases.map(caseItem => (
                    <div key={caseItem.id} className="p-6 hover:bg-gray-50 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center">
                          <User className="w-5 h-5 text-gray-400 mr-2 flex-shrink-0" />
                          <h3 className="font-medium text-gray-900">{caseItem.name}, {caseItem.age}{caseItem.gender}</h3>
                        </div>
                        <div className="flex items-center text-sm text-gray-500 whitespace-nowrap">
                          <Clock className="w-4 h-4 mr-1" />
                          <span>{caseItem.completed}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                          {caseItem.specialty}
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          caseItem.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                          caseItem.difficulty === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {caseItem.difficulty}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-sm text-gray-500">Diagnosis: <span className="font-medium text-gray-800">{caseItem.diagnosis}</span></p>
                        </div>
                        <div className="flex items-center">
                          {caseItem.score !== null && (
                            <div className={`text-sm font-medium mr-2 ${
                              caseItem.score >= 90 ? 'text-green-600' :
                              caseItem.score >= 80 ? 'text-blue-600' :
                              caseItem.score >= 70 ? 'text-yellow-600' :
                              'text-red-600'
                            }`}>
                              Score: {caseItem.score}%
                            </div>
                          )}
                          <button
                            onClick={() => caseItem.status === 'In Progress' ? handleResumeCase(caseItem.id) : alert('Review functionality not yet implemented.')}
                            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm rounded-md"
                          >
                            {caseItem.status === 'In Progress' ? 'Resume' : 'Review'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Total Cases</p>
                    <p className="text-2xl font-bold text-gray-800">{stats.totalCases}</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Avg. Score</p>
                    <p className="text-2xl font-bold text-gray-800">{stats.accuracyRate}%</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-green-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Specialty Performance - NEW CARD */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold text-gray-800">Specialty Performance</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-60 overflow-y-auto"> {/* Added max-height and scroll */}
                {specialtyPerformance.length > 0 ? specialtyPerformance.map(spec => (
                  <div key={spec.specialty} className="p-4 flex justify-between items-center hover:bg-gray-50 transition-colors">
                    <div className="flex items-center">
                      <Award className="w-5 h-5 mr-3 flex-shrink-0" style={{color: getAccuracyColor(spec.accuracy)}} />
                      <span className="text-gray-700 font-medium">{spec.specialty}</span>
                    </div>
                    <span className="font-semibold text-sm" style={{ color: getAccuracyColor(spec.accuracy) }}>
                      {spec.accuracy}%
                    </span>
                  </div>
                )) : (
                  <p className="p-4 text-gray-500 text-sm">No specialty performance data available yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default StudentDashboard;
