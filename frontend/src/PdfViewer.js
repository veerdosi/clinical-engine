import React, { useState, useEffect } from 'react';
import './PdfViewer.css';

const PdfViewer = ({ reportId, reportType, onClose }) => {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!reportId || !reportType) return;
    
    const fetchPdf = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Determine which API endpoint to use based on report type
        const endpoint = reportType === 'lab' 
          ? '/api/generate-lab-pdf'
          : '/api/generate-imaging-pdf';
        
        // Create the appropriate request body based on report type
        const requestBody = reportType === 'lab'
          ? { result_id: reportId }
          : { report_id: reportId };
        
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate PDF');
        }
        
        const data = await response.json();
        
        if (!data.pdf_url) {
          throw new Error('No PDF URL returned from server');
        }
        
        // Add a timestamp to prevent caching
        setPdfUrl(`${data.pdf_url}?t=${new Date().getTime()}`);
      } catch (err) {
        console.error('Error generating PDF:', err);
        setError(err.message || 'Failed to generate PDF');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPdf();
  }, [reportId, reportType]);

  if (loading) {
    return (
      <div className="pdf-viewer">
        <div className="pdf-viewer-header">
          <h3>Generating PDF Report</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="pdf-loading">
          <div className="pdf-loading-spinner"></div>
          <p>Generating PDF report...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pdf-viewer">
        <div className="pdf-viewer-header">
          <h3>Error</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="pdf-error">
          <p>Error generating PDF: {error}</p>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (!pdfUrl) {
    return null;
  }

  return (
    <div className="pdf-viewer">
      <div className="pdf-viewer-header">
        <h3>{reportType === 'lab' ? 'Laboratory Report' : 'Imaging Report'}</h3>
        <div className="pdf-viewer-actions">
          <a 
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="open-new-tab-btn"
          >
            Open in New Tab
          </a>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
      </div>
      <div className="pdf-frame-container">
        <iframe
          src={pdfUrl}
          title={`${reportType === 'lab' ? 'Lab' : 'Imaging'} Report PDF`}
          className="pdf-frame"
        />
      </div>
    </div>
  );
};

export default PdfViewer;