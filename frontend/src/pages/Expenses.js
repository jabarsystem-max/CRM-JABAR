import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Expenses = () => {
  const { token } = useAuth();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    category: 'Marketing',
    amount: '',
    payment_status: 'Unpaid',
    notes: ''
  });

  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API_URL}/expenses`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setExpenses(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching expenses:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/expenses`, {
        ...formData,
        amount: parseFloat(formData.amount)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ category: 'Marketing', amount: '', payment_status: 'Unpaid', notes: '' });
      fetchExpenses();
    } catch (error) {
      console.error('Error creating expense:', error);
      alert('Kunne ikke registrere utgift');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  const categories = ['COGS', 'Marketing', 'Shipping', 'Software', 'Operations'];
  const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);
  const unpaid = expenses.filter(e => e.payment_status === 'Unpaid').reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">💸 Utgifter</h1>
          <p className="page-subtitle">Administrer alle utgifter og kostnader</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny utgift</button>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">💸</div>
          <div>
            <div className="stat-value">{Math.round(totalExpenses)} kr</div>
            <div className="stat-label">Totale utgifter</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div>
            <div className="stat-value">{Math.round(unpaid)} kr</div>
            <div className="stat-label">Ubetalt</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div>
            <div className="stat-value">{expenses.length}</div>
            <div className="stat-label">Registrerte utgifter</div>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Dato</th>
              <th>Kategori</th>
              <th>Beløp</th>
              <th>Status</th>
              <th>Merknad</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map(expense => (
              <tr key={expense.id}>
                <td>{new Date(expense.date).toLocaleDateString('nb-NO')}</td>
                <td><span className="badge badge-omega">{expense.category}</span></td>
                <td><strong>{Math.round(expense.amount)} kr</strong></td>
                <td>
                  <span className={`badge badge-${expense.payment_status === 'Paid' ? 'success' : 'warning'}`}>
                    {expense.payment_status === 'Paid' ? 'Betalt' : 'Ubetalt'}
                  </span>
                </td>
                <td>{expense.notes || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny utgift</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Kategori *</label>
                <select required value={formData.category}
                  onChange={e => setFormData({...formData, category: e.target.value})} className="form-select">
                  {categories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Beløp (kr) *</label>
                <input type="number" step="0.01" required value={formData.amount}
                  onChange={e => setFormData({...formData, amount: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Betalingsstatus</label>
                <select value={formData.payment_status}
                  onChange={e => setFormData({...formData, payment_status: e.target.value})} className="form-select">
                  <option value="Unpaid">Ubetalt</option>
                  <option value="Paid">Betalt</option>
                </select>
              </div>
              <div className="form-group">
                <label>Merknad</label>
                <textarea value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})} className="form-textarea" />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Registrer utgift</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Expenses;
