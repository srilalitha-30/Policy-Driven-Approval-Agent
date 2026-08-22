import React, { useState } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import Rules from './pages/Rules';
import Claims from './pages/Claims';
import './styles.css';

function App() {
  const [currentPage, setCurrentPage] = useState('Dashboard');

  const renderPage = () => {
    switch (currentPage) {
      case 'Dashboard':
        return <Dashboard />;
      case 'Rules':
        return <Rules />;
      case 'Claims':
        return <Claims />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app">
      <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
