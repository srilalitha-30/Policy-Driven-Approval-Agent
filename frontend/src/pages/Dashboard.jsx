import React, { useState, useEffect } from 'react';
import { dashboardAPI, claimsAPI, evaluationAPI } from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await dashboardAPI.getStats();
      setStats(res.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="dashboard">
      <h1>Approval Agent Dashboard</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Claims</h3>
          <p className="stat-number">{stats?.total_claims || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>Total Rules</h3>
          <p className="stat-number">{stats?.total_rules || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>Active Rules</h3>
          <p className="stat-number">{stats?.active_rules || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>Total Evaluations</h3>
          <p className="stat-number">{stats?.total_evaluations || 0}</p>
        </div>
      </div>

      <div className="decisions-section">
        <h2>Decision Distribution</h2>
        <div className="decision-cards">
          <div className="decision-card approve">
            <span className="badge">APPROVE</span>
            <p className="count">{stats?.decisions_distribution?.APPROVE || 0}</p>
          </div>
          
          <div className="decision-card reject">
            <span className="badge">REJECT</span>
            <p className="count">{stats?.decisions_distribution?.REJECT || 0}</p>
          </div>
          
          <div className="decision-card escalate">
            <span className="badge">ESCALATE</span>
            <p className="count">{stats?.decisions_distribution?.ESCALATE || 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
