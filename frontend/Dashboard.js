// pages/Dashboard.js
import React from 'react';
import { Link } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <div className="sidebar">
        <h3>Quick Access</h3>
        <div className="sidebar-links">
          <Link to="/patient-chat" className="sidebar-link">
            Virtual Patient Chat
          </Link>
          <Link to="/simulations" className="sidebar-link">
            Procedural Simulations
          </Link>
          <Link to="/" className="sidebar-link active">
            Performance Dashboard
          </Link>
        </div>
      </div>
      
      <div className="dashboard-content">
        <div className="dashboard-row">
          <div className="dashboard-card">
            <h3>Statistics</h3>
            <div className="statistics-chart">
              <img src="/images/performance-stats.png" alt="Performance statistics" />
            </div>
            <p className="card-description">
              Your current performance statistics over the last month, showcasing areas of improvement and consistency.
            </p>
          </div>
          
          <div className="dashboard-card">
            <h3>Progress Tracking</h3>
            <div className="progress-chart">
              <img src="/images/progress-chart.png" alt="Progress tracking chart" />
            </div>
            <p className="card-description">
              Track your progress over various healthcare scenarios and understand your learning curve.
            </p>
          </div>
          
          <div className="dashboard-card">
            <h3>Achievements</h3>
            <div className="achievements-list">
              <p>Completed 10 simulation scenarios</p>
              <p>Achieved 85% accuracy in diagnosis</p>
              <p>Mastered 5 new medical procedures</p>
            </div>
          </div>
        </div>
        
        <div className="recommendations-section">
          <h3>Recommendations for Improvement</h3>
          <p className="recommendation-intro">
            Based on your performance data, we recommend focusing on the following areas to enhance your skills:
          </p>
          <ul className="recommendations-list">
            <li>Spend more time on patient interaction scenarios.</li>
            <li>Review the latest medical protocols for increased proficiency.</li>
            <li>Engage in peer review sessions for collaborative learning.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
