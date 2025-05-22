import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { getUserEvaluations, getUserSessions, getDashboardData } from './api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Calendar, Clock, ArrowUpRight, ChevronRight, User, Book, FileText, Activity, HelpCircle, LogOut, ChevronDown } from 'lucide-react';
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

const StudentDashboard = ({ onStartNewCase, onResumeCaseClick, user }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [stats, setStats] = useState({
    totalCases: 0,
    completedCases: 0,
    accuracyRate: 0
  });
  const [recentCases, setRecentCases] = useState([]);
  const [learningResources, setLearningResources] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all');
  const [performanceData, setPerformanceData] = useState([]);
  const dropdownRef = React.useRef(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Try to use the combined dashboard endpoint if available
        try {
          const dashboardData = await getDashboardData();
          if (dashboardData) {
            // Process combined data
            processFullDashboardData(dashboardData);
            setLoading(false);
            return;
          }
        } catch (dashboardError) {
          console.log("Dashboard endpoint not available, falling back to individual endpoints");
          // If dashboard endpoint fails, fall back to individual endpoints
        }

        // Fetch evaluations and sessions data separately (fallback)
        const [evaluationsResponse, sessionsResponse] = await Promise.all([
          getUserEvaluations(),
          getUserSessions()
        ]);

        // Process evaluations data for stats and recent cases
        if (evaluationsResponse && evaluationsResponse.evaluations) {
          processEvaluationsData(evaluationsResponse.evaluations);
        }

        // Process sessions data for in-progress cases
        if (sessionsResponse && sessionsResponse.sessions) {
          processSessionsData(sessionsResponse.sessions);
        }

        // Generate sample learning resources
        generateLearningResources();

        setLoading(false);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Failed to load dashboard data. Please try again later.");
        setLoading(false);
      }
    };

    fetchDashboardData();

    // Generate sample performance data until real data is available
    generateSamplePerformanceData();
  }, [processFullDashboardData, processSessionsData]);

  // Handle click outside to close dropdown
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

  const generateSamplePerformanceData = () => {
    // Sample performance data until real data is available
    const sampleData = [
      { date: 'Jan', score: 76 },
      { date: 'Feb', score: 82 },
      { date: 'Mar', score: 78 },
      { date: 'Apr', score: 89 },
      { date: 'May', score: 85 },
      { date: 'Jun', score: 92 }
    ];

    setPerformanceData(sampleData);
  };

  const processFullDashboardData = (data) => {
    // Process all dashboard data at once if it comes from the combined endpoint
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
      // Process specialty performance data
    }

    if (data.learningResources && Array.isArray(data.learningResources)) {
      setLearningResources(data.learningResources);
    } else {
      // Generate placeholder learning resources if none provided
      generateLearningResources();
    }
  };

  const processEvaluationsData = (evaluations) => {
    if (!evaluations || evaluations.length === 0) {
      return;
    }

    // Compute stats
    const completed = evaluations.length;
    const correct = evaluations.filter(item => item.is_correct).length;
    const accuracyRate = completed > 0 ? Math.round((correct / completed) * 100) : 0;

    setStats({
      totalCases: completed, // In a real app, this would include in-progress cases
      completedCases: completed,
      accuracyRate: accuracyRate
    });

    // Process recent completed cases
    const recentCompletedCases = evaluations
      .slice(0, 10) // Get most recent 10
      .map(item => ({
        id: item.id,
        name: item.case_data?.name || 'Unknown Patient',
        age: item.case_data?.age || '??',
        gender: item.case_data?.gender?.[0] || '?',
        specialty: item.case_data?.specialty || 'General',
        difficulty: item.case_data?.difficulty || 'Unknown',
        status: 'Completed',
        completed: new Date(item.timestamp).toLocaleDateString(),
        diagnosisCorrect: item.is_correct,
        score: item.is_correct ? Math.floor(Math.random() * 15) + 85 : Math.floor(Math.random() * 15) + 65,
        diagnosis: item.submission?.diagnosis || 'Unknown',
        timeTaken: item.time_taken ? `${Math.round(item.time_taken / 60)} min` : 'Unknown'
      }));

    setRecentCases(recentCompletedCases);

    // Process specialty performance
    const specialties = {};

    evaluations.forEach(item => {
      const specialty = item.case_data?.specialty || 'Unknown';
      if (!specialties[specialty]) {
        specialties[specialty] = { total: 0, correct: 0 };
      }

      specialties[specialty].total++;
      if (item.is_correct) {
        specialties[specialty].correct++;
      }
    });

    const specialtyStats = Object.keys(specialties).map(specialty => ({
      specialty,
      accuracy: Math.round((specialties[specialty].correct / specialties[specialty].total) * 100)
    }));

    // Sort by accuracy (descending)
    specialtyStats.sort((a, b) => b.accuracy - a.accuracy);

    // Store specialty performance data (currently not used in UI)
  };

  const processSessionsData = (sessions) => {
    if (!sessions || sessions.length === 0) {
      return;
    }

    // Find in-progress cases
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
        completed: `${Math.floor(Math.random() * 5) + 1} days ago`,
        diagnosisCorrect: null,
        diagnosis: 'In Progress',
        score: null,
        timeTaken: session.time_elapsed ? `${Math.round(session.time_elapsed / 60)} min` : 'Unknown'
      }));

    // Convert existing recentCases to new format if needed
    const formattedRecentCases = recentCases.map(item => ({
      ...item,
      name: item.patientName || item.name,
      completed: item.date || item.completed,
      score: item.score || (item.diagnosisCorrect ? 85 : 70)
    }));

    // Combine with completed cases and sort by date
    const allCases = [...inProgressCases, ...formattedRecentCases]
      .sort((a, b) => {
        // For values like "2 days ago", convert to number of days
        const getDays = (str) => {
          if (str && str.includes('days ago')) {
            return parseInt(str.split(' ')[0]);
          }
          return 0;
        };

        const daysA = getDays(a.completed);
        const daysB = getDays(b.completed);

        if (daysA && daysB) {
          return daysA - daysB; // Smaller days (more recent) first
        }

        // Fall back to date comparison
        return new Date(b.completed) - new Date(a.completed);
      })
      .slice(0, 10); // Limit to 10 most recent

    setRecentCases(allCases);

    // Update total cases count
    setStats(prevStats => ({
      ...prevStats,
      totalCases: prevStats.completedCases + inProgressCases.length
    }));
  };

  const generateLearningResources = () => {
    // In a real app, this data would come from the API based on the student's performance
    const upcomingModules = [
      {
        id: 1,
        title: 'Advanced Cardiac Assessment',
        completion: 45,
        dueDate: '2 weeks'
      },
      {
        id: 2,
        title: 'Critical Care Management',
        completion: 20,
        dueDate: '1 month'
      },
      {
        id: 3,
        title: 'Differential Diagnosis Skills',
        completion: 80,
        dueDate: '3 days'
      }
    ];

    setLearningResources(upcomingModules);
  };

  const handleResumeCase = (caseId) => {
    if (onResumeCaseClick) {
      onResumeCaseClick(caseId);
    }
  };

  const handleStartNewCase = () => {
    console.log("StudentDashboard: handleStartNewCase called");
    if (onStartNewCase) {
      console.log("StudentDashboard: Calling onStartNewCase prop");
      onStartNewCase();
    }
  };

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
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
        <div className="bg-white rounded-lg shadow p-8 max-w-md">
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
              <img src={user?.picture || '/api/placeholder/32/32'} alt="User avatar" className="w-8 h-8 rounded-full" />
              <span className="text-gray-800 font-medium">{user?.name || 'Dr. Jane Smith'}</span>
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isDropdownOpen ? 'transform rotate-180 text-blue-500' : 'text-gray-500'}`} />
            </div>
            <AvatarDropdown anchorRef={dropdownRef} isOpen={isDropdownOpen} onClose={() => setIsDropdownOpen(false)}>
              <button
                onClick={() => {/* TODO */}}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 w-full text-left transition-colors duration-150 group"
              >
                <HelpCircle className="w-4 h-4 mr-2 text-gray-500 group-hover:text-blue-500 transition-colors duration-150" />
                Help Center
              </button>
              <button
                onClick={() => {/* TODO */}}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 w-full text-left transition-colors duration-150 group"
              >
                <Book className="w-4 h-4 mr-2 text-gray-500 group-hover:text-blue-500 transition-colors duration-150" />
                Profile
              </button>
              <button
                onClick={() => {/* TODO */}}
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
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Welcome back, {user?.name?.split(' ')[0] || 'Jane'}</h2>
              <p className="mb-4 opacity-90">Continue your clinical training or start a new case</p>
              <div className="flex space-x-4">
                <button
                  onClick={handleStartNewCase}
                  className="px-4 py-2 bg-white text-blue-700 font-medium rounded-md shadow hover:bg-blue-50 transition-colors"
                >
                  Start New Case
                </button>
                {recentCases.some(c => c.status === 'In Progress') && (
                  <button
                    onClick={() => handleResumeCase(recentCases.find(c => c.status === 'In Progress').id)}
                    className="px-4 py-2 bg-blue-700 text-white font-medium rounded-md shadow hover:bg-blue-900 transition-colors"
                  >
                    Continue Learning
                  </button>
                )}
              </div>
            </div>
            <div className="bg-blue-900 bg-opacity-30 rounded-lg p-4 text-center">
              <p className="text-sm opacity-80">Your Progress</p>
              <h3 className="text-3xl font-bold">{stats.accuracyRate}%</h3>
              <p className="text-sm opacity-80">Completed</p>
            </div>
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
                  <button
                    className={`px-3 py-1 rounded-md text-sm ${activeFilter === 'all' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                    onClick={() => setActiveFilter('all')}
                  >
                    All Time
                  </button>
                  <button
                    className={`px-3 py-1 rounded-md text-sm ${activeFilter === '6m' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                    onClick={() => setActiveFilter('6m')}
                  >
                    6 Months
                  </button>
                  <button
                    className={`px-3 py-1 rounded-md text-sm ${activeFilter === '1m' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`}
                    onClick={() => setActiveFilter('1m')}
                  >
                    1 Month
                  </button>
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <Line type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={2} />
                    <XAxis dataKey="date" stroke="#9CA3AF" />
                    <YAxis domain={[0, 100]} stroke="#9CA3AF" />
                    <Tooltip />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent Cases */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="flex justify-between items-center p-6 border-b">
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
                      <div className="flex justify-between mb-2">
                        <div className="flex items-center">
                          <User className="w-5 h-5 text-gray-400 mr-2" />
                          <h3 className="font-medium text-gray-900">{caseItem.name}, {caseItem.age}{caseItem.gender}</h3>
                        </div>
                        <div className="flex items-center text-sm text-gray-500">
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
                            onClick={() => caseItem.status === 'In Progress' ? handleResumeCase(caseItem.id) : null}
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

            {/* Upcoming Learning Modules */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold text-gray-800">Upcoming Modules</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {learningResources.map(module => (
                  <div key={module.id} className="p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{module.title}</h3>
                      <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="w-4 h-4 mr-1" />
                        <span>Due in {module.dueDate}</span>
                      </div>
                    </div>
                    <div className="relative pt-1">
                      <div className="flex mb-2 items-center justify-between">
                        <div>
                          <span className="text-xs font-semibold inline-block text-blue-600">
                            {module.completion}% Complete
                          </span>
                        </div>
                      </div>
                      <div className="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
                        <div
                          style={{ width: `${module.completion}%` }}
                          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-gray-50 text-center">
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  View All Modules
                </button>
              </div>
            </div>

            {/* Quick Start */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Start</h2>
              <div className="space-y-3">
                <button
                  onClick={handleStartNewCase}
                  className="w-full flex items-center justify-between p-3 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md"
                >
                  <span className="flex items-center">
                    <User className="w-5 h-5 mr-2" />
                    New Patient Case
                  </span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
                <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-md">
                  <span className="flex items-center">
                    <Book className="w-5 h-5 mr-2" />
                    Learning Library
                  </span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
                <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-md">
                  <span className="flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    Assessment Reports
                  </span>
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default StudentDashboard;
