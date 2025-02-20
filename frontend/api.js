// services/api.js
// This file contains the API service for communicating with the backend

import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add request interceptor for auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Virtual Patient API
// Simulation API
export const simulationApi = {
  // Get available simulations
  getSimulations: (filters) => api.get('/simulations', { params: filters }),
  
  // Get specific simulation data
  getSimulationById: (simulationId) => api.get(`/simulations/${simulationId}`),
  
  // Start a new simulation session
  startSimulation: (simulationId, difficulty) => 
    api.post('/simulation-sessions', { simulationId, difficulty }),
  
  // Submit user action in simulation
  submitAction: (sessionId, action) => 
    api.post(`/simulation-sessions/${sessionId}/actions`, action),
  
  // End simulation session
  endSimulation: (sessionId, completed = true) => 
    api.post(`/simulation-sessions/${sessionId}/end`, { completed }),
  
  // Get feedback for an action
  getActionFeedback: (sessionId, actionId) => 
    api.get(`/simulation-sessions/${sessionId}/actions/${actionId}/feedback`),
  
  // Get simulation results/summary
  getSimulationResults: (sessionId) => 
    api.get(`/simulation-sessions/${sessionId}/results`),
};

// Analytics and Performance API
export const analyticsApi = {
  // Get user performance metrics
  getUserMetrics: (timeframe = 'month') => 
    api.get('/analytics/user-metrics', { params: { timeframe } }),
  
  // Get progress tracking data
  getProgressData: () => api.get('/analytics/progress'),
  
  // Get achievement data
  getAchievements: () => api.get('/analytics/achievements'),
  
  // Get recommendations based on performance
  getRecommendations: () => api.get('/analytics/recommendations'),
  
  // Get simulation history
  getSimulationHistory: (filters) => 
    api.get('/analytics/simulation-history', { params: filters }),
};

// User API
export const userApi = {
  // User authentication
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => api.post('/auth/logout'),
  refreshToken: () => api.post('/auth/refresh-token'),
  
  // User profile
  getUserProfile: () => api.get('/users/profile'),
  updateUserProfile: (profileData) => api.put('/users/profile', profileData),
  updatePassword: (passwordData) => api.put('/users/password', passwordData),
  
  // User settings
  getUserSettings: () => api.get('/users/settings'),
  updateUserSettings: (settings) => api.put('/users/settings', settings),
};

// Virtual Patient API
export const virtualPatientApi = {
  // Get available patient profiles
  getPatients: () => api.get('/patients'),
  
  // Get specific patient data
  getPatientById: (patientId) => api.get(`/patients/${patientId}`),
  
  // Send message to AI patient and get response
  sendMessage: (patientId, message) => api.post(`/patients/${patientId}/chat`, { message }),
  
  // Get patient medical records
  getPatientRecords: (patientId) => api.get(`/patients/${patientId}/records`),
  
  // Get patient lab results
  getPatientLabResults: (patientId) => api.get(`/patients/${patientId}/lab-results`),
  
  // Get patient imaging studies
  getPatientImaging: (patientId) => api.get(`/patients/${patientId}/imaging`),
  
  // End current patient session
  endPatientSession: (sessionId) => api.post(`/sessions/${sessionId}/end`)
}