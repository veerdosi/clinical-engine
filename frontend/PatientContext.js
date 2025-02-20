// context/PatientContext.js
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { virtualPatientApi } from '../services/api';
import { useAppContext } from './AppContext';

// Initial state
const initialState = {
  currentPatient: null,
  patientList: [],
  chatHistory: [],
  labResults: null,
  imaging: null,
  medicalRecords: null,
  sessionId: null,
  isLoading: false,
  error: null,
};

// Action types
const actions = {
  SET_CURRENT_PATIENT: 'SET_CURRENT_PATIENT',
  SET_PATIENT_LIST: 'SET_PATIENT_LIST',
  SET_CHAT_HISTORY: 'SET_CHAT_HISTORY',
  ADD_MESSAGE: 'ADD_MESSAGE',
  SET_LAB_RESULTS: 'SET_LAB_RESULTS',
  SET_IMAGING: 'SET_IMAGING',
  SET_MEDICAL_RECORDS: 'SET_MEDICAL_RECORDS',
  SET_SESSION_ID: 'SET_SESSION_ID',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_DATA: 'CLEAR_DATA',
};

// Reducer
const patientReducer = (state, action) => {
  switch (action.type) {
    case actions.SET_CURRENT_PATIENT:
      return { ...state, currentPatient: action.payload };
    case actions.SET_PATIENT_LIST:
      return { ...state, patientList: action.payload };
    case actions.SET_CHAT_HISTORY:
      return { ...state, chatHistory: action.payload };
    case actions.ADD_MESSAGE:
      return { 
        ...state, 
        chatHistory: [...state.chatHistory, action.payload] 
      };
    case actions.SET_LAB_RESULTS:
      return { ...state, labResults: action.payload };
    case actions.SET_IMAGING:
      return { ...state, imaging: action.payload };
    case actions.SET_MEDICAL_RECORDS:
      return { ...state, medicalRecords: action.payload };
    case actions.SET_SESSION_ID:
      return { ...state, sessionId: action.payload };
    case actions.SET_LOADING:
      return { ...state, isLoading: action.payload };
    case actions.SET_ERROR:
      return { ...state, error: action.payload };
    case actions.CLEAR_DATA:
      return { ...initialState, patientList: state.patientList };
    default:
      return state;
  }
};

// Create context
const PatientContext = createContext();

