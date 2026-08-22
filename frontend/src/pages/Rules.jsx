import React, { useState, useEffect } from 'react';
import { rulesAPI } from '../services/api';

export default function Rules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({ natural_language: '', priority: 50 });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const res = await rulesAPI.getAllRules();
      setRules(res.data);
    } catch (error) {
      setError('Error fetching rules');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      await rulesAPI.createRule(formData.natural_language, formData.priority);
      setFormData({ natural_language: '', priority: 50 });
      setShowCreateForm(false);
      fetchRules();
    } catch (error) {
      setError(error.response?.data?.detail || 'Error creating rule');
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm('Are you sure?')) {
      try {
        await rulesAPI.deleteRule(ruleId);
        fetchRules();
      } catch (error) {
        setError('Error deleting rule');
      }
    }
  };

  const handleToggleStatus = async (ruleId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      await rulesAPI.updateRule(ruleId, { status: newStatus });
      fetchRules();
    } catch (error) {
      setError('Error updating rule');
    }
  };

  if (loading) return <div className="loading">Loading rules...</div>;

  return (
    <div className="rules-container">
      <div className="rules-header">
        <h1>Approval Rules</h1>
        <button className="btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? 'Cancel' : '+ Add Rule'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showCreateForm && (
        <div className="form-card">
          <h2>Create New Rule</h2>
          <form onSubmit={handleCreateRule}>
            <div className="form-group">
              <label>Natural Language Rule *</label>
              <textarea
                value={formData.natural_language}
                onChange={(e) => setFormData({...formData, natural_language: e.target.value})}
                placeholder="e.g., Auto-approve expenses under $500 for Sales."
                required
              />
              <small>Describe the rule in plain English</small>
            </div>

            <div className="form-group">
              <label>Priority (0-100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={formData.priority}
                onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
              />
              <small>Higher priority rules take precedence</small>
            </div>

            <button type="submit" className="btn-primary">Create Rule</button>
          </form>
        </div>
      )}

      <div className="rules-table">
        {rules.length === 0 ? (
          <p className="empty-message">No rules configured yet. Create one to get started.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Rule</th>
                <th>Decision</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.map(rule => (
                <tr key={rule.id}>
                  <td>
                    <strong>{rule.name}</strong>
                    <small>{rule.natural_language}</small>
                  </td>
                  <td>
                    <span className={`badge badge-${rule.decision.toLowerCase()}`}>
                      {rule.decision}
                    </span>
                  </td>
                  <td>{rule.priority}</td>
                  <td>
                    <span className={`status-badge ${rule.status}`}>
                      {rule.status}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="btn-small"
                      onClick={() => handleToggleStatus(rule.id, rule.status)}
                    >
                      {rule.status === 'active' ? 'Disable' : 'Enable'}
                    </button>
                    <button 
                      className="btn-small btn-danger"
                      onClick={() => handleDeleteRule(rule.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
