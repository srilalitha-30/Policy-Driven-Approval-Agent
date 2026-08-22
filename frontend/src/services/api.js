import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const rulesAPI = {
  getAllRules: () => api.get('/rules'),
  createRule: (naturalLanguage, priority) => 
    api.post('/rules', { natural_language: naturalLanguage, priority }),
  getRule: (id) => api.get(`/rules/${id}`),
  updateRule: (id, data) => api.put(`/rules/${id}`, data),
  deleteRule: (id) => api.delete(`/rules/${id}`),
};

export const claimsAPI = {
  getAllClaims: () => api.get('/claims'),
  createClaim: (claim) => api.post('/claims', claim),
  getClaim: (id) => api.get(`/claims/${id}`),
};

export const evaluationAPI = {
  evaluateClaim: (claimId) => api.post(`/evaluate/${claimId}`),
  getEvaluation: (claimId) => api.get(`/evaluations/${claimId}`),
  getAllEvaluations: () => api.get('/evaluations'),
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard'),
};
