import React, { useState, useRef, useEffect } from 'react';
import { sendMessage } from './api';
import './ChatWindow.css';

const ChatWindow = ({ 
  isDiagnosisSubmitted, 
  isNewCase, 
  onNewCaseStart, 
  conversationHistory = [], 
  onNewMessage 
}) => {
  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [preferVoiceResponse, setPreferVoiceResponse] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatHistoryRef = useRef(null);
  
  // Effect to auto-scroll to bottom of chat when new messages arrive
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [conversationHistory]);
  
  // Effect to handle cleanup of voice recording
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [isRecording]);
  
  // Effect to clear chat input when new case starts
  useEffect(() => {
    if (isNewCase) {
      setMessage("");
      setIsLoading(false);
      setIsRecording(false);
      
      // Notify parent component that we've processed the new case
      if (onNewCaseStart) {
        onNewCaseStart();
      }
    }
  }, [isNewCase, onNewCaseStart]);
  
  const onMessageReceived = (msg) => {
    onNewMessage(msg);
  };

  const startRecording = async () => {
    if (isLoading || isDiagnosisSubmitted) return; // Prevent recording if loading or diagnosis submitted
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = handleAudioStop;
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access your microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAudioStop = async () => {
    try {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      await handleVoiceMessage(audioBlob);
    } catch (error) {
      console.error("Error processing audio:", error);
      onMessageReceived({ 
        sender: 'system', 
        text: "Error processing voice input. Please try again or use text input." 
      });
      setIsLoading(false);
    }
  };

  // Handle voice message
  const handleVoiceMessage = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('includeVoiceResponse', preferVoiceResponse.toString());
    
    onMessageReceived({ sender: 'user', text: "🎤 [Voice message]" });
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/voice-chat', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Voice chat API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.audio && preferVoiceResponse) {
        const audio = new Audio("data:audio/mpeg;base64," + result.audio);
        audio.play();
      }
      
      onMessageReceived({ 
        sender: 'patient', 
        text: result.text,
        hasAudio: !!result.audio,
        audio: result.audio
      });
    } catch (error) {
      console.error("Error sending voice message:", error);
      onMessageReceived({ 
        sender: 'patient', 
        text: "Error: Unable to process voice message. Please try again." 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !isDiagnosisSubmitted) {
      setIsLoading(true);
      const userMessage = message;
      onMessageReceived({ sender: 'user', text: userMessage });
      setMessage("");
      
      try {
        const formData = new FormData();
        formData.append('message', userMessage);
        formData.append('includeVoiceResponse', preferVoiceResponse.toString());
        formData.append('isTextInput', 'true');
        
        const response = await fetch('/api/voice-chat', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.audio && preferVoiceResponse) {
          const audio = new Audio("data:audio/mpeg;base64," + result.audio);
          audio.play();
        }
        
        onMessageReceived({
          sender: 'patient',
          text: result.text,
          hasAudio: !!result.audio,
          audio: result.audio
        });
      } catch (error) {
        console.error("Error sending text message:", error);
        onMessageReceived({
          sender: 'patient',
          text: `Error: ${error.message || "Unable to reach backend. Please try again."}`
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-controls">
        <label>
          <input
            type="checkbox"
            checked={preferVoiceResponse}
            onChange={(e) => setPreferVoiceResponse(e.target.checked)}
            disabled={isLoading || isDiagnosisSubmitted}
          />
          Enable voice responses
        </label>
      </div>
      
      <div className="chat-history" ref={chatHistoryRef}>
        {conversationHistory.length === 0 && (
          <div className="chat-welcome">
            <p>Begin the patient interview. Ask questions to gather information about the patient's symptoms, medical history, and current condition.</p>
          </div>
        )}
        
        {conversationHistory.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            <p>{msg.text}</p>
            {msg.hasAudio && !preferVoiceResponse && msg.audio && (
              <button 
                className="play-audio-btn"
                onClick={() => {
                  const audio = new Audio("data:audio/mpeg;base64," + msg.audio);
                  audio.play();
                }}
              >
                🔊 Play response
              </button>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="chat-message system">
            <p>Processing...</p>
          </div>
        )}
        
        {isDiagnosisSubmitted && (
          <div className="chat-message system diagnosis-submitted">
            <p>You have submitted your final diagnosis. This conversation is now complete.</p>
          </div>
        )}
      </div>
      
      <div className="voice-controls">
        <button
          type="button"
          className={`voice-btn ${isRecording ? 'recording' : ''}`}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isLoading || isDiagnosisSubmitted}
        >
          {isRecording ? '⏹️ Stop Recording' : '🎤 Start Recording'}
        </button>
      </div>
      
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder={
            isDiagnosisSubmitted ? "Conversation complete" : 
            isLoading ? "Processing..." : 
            "Ask the patient..."
          }
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={isLoading || isRecording || isDiagnosisSubmitted}
        />
        <button 
          type="submit" 
          disabled={isLoading || isRecording || !message.trim() || isDiagnosisSubmitted}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;