import React, { useState, useEffect, useRef, useCallback } from 'react';
import './InactivityReminder.css';

const InactivityReminder = ({ inactivityThreshold = 120 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const inactivityTimerRef = useRef(null); // Use useRef for the timer ID

  // Memoize resetTimer because it's a dependency of useEffect and dismissReminder
  // It depends on inactivityThreshold, so that should be in its dependency array.
  const resetTimer = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }

    inactivityTimerRef.current = setTimeout(() => {
      setIsVisible(true);
    }, inactivityThreshold * 1000); // Convert to milliseconds
  }, [inactivityThreshold]);

  // Memoize dismissReminder because it's used as an event handler
  // It depends on resetTimer.
  const dismissReminder = useCallback(() => {
    setIsVisible(false);
    resetTimer();
  }, [resetTimer]);

  useEffect(() => {
    // Set up event listeners for user activity
    const activityEvents = ['mousedown', 'keypress', 'scroll', 'touchstart'];

    const handleUserActivity = () => {
      // isVisible is read here, so it should be a dependency
      if (isVisible) {
        setIsVisible(false); // Directly set state, no need for isVisible as dependency for this line
      }
      resetTimer(); // resetTimer is memoized and included as a dependency
    };

    // Add event listeners
    activityEvents.forEach(event => {
      window.addEventListener(event, handleUserActivity);
    });

    // Initialize timer
    resetTimer();

    // Clean up
    return () => {
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }

      activityEvents.forEach(event => {
        window.removeEventListener(event, handleUserActivity);
      });
    };
  }, [isVisible, resetTimer]); // resetTimer is stable due to useCallback, isVisible triggers re-evaluation if it changes.

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