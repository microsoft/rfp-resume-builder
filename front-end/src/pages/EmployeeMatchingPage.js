import React, { useState } from 'react';
import { FileText, Users, ExternalLink, Briefcase, Star } from 'lucide-react';
import RFPSelector from '../components/rfp/RFPSelector';

const EmployeeMatchingPage = () => {
  const [selectedRFP, setSelectedRFP] = useState(null);
  const [matchingResults, setMatchingResults] = useState([]);
  const [refineSearch, setRefineSearch] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleRFPSelect = (rfpName) => {
    setSelectedRFP(rfpName);
  };

  const handleRunMatching = async () => {
    if (!selectedRFP) {
      alert("Please select an RFP before running the matching process.");
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rfpName: selectedRFP,
          feedback: refineSearch,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setMatchingResults(data.results);
      } else {
        alert(data.error || 'An error occurred during the search');
      }
    } catch (error) {
      console.error('Error during search:', error);
      alert('An error occurred during the search');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResumeClick = (resumeName) => {
    // TODO: Implement the logic to fetch and display the resume
    console.log(`Fetching resume: ${resumeName}`);
  };

  return (
    <div className="flex flex-col h-full pt-4">
      <div className="text-center mb-8 pb-2">
        <div className="flex justify-center items-center mb-2">
          <Users className="text-blue-400 mr-2" size={36} />
          <h1 className="text-4xl font-bold leading-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
            Employee Matching
          </h1>
        </div>
        <p className="text-lg font-semibold mt-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-purple-400">
          Find the right people for your proposal
        </p>
      </div>
      <div className="flex flex-1 px-4 pb-16">
        <div className="w-64 pr-4 flex flex-col space-y-4">
          <RFPSelector
            selectedRFPs={selectedRFP}
            onSelectRFP={handleRFPSelect}
            multiSelect={false}
          />
          <button
            onClick={handleRunMatching}
            className={`w-full bg-blue-600 hover:bg-green text-white font-bold py-2 px-4 rounded-full transition duration-300`}
          >
            Run Matching
          </button>
          <div className="bg-gray-800 bg-opacity-50 rounded-xl p-4 shadow-lg border border-gray-700">
            <h2 className="text-xl font-semibold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
              Refine Search
            </h2>
            <textarea
              className="w-full h-24 bg-gray-700 bg-opacity-50 rounded-lg p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Let me know if I need to refine my search"
              value={refineSearch}
              onChange={(e) => setRefineSearch(e.target.value)}
            ></textarea>
          </div>
        </div>

        <div className="flex-1 px-4">
          <div className="bg-gray-800 bg-opacity-50 rounded-xl p-6 shadow-lg h-[calc(100%-4rem)] border border-gray-700">
            <h2 className="text-2xl font-semibold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
              Results
            </h2>
            {isLoading ? (
              <p className="text-gray-400 text-lg">Searching...</p>
            ) : matchingResults.length > 0 ? (
              <div className="space-y-4 overflow-y-auto h-[calc(100%-3rem)]">
                {matchingResults.map((result, index) => (
                  <div key={index} className="bg-gray-700 bg-opacity-50 rounded-lg p-4 hover:bg-opacity-70 transition-all duration-300">
                    <div className="flex justify-between items-start">
                      <div className="flex-grow">
                        <div className="flex items-center space-x-2">
                          <FileText className="text-blue-400 flex-shrink-0" size={20} />
                          <button
                            onClick={() => handleResumeClick(result.name)}
                            className="text-blue-400 text-lg font-semibold hover:text-blue-300 transition duration-300 flex items-center"
                          >
                            {result.name}
                            <ExternalLink className="ml-2 h-4 w-4" />
                          </button>
                        </div>
                        <div className="flex items-center mt-1 text-gray-300">
                          <Briefcase className="mr-2" size={16} />
                          <span className="font-medium">{result.jobTitle}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1 bg-blue-500 bg-opacity-20 rounded-full px-3 py-1">
                        <Star className="text-yellow-400" size={16} />
                        <span className="text-sm font-medium text-blue-300">{result.experienceLevel}</span>
                      </div>
                    </div>
                    <p className="mt-2 text-gray-400 text-sm">{result.explanation}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-lg">Run matching to see results</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeMatchingPage;