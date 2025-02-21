import React from 'react';
import './PatientProfile.css';

const PatientProfile = ({ patient }) => {
  return (
    <div className="patient-profile">
      <h2>{patient.name}</h2>
      <p><strong>Age:</strong> {patient.age}</p>
      <p><strong>Gender:</strong> {patient.gender}</p>
      <p><strong>History:</strong> {patient.history}</p>
      <p><strong>Presenting Complaint:</strong> {patient.presentingComplaint}</p>
    </div>
  );
};

export default PatientProfile;
