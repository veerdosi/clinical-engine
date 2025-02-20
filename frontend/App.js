import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import VirtualPatientChat from './pages/VirtualPatientChat';
import Dashboard from './pages/Dashboard';
import ProceduralSimulations from './pages/ProceduralSimulations';

import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route 
            path="/" 
            element={
              <>
                <Navbar />
                <Dashboard />
              </>
            } 
          />
          <Route 
            path="/patient-chat" 
            element={
              <>
                <Navbar />
                <VirtualPatientChat />
              </>
            } 
          />
          <Route 
            path="/simulations" 
            element={
              <>
                <Navbar />
                <ProceduralSimulations />
              </>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
