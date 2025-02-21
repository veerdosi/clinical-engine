import React, { useEffect, useState } from 'react';
import { getLabReport } from './api';
import './LabAnalysis.css';

const LabAnalysis = () => {
  const [labReport, setLabReport] = useState("");

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getLabReport();
        setLabReport(data.report);
      } catch (error) {
        setLabReport("Error fetching lab report.");
      }
    };
    fetchReport();
  }, []);

  return (
    <div className="lab-analysis">
      <h3>Lab Work Analysis</h3>
      <div className="chart-placeholder">
        <p>{labReport || "Loading lab report..."}</p>
      </div>
    </div>
  );
};

export default LabAnalysis;
