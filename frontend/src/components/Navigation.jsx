import React from 'react';

export default function Navigation({ currentPage, setCurrentPage }) {
  const pages = ['Dashboard', 'Rules', 'Claims'];

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h1>Policy-Driven Approval Agent</h1>
      </div>
      
      <ul className="nav-links">
        {pages.map(page => (
          <li key={page}>
            <button
              className={currentPage === page ? 'active' : ''}
              onClick={() => setCurrentPage(page)}
            >
              {page}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
