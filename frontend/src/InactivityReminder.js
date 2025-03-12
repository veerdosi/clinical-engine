import React, { useState, useEffect } from 'react';
import './InactivityReminder.css';

const InactivityReminder = ({ inactivityThreshold = 120 }) => {
  const [isVisible, setIsVisible] = useState(false);
  let inactivityTimer = null;

  const resetTimer = () => {
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
    }
    
    inactivityTimer = setTimeout(() => {
      setIsVisible(true);
    }, inactivityThreshold * 1000); // Convert to milliseconds
  };

  const dismissReminder = () => {
    setIsVisible(false);
    resetTimer();
  };

  useEffect(() => {
    // Set up event listeners for user activity
    const activityEvents = ['mousedown', 'keypress', 'scroll', 'touchstart'];
    
    const handleUserActivity = () => {
      if (isVisible) {
        setIsVisible(false);
      }
      resetTimer();
    };
    
    // Add event listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, handleUserActivity);
    });
    
    // Initialize timer
    resetTimer();
    
    // Clean up
    return () => {
      if (inactivityTimer) {
        clearTimeout(inactivityTimer);
      }
      
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleUserActivity);
      });
    };
  }, [isVisible]);

  if (!isVisible) {
    return null;
  }

  return (
    <div className="inactivity-reminder">
      <div className="reminder-content">
        <h3>Are you still there?</h3>
        <p>We've noticed you haven't taken any actions for a while. In a clinical setting, timely decisions are critical for patient care.</p>
        <button onClick={dismissReminder}>Continue</button>
      </div>
    </div>
  );
};

export default InactivityReminder;
