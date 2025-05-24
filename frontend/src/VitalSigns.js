import React, { useState, useEffect, useRef } from 'react';
import './VitalSigns.css';

const VitalSigns = ({ vitals: propsVitals }) => {
  // State to hold fetched vital signs data
  const [vitals, setVitals] = useState(null);

  // Fetch vital signs data when the component mounts
  useEffect(() => {
    const fetchVitalSigns = async () => {
      try {
        const response = await fetch('/api/physical-exam', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ system: 'vital_signs' })
        });
        if (!response.ok) {
          throw new Error('Failed to fetch vital signs');
        }
        const data = await response.json();

        // If backend returns structured vital signs, use them; otherwise generate random ones
        if (data.findings && typeof data.findings === 'object' && !Array.isArray(data.findings)) {
          setVitals(data.findings);
        } else {
          // Don't generate random values, use null to show we need real data
          console.log('No structured vital signs from backend, data:', data);
          setVitals(null);
        }
      } catch (err) {
        console.error('Error fetching vital signs:', err);
        // On error, don't generate random values
        setVitals(null);
      }
    };

    // Use props vitals if provided, otherwise fetch from API
    if (propsVitals && typeof propsVitals === 'object') {
      setVitals(propsVitals);
    } else {
      fetchVitalSigns();
    }
  }, [propsVitals]);

  // Default vital sign values (only used if no real data available)
  const defaultVitals = {
    HR: "72 bpm",
    BP: "120/80 mmHg",
    RR: "16 breaths/min",
    Temp: "37.0 °C",
    SpO2: "98%",
    Pain: "0/10"
  };

  // Use actual vitals if available, otherwise use defaults
  const currentVitals = vitals || defaultVitals;

  // Format vital signs for display - handle both structured data and string formats
  const formatVitalSigns = (vitals) => {
    // Handle different vital signs formats from backend/Perplexity
    const hr = vitals.HR || vitals.heart_rate || vitals.hr || vitals['Heart Rate'] || defaultVitals.HR;
    const bp = vitals.BP || vitals.blood_pressure || vitals.bp || vitals['Blood Pressure'] || defaultVitals.BP;
    const rr = vitals.RR || vitals.respiratory_rate || vitals.rr || vitals['Respiratory Rate'] || defaultVitals.RR;
    const temp = vitals.Temp || vitals.Temperature || vitals.temperature || vitals.temp || vitals['Temperature'] || defaultVitals.Temp;
    const spo2 = vitals.SpO2 || vitals.oxygen_saturation || vitals.spo2 || vitals['Oxygen Saturation'] || vitals['SpO2'] || defaultVitals.SpO2;
    const pain = vitals.Pain || vitals.pain_score || vitals.pain || vitals['Pain Score'] || vitals['Pain'] || defaultVitals.Pain;

    return {
      HR: typeof hr === 'string' ? hr : `${hr} bpm`,
      BP: typeof bp === 'string' ? bp : `${bp} mmHg`,
      RR: typeof rr === 'string' ? rr : `${rr} breaths/min`,
      Temp: typeof temp === 'string' ? temp : `${temp} °C`,
      SpO2: typeof spo2 === 'string' ? spo2 : `${spo2}%`,
      Pain: typeof pain === 'string' ? pain : `${pain}/10`
    };
  };

  const allVitals = formatVitalSigns(currentVitals);

  return (
    <div className="vital-signs-dashboard">
      <h3 className="vital-signs-title">Vital Signs Monitor</h3>
      <div className="vital-signs-grid">
        {/* Heart Rate Monitor */}
        <div className={`vital-sign-card ${(parseInt(allVitals.HR) < 60 || parseInt(allVitals.HR) > 100) ? 'abnormal' : ''}`}>
          <div className="vital-sign-header">
            <h4>Heart Rate</h4>
            <span className="vital-value">{allVitals.HR}</span>
          </div>
          <div className="vital-visualization">
            <HeartRateMonitor rate={parseInt(allVitals.HR) || 72} />
          </div>
        </div>

        {/* Blood Pressure */}
        {(() => {
          const bpMatch = allVitals.BP.match(/(\d+)\/(\d+)/);
          const systolic = bpMatch ? parseInt(bpMatch[1]) : 120;
          const diastolic = bpMatch ? parseInt(bpMatch[2]) : 80;
          const isBPAbnormal = systolic < 90 || systolic > 140 || diastolic < 60 || diastolic > 90;
          return (
            <div className={`vital-sign-card ${isBPAbnormal ? 'abnormal' : ''}`}>
              <div className="vital-sign-header">
                <h4>Blood Pressure</h4>
                <span className="vital-value">{allVitals.BP}</span>
              </div>
              <div className="vital-visualization">
                <BloodPressureVisual systolic={systolic} diastolic={diastolic} />
              </div>
            </div>
          );
        })()}

        {/* Respiratory Rate */}
        <div className={`vital-sign-card ${(() => {
            const rr = parseInt(allVitals.RR) || 16;
            return (rr < 12 || rr > 20) ? 'abnormal' : '';
          })()}`}>
          <div className="vital-sign-header">
            <h4>Respiratory Rate</h4>
            <span className="vital-value">{allVitals.RR}</span>
          </div>
          <div className="vital-visualization">
            <RespiratoryRateVisual rate={parseInt(allVitals.RR) || 16} />
          </div>
        </div>

        {/* Temperature */}
        <div className={`vital-sign-card ${(() => {
            const tempMatch = allVitals.Temp.match(/(\d+\.?\d*)/);
            const temperature = tempMatch ? parseFloat(tempMatch[0]) : 37.0;
            return (temperature < 36.5 || temperature > 37.5) ? 'abnormal' : '';
          })()}`}>
          <div className="vital-sign-header">
            <h4>Temperature</h4>
            <span className="vital-value">{allVitals.Temp}</span>
          </div>
          <div className="vital-visualization">
            <TemperatureVisual temperature={parseFloat((allVitals.Temp.match(/(\d+\.?\d*)/) || [])[0]) || 37.0} />
          </div>
        </div>

        {/* Oxygen Saturation */}
        <div className={`vital-sign-card ${(() => {
            const o2 = parseInt(allVitals.SpO2) || 98;
            return (o2 < 95) ? 'abnormal' : '';
          })()}`}>
          <div className="vital-sign-header">
            <h4>O₂ Saturation</h4>
            <span className="vital-value">{allVitals.SpO2}</span>
          </div>
          <div className="vital-visualization">
            <OxygenSaturationVisual value={parseInt(allVitals.SpO2) || 98} />
          </div>
        </div>

        {/* Pain Score */}
        <div className="vital-sign-card">
          <div className="vital-sign-header">
            <h4>Pain Score</h4>
            <span className="vital-value">{allVitals.Pain}</span>
          </div>
          <div className="vital-visualization">
            <PainScoreVisual score={parseInt(allVitals.Pain) || 0} />
          </div>
        </div>
      </div>
    </div>
  );
};

