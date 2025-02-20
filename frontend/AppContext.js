// context/AppContext.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { userApi, analyticsApi } from '../services/api';

// Initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  metrics: null,
  achievements: null,
  systemNotifications: [],
};

// Action types
const actions = {
  SET_USER: 'SET_USER',
  SET_AUTH_STATUS: 'SET_AUTH_STATUS',
  SET_LOADING: 'SET_LOADING',
  SET_METRICS: 'SET_METRICS',
  SET_ACHIEVEMENTS: 'SET_ACHIEVEMENTS',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  CLEAR_NOTIFICATIONS: 'CLEAR_NOTIFICATIONS',
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case actions.SET_USER:
      return { ...state, user: action.payload };
    case actions.SET_AUTH_STATUS:
      return { ...state, isAuthenticated: action.payload };
    case actions.SET_LOADING:
      return { ...state, isLoading: action.payload };
    case actions.SET_METRICS:
      return { ...state, metrics: action.payload };
    case actions.SET_ACHIEVEMENTS:
      return { ...state, achievements: action.payload };
    case actions.ADD_NOTIFICATION:
      return { 
        ...state, 
        systemNotifications: [...state.systemNotifications, 
          { id: Date.now(), ...action.payload }] 
      };
    case actions.REMOVE_NOTIFICATION:
      return { 
        ...state, 
        systemNotifications: state.systemNotifications.filter(
          notification => notification.id !== action.payload
        ) 
      };
    case actions.CLEAR_NOTIFICATIONS:
      return { ...state, systemNotifications: [] };
    default:
      return state;
  }
};

// Create context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Check authentication status on initial load
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Check if token exists
        const token = localStorage.getItem('auth_token');
        if (!token) {
          dispatch({ type: actions.SET_LOADING, payload: false });
          return;
        }

        // Validate token and get user data
        const response = await userApi.getUserProfile();
        dispatch({ type: actions.SET_USER, payload: response.data });
        dispatch({ type: actions.SET_AUTH_STATUS, payload: true });
        
        // Load user metrics
        loadUserMetrics();
        loadAchievements();
      } catch (error) {
        console.error('Auth check failed:', error);
        // Clear invalid token
        localStorage.removeItem('auth_token');
        dispatch({ type: actions.SET_AUTH_STATUS, payload: false });
      } finally {
        dispatch({ type: actions.SET_LOADING, payload: false });
      }
    };

    checkAuthStatus();
  }, []);

  // Load user performance metrics
  const loadUserMetrics = async () => {
    try {
      const response = await analyticsApi.getUserMetrics();
      dispatch({ type: actions.SET_METRICS, payload: response.data });
    } catch (error) {
      console.error('Failed to load metrics:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load performance metrics',
      });
    }
  };

  // Load user achievements
  const loadAchievements = async () => {
    try {
      const response = await analyticsApi.getAchievements();
      dispatch({ type: actions.SET_ACHIEVEMENTS, payload: response.data });
    } catch (error) {
      console.error('Failed to load achievements:', error);
    }
  };

  // Login
  const login = async (credentials) => {
    dispatch({ type: actions.SET_LOADING, payload: true });
    try {
      const response = await userApi.login(credentials);
      localStorage.setItem('auth_token', response.data.token);
      dispatch({ type: actions.SET_USER, payload: response.data.user });
      dispatch({ type: actions.SET_AUTH_STATUS, payload: true });
      
      // Load user data
      await Promise.all([loadUserMetrics(), loadAchievements()]);
      
      addNotification({
        type: 'success',
        message: 'Login successful. Welcome back!',
      });
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      addNotification({
        type: 'error',
        message: error.response?.data?.message || 'Login failed. Please check your credentials.',
      });
      return { 
        success: false, 
        message: error.response?.data?.message || 'Authentication failed' 
      };
    } finally {
      dispatch({ type: actions.SET_LOADING, payload: false });
    }
  };

  // Logout
  const logout = async () => {
    dispatch({ type: actions.SET_LOADING, payload: true });
    try {
      await userApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Always clear local data regardless of API success
      localStorage.removeItem('auth_token');
      dispatch({ type: actions.SET_USER, payload: null });
      dispatch({ type: actions.SET_AUTH_STATUS, payload: false });
      dispatch({ type: actions.SET_METRICS, payload: null });
      dispatch({ type: actions.SET_ACHIEVEMENTS, payload: null });
      dispatch({ type: actions.SET_LOADING, payload: false });
    }
  };

  // Add system notification
  const addNotification = (notification) => {
    const { message, type = 'info', duration = 5000 } = notification;
    
    dispatch({
      type: actions.ADD_NOTIFICATION,
      payload: { message, type, duration }
    });
    
    // Auto-remove notification after duration
    if (duration) {
      const notificationId = Date.now();
      setTimeout(() => {
        dispatch({
          type: actions.REMOVE_NOTIFICATION,
          payload: notificationId
        });
      }, duration);
    }
  };

  // Remove notification
  const removeNotification = (id) => {
    dispatch({
      type: actions.REMOVE_NOTIFICATION,
      payload: id
    });
  };

  // Provide context value
  const contextValue = {
    ...state,
    login,
    logout,
    loadUserMetrics,
    loadAchievements,
    addNotification,
    removeNotification,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the app context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
