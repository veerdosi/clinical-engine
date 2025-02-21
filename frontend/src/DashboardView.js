import React from 'react';
import './DashboardView.css';

const DashboardView = () => {
  // Dummy data for demonstration; replace with dynamic data.
  const stats = {
    simulationsCompleted: 12,
    diagnosticAccuracy: "85%",
    timeEfficiency: "70%",
  };

  const achievements = [
    "Completed 10 simulations",
    "Achieved 90% accuracy in 5 cases",
    "First simulation session"
  ];

  const recommendations = [
    "Review chest pain case protocols",
    "Focus on diagnostic reasoning in emergency cases",
    "Practice ordering appropriate imaging studies"
  ];

  return (
    <div className="dashboard">
      <h2>Performance Dashboard</h2>
      <div className="dashboard-section stats">
        <h3>Statistics</h3>
        <ul>
          <li>Simulations Completed: {stats.simulationsCompleted}</li>
          <li>Diagnostic Accuracy: {stats.diagnosticAccuracy}</li>
          <li>Time Efficiency: {stats.timeEfficiency}</li>
        </ul>
      </div>
      <div className="dashboard-section progress">
        <h3>Progress Tracking</h3>
        <div className="chart-placeholder">
          <p>Progress Chart Placeholder</p>
        </div>
      </div>
      <div className="dashboard-section achievements">
        <h3>Achievements</h3>
        <ul>
          {achievements.map((ach, index) => (
            <li key={index}>{ach}</li>
          ))}
        </ul>
      </div>
      <div className="dashboard-section recommendations">
        <h3>Recommendations for Improvement</h3>
        <ul>
          {recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default DashboardView;
