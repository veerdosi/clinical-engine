// components/Navbar.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  const location = useLocation();
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <i className="heartbeat-icon"></i>
        <Link to="/">VirtualHealthSim</Link>
      </div>
      
      <div className="navbar-links">
        <Link 
          to="/patient-chat"
          className={location.pathname === '/patient-chat' ? 'active' : ''}
        >
          Virtual Patient Chat
        </Link>
        <Link 
          to="/simulations"
          className={location.pathname === '/simulations' ? 'active' : ''}
        >
          Procedural Simulations
        </Link>
        <Link 
          to="/"
          className={location.pathname === '/' ? 'active' : ''}
        >
          Performance Dashboard
        </Link>
      </div>
      
      <div className="navbar-actions">
        <Link to="/" className="nav-button">Home</Link>
        <Link to="/" className="nav-button">Dashboard</Link>
        <Link to="/settings" className="nav-button">Settings</Link>
      </div>
    </nav>
  );
};

export default Navbar;
