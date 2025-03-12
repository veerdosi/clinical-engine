import React from 'react';
import './TimelineVisualization.css';

const TimelineVisualization = ({ timelineData, efficiencyMetrics }) => {
  if (!timelineData || timelineData.length === 0) {
    return (
      <div className="timeline-placeholder">
        <p>No timeline data available.</p>
      </div>
    );
  }

  // Sort timeline by timestamp
  const sortedTimeline = [...timelineData].sort((a, b) => 
    new Date(a.timestamp) - new Date(b.timestamp)
  );

  // Convert seconds to readable format
  const formatDuration = (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  // Get icon for activity type
  const getActivityIcon = (type) => {
    switch (type) {
      case 'session_start':
        return '🏁';
      case 'patient_interaction':
        return '💬';
      case 'physical_exam':
        return '👨‍⚕️';
      case 'verified_procedure':
        return '✓';
      case 'test_order':
        return '🧪';
      case 'imaging_order':
        return '📷';
      case 'notes_update':
        return '📝';
      case 'diagnosis_submission':
        return '🏆';
      default:
        return '•';
    }
  };

  // Get color for activity type
  const getActivityColor = (type) => {
    switch (type) {
      case 'session_start':
        return '#4caf50';
      case 'patient_interaction':
        return '#2196f3';
      case 'physical_exam':
        return '#ff9800';
      case 'verified_procedure':
        return '#ff5722';
      case 'test_order':
        return '#9c27b0';
      case 'imaging_order':
        return '#e91e63';
      case 'notes_update':
        return '#795548';
      case 'diagnosis_submission':
        return '#f44336';
      default:
        return '#607d8b';
    }
  };

  // Process efficiency metrics for display
  const getMetricsDisplay = () => {
    if (!efficiencyMetrics) return null;
    
    return (
      <div className="timeline-metrics">
        <h4>Workflow Metrics</h4>
        <div className="metrics-grid">
          {efficiencyMetrics.session_duration_seconds && (
            <div className="metric-item">
              <span className="metric-label">Total Time:</span>
              <span className="metric-value">{formatDuration(efficiencyMetrics.session_duration_seconds)}</span>
            </div>
          )}
          {efficiencyMetrics.history_taking_time_seconds && (
            <div className="metric-item">
              <span className="metric-label">History Taking:</span>
              <span className="metric-value">{formatDuration(efficiencyMetrics.history_taking_time_seconds)}</span>
            </div>
          )}
          {efficiencyMetrics.physical_exam_time_seconds && (
            <div className="metric-item">
              <span className="metric-label">Physical Exams:</span>
              <span className="metric-value">{formatDuration(efficiencyMetrics.physical_exam_time_seconds)}</span>
            </div>
          )}
          {efficiencyMetrics.time_to_diagnosis_seconds && (
            <div className="metric-item">
              <span className="metric-label">Time to Diagnosis:</span>
              <span className="metric-value">{formatDuration(efficiencyMetrics.time_to_diagnosis_seconds)}</span>
            </div>
          )}
          <div className="metric-item">
            <span className="metric-label">Idle Periods:</span>
            <span className="metric-value">{efficiencyMetrics.idle_periods_count || 0}</span>
          </div>
          {efficiencyMetrics.total_idle_time_seconds && (
            <div className="metric-item">
              <span className="metric-label">Total Idle Time:</span>
              <span className="metric-value">{formatDuration(efficiencyMetrics.total_idle_time_seconds)}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="timeline-visualization">
      <h3>Clinical Workflow Timeline</h3>
      
      {getMetricsDisplay()}
      
      <div className="timeline-container">
        <div className="timeline-line"></div>
        {sortedTimeline.map((event, index) => (
          <div 
            key={index} 
            className="timeline-event"
            style={{
              '--event-color': getActivityColor(event.activity_type)
            }}
          >
            <div className="timeline-dot">
              <span className="event-icon">{getActivityIcon(event.activity_type)}</span>
            </div>
            <div className="timeline-content">
              <div className="event-time">{formatDuration(event.time_since_start)}</div>
              <div className="event-type">{event.activity_type.replace(/_/g, ' ')}</div>
              <div className="event-description">{event.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineVisualization;