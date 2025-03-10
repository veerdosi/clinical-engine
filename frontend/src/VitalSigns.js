import React, { useState, useEffect, useRef } from 'react';

// Add this style tag to your component
const VitalSignsCSS = () => {
  return (
    <style>
      {`
        .vital-signs-dashboard {
          background-color: #1a1a2e;
          border-radius: 8px;
          padding: 1rem;
          font-family: 'Roboto', sans-serif;
          color: #eaeaea;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
          overflow: hidden;
        }
        
        .vital-signs-title {
          color: #4aed4f;
          margin-top: 0;
          margin-bottom: 1rem;
          font-size: 1.2rem;
          text-align: center;
          letter-spacing: 1px;
          text-transform: uppercase;
          border-bottom: 1px solid #333345;
          padding-bottom: 0.5rem;
        }
        
        .vital-signs-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1rem;
        }
        
        .vital-sign-card {
          background-color: #16213e;
          border-radius: 6px;
          padding: 1rem;
          border-left: 3px solid #4aed4f;
          transition: all 0.3s ease;
        }
        
        .vital-sign-card.abnormal {
          border-left-color: #e74c3c;
          animation: pulse-warning 2s infinite;
        }
        
        .vital-sign-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }
        
        .vital-sign-header h4 {
          margin: 0;
          font-size: 1rem;
          font-weight: 500;
          color: #a5a5a5;
        }
        
        .vital-value {
          font-size: 1.2rem;
          font-weight: 700;
          color: #4aed4f;
        }
        
        .vital-sign-card.abnormal .vital-value {
          color: #e74c3c;
        }
        
        .vital-visualization {
          height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        /* Heart Rate Monitor Styles */
        .heart-rate-monitor {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: #0a0a18;
          border-radius: 4px;
          padding: 0.5rem;
        }
        
        .heart-rate-monitor canvas {
          max-width: 100%;
          height: auto;
        }
        
        /* Respiratory Rate Visualization Styles */
        .respiratory-visual {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .lungs-container {
          display: flex;
          justify-content: center;
          gap: 5px;
          animation: breathing var(--breathing-duration, 4s) infinite ease-in-out;
        }
        
        .lung {
          width: 40px;
          height: 60px;
          background-color: #7b98ef;
          border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
        }
        
        .left-lung {
          transform-origin: right center;
        }
        
        .right-lung {
          transform-origin: left center;
        }
        
        @keyframes breathing {
          0%, 100% {
            transform: scale(0.8);
            opacity: 0.7;
          }
          50% {
            transform: scale(1);
            opacity: 1;
          }
        }
        
        /* Blood Pressure Visualization */
        .bp-visual {
          width: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }
        
        .bp-gauge {
          width: 100%;
          height: 70px;
          display: flex;
          gap: 1rem;
          align-items: flex-end;
        }
        
        .bp-bar {
          flex: 1;
          background-color: #2ecc71;
          border-radius: 4px 4px 0 0;
          position: relative;
          transition: height 1s ease-in-out;
          display: flex;
          align-items: flex-start;
          justify-content: center;
        }
        
        .bp-bar span {
          background-color: rgba(0, 0, 0, 0.6);
          color: white;
          padding: 2px 4px;
          border-radius: 3px;
          font-size: 0.8rem;
          margin-top: 2px;
        }
        
        .bp-labels {
          display: flex;
          width: 100%;
          justify-content: space-around;
          font-size: 0.8rem;
          color: #a5a5a5;
        }
        
        /* Temperature Visualization */
        .temperature-visual {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100%;
        }
        
        .thermometer {
          display: flex;
          flex-direction: column;
          align-items: center;
          position: relative;
        }
        
        .thermometer-bulb {
          width: 16px;
          height: 16px;
          background-color: #ccc;
          border-radius: 50%;
          margin-top: 2px;
        }
        
        .thermometer-stem {
          width: 8px;
          height: 70px;
          background-color: #ccc;
          border-radius: 4px;
          margin-top: -2px;
          position: relative;
          overflow: hidden;
        }
        
        .thermometer-fill {
          position: absolute;
          bottom: 0;
          left: 0;
          width: 100%;
          background-color: #2ecc71;
          transition: height 1s ease-in-out;
        }
        
        /* Oxygen Saturation Visualization */
        .oxygen-visual {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100%;
        }
        
        .oxygen-pulse {
          width: 60px;
          height: 60px;
          background-color: #0a0a18;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          animation: pulse 2s infinite;
        }
        
        .oxygen-pulse:before {
          content: '';
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          background-color: var(--pulse-color, #2ecc71);
          opacity: var(--pulse-opacity, 0.5);
          animation: pulse 2s infinite;
        }
        
        .oxygen-icon {
          font-size: 1.5rem;
          font-weight: bold;
          color: var(--pulse-color, #2ecc71);
          z-index: 1;
        }
        
        @keyframes pulse {
          0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7);
          }
          
          70% {
            transform: scale(1);
            box-shadow: 0 0 0 10px rgba(46, 204, 113, 0);
          }
          
          100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(46, 204, 113, 0);
          }
        }
        
        /* Pain Score Visualization */
        .pain-visual {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          height: 100%;
        }
        
        .pain-face {
          font-size: 2.5rem;
        }
        
        .pain-scale {
          width: 100%;
          height: 8px;
          background-color: #0a0a18;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .pain-scale-bar {
          height: 100%;
          background-color: #2ecc71;
          border-radius: 4px;
          transition: width 0.5s ease-in-out;
        }
        
        /* Warning animation */
        @keyframes pulse-warning {
          0% {
            box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(231, 76, 60, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(231, 76, 60, 0);
          }
        }
      `}
    </style>
  );
};

const VitalSigns = ({ vitals }) => {
  // Default vitals if none are provided
  const defaultVitals = {
    HR: "72 bpm",
    BP: "120/80 mmHg",
    RR: "16 breaths/min",
    Temp: "37.0 °C",
    SpO2: "98%",
    Pain: "0/10"
  };

  // Combine provided vitals with defaults
  const allVitals = { ...defaultVitals, ...vitals };
  
  // Parse numeric values from strings
  const heartRate = parseInt(allVitals.HR) || 72;
  const respiratoryRate = parseInt(allVitals.RR) || 16;
  const oxygenSaturation = parseInt(allVitals.SpO2) || 98;
  const painScore = parseInt(allVitals.Pain) || 0;
  
  // Parse temperature
  const tempMatch = allVitals.Temp.match(/(\d+\.?\d*)/);
  const temperature = tempMatch ? parseFloat(tempMatch[0]) : 37.0;
  
  // Parse blood pressure
  const bpMatch = allVitals.BP.match(/(\d+)\/(\d+)/);
  const systolic = bpMatch ? parseInt(bpMatch[1]) : 120;
  const diastolic = bpMatch ? parseInt(bpMatch[2]) : 80;
  
  // Determine if values are abnormal
  const isHeartRateAbnormal = heartRate < 60 || heartRate > 100;
  const isRespRateAbnormal = respiratoryRate < 12 || respiratoryRate > 20;
  const isO2Abnormal = oxygenSaturation < 95;
  const isTempAbnormal = temperature < 36.5 || temperature > 37.5;
  const isBPAbnormal = systolic < 90 || systolic > 140 || diastolic < 60 || diastolic > 90;
  
  return (
    <div className="vital-signs-dashboard">
      <VitalSignsCSS />
      <h3 className="vital-signs-title">Vital Signs Monitor</h3>
      
      <div className="vital-signs-grid">
        {/* Heart Rate Monitor */}
        <div className={`vital-sign-card ${isHeartRateAbnormal ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>Heart Rate</h4>
            <span className="vital-value">{allVitals.HR}</span>
          </div>
          <div className="vital-visualization">
            <HeartRateMonitor rate={heartRate} />
          </div>
        </div>
        
        {/* Blood Pressure */}
        <div className={`vital-sign-card ${isBPAbnormal ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>Blood Pressure</h4>
            <span className="vital-value">{allVitals.BP}</span>
          </div>
          <div className="vital-visualization">
            <BloodPressureVisual systolic={systolic} diastolic={diastolic} />
          </div>
        </div>
        
        {/* Respiratory Rate */}
        <div className={`vital-sign-card ${isRespRateAbnormal ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>Respiratory Rate</h4>
            <span className="vital-value">{allVitals.RR}</span>
          </div>
          <div className="vital-visualization">
            <RespiratoryRateVisual rate={respiratoryRate} />
          </div>
        </div>
        
        {/* Temperature */}
        <div className={`vital-sign-card ${isTempAbnormal ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>Temperature</h4>
            <span className="vital-value">{allVitals.Temp}</span>
          </div>
          <div className="vital-visualization">
            <TemperatureVisual temperature={temperature} />
          </div>
        </div>
        
        {/* Oxygen Saturation */}
        <div className={`vital-sign-card ${isO2Abnormal ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>O₂ Saturation</h4>
            <span className="vital-value">{allVitals.SpO2}</span>
          </div>
          <div className="vital-visualization">
            <OxygenSaturationVisual value={oxygenSaturation} />
          </div>
        </div>
        
        {/* Pain Score */}
        <div className="vital-sign-card">
          <div className="vital-sign-header">
            <h4>Pain Score</h4>
            <span className="vital-value">{allVitals.Pain}</span>
          </div>
          <div className="vital-visualization">
            <PainScoreVisual score={painScore} />
          </div>
        </div>
      </div>
    </div>
  );
};

// Heart Rate Monitor Component
const HeartRateMonitor = ({ rate }) => {
  const canvasRef = useRef(null);
  const [ecgPoints, setEcgPoints] = useState([]);
  
  // ECG pattern generation
  useEffect(() => {
    // Adjust timing based on heart rate (60bpm = 1000ms per beat)
    const beatDuration = 60000 / rate; // Duration of one heartbeat in ms
    const pointsPerBeat = 100; // Resolution of our ECG
    const totalPoints = 150; // Number of points to show on screen
    
    // Generate one normal ECG complex
    const generateECGPattern = () => {
      const pattern = [];
      // P wave
      for (let i = 0; i < 10; i++) {
        pattern.push(5 + Math.sin(i * 0.3) * 3);
      }
      // PR segment
      for (let i = 0; i < 5; i++) {
        pattern.push(5);
      }
      // QRS complex
      pattern.push(2); // Q
      pattern.push(25); // R
      pattern.push(0); // S
      // ST segment
      for (let i = 0; i < 10; i++) {
        pattern.push(5 + Math.sin(i * 0.1) * 1);
      }
      // T wave
      for (let i = 0; i < 15; i++) {
        pattern.push(5 + Math.sin(i * 0.2) * 4);
      }
      // TP segment (rest of the cycle)
      const remaining = pointsPerBeat - pattern.length;
      for (let i = 0; i < remaining; i++) {
        pattern.push(5);
      }
      return pattern;
    };
    
    // Get the base pattern
    const basePattern = generateECGPattern();
    
    // Function to animate the ECG
    let animationId;
    let currentPoint = 0;
    let points = Array(totalPoints).fill(5); // Initialize with baseline
    
    const animate = () => {
      // Get modulo position in pattern
      const patternPos = currentPoint % basePattern.length;
      
      // Update points array
      points = [...points.slice(1), basePattern[patternPos]];
      setEcgPoints([...points]);
      
      // Draw waveform to canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        ctx.beginPath();
        ctx.strokeStyle = '#4aed4f';
        ctx.lineWidth = 2;
        
        // Draw the ECG line
        for (let i = 0; i < points.length; i++) {
          const x = (i / points.length) * width;
          const y = height - (points[i] / 30) * height;
          
          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        
        ctx.stroke();
      }
      
      currentPoint++;
      // Calculate time for next frame based on heart rate
      const frameDelay = beatDuration / pointsPerBeat;
      animationId = setTimeout(animate, frameDelay);
    };
    
    animate();
    
    // Cleanup
    return () => clearTimeout(animationId);
  }, [rate]);
  
  return (
    <div className="heart-rate-monitor">
      <canvas ref={canvasRef} width={300} height={80} />
    </div>
  );
};

// Respiratory Rate Visualization
const RespiratoryRateVisual = ({ rate }) => {
  // Calculate animation duration based on respiratory rate
  const animationDuration = 60 / rate; // in seconds
  
  return (
    <div className="respiratory-visual" style={{ '--breathing-duration': `${animationDuration}s` }}>
      <div className="lungs-container">
        <div className="lung left-lung"></div>
        <div className="lung right-lung"></div>
      </div>
    </div>
  );
};

// Blood Pressure Visualization
const BloodPressureVisual = ({ systolic, diastolic }) => {
  // Calculate proportion of normal range (for visualization)
  const maxSystolic = 180;
  const systolicPercentage = Math.min(100, (systolic / maxSystolic) * 100);
  const diastolicPercentage = Math.min(100, (diastolic / maxSystolic) * 100);
  
  // Determine status colors
  const getSystolicColor = () => {
    if (systolic < 90) return '#3498db'; // Low - blue
    if (systolic > 140) return '#e74c3c'; // High - red
    return '#2ecc71'; // Normal - green
  };
  
  const getDiastolicColor = () => {
    if (diastolic < 60) return '#3498db'; // Low - blue
    if (diastolic > 90) return '#e74c3c'; // High - red
    return '#2ecc71'; // Normal - green
  };
  
  return (
    <div className="bp-visual">
      <div className="bp-gauge">
        <div className="bp-bar systolic" 
             style={{ 
               height: `${systolicPercentage}%`, 
               backgroundColor: getSystolicColor() 
             }}>
          <span>{systolic}</span>
        </div>
        <div className="bp-bar diastolic" 
             style={{ 
               height: `${diastolicPercentage}%`, 
               backgroundColor: getDiastolicColor() 
             }}>
          <span>{diastolic}</span>
        </div>
      </div>
      <div className="bp-labels">
        <div>Systolic</div>
        <div>Diastolic</div>
      </div>
    </div>
  );
};

// Temperature Visualization
const TemperatureVisual = ({ temperature }) => {
  // Calculate temperature visualization
  const minTemp = 35; // °C
  const maxTemp = 40; // °C
  let percentage = Math.max(0, Math.min(100, ((temperature - minTemp) / (maxTemp - minTemp)) * 100));
  
  // Determine color based on temperature
  const getColor = () => {
    if (temperature < 36.5) return '#3498db'; // Low - blue
    if (temperature > 37.5) return '#e74c3c'; // High - red
    return '#2ecc71'; // Normal - green
  };
  
  return (
    <div className="temperature-visual">
      <div className="thermometer">
        <div className="thermometer-bulb"></div>
        <div className="thermometer-stem">
          <div className="thermometer-fill" 
               style={{ 
                 height: `${percentage}%`, 
                 backgroundColor: getColor() 
               }}>
          </div>
        </div>
      </div>
    </div>
  );
};

// Oxygen Saturation Visualization
const OxygenSaturationVisual = ({ value }) => {
  // Calculate opacity for pulse (make it more intense for higher values)
  const pulseOpacity = Math.max(0.2, Math.min(0.8, value / 100));
  
  // Get color based on oxygen level
  const getColor = () => {
    if (value < 90) return '#e74c3c'; // Critical - red
    if (value < 95) return '#f39c12'; // Concerning - orange
    return '#2ecc71'; // Normal - green
  };
  
  return (
    <div className="oxygen-visual">
      <div className="oxygen-pulse" 
           style={{ 
             '--pulse-color': getColor(),
             '--pulse-opacity': pulseOpacity
           }}>
        <div className="oxygen-icon">O₂</div>
      </div>
    </div>
  );
};

// Pain Score Visualization
const PainScoreVisual = ({ score }) => {
  // Map pain scores to emoji and colors
  const painFaces = [
    { emoji: "😊", color: "#2ecc71" }, // 0
    { emoji: "🙂", color: "#7fd857" }, // 1
    { emoji: "😐", color: "#a5d443" }, // 2
    { emoji: "🙁", color: "#c6cb31" }, // 3
    { emoji: "😟", color: "#e7c131" }, // 4
    { emoji: "😣", color: "#e9a632" }, // 5
    { emoji: "😖", color: "#e88c34" }, // 6
    { emoji: "😫", color: "#e67136" }, // 7
    { emoji: "😩", color: "#e55837" }, // 8
    { emoji: "😭", color: "#e44038" }, // 9
    { emoji: "🤯", color: "#e32839" }  // 10
  ];
  
  // Get the appropriate face for the score
  const faceIndex = Math.max(0, Math.min(10, Math.floor(score)));
  const { emoji, color } = painFaces[faceIndex];
  
  return (
    <div className="pain-visual" style={{ color }}>
      <div className="pain-face">{emoji}</div>
      <div className="pain-scale">
        <div className="pain-scale-bar" style={{ width: `${score * 10}%`, backgroundColor: color }}></div>
      </div>
    </div>
  );
};

export default VitalSigns;