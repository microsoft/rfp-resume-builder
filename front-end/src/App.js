import React, { useState } from 'react';
import Layout from './components/layout/Layout';
import MainPage from './pages/MainPage';
import RFPUploadPage from './pages/RFPUploadPage';
import EmployeeMatchingPage from './pages/EmployeeMatchingPage';
import { RFPListProvider } from './components/rfp/RFPListContext';


const App = () => {
  const [activePage, setActivePage] = useState('Main');

  const pages = ['Main', 'RFP Upload', 'Employee Matching'];

  const renderActivePage = () => {
    switch (activePage) {
      case 'Main':
        return <MainPage setActivePage={setActivePage} />;
      case 'RFP Upload':
        return <RFPUploadPage />;
      case 'Employee Matching':
          return <EmployeeMatchingPage />;
      default:
        return null;
    }
  };

  return (
    <RFPListProvider>
      <Layout pages={pages} activePage={activePage} setActivePage={setActivePage}>
        {renderActivePage()}
      </Layout>
    </RFPListProvider>
  );
};

export default App;