// Heart Rate Monitor Component
const HeartRateMonitor = ({ rate }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const beatDuration = 60000 / rate; // ms per beat
    const pointsPerBeat = 100;
    const totalPoints = 150;

    // Generate one ECG pattern
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
      pattern.push(2);   // Q
      pattern.push(25);  // R
      pattern.push(0);   // S
      // ST segment
      for (let i = 0; i < 10; i++) {
        pattern.push(5 + Math.sin(i * 0.1) * 1);
      }
      // T wave
      for (let i = 0; i < 15; i++) {
        pattern.push(5 + Math.sin(i * 0.2) * 4);
      }
      // TP segment (baseline)
      const remaining = pointsPerBeat - pattern.length;
      for (let i = 0; i < remaining; i++) {
        pattern.push(5);
      }
      return pattern;
    };

    const basePattern = generateECGPattern();
    let animationId;
    let currentPoint = 0;
    let points = Array(totalPoints).fill(5);

    const animate = () => {
      const patternPos = currentPoint % basePattern.length;
      points = [...points.slice(1), basePattern[patternPos]];
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);
        ctx.beginPath();
        ctx.strokeStyle = '#4aed4f';
        ctx.lineWidth = 2;
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
      const frameDelay = beatDuration / pointsPerBeat;
      animationId = setTimeout(animate, frameDelay);
    };

    animate();
    return () => clearTimeout(animationId);
  }, [rate]);

  return (
    <div className="heart-rate-monitor">
      <canvas ref={canvasRef} width={300} height={80} />
    </div>
  );
};

// Respiratory Rate Visualization Component
const RespiratoryRateVisual = ({ rate }) => {
  const animationDuration = 60 / rate; // seconds per breath cycle
  return (
    <div className="respiratory-visual" style={{ '--breathing-duration': `${animationDuration}s` }}>
      <div className="lungs-container">
        <div className="lung left-lung"></div>
        <div className="lung right-lung"></div>
      </div>
    </div>
  );
};

// Blood Pressure Visualization Component
const BloodPressureVisual = ({ systolic, diastolic }) => {
  const maxSystolic = 180;
  const systolicPercentage = Math.min(100, (systolic / maxSystolic) * 100);
  const diastolicPercentage = Math.min(100, (diastolic / maxSystolic) * 100);

  const getSystolicColor = () => {
    if (systolic < 90) return '#3498db';
    if (systolic > 140) return '#e74c3c';
    return '#2ecc71';
  };

  const getDiastolicColor = () => {
    if (diastolic < 60) return '#3498db';
    if (diastolic > 90) return '#e74c3c';
    return '#2ecc71';
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

// Temperature Visualization Component
const TemperatureVisual = ({ temperature }) => {
  const minTemp = 35; // °C
  const maxTemp = 40; // °C
  let percentage = Math.max(0, Math.min(100, ((temperature - minTemp) / (maxTemp - minTemp)) * 100));

  const getColor = () => {
    if (temperature < 36.5) return '#3498db';
    if (temperature > 37.5) return '#e74c3c';
    return '#2ecc71';
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

// Oxygen Saturation Visualization Component
const OxygenSaturationVisual = ({ value }) => {
  const pulseOpacity = Math.max(0.2, Math.min(0.8, value / 100));

  const getColor = () => {
    if (value < 90) return '#e74c3c';
    if (value < 95) return '#f39c12';
    return '#2ecc71';
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

// Pain Score Visualization Component
const PainScoreVisual = ({ score }) => {
  const painFaces = [
    { emoji: "😊", color: "#2ecc71" },
    { emoji: "🙂", color: "#7fd857" },
    { emoji: "😐", color: "#a5d443" },
    { emoji: "🙁", color: "#c6cb31" },
    { emoji: "😟", color: "#e7c131" },
    { emoji: "😣", color: "#e9a632" },
    { emoji: "😖", color: "#e88c34" },
    { emoji: "😫", color: "#e67136" },
    { emoji: "😩", color: "#e55837" },
    { emoji: "😭", color: "#e44038" },
    { emoji: "🤯", color: "#e32839" }
  ];

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
