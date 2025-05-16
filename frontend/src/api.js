// api.js
import { getToken, authFetch } from './auth';

// Helper function to create authenticated request headers
const getAuthHeaders = (contentType = 'application/json') => {
  const headers = {
    'Content-Type': contentType
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

export const sendMessage = async (message, includeVoiceResponse = true) => {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        message,
        includeVoiceResponse  // Parameter to control whether to generate voice
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        `API Error (${response.status}): ${errorData.error || response.statusText}`
      );
    }

    return response.json();
  } catch (error) {
    console.error("Error in sendMessage:", error);
    throw error;
  }
};

// Get current case
export const getCurrentCase = async () => {
  try {
    const response = await fetch('/api/current-case', {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get current case: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error getting current case:", error);
    throw error;
  }
};

// Generate new case - fixed version with direct token access
export const generateNewCase = async (specialty, difficulty) => {
  try {
    console.log("Generating new case:", { specialty, difficulty });
    // Get the token directly to ensure it's available
    const token = localStorage.getItem('authToken');

    if (!token) {
      console.error("No auth token found in localStorage");
      throw new Error("Authentication required");
    }

    console.log("Using token:", token.substring(0, 10) + "...");

    // This route is protected and requires authentication
    const response = await fetch('/api/new-case', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        specialty,
        difficulty
      })
    });

    console.log("Response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response:", errorText);
      throw new Error(`Failed to generate case: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error generating new case:", error);
    throw error;
  }
};

// Save notes
export const saveNotes = async (notes, case_id) => {
  try {
    const response = await authFetch('/api/save-notes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        notes,
        case_id
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to save notes: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error saving notes:", error);
    throw error;
  }
};

// Submit diagnosis
export const submitDiagnosis = async (diagnosis, notes, case_id) => {
  try {
    const response = await authFetch('/api/submit-diagnosis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        diagnosis,
        notes,
        case_id
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to submit diagnosis: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error submitting diagnosis:", error);
    throw error;
  }
};

// Order lab test
export const orderLabTest = async (test) => {
  try {
    const response = await authFetch('/api/order-lab', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        test
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to order lab test: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error ordering lab test:", error);
    throw error;
  }
};

// Order imaging
export const orderImaging = async (imaging) => {
  try {
    const response = await authFetch('/api/order-imaging', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        imaging
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to order imaging: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error ordering imaging:", error);
    throw error;
  }
};

// Perform physical exam
export const performPhysicalExam = async (system, procedure_verified = false) => {
  try {
    const response = await authFetch('/api/physical-exam', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        system,
        procedure_verified
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to perform physical exam: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error performing physical exam:", error);
    throw error;
  }
};

// Get user evaluation history
export const getUserEvaluations = async (page = 1, perPage = 10) => {
  try {
    const response = await authFetch(`/api/evaluations/history?page=${page}&per_page=${perPage}`);

    if (!response.ok) {
      throw new Error(`Failed to get evaluation history: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error getting evaluation history:", error);
    throw error;
  }
};

// Get evaluation details
export const getEvaluationDetails = async (evaluationId) => {
  try {
    const response = await authFetch(`/api/evaluations/${evaluationId}`);

    if (!response.ok) {
      throw new Error(`Failed to get evaluation details: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error getting evaluation details:", error);
    throw error;
  }
};

// Get user session history
export const getUserSessions = async (page = 1, perPage = 10) => {
  try {
    const response = await authFetch(`/api/sessions/history?page=${page}&per_page=${perPage}`);

    if (!response.ok) {
      throw new Error(`Failed to get session history: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    console.error("Error getting session history:", error);
    throw error;
  }
};

// Test authentication
export const testAuth = async () => {
  try {
    console.log("Testing authentication...");
    const token = localStorage.getItem('authToken');

    if (!token) {
      console.error("No auth token found in localStorage");
      return { authenticated: false, error: "No token found" };
    }

    const response = await fetch('/api/auth/test', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    console.log("Auth test response status:", response.status);

    if (!response.ok) {
      console.error("Auth test failed:", response.statusText);
      return { authenticated: false, error: response.statusText };
    }

    const data = await response.json();
    console.log("Auth test result:", data);
    return data;
  } catch (error) {
    console.error("Error testing authentication:", error);
    return { authenticated: false, error: error.message };
  }
};
