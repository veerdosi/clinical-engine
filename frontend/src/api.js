// api.js
export const sendMessage = async (message, includeVoiceResponse = true) => {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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