import React from 'react';
import NewWindow from 'react-new-window';

const ResumeViewer = ({ resumeName, isEnhanced, isWindowOpen, onClose }) => {
  if (!resumeName || !isWindowOpen) {
    return null;
  }

  const pdfUrl = `http://localhost:5000/resume?resumeName=${resumeName}`;

  return (
    <NewWindow onUnload={onClose}>
      <div>
        <iframe src={pdfUrl} width="100%" height="600px" title="Resume Viewer"></iframe>
      </div>
    </NewWindow>
  );
};

export default ResumeViewer;