import React, { useState } from 'react';
import ChatWindow from './ChatWindow';
import LabAnalysis from './LabAnalysis';
import MedicalImaging from './MedicalImaging';
import PatientProfile from './PatientProfile';
import './SimulationView.css';

const SimulationView = () => {
  // In a real app, these data would come from backend responses.
  const [conversation, setConversation] = useState([]);
  const dummyPatient = {
    name: "John Smith",
    age: 45,
    gender: "Male",
    history: "Hypertension, diabetes",
    presentingComplaint: "Chest pain"
  };

  // Example handler for sending a message. Replace with API integration.
  const handleSend = (message) => {
    // Append message to conversation history
    setConversation(prev => [...prev, { sender: 'user', text: message }]);
    // Simulate a reply from the virtual patient
    setTimeout(() => {
      setConversation(prev => [...prev, { sender: 'patient', text: "I'm feeling a bit better now." }]);
    }, 1000);
  };

  return (
    <div className="simulation-container">
      <div className="left-panel">
        <ChatWindow conversation={conversation} onSend={handleSend} />
      </div>
      <div className="right-panel">
        <PatientProfile patient={dummyPatient} />
        <LabAnalysis />
        <MedicalImaging />
      </div>
    </div>
  );
};

export default SimulationView;
