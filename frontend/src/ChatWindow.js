// ChatWindow.js
import React, { useState } from 'react';
import { sendMessage } from './api';
import './ChatWindow.css';

const ChatWindow = ({ conversation, onMessageReceived }) => {
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim()) {
      // Update conversation immediately with the user's message
      onMessageReceived({ sender: 'user', text: message });
      try {
        const response = await sendMessage(message);
        // Append the backend's mock response to conversation
        onMessageReceived({ sender: 'patient', text: response.text });
      } catch (error) {
        onMessageReceived({ sender: 'patient', text: "Error: Unable to reach backend" });
      }
      setMessage("");
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-history">
        {conversation.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            <p>{msg.text}</p>
          </div>
        ))}
      </div>
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask the patient..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatWindow;
