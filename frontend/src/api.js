// src/api.js
export const sendMessage = async (message) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    if (!response.ok) throw new Error("Chat API error");
    return response.json();
  };
  
  export const getLabReport = async () => {
    const response = await fetch('/api/lab-report');
    if (!response.ok) throw new Error("Lab report API error");
    return response.json();
  };
  
  export const getImaging = async () => {
    const response = await fetch('/api/imaging');
    if (!response.ok) throw new Error("Imaging API error");
    return response.json();
  };
  