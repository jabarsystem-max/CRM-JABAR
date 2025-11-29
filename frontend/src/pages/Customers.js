import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Customers = () => {
  const { token } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    postal_code: ''
  });

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API_URL}/customers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching customers:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/customers`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ name: '', email: '', phone: '', address: '', city: '', postal_code: '' });
      fetchCustomers();
    } catch (error) {
      console.error('Error creating customer:', error);
      alert('Kunne ikke opprette kunde');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">👥 Kunder</h1>
          <p className="page-subtitle">Administrer kunderegisteret</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Ny kunde
        </button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Navn</th>
              <th>E-post</th>
              <th>Telefon</th>
              <th>By</th>
              <th>Registrert</th>
            </tr>
          </thead>
          <tbody>
            {customers.map(customer => (
              <tr key={customer.id}>
                <td><strong>{customer.name}</strong></td>
                <td>{customer.email}</td>
                <td>{customer.phone || '-'}</td>
                <td>{customer.city || '-'}</td>
                <td>{new Date(customer.created_at).toLocaleDateString('nb-NO')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny kunde</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Navn *</label>
                <input type="text" required value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>E-post *</label>
                <input type="email" required value={formData.email}
                  onChange={e => setFormData({...formData, email: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Telefon</label>
                <input type="text" value={formData.phone}
                  onChange={e => setFormData({...formData, phone: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Adresse</label>
                <input type="text" value={formData.address}
                  onChange={e => setFormData({...formData, address: e.target.value})} className="form-input" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Postnummer</label>
                  <input type="text" value={formData.postal_code}
                    onChange={e => setFormData({...formData, postal_code: e.target.value})} className="form-input" />
                </div>
                <div className="form-group">
                  <label>By</label>
                  <input type="text" value={formData.city}
                    onChange={e => setFormData({...formData, city: e.target.value})} className="form-input" />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Opprett kunde</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;