// Provider component
export const PatientProvider = ({ children }) => {
  const [state, dispatch] = useReducer(patientReducer, initialState);
  const { isAuthenticated, addNotification } = useAppContext();

  // Load patient list when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadPatientList();
    }
  }, [isAuthenticated]);

  // Load list of available patients
  const loadPatientList = async () => {
    dispatch({ type: actions.SET_LOADING, payload: true });
    try {
      const response = await virtualPatientApi.getPatients();
      dispatch({ type: actions.SET_PATIENT_LIST, payload: response.data });
    } catch (error) {
      console.error('Failed to load patient list:', error);
      dispatch({ 
        type: actions.SET_ERROR, 
        payload: 'Unable to load patient list. Please try again later.' 
      });
      addNotification({
        type: 'error',
        message: 'Failed to load patient database',
      });
    } finally {
      dispatch({ type: actions.SET_LOADING, payload: false });
    }
  };

  // Load a specific patient
  const loadPatient = async (patientId) => {
    dispatch({ type: actions.SET_LOADING, payload: true });
    dispatch({ type: actions.CLEAR_DATA });
    
    try {
      // Load patient data
      const patientResponse = await virtualPatientApi.getPatientById(patientId);
      dispatch({ type: actions.SET_CURRENT_PATIENT, payload: patientResponse.data });
      
      // Create a new chat session
      const sessionResponse = await virtualPatientApi.startPatientSession(patientId);
      dispatch({ type: actions.SET_SESSION_ID, payload: sessionResponse.data.sessionId });
      
      // Initialize empty chat with system greeting
      dispatch({ 
        type: actions.SET_CHAT_HISTORY, 
        payload: [{
          id: 1,
          sender: 'system',
          content: `Hello, I'm here to help with any medical questions you might have.`,
          timestamp: new Date().toISOString(),
        }]
      });
      
      // Load initial patient data
      await Promise.all([
        loadPatientRecords(patientId),
        loadPatientLabResults(patientId),
        loadPatientImaging(patientId)
      ]);
      
      return patientResponse.data;
    } catch (error) {
      console.error('Failed to load patient:', error);
      dispatch({ 
        type: actions.SET_ERROR, 
        payload: 'Unable to load patient data. Please try again later.' 
      });
      addNotification({
        type: 'error',
        message: 'Failed to initialize patient session',
      });
      return null;
    } finally {
      dispatch({ type: actions.SET_LOADING, payload: false });
    }
  };

  // Load patient medical records
  const loadPatientRecords = async (patientId) => {
    try {
      const response = await virtualPatientApi.getPatientRecords(patientId);
      dispatch({ type: actions.SET_MEDICAL_RECORDS, payload: response.data });
    } catch (error) {
      console.error('Failed to load medical records:', error);
    }
  };

  // Load patient lab results
  const loadPatientLabResults = async (patientId) => {
    try {
      const response = await virtualPatientApi.getPatientLabResults(patientId);
      dispatch({ type: actions.SET_LAB_RESULTS, payload: response.data });
    } catch (error) {
      console.error('Failed to load lab results:', error);
    }
  };

  // Load patient imaging studies
  const loadPatientImaging = async (patientId) => {
    try {
      const response = await virtualPatientApi.getPatientImaging(patientId);
      dispatch({ type: actions.SET_IMAGING, payload: response.data });
    } catch (error) {
      console.error('Failed to load imaging studies:', error);
    }
  };

  // Send message to virtual patient
  const sendMessage = async (message) => {
    if (!state.sessionId || !state.currentPatient) {
      addNotification({
        type: 'error',
        message: 'No active patient session',
      });
      return null;
    }
    
    // Add user message to chat
    const userMessage = {
      id: state.chatHistory.length + 1,
      sender: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    
    dispatch({ type: actions.ADD_MESSAGE, payload: userMessage });
    
    // Send to API
    try {
      const response = await virtualPatientApi.sendMessage(
        state.sessionId,
        message
      );
      
      // Add AI response to chat
      const aiResponse = {
        id: state.chatHistory.length + 2,
        sender: 'ai',
        content: response.data.message,
        timestamp: new Date().toISOString(),
        additionalData: response.data.additionalData || null,
      };
      
      dispatch({ type: actions.ADD_MESSAGE, payload: aiResponse });
      
      // If response contains updated lab results or imaging, update those too
      if (response.data.updatedLabResults) {
        dispatch({ type: actions.SET_LAB_RESULTS, payload: response.data.updatedLabResults });
      }
      
      if (response.data.updatedImaging) {
        dispatch({ type: actions.SET_IMAGING, payload: response.data.updatedImaging });
      }
      
      return aiResponse;
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message to chat
      const errorMessage = {
        id: state.chatHistory.length + 2,
        sender: "system",
        content: "I apologize, but I'm having trouble processing your request. Please try again.",
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      dispatch({ type: actions.ADD_MESSAGE, payload: errorMessage });
      return null;
    }
  };

  // End current patient session
  const endPatientSession = async () => {
    if (state.sessionId) {
      try {
        await virtualPatientApi.endPatientSession(state.sessionId);
      } catch (error) {
        console.error('Failed to properly end session:', error);
      }
    }
    
    dispatch({ type: actions.CLEAR_DATA });
  };

  // Provide context value
  const contextValue = {
    ...state,
    loadPatientList,
    loadPatient,
    sendMessage,
    endPatientSession,
  };

  return (
    <PatientContext.Provider value={contextValue}>
      {children}
    </PatientContext.Provider>
  );
};

// Custom hook to use the patient context
export const usePatientContext = () => {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error('usePatientContext must be used within a PatientProvider');
  }
  return context;
};
