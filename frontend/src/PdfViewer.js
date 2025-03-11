import React, { useState } from 'react';

const PdfViewer = ({ pdfUrl }) => {
  const [viewerType, setViewerType] = useState('iframe');
  
  if (!pdfUrl) return null;

  // Remove any leading slash and add the backend URL
  const cleanUrl = pdfUrl.replace(/^\//, '');
  // const fullUrl = `http://localhost:5000/${cleanUrl}`;
  const urlWithTimestamp = `${cleanUrl}?t=${new Date().getTime()}`;

  const renderViewer = () => {
    switch (viewerType) {
      case 'iframe':
        return (
          <iframe
            src={urlWithTimestamp}
            title="Lab Report PDF"
            width="100%"
            height="100%"
            style={{ border: '1px solid #ccc' }}
          />
        );
      case 'embed':
        return (
          <embed
            src={urlWithTimestamp}
            type="application/pdf"
            width="100%"
            height="100%"
          />
        );
      case 'object':
        return (
          <object
            data={urlWithTimestamp}
            type="application/pdf"
            width="100%"
            height="100%"
          >
            <p>PDF cannot be displayed</p>
          </object>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <div style={{ marginBottom: '10px' }}>
        <button onClick={() => setViewerType('iframe')}>Try iframe</button>
        <button onClick={() => setViewerType('embed')}>Try embed</button>
        <button onClick={() => setViewerType('object')}>Try object</button>
        <a 
          href={urlWithTimestamp}
          target="_blank"
          rel="noopener noreferrer"
          style={{ marginLeft: '10px' }}
        >
          Open PDF in new tab
        </a>
      </div>
      {renderViewer()}
    </div>
  );
};

export default PdfViewer;