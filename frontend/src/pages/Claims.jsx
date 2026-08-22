import React, { useState, useEffect } from 'react';
import { claimsAPI, evaluationAPI } from '../services/api';

export default function Claims() {
  const [claims, setClaims] = useState([]);
  const [evaluations, setEvaluations] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    employee: '',
    department: '',
    category: '',
    amount: '',
    date: new Date().toISOString().split('T')[0],
    description: ''
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClaims();
    fetchEvaluations();
  }, []);

  const fetchClaims = async () => {
    try {
      const res = await claimsAPI.getAllClaims();
      setClaims(res.data);
    } catch (error) {
      setError('Error fetching claims');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvaluations = async () => {
    try {
      const res = await evaluationAPI.getAllEvaluations();
      const evalMap = {};
      res.data.forEach(evaluation => {
        evalMap[evaluation.claim_id] = evaluation;
      });
      setEvaluations(evalMap);
    } catch (error) {
      console.error('Error fetching evaluations:', error);
    }
  };

  const handleEvaluateClaim = async (claimId) => {
    try {
      await evaluationAPI.evaluateClaim(claimId);
      fetchEvaluations();
    } catch (error) {
      setError('Error evaluating claim');
    }
  };

  const handleCreateClaim = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await claimsAPI.createClaim({
        ...formData,
        amount: parseFloat(formData.amount)
      });
      
      setFormData({
        id: '',
        employee: '',
        department: '',
        category: '',
        amount: '',
        date: new Date().toISOString().split('T')[0],
        description: ''
      });
      setShowCreateForm(false);
      fetchClaims();
    } catch (error) {
      setError(error.response?.data?.detail || 'Error creating claim');
    }
  };

  if (loading) return <div className="loading">Loading claims...</div>;

  const selectedEval = selectedClaim ? evaluations[selectedClaim.id] : null;

  return (
    <div className="claims-container">
      <div className="claims-header">
        <h1>Expense Claims</h1>
        <button className="btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
          {showCreateForm ? 'Cancel' : '+ Add Claim'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showCreateForm && (
        <div className="form-card">
          <h2>Create New Claim</h2>
          <form onSubmit={handleCreateClaim}>
            <div className="form-row">
              <div className="form-group">
                <label>Claim ID *</label>
                <input
                  type="text"
                  value={formData.id}
                  onChange={(e) => setFormData({...formData, id: e.target.value})}
                  placeholder="EXP-001"
                  required
                />
              </div>
              <div className="form-group">
                <label>Employee *</label>
                <input
                  type="text"
                  value={formData.employee}
                  onChange={(e) => setFormData({...formData, employee: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({...formData, department: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Category *</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Amount ($) *</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData({...formData, amount: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Date *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </div>

            <button type="submit" className="btn-primary">Create Claim</button>
          </form>
        </div>
      )}

      <div className="claims-content">
        <div className="claims-list">
          {claims.length === 0 ? (
            <p className="empty-message">No claims yet. Create one to get started.</p>
          ) : (
            claims.map(claim => {
              const evaluation = evaluations[claim.id];
              return (
                <div
                  key={claim.id}
                  className={`claim-card ${selectedClaim?.id === claim.id ? 'selected' : ''}`}
                  onClick={() => setSelectedClaim(claim)}
                >
                  <div className="claim-header">
                    <h3>{claim.id}</h3>
                    {evaluation && (
                      <span className={`badge badge-${evaluation.decision.toLowerCase()}`}>
                        {evaluation.decision}
                      </span>
                    )}
                  </div>
                  
                  <p><strong>Employee:</strong> {claim.employee}</p>
                  <p><strong>Department:</strong> {claim.department || 'N/A'}</p>
                  <p><strong>Amount:</strong> ${claim.amount.toFixed(2)}</p>
                  <p><strong>Category:</strong> {claim.category}</p>

                  {!evaluation && (
                    <button 
                      className="btn-small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEvaluateClaim(claim.id);
                      }}
                    >
                      Evaluate
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {selectedClaim && (
          <div className="claim-details">
            <h2>Claim Details: {selectedClaim.id}</h2>
            
            <div className="details-card">
              <p><strong>Employee:</strong> {selectedClaim.employee}</p>
              <p><strong>Department:</strong> {selectedClaim.department || 'Not specified'}</p>
              <p><strong>Category:</strong> {selectedClaim.category}</p>
              <p><strong>Amount:</strong> ${selectedClaim.amount.toFixed(2)}</p>
              <p><strong>Currency:</strong> {selectedClaim.currency}</p>
              <p><strong>Date:</strong> {selectedClaim.date}</p>
              <p><strong>Description:</strong> {selectedClaim.description}</p>

              {!selectedEval && (
                <button 
                  className="btn-primary"
                  onClick={() => handleEvaluateClaim(selectedClaim.id)}
                >
                  Evaluate Claim
                </button>
              )}
            </div>

            {selectedEval && (
              <div className="evaluation-card">
                <h3>Evaluation Result</h3>
                
                <div className="decision-result">
                  <span className={`badge badge-${selectedEval.decision.toLowerCase()}`}>
                    {selectedEval.decision}
                  </span>
                  <p className="timestamp">Evaluated: {new Date(selectedEval.timestamp).toLocaleString()}</p>
                </div>

                <div className="rationale">
                  <h4>Rationale</h4>
                  <p>{selectedEval.winning_rule_name}</p>
                  <pre>{selectedEval.rationale}</pre>
                </div>

                {selectedEval.evaluation_trace && selectedEval.evaluation_trace.length > 0 && (
                  <div className="trace">
                    <h4>Condition Evaluation</h4>
                    <ul>
                      {selectedEval.evaluation_trace.map((trace, idx) => (
                        <li key={idx} className={trace.result ? 'match' : 'no-match'}>
                          <strong>{trace.condition}</strong>
                          <br />
                          Actual Value: {typeof trace.actual_value === 'object' 
                            ? JSON.stringify(trace.actual_value) 
                            : trace.actual_value}
                          <br />
                          Result: {trace.result ? '✓ True' : '✗ False'}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedEval.matched_rules && selectedEval.matched_rules.length > 1 && (
                  <div className="matched-rules">
                    <h4>All Matched Rules</h4>
                    <ul>
                      {selectedEval.matched_rules.map((rule, idx) => (
                        <li key={idx}>
                          <strong>{rule.rule_name}</strong> 
                          <span className={`badge badge-${rule.decision.toLowerCase()}`}>
                            {rule.decision}
                          </span>
                          Priority: {rule.priority}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
