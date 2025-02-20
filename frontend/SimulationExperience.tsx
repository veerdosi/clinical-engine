import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, RefreshCw, AlertTriangle, Check, X, ThumbsUp, ThumbsDown, BarChart2 } from 'lucide-react';

const SimulationExperience = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const [timer, setTimer] = useState(300); // 5 minutes in seconds
  const [isTimerRunning, setIsTimerRunning] = useState(true);
  const [userActions, setUserActions] = useState([]);
  const [vitals, setVitals] = useState({
    heartRate: 95,
    bloodPressure: '138/88',
    oxygenSaturation: 94,
    respiratoryRate: 20,
    temperature: 99.1
  });

  // Example simulation procedure steps
  const procedureSteps = [
    {
      id: 1,
      instruction: "Prepare equipment and verify patient identity",
      correctAction: "identifyPatient",
      options: [
        { id: "identifyPatient", text: "Check ID band and confirm identity" },
        { id: "prepareAirway", text: "Prepare airway equipment" },
        { id: "administerSedation", text: "Administer sedation" },
        { id: "positionPatient", text: "Position patient" }
      ],
      hint: "Always start with patient identification for safety",
      feedback: {
        correct: "Excellent! Patient safety begins with proper identification.",
        incorrect: "Patient identification is critical before any procedure."
      }
    },
    {
      id: 2,
      instruction: "Assess airway and prepare oxygenation",
      correctAction: "assessAirway",
      options: [
        { id: "assessAirway", text: "Examine airway anatomy and position head" },
        { id: "insertLaryngoscope", text: "Insert laryngoscope" },
        { id: "administerSedation", text: "Administer sedation" },
        { id: "insertTube", text: "Insert endotracheal tube" }
      ],
      hint: "Proper assessment helps predict difficult airways",
      feedback: {
        correct: "Good assessment! This helps identify potential difficulties.",
        incorrect: "Airway assessment must precede instrument insertion."
      }
    },
    {
      id: 3,
      instruction: "Pre-oxygenate the patient",
      correctAction: "preOxygenate",
      options: [
        { id: "insertLaryngoscope", text: "Insert laryngoscope" },
        { id: "preOxygenate", text: "Deliver 100% oxygen via mask for 3 minutes" },
        { id: "administerSedation", text: "Administer sedation" },
        { id: "checkEquipment", text: "Check laryngoscope bulb" }
      ],
      hint: "Pre-oxygenation extends safe apnea time",
      feedback: {
        correct: "Perfect! Pre-oxygenation creates an oxygen reservoir in the lungs.",
        incorrect: "The patient needs pre-oxygenation before proceeding."
      }
    },
  ];

  // Handle timer countdown
  useEffect(() => {
    let interval;
    if (isTimerRunning && timer > 0) {
      interval = setInterval(() => {
        setTimer(prevTimer => prevTimer - 1);
        
        // Randomly fluctuate vitals slightly for realism
        setVitals(prevVitals => ({
          heartRate: Math.floor(prevVitals.heartRate + (Math.random() * 3 - 1.5)),
          bloodPressure: `${Math.floor(parseInt(prevVitals.bloodPressure.split('/')[0]) + (Math.random() * 4 - 2))}/${Math.floor(parseInt(prevVitals.bloodPressure.split('/')[1]) + (Math.random() * 4 - 2))}`,
          oxygenSaturation: Math.min(100, Math.floor(prevVitals.oxygenSaturation + (Math.random() * 2 - 0.75))),
          respiratoryRate: Math.floor(prevVitals.respiratoryRate + (Math.random() * 2 - 1)),
          temperature: parseFloat((prevVitals.temperature + (Math.random() * 0.2 - 0.1)).toFixed(1))
        }));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, timer]);

  // Format timer to mm:ss
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };

  const handleActionSelect = (actionId) => {
    const currentProcedureStep = procedureSteps[currentStep];
    const isCorrect = actionId === currentProcedureStep.correctAction;
    
    // Record user action
    setUserActions(prev => [...prev, {
      step: currentStep + 1,
      action: actionId,
      isCorrect,
      timeRemaining: timer
    }]);
    
    // Set feedback
    setFeedback({
      isCorrect,
      message: isCorrect ? 
        currentProcedureStep.feedback.correct : 
        currentProcedureStep.feedback.incorrect
    });
    
    // If wrong action, adjust vitals slightly negatively
    if (!isCorrect) {
      setVitals(prev => ({
        ...prev,
        heartRate: prev.heartRate + 5,
        oxygenSaturation: Math.max(85, prev.oxygenSaturation - 3)
      }));
    }
    
    // Pause timer during feedback
    setIsTimerRunning(false);
  };

  const proceedToNextStep = () => {
    if (currentStep < procedureSteps.length - 1) {
      setCurrentStep(prevStep => prevStep + 1);
      setFeedback(null);
      setShowHint(false);
      setIsTimerRunning(true);
    } else {
      // End of simulation
      console.log("Simulation complete", userActions);
    }
  };

  const resetSimulation = () => {
    setCurrentStep(0);
    setFeedback(null);
    setShowHint(false);
    setTimer(300);
    setIsTimerRunning(true);
    setUserActions([]);
    setVitals({
      heartRate: 95,
      bloodPressure: '138/88',
      oxygenSaturation: 94,
      respiratoryRate: 20,
      temperature: 99.1
    });
  };

  // Calculate warning class for vitals
  const getVitalClass = (vital, value) => {
    switch(vital) {
      case 'heartRate':
        return value > 120 || value < 60 ? 'warning' : 'normal';
      case 'oxygenSaturation':
        return value < 90 ? 'danger' : value < 94 ? 'warning' : 'normal';
      case 'respiratoryRate':
        return value > 28 || value < 10 ? 'warning' : 'normal';
      default:
        return 'normal';
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-50">
      {/* Header with controls */}
      <div className="bg-gray-900 text-white p-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button className="flex items-center space-x-2 px-3 py-1 rounded bg-gray-800 hover:bg-gray-700">
            <ChevronLeft size={16} />
            <span>Exit</span>
          </button>
          <h1 className="text-xl font-semibold">Endotracheal Intubation Simulation</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded-lg flex items-center space-x-2 ${timer < 60 ? 'bg-red-500' : 'bg-gray-800'}`}>
            <span className="text-sm font-mono">{formatTime(timer)}</span>
          </div>
          <button 
            onClick={resetSimulation}
            className="p-2 rounded hover:bg-gray-700"
            title="Reset Simulation"
          >
            <RefreshCw size={20} />
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Simulation visualization */}
        <div className="w-2/3 p-6 flex flex-col">
          <div className="bg-white rounded-lg shadow-md flex-1 p-4 flex flex-col">
            {/* Visualization area */}
            <div className="flex-1 flex items-center justify-center mb-4 border rounded-lg relative">
              {/* Would contain 3D model or animation in real implementation */}
              <div className="text-center">
                <img 
                  src="/api/placeholder/600/400" 
                  alt="Intubation Procedure Visualization" 
                  className="mb-4 mx-auto rounded"
                />
                <p className="text-gray-600 text-sm">
                  Step {currentStep + 1}: {procedureSteps[currentStep].instruction}
                </p>
              </div>
              
              {/* Patient vitals overlay */}
              <div className="absolute top-4 right-4 bg-black bg-opacity-75 text-white p-3 rounded-lg">
                <h3 className="text-sm font-semibold mb-2">Patient Vitals</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>HR:</span> 
                    <span className={getVitalClass('heartRate', vitals.heartRate)}>
                      {vitals.heartRate} bpm
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>BP:</span> 
                    <span>{vitals.bloodPressure} mmHg</span>
                  </div>
                  <div className="flex justify-between">
                    <span>SpO₂:</span> 
                    <span className={getVitalClass('oxygenSaturation', vitals.oxygenSaturation)}>
                      {vitals.oxygenSaturation}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>RR:</span> 
                    <span className={getVitalClass('respiratoryRate', vitals.respiratoryRate)}>
                      {vitals.respiratoryRate} /min
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Temp:</span> 
                    <span>{vitals.temperature}°F</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Action area */}
            <div className="bg-gray-100 rounded-lg p-4">
              {feedback ? (
                <div className={`p-4 rounded-lg mb-4 ${feedback.isCorrect ? 'bg-green-100 border border-green-300' : 'bg-red-100 border border-red-300'}`}>
                  <div className="flex items-start">
                    {feedback.isCorrect ? 
                      <Check className="text-green-600 mr-3 flex-shrink-0" /> :
                      <AlertTriangle className="text-red-600 mr-3 flex-shrink-0" />
                    }
                    <div>
                      <h3 className={`font-semibold ${feedback.isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                        {feedback.isCorrect ? 'Correct Action' : 'Incorrect Action'}
                      </h3>
                      <p className="mt-1">{feedback.message}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end">
                    <button 
                      onClick={proceedToNextStep}
                      className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 flex items-center"
                    >
                      {currentStep < procedureSteps.length - 1 ? (
                        <>Next Step <ChevronRight size={16} className="ml-1" /></>
                      ) : (
                        <>Complete Simulation <Check size={16} className="ml-1" /></>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <h3 className="font-semibold mb-3">Select the appropriate action:</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {procedureSteps[currentStep].options.map(option => (
                      <button
                        key={option.id}
                        onClick={() => handleActionSelect(option.id)}
                        className="p-3 bg-white border border-gray-300 rounded-lg text-left hover:bg-blue-50 hover:border-blue-200 transition-colors"
                      >
                        {option.text}
                      </button>
                    ))}
                  </div>
                  
                  {showHint ? (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <span className="font-semibold">Hint:</span> {procedureSteps[currentStep].hint}
                      </p>
                    </div>
                  ) : (
                    <button 
                      onClick={() => setShowHint(true)}
                      className="mt-4 text-blue-600 text-sm hover:underline"
                    >
                      Need a hint?
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* Right panel - Progress and guides */}
        <div className="w-1/3 bg-gray-100 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <h2 className="font-semibold text-lg mb-3">Procedure Progress</h2>
            <div className="space-y-2">
              {procedureSteps.map((step, index) => (
                <div 
                  key={step.id}
                  className={`flex items-center p-2 rounded-lg ${
                    index === currentStep ? 'bg-blue-100 border-l-4 border-blue-500' :
                    index < currentStep ? 'bg-gray-100' : 'text-gray-500'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 flex-shrink-0 ${
                    index < currentStep ? 'bg-green-500 text-white' :
                    index === currentStep ? 'bg-blue-500 text-white' : 'bg-gray-300 text-gray-600'
                  }`}>
                    {index < currentStep ? <Check size={14} /> : index + 1}
                  </div>
                  <span className={`text-sm ${index === currentStep ? 'font-medium' : ''}`}>
                    {step.instruction}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-4 mb-4">
            <h2 className="font-semibold text-lg mb-3">Performance</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">Accuracy</span>
                <div className="w-2/3 bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{width: `${userActions.filter(a => a.isCorrect).length / Math.max(1, userActions.length) * 100}%`}}
                  ></div>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Time Efficiency</span>
                <div className="w-2/3 bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-green-500 h-2.5 rounded-full"
                    style={{width: `${(timer / 300) * 100}%`}}
                  ></div>
                </div>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <div>
                  <span className="font-medium">Steps Completed:</span> {Math.min(currentStep, procedureSteps.length)}/{procedureSteps.length}
                </div>
                <div>
                  <span className="font-medium">Errors:</span> {userActions.filter(a => !a.isCorrect).length}
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-4">
            <h2 className="font-semibold text-lg mb-3">Reference Guide</h2>
            <div className="text-sm space-y-2">
              <p><span className="font-medium">Indication:</span> Securing airway for mechanical ventilation</p>
              <p><span className="font-medium">Contraindications:</span> Severe maxillofacial trauma, complete upper airway obstruction</p>
              <p><span className="font-medium">Key Complications:</span></p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Hypoxemia during attempt</li>
                <li>Esophageal intubation</li>
                <li>Dental trauma</li>
                <li>Laryngospasm/bronchospasm</li>
              </ul>
              <div className="mt-4">
                <button className="flex items-center text-blue-600 hover:underline">
                  <BarChart2 size={14} className="mr-1" />
                  View full procedure manual
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationExperience;
