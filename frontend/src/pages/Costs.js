import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Costs = () => {
  const { token } = useAuth();
  const [costs, setCosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    category: 'marketing',
    description: '',
    amount: '',
    recurring: false
  });

  const fetchCosts = async () => {
    try {
      const response = await axios.get(`${API_URL}/costs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCosts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching costs:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCosts();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/costs`, {
        ...formData,
        amount: parseFloat(formData.amount)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ category: 'marketing', description: '', amount: '', recurring: false });
      fetchCosts();
    } catch (error) {
      console.error('Error creating cost:', error);
      alert('Kunne ikke registrere kostnad');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  const totalCosts = costs.reduce((sum, cost) => sum + cost.amount, 0);
  const recurringCosts = costs.filter(c => c.recurring).reduce((sum, cost) => sum + cost.amount, 0);

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">💸 Kostnader</h1>
          <p className="page-subtitle">Administrer utgifter og kostnader</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny kostnad</button>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">💸</div>
          <div>
            <div className="stat-value">{Math.round(totalCosts)} kr</div>
            <div className="stat-label">Totale kostnader</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔁</div>
          <div>
            <div className="stat-value">{Math.round(recurringCosts)} kr</div>
            <div className="stat-label">Faste kostnader</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div>
            <div className="stat-value">{costs.length}</div>
            <div className="stat-label">Registrerte kostnader</div>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Kategori</th>
              <th>Beskrivelse</th>
              <th>Beløp</th>
              <th>Type</th>
              <th>Dato</th>
            </tr>
          </thead>
          <tbody>
            {costs.map(cost => (
              <tr key={cost.id}>
                <td><span className="badge badge-omega">{cost.category}</span></td>
                <td>{cost.description}</td>
                <td><strong>{Math.round(cost.amount)} kr</strong></td>
                <td>
                  {cost.recurring ? (
                    <span className="badge badge-warning">Fast</span>
                  ) : (
                    <span className="badge badge-d3">Engangskostnad</span>
                  )}
                </td>
                <td>{new Date(cost.date).toLocaleDateString('nb-NO')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny kostnad</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Kategori *</label>
                <select required value={formData.category}
                  onChange={e => setFormData({...formData, category: e.target.value})} className="form-select">
                  <option value="marketing">Markedsføring</option>
                  <option value="shipping">Frakt</option>
                  <option value="software">Programvare</option>
                  <option value="rent">Husleie</option>
                  <option value="utilities">Strøm/Internett</option>
                  <option value="salaries">Lønn</option>
                  <option value="other">Annet</option>
                </select>
              </div>
              <div className="form-group">
                <label>Beskrivelse *</label>
                <input type="text" required value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Beløp (kr) *</label>
                <input type="number" step="0.01" required value={formData.amount}
                  onChange={e => setFormData({...formData, amount: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input type="checkbox" checked={formData.recurring}
                    onChange={e => setFormData({...formData, recurring: e.target.checked})} />
                  <span>Fast kostnad (månedlig)</span>
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Registrer kostnad</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Costs;
