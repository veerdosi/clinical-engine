import React, { useState } from 'react';
import SimulationView from './SimulationView';
import DashboardView from './DashboardView';
import './app.css';

function App() {
    const [view, setView] = useState("simulation");
  
    return (
      <div className="App">
        <header className="App-header">
          <h1>VirtualHealthSim</h1>
          <nav className="nav-buttons">
            <button onClick={() => setView("simulation")}>Simulation</button>
            <button onClick={() => setView("dashboard")}>Dashboard</button>
          </nav>
        </header>
        <main>
          {view === "simulation" ? <SimulationView /> : <DashboardView />}
        </main>
      </div>
    );
  }
  
  export default App;