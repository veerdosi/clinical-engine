// MedicalImaging.js
import React, { useEffect, useState } from 'react';
import { getImaging } from './api';
import './MedicalImaging.css';

const MedicalImaging = () => {
  const [imageUrl, setImageUrl] = useState("");

  useEffect(() => {
    const fetchImaging = async () => {
      try {
        const data = await getImaging();
        setImageUrl(data.image_url);
      } catch (error) {
        console.error("Imaging fetch error:", error);
      }
    };
    fetchImaging();
  }, []);

  return (
    <div className="medical-imaging">
      <h3>Medical Imaging</h3>
      {imageUrl ? (
        <img src={imageUrl} alt="Medical Imaging" />
      ) : (
        <p>Loading imaging...</p>
      )}
    </div>
  );
};

export default MedicalImaging;
