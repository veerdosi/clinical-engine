// pages/VirtualPatientChat.js
import React, { useState, useRef, useEffect } from 'react';
import './VirtualPatientChat.css';

const VirtualPatientChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: "Hello, I'm here to help with any medical questions you might have.",
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  
  // Mock patient data
  const patientData = {
    name: 'John Smith',
    age: 45,
    medicalHistory: 'Hypertension, Asthma',
    image: '/images/patient-profile.jpg'
  };

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: inputValue,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    // Simulate AI response based on user input
    simulateResponse(inputValue);
  };

  // Simulated AI response logic
  const simulateResponse = (userInput) => {
    setTimeout(() => {
      let response;
      
      if (userInput.toLowerCase().includes('blood test')) {
        response = {
          id: messages.length + 2,
          sender: 'ai',
          text: "Here are the blood test results:",
          timestamp: new Date(),
          hasChart: true,
        };
      } else if (userInput.toLowerCase().includes('x-ray')) {
        response = {
          id: messages.length + 2,
          sender: 'ai',
          text: "",
          timestamp: new Date(),
          hasXray: true,
        };
      } else {
        response = {
          id: messages.length + 2,
          sender: 'ai',
          text: "I'll need more information to help you with that. Can you provide more details about your symptoms or questions?",
          timestamp: new Date(),
        };
      }
      
      setMessages((prev) => [...prev, response]);
    }, 1000);
  };

  // End current session
  const handleEndSession = () => {
    // In a real app, this would save session data and reset the chat
    if (window.confirm('Are you sure you want to end this session?')) {
      setMessages([{
        id: 1,
        sender: 'ai',
        text: "Hello, I'm here to help with any medical questions you might have.",
        timestamp: new Date(),
      }]);
    }
  };

  return (
    <div className="virtual-patient-page">
      <div className="chat-container">
        <div className="chat-header">
          <h2>Chat with Virtual</h2>
          <button 
            className="end-session-btn"
            onClick={handleEndSession}
          >
            End Session
          </button>
        </div>
        
        <div className="messages-container">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
            >
              <div className="message-content">
                {message.text && <p>{message.text}</p>}
                {message.hasChart && (
                  <div className="chart-container">
                    <img src="/images/blood-test-chart.png" alt="Blood test results chart" />
                  </div>
                )}
                {message.hasXray && (
                  <div className="xray-container">
                    <img src="/images/chest-xray.png" alt="Chest X-ray" />
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <form className="message-input-container" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <button type="submit" className="send-btn">Send</button>
          <button type="button" className="voice-btn">
            <i className="mic-icon"></i>
          </button>
        </form>
      </div>
      
      <div className="patient-sidebar">
        <div className="patient-profile">
          <img src={patientData.image} alt={patientData.name} className="patient-image" />
          <h3>{patientData.name}</h3>
          <p>Age: {patientData.age}</p>
          <p>Medical History: {patientData.medicalHistory}</p>
        </div>
        
        <div className="lab-analysis">
          <h3>Labwork Analysis</h3>
          <div className="analysis-chart">
            <img src="/images/lab-trend-chart.png" alt="Lab analysis chart" />
          </div>
        </div>
        
        <div className="medical-imaging">
          <h3>Medical Imaging</h3>
          <div className="imaging-grid">
            <img src="/images/brain-scan1.png" alt="Brain scan" />
            <img src="/images/brain-scan2.png" alt="Brain scan" />
            <img src="/images/brain-scan3.png" alt="Brain scan" />
            <img src="/images/brain-scan4.png" alt="Brain scan" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default VirtualPatientChat;
