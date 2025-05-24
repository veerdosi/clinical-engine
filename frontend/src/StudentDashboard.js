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
        if (!combinedDataUsed) {
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
    processSessionsData
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-lg border-b border-slate-200/60 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 flex items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Clinical Engine</h1>
              <p className="text-sm text-slate-600 font-medium">Medical Training Platform</p>
            </div>
          </div>

          <div className="relative inline-block" ref={dropdownRef}>
            <div
              onClick={toggleDropdown}
              className={`flex items-center space-x-4 cursor-pointer px-4 py-3 rounded-2xl transition-all duration-300 ${
                isDropdownOpen
                  ? 'bg-blue-50 ring-2 ring-blue-200/60 shadow-lg scale-105'
                  : 'hover:bg-slate-50 hover:shadow-md hover:scale-102'
              }`}
            >
              <img
                src={user?.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'User')}&background=4f46e5&color=ffffff&bold=true`}
                alt="User avatar"
                className="w-11 h-11 rounded-full ring-3 ring-white shadow-lg"
              />
              <div className="text-left">
                <p className="text-base font-bold text-slate-800">{user?.name || 'Dr. Jane Smith'}</p>
                <p className="text-sm text-slate-500 font-medium">Medical Student</p>
              </div>
              <ChevronDown className={`w-5 h-5 transition-all duration-300 ${
                isDropdownOpen ? 'rotate-180 text-blue-600' : 'text-slate-400'
              }`} />
            </div>
            <AvatarDropdown anchorRef={dropdownRef} isOpen={isDropdownOpen} onClose={() => setIsDropdownOpen(false)}>
              <button
                onClick={() => { /* TODO: Implement Help Center navigation */ }}
                className="flex items-center px-5 py-4 text-base text-slate-700 hover:bg-blue-50 hover:text-blue-700 w-full text-left transition-all duration-200 group first:rounded-t-lg"
              >
                <HelpCircle className="w-5 h-5 mr-4 text-slate-400 group-hover:text-blue-500 transition-colors duration-200" />
                Help Center
              </button>
              <button
                onClick={() => { /* TODO: Implement Profile navigation */ }}
                className="flex items-center px-5 py-4 text-base text-slate-700 hover:bg-blue-50 hover:text-blue-700 w-full text-left transition-all duration-200 group"
              >
                <User className="w-5 h-5 mr-4 text-slate-400 group-hover:text-blue-500 transition-colors duration-200" />
                Profile Settings
              </button>
              <button
                onClick={() => { /* TODO: Implement Logout */ }}
                className="flex items-center px-5 py-4 text-base text-slate-700 hover:bg-red-50 hover:text-red-700 w-full text-left transition-all duration-200 group last:rounded-b-lg"
              >
                <LogOut className="w-5 h-5 mr-4 text-slate-400 group-hover:text-red-500 transition-colors duration-200" />
                Sign Out
              </button>
            </AvatarDropdown>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-12 space-y-12">
        {/* Welcome Section */}
        <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-2xl shadow-xl">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-transparent"></div>
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
          <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-white/5 rounded-full blur-xl"></div>
          <div className="relative p-8 lg:p-12">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-8 lg:space-y-0">
              <div className="flex-1 space-y-6">
                <div>
                  <h2 className="text-4xl font-bold text-white mb-3">
                    Welcome back, {user?.name?.split(' ')[0] || 'User'}! 👋
                  </h2>
                  <p className="text-blue-100 text-xl font-medium">Continue your clinical journey or explore new cases.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <button
                    onClick={handleStartNewCase}
                    className="group relative px-8 py-4 bg-white text-blue-700 font-bold rounded-2xl shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-3"
                  >
                    <span className="text-lg">Start New Case</span>
                    <ArrowUpRight className="w-6 h-6 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform duration-300" />
                  </button>
                  {recentCases.find(c => c.status === 'In Progress') && (
                    <button
                      onClick={() => {
                          const inProgress = recentCases.find(c => c.status === 'In Progress');
                          if (inProgress) handleResumeCase(inProgress.id);
                      }}
                      className="px-8 py-4 bg-blue-800/60 backdrop-blur-sm text-white font-bold rounded-2xl border-2 border-blue-400/40 hover:bg-blue-700/70 hover:border-blue-300/60 hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-3"
                    >
                      <span className="text-lg">Continue Learning</span>
                      <ChevronRight className="w-6 h-6" />
                    </button>
                  )}
                </div>
              </div>
              {stats.completedCases > 0 && (
                <div className="bg-white/15 backdrop-blur-md rounded-3xl p-8 text-center border border-white/30 shadow-2xl">
                  <p className="text-blue-200 text-sm font-semibold mb-2">Overall Performance</p>
                  <h3 className="text-5xl font-bold text-white mb-2">{stats.accuracyRate}%</h3>
                  <p className="text-blue-200 text-base font-medium">Average Score</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 lg:gap-12">
          {/* Left Column */}
          <div className="xl:col-span-3 space-y-8 lg:space-y-12">
            {/* Performance Chart */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 p-6 lg:p-8 hover:shadow-xl transition-all duration-300">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">Performance Trends</h2>
                  <p className="text-slate-600 text-sm">Track your clinical diagnostic accuracy over time</p>
                </div>
                <div className="flex space-x-1 bg-slate-100 rounded-xl p-1">
                  {['all', '6m', '1m'].map(filter => (
                    <button
                      key={filter}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        activeFilter === filter
                          ? 'bg-white text-blue-700 shadow-sm ring-1 ring-blue-200'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
                      }`}
                      onClick={() => setActiveFilter(filter)}
                    >
                      {filter === 'all' ? 'All Time' : filter.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-80 rounded-xl bg-gradient-to-br from-blue-50/50 to-indigo-50/30 p-4">
                {performanceData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={performanceData} margin={{ top: 20, right: 30, bottom: 20, left: 0 }}>
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="url(#colorGradient)"
                        strokeWidth={3}
                        dot={{ r: 6, fill: '#3B82F6', strokeWidth: 2, stroke: '#fff' }}
                        activeDot={{ r: 8, fill: '#1D4ED8', stroke: '#fff', strokeWidth: 3 }}
                      />
                      <XAxis
                        dataKey="date"
                        stroke="#64748B"
                        fontSize="0.8rem"
                        fontWeight="500"
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        stroke="#64748B"
                        fontSize="0.8rem"
                        fontWeight="500"
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
                          backdropFilter: 'blur(10px)'
                        }}
                      />
                      <defs>
                        <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#3B82F6" />
                          <stop offset="100%" stopColor="#1D4ED8" />
                        </linearGradient>
                      </defs>
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
                        <Activity className="w-8 h-8 text-slate-400" />
                      </div>
                      <p className="text-slate-600 font-medium">No performance data yet</p>
                      <p className="text-slate-500 text-sm">Complete some cases to see your progress</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Recent Cases */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div className="flex justify-between items-center p-6 lg:p-8 border-b border-slate-200/60">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-1">Recent Cases</h2>
                  <p className="text-slate-600 text-sm">Your latest clinical case activities</p>
                </div>
                <button className="group px-6 py-3 bg-slate-100 text-slate-700 font-bold rounded-2xl shadow-md hover:bg-slate-200 hover:shadow-lg hover:scale-105 transition-all duration-300 flex items-center space-x-2">
                  View All
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
                </button>
              </div>

              {recentCases.length === 0 ? (
                <div className="p-8 lg:p-12 text-center flex flex-col items-center justify-center">
                  <div className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-2xl shadow-lg hover:shadow-2xl hover:from-blue-700 hover:to-blue-800 hover:scale-105 transition-all duration-300 mx-auto">
                    <FileText className="w-10 h-10 text-blue-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">No cases yet</h3>
                  <p className="text-slate-600 mb-6">Start your first clinical case to begin your medical training journey!</p>
                  <button
                    onClick={handleStartNewCase}
                    className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-2xl shadow-lg hover:shadow-2xl hover:from-blue-700 hover:to-blue-800 hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2"
                  >
                    Start First Case
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-slate-200/60">
                  {recentCases.map(caseItem => (
                    <div key={caseItem.id} className="p-6 lg:p-8 hover:bg-gradient-to-r hover:from-blue-50/30 hover:to-indigo-50/20 transition-all duration-200 group">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center mr-4 group-hover:scale-110 transition-transform duration-200">
                            <User className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-slate-900 text-lg">{caseItem.name}, {caseItem.age}{caseItem.gender}</h3>
                            <div className="flex items-center text-sm text-slate-500 mt-1">
                              <Clock className="w-4 h-4 mr-1" />
                              <span>{caseItem.completed}</span>
                            </div>
                          </div>
                        </div>
                        {caseItem.score !== null && (
                          <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            caseItem.score >= 90 ? 'bg-green-100 text-green-800' :
                            caseItem.score >= 80 ? 'bg-blue-100 text-blue-800' :
                            caseItem.score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {caseItem.score}%
                          </div>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2 mb-4">
                        <span className="px-3 py-1 text-xs font-semibold bg-blue-100 text-blue-700 rounded-full border border-blue-200">
                          {caseItem.specialty}
                        </span>
                        <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                          caseItem.difficulty === 'Easy' ? 'bg-green-50 text-green-700 border-green-200' :
                          caseItem.difficulty === 'Moderate' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                          'bg-red-50 text-red-700 border-red-200'
                        }`}>
                          {caseItem.difficulty}
                        </span>
                        {caseItem.status === 'In Progress' && (
                          <span className="px-3 py-1 text-xs font-semibold bg-orange-100 text-orange-700 rounded-full border border-orange-200 animate-pulse">
                            In Progress
                          </span>
                        )}
                      </div>

                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-sm text-slate-600">
                            <span className="font-medium text-slate-700">Diagnosis:</span> {caseItem.diagnosis}
                          </p>
                          {caseItem.timeTaken && (
                            <p className="text-xs text-slate-500 mt-1">Time: {caseItem.timeTaken}</p>
                          )}
                        </div>
                        <button
                          onClick={() => caseItem.status === 'In Progress' ? handleResumeCase(caseItem.id) : alert('Review functionality not yet implemented.')}
                          className={`px-6 py-3 rounded-2xl font-bold transition-all duration-300 ${
                            caseItem.status === 'In Progress'
                              ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl hover:scale-105'
                              : 'bg-slate-100 text-slate-700 hover:bg-slate-200 shadow-md hover:shadow-lg hover:scale-105'
                          }`}
                        >
                          {caseItem.status === 'In Progress' ? 'Resume' : 'Review'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div className="xl:col-span-1 space-y-8 lg:space-y-12">
            {/* Stats */}
            <div className="grid grid-cols-1 gap-4 lg:gap-6">
              <div className="rounded-2xl shadow-lg p-6 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300" style={{background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'}}>
                <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-300"></div>
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-right">
                      <p className="text-blue-100 text-sm font-medium">Total Cases</p>
                      <p className="text-3xl font-bold">{stats.totalCases}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl shadow-lg p-6 text-white overflow-hidden relative group hover:shadow-xl transition-all duration-300" style={{background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'}}>
                <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-300"></div>
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <Activity className="w-6 h-6 text-white" />
                    </div>
                    <div className="text-right">
                      <p className="text-emerald-100 text-sm font-medium">Avg. Score</p>
                      <p className="text-3xl font-bold">{stats.accuracyRate}%</p>
                    </div>
                  </div>
                  <div className="h-1 bg-white/20 rounded-full overflow-hidden">
                    <div className="h-full bg-white rounded-full" style={{width: `${stats.accuracyRate}%`}}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Specialty Performance */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-lg border border-white/20 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div className="p-6 lg:p-8 border-b border-slate-200/60">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900 mb-1">Specialty Performance</h2>
                    <p className="text-slate-600 text-sm">Your accuracy across medical specialties</p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center">
                    <Award className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
              </div>

              <div className="max-h-80 overflow-y-auto">
                {specialtyPerformance.length > 0 ? (
                  <div className="p-2">
                    {specialtyPerformance.map((spec, index) => (
                      <div key={spec.specialty} className="group p-4 m-2 rounded-xl hover:bg-gradient-to-r hover:from-slate-50 hover:to-blue-50/30 transition-all duration-200">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
                              index === 0 ? 'bg-yellow-100' :
                              index === 1 ? 'bg-gray-100' :
                              index === 2 ? 'bg-orange-100' : 'bg-blue-100'
                            }`}>
                              <Award className={`w-4 h-4 ${
                                index === 0 ? 'text-yellow-600' :
                                index === 1 ? 'text-gray-600' :
                                index === 2 ? 'text-orange-600' : 'text-blue-600'
                              }`} />
                            </div>
                            <div>
                              <span className="text-slate-800 font-semibold text-sm">{spec.specialty}</span>
                              {index < 3 && (
                                <span className={`ml-2 px-2 py-0.5 text-xs font-medium rounded-full ${
                                  index === 0 ? 'bg-yellow-100 text-yellow-700' :
                                  index === 1 ? 'bg-gray-100 text-gray-700' :
                                  'bg-orange-100 text-orange-700'
                                }`}>
                                  {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="font-bold text-lg" style={{ color: getAccuracyColor(spec.accuracy) }}>
                              {spec.accuracy}%
                            </span>
                          </div>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500 ease-out"
                            style={{
                              width: `${spec.accuracy}%`,
                              background: `linear-gradient(90deg, ${getAccuracyColor(spec.accuracy)}, ${getAccuracyColor(spec.accuracy)}dd)`
                            }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center">
                      <Award className="w-8 h-8 text-purple-500" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-2">No data yet</h3>
                    <p className="text-slate-600 text-sm">Complete cases across different specialties to see your performance breakdown.</p>
                  </div>
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
