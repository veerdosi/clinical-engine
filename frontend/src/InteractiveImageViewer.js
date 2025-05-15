import React, { useState, useRef } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { Stage, Layer, Line, Text } from 'react-konva';
import './InteractiveImageViewer.css';

const InteractiveImageViewer = ({
  imageUrl,
  imagingType,
  showReferenceImage = true,
  showTools = true
}) => {
  const [activeTab, setActiveTab] = useState('patient');
  const [tool, setTool] = useState('pan'); // pan, zoom, measure
  const [measureStart, setMeasureStart] = useState(null);
  const [measureEnd, setMeasureEnd] = useState(null);
  const [measureLines, setMeasureLines] = useState([]);
  const [zoomFactor, setZoomFactor] = useState(1);

  const stageRef = useRef(null);
  const containerRef = useRef(null);

  // Map the imaging types to their reference image paths
  const referenceImageMap = {
    'CXR': '/assets/cxr.jpeg',
    'X-ray': '/assets/cxr.jpeg', // Default to chest X-ray
    'CT Chest': '/assets/cct.jpg',
    'CT Abdomen/Pelvis': '/assets/act.jpg',
    'CT Head': '/assets/cct.jpg',
    'MRI Brain': '/assets/bmri.jpeg',
    'MRI Spine': '/assets/bmri.jpeg',
    'Ultrasound Abdomen': '/assets/aus.jpeg',
    'Echocardiogram': '/assets/echo.png',
    'ECG': '/assets/ecg.jpg'
  };

  // Determine the reference image based on the imaging type
  const referenceImageUrl = referenceImageMap[imagingType] || '/assets/cxr.jpeg';

  const handleMeasureMouseDown = (e) => {
    if (tool !== 'measure') return;

    // Get the position of the click relative to the stage
    const stage = stageRef.current;
    const pointerPos = stage.getPointerPosition();

    if (!measureStart) {
      setMeasureStart(pointerPos);
    } else {
      setMeasureEnd(pointerPos);
      setMeasureLines(prevLines => [...prevLines, {
        start: measureStart,
        end: pointerPos,
        length: calculateDistance(measureStart, pointerPos)
      }]);
      setMeasureStart(null);
    }
  };

  const handleMeasureMouseMove = (e) => {
    if (tool !== 'measure' || !measureStart) return;

    const stage = stageRef.current;
    const pointerPos = stage.getPointerPosition();
    setMeasureEnd(pointerPos);
  };

  const calculateDistance = (p1, p2) => {
    if (!p1 || !p2) return 0;
    // This is a simple pixel distance. In a real medical app, you would convert to mm or cm
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy).toFixed(2);
  };

  const clearMeasurements = () => {
    setMeasureLines([]);
    setMeasureStart(null);
    setMeasureEnd(null);
  };

  const getCurrentImageUrl = () => {
    return activeTab === 'patient' ? imageUrl : referenceImageUrl;
  };

  return (
    <div className="interactive-image-viewer" ref={containerRef}>
      {showTools && (
        <div className="image-viewer-toolbar">
          {showReferenceImage && (
            <div className="image-tabs">
              <button
                className={activeTab === 'patient' ? 'active' : ''}
                onClick={() => setActiveTab('patient')}
              >
                Patient Image
              </button>
              <button
                className={activeTab === 'reference' ? 'active' : ''}
                onClick={() => setActiveTab('reference')}
              >
                Reference Normal
              </button>
            </div>
          )}

          <div className="tool-buttons">
            <button
              className={tool === 'pan' ? 'active' : ''}
              onClick={() => setTool('pan')}
              title="Pan"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M12.5 3a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1h5zm0 3a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1h5zm.5 3.5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h5a.5.5 0 0 0 .5-.5zm-.5 2.5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1h5z"/>
                <path d="M3 0h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2v-1h1v1a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v1H1V2a2 2 0 0 1 2-2z"/>
              </svg>
            </button>
            <button
              className={tool === 'zoom' ? 'active' : ''}
              onClick={() => setTool('zoom')}
              title="Zoom"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11zM13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0z"/>
                <path d="M10.344 11.742c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1 6.538 6.538 0 0 1-1.398 1.4z"/>
                <path fillRule="evenodd" d="M6.5 3a.5.5 0 0 1 .5.5V6h2.5a.5.5 0 0 1 0 1H7v2.5a.5.5 0 0 1-1 0V7H3.5a.5.5 0 0 1 0-1H6V3.5a.5.5 0 0 1 .5-.5z"/>
              </svg>
            </button>
            <button
              className={tool === 'measure' ? 'active' : ''}
              onClick={() => setTool('measure')}
              title="Measure"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 0a1 1 0 0 1 1 1v6h1.25a.75.75 0 0 1 0 1.5H9v1h1.25a.75.75 0 0 1 0 1.5H9v1h1.25a.75.75 0 0 1 0 1.5H9v1h1.25a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1 0-1.5H9v-1H7.75a.75.75 0 0 1 0-1.5H9v-1H7.75a.75.75 0 0 1 0-1.5H9v-1H7.75a.75.75 0 0 1 0-1.5H9V1a1 1 0 0 1 1-1z"/>
              </svg>
            </button>
            <button onClick={clearMeasurements} title="Clear Measurements">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M11 1.5v1h3.5a.5.5 0 0 1 0 1h-.538l-.853 10.66A2 2 0 0 1 11.115 16h-6.23a2 2 0 0 1-1.994-1.84L2.038 3.5H1.5a.5.5 0 0 1 0-1H5v-1A1.5 1.5 0 0 1 6.5 0h3A1.5 1.5 0 0 1 11 1.5Zm-5 0v1h4v-1a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5ZM4.5 5.029l.5 8.5a.5.5 0 1 0 .998-.06l-.5-8.5a.5.5 0 1 0-.998.06Zm6.53-.528a.5.5 0 0 0-.528.47l-.5 8.5a.5.5 0 0 0 .998.058l.5-8.5a.5.5 0 0 0-.47-.528ZM8 4.5a.5.5 0 0 0-.5.5v8.5a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5Z"/>
              </svg>
            </button>
          </div>
        </div>
      )}

      <div className="image-container">
        <TransformWrapper
          initialScale={1}
          minScale={0.5}
          maxScale={4}
          disabled={tool === 'measure'}
          onZoom={(ref) => setZoomFactor(ref.state.scale)}
        >
          <TransformComponent wrapperClass="transform-wrapper">
            <div className="image-stage-container">
              <Stage
                width={500}
                height={500}
                ref={stageRef}
                onMouseDown={handleMeasureMouseDown}
                onMouseMove={handleMeasureMouseMove}
                style={{ position: 'absolute', top: 0, left: 0 }}
              >
                <Layer>
                  {/* Render all saved measurement lines */}
                  {measureLines.map((line, i) => (
                    <React.Fragment key={i}>
                      <Line
                        points={[line.start.x, line.start.y, line.end.x, line.end.y]}
                        stroke="#ff0000"
                        strokeWidth={2 / zoomFactor}
                        dash={[5 / zoomFactor, 5 / zoomFactor]}
                      />
                      <Text
                        x={(line.start.x + line.end.x) / 2}
                        y={(line.start.y + line.end.y) / 2 - 10 / zoomFactor}
                        text={`${line.length} px`}
                        fontSize={16 / zoomFactor}
                        fill="#ff0000"
                      />
                    </React.Fragment>
                  ))}

                  {/* Render the current measurement line being drawn */}
                  {measureStart && measureEnd && (
                    <React.Fragment>
                      <Line
                        points={[measureStart.x, measureStart.y, measureEnd.x, measureEnd.y]}
                        stroke="#ff0000"
                        strokeWidth={2 / zoomFactor}
                        dash={[5 / zoomFactor, 5 / zoomFactor]}
                      />
                      <Text
                        x={(measureStart.x + measureEnd.x) / 2}
                        y={(measureStart.y + measureEnd.y) / 2 - 10 / zoomFactor}
                        text={`${calculateDistance(measureStart, measureEnd)} px`}
                        fontSize={16 / zoomFactor}
                        fill="#ff0000"
                      />
                    </React.Fragment>
                  )}
                </Layer>
              </Stage>
              <img
                src={getCurrentImageUrl()}
                alt={activeTab === 'patient' ? "Patient imaging result" : "Reference normal imaging"}
                className="viewer-image"
              />
            </div>
          </TransformComponent>
        </TransformWrapper>
      </div>

      <div className="image-info">
        <p><strong>{activeTab === 'patient' ? 'Patient Image' : 'Reference Normal'}</strong></p>
        <div className="zoom-info">
          <span>Zoom: {Math.round(zoomFactor * 100)}%</span>
        </div>
      </div>
    </div>
  );
};

export default InteractiveImageViewer;
