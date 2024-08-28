import React from 'react';
import { ExternalLink } from 'lucide-react';

const EnhancedResumes = ({ enhancedResults, onResumeClick, selectedEnhancedResumes, onEnhancedResumeSelect }) => {
  if (enhancedResults.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 bg-gray-800 bg-opacity-50 rounded-xl p-6 shadow-lg">
      <h3 className="text-xl font-semibold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">
        Enhanced Resumes
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {enhancedResults.map((result) => (
          <div key={result.enhancedResumeName} className="bg-gray-700 bg-opacity-40 rounded-lg p-4 hover:bg-opacity-60 transition-all duration-300 flex items-center">
            <input
              type="checkbox"
              checked={selectedEnhancedResumes.includes(result.enhancedResumeName)}
              onChange={() => onEnhancedResumeSelect(result.enhancedResumeName)}
              className="form-checkbox h-5 w-5 text-blue-600 transition duration-150 ease-in-out mr-3"
            />
            <a
              href="#"
              className="text-blue-400 hover:text-blue-300 transition duration-300 flex items-center flex-grow"
              onClick={(e) => {
                e.preventDefault();
                onResumeClick(result.enhancedResumeName);
              }}
            >
              {result.name} (Enhanced)
              <ExternalLink className="ml-2 h-4 w-4" />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EnhancedResumes;