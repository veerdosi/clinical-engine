import React, { useState, useEffect } from 'react';
import { getUserEvaluations, getUserSessions, getDashboardData } from './api';
import './StudentDashboard.css';

const StudentDashboard = ({ onStartNewCase, onResumeCaseClick, user }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalCases: 0,
    completedCases: 0,
    accuracyRate: 0
  });
  const [recentCases, setRecentCases] = useState([]);
  const [specialtyPerformance, setSpecialtyPerformance] = useState([]);
  const [learningResources, setLearningResources] = useState([]);

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
  }, []);

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
      setSpecialtyPerformance(data.specialtyPerformance);
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
        patientName: item.case_data?.name || 'Unknown Patient',
        age: item.case_data?.age || '??',
        gender: item.case_data?.gender?.[0] || '?',
        specialty: item.case_data?.specialty || 'General',
        difficulty: item.case_data?.difficulty || 'Unknown',
        status: 'Completed',
        date: new Date(item.timestamp).toLocaleDateString(),
        diagnosisCorrect: item.is_correct,
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

    setSpecialtyPerformance(specialtyStats);
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
        patientName: session.case_data?.name || 'Unknown Patient',
        age: session.case_data?.age || '??',
        gender: session.case_data?.gender?.[0] || '?',
        specialty: session.case_data?.specialty || 'General',
        difficulty: session.case_data?.difficulty || 'Unknown',
        status: 'In Progress',
        date: new Date(session.last_activity).toLocaleDateString(),
        diagnosisCorrect: null,
        timeTaken: session.time_elapsed ? `${Math.round(session.time_elapsed / 60)} min` : 'Unknown'
      }));

    // Combine with completed cases and sort by date
    const allCases = [...inProgressCases, ...recentCases]
      .sort((a, b) => new Date(b.date) - new Date(a.date))
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
    const resources = [
      { title: "Advanced Cardiac Auscultation", type: "Video", link: "#" },
      { title: "Neurological Assessment Techniques", type: "Article", link: "#" },
      { title: "Common Misdiagnoses in Internal Medicine", type: "Study", link: "#" },
      { title: "Pulmonary Function Tests Interpretation", type: "Guide", link: "#" }
    ];

    setLearningResources(resources);
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

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  return (
    <div className="student-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <h1>Clinical Engine</h1>
        {user && (
          <div className="user-profile">
            {user.picture && <img src={user.picture} alt={user.name} className="user-avatar" />}
            <span className="user-name">{user.name}</span>
          </div>
        )}
      </header>

      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="welcome-message">
          <h2>Welcome back, {user?.name || 'Student'}!</h2>
          <p>Continue your clinical training or start a new case.</p>
        </div>
        <div className="action-buttons">
          {recentCases.some(c => c.status === 'In Progress') && (
            <button
              className="resume-case-btn"
              onClick={() => handleResumeCase(recentCases.find(c => c.status === 'In Progress').id)}
            >
              Resume Case
            </button>
          )}
          <button
            className="new-case-btn"
            onClick={handleStartNewCase}
          >
            Start New Case
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-section">
        <div className="stat-card">
          <div className="stat-header">
            <h3>Total Cases</h3>
            <div className="stat-icon total-icon"></div>
          </div>
          <div className="stat-value">{stats.totalCases}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <h3>Completed Cases</h3>
            <div className="stat-icon completed-icon"></div>
          </div>
          <div className="stat-value">{stats.completedCases}</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <h3>Diagnosis Accuracy</h3>
            <div className="stat-icon accuracy-icon"></div>
          </div>
          <div className="stat-value">{stats.accuracyRate}%</div>
        </div>
      </div>

      {/* Recent Cases & Performance */}
      <div className="dashboard-grid">
        {/* Recent Cases */}
        <div className="recent-cases-section">
          <div className="section-header">
            <h3>Recent Cases</h3>
            <a href="#" className="view-all-link">View all</a>
          </div>

          {recentCases.length === 0 ? (
            <div className="no-cases-message">
              <p>You haven't completed any cases yet. Start a new case to begin your training!</p>
            </div>
          ) : (
            <table className="cases-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Specialty</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentCases.map(caseItem => (
                  <tr key={caseItem.id}>
                    <td>
                      <div className="patient-name">{caseItem.patientName}</div>
                      <div className="patient-details">{caseItem.age}{caseItem.gender}, {caseItem.date}</div>
                    </td>
                    <td>
                      <div className="specialty-name">{caseItem.specialty}</div>
                      <div className="difficulty-level">{caseItem.difficulty}</div>
                    </td>
                    <td>
                      {caseItem.status === "Completed" ? (
                        <span className={`status-badge ${caseItem.diagnosisCorrect ? 'correct' : 'incorrect'}`}>
                          {caseItem.diagnosisCorrect ? 'Correct' : 'Incorrect'}
                        </span>
                      ) : (
                        <span className="status-badge in-progress">
                          In Progress
                        </span>
                      )}
                    </td>
                    <td>
                      {caseItem.status === "In Progress" ? (
                        <button
                          className="resume-btn"
                          onClick={() => handleResumeCase(caseItem.id)}
                        >
                          Resume
                        </button>
                      ) : (
                        <button className="review-btn">Review</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Performance & Resources */}
        <div className="sidebar-sections">
          {/* Performance by Specialty */}
          <div className="performance-section">
            <h3>Performance by Specialty</h3>

            {specialtyPerformance.length === 0 ? (
              <div className="no-data-message">
                <p>Complete more cases to see your performance by specialty.</p>
              </div>
            ) : (
              <div className="specialty-list">
                {specialtyPerformance.map(item => (
                  <div key={item.specialty} className="specialty-item">
                    <div className="specialty-header">
                      <span className="specialty-name">{item.specialty}</span>
                      <span className="specialty-accuracy">{item.accuracy}%</span>
                    </div>
                    <div className="specialty-progress-bar">
                      <div
                        className="specialty-progress-value"
                        style={{ width: `${item.accuracy}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Learning Resources */}
          <div className="resources-section">
            <div className="section-header">
              <h3>Learning Resources</h3>
              <a href="#" className="view-all-link">View all</a>
            </div>

            <ul className="resources-list">
              {learningResources.map((resource, index) => (
                <li key={index} className="resource-item">
                  <a href={resource.link} className="resource-link">
                    <span className="resource-title">{resource.title}</span>
                    <span className="resource-type">{resource.type}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
