import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Customers = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState('All');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    zip_code: '',
    city: '',
    type: 'Private',
    status: 'New',
    tags: '',
    notes: '',
    next_step: ''
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
      setFormData({ name: '', email: '', phone: '', address: '', zip_code: '', city: '', type: 'Private', status: 'New', tags: '', notes: '', next_step: '' });
      fetchCustomers();
    } catch (error) {
      console.error('Error creating customer:', error);
      alert('Kunne ikke opprette kunde');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  const statuses = ['Lead', 'New', 'Active', 'VIP', 'Inactive', 'Lost'];
  const filteredCustomers = filter === 'All' ? customers : customers.filter(c => c.status === filter);

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">👥 Kunder</h1>
          <p className="page-subtitle">Administrer kundeforhold og historikk</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny kunde</button>
      </div>

      <div className="filter-bar">
        <button className={`filter-btn ${filter === 'All' ? 'active' : ''}`} onClick={() => setFilter('All')}>Alle ({customers.length})</button>
        {statuses.map(s => (
          <button key={s} className={`filter-btn ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
            {s} ({customers.filter(c => c.status === s).length})
          </button>
        ))}
      </div>

      <div className="grid">
        {filteredCustomers.map(customer => (
          <div key={customer.id} className="card-item clickable" onClick={() => navigate(`/customers/${customer.id}`)}>
            <div className="card-header">
              <h3 className="card-title">{customer.name}</h3>
              <span className={`badge badge-${customer.status === 'VIP' ? 'success' : customer.status === 'Active' ? 'omega' : 'warning'}`}>
                {customer.status}
              </span>
            </div>
            <p className="card-text">{
              customer.type === 'Business' ? '🏛️ ' : '👤 '
            }{customer.type}</p>
            <div className="card-stats">
              <div className="stat">
                <span className="stat-label">Total verdi</span>
                <span className="stat-value">{Math.round(customer.total_value || 0)} kr</span>
              </div>
              <div className="stat">
                <span className="stat-label">Antall ordrer</span>
                <span className="stat-value">{customer.order_count || 0}</span>
              </div>
              <div className="stat">
                <span className="stat-label">E-post</span>
                <span className="stat-value">{customer.email}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Telefon</span>
                <span className="stat-value">{customer.phone || '-'}</span>
              </div>
            </div>
            {customer.favorite_product && (
              <p className="card-text" style={{marginTop: '10px'}}>
                <strong>Favoritt:</strong> {customer.favorite_product}
              </p>
            )}
            {customer.tags && (
              <p className="card-text" style={{marginTop: '5px'}}>
                <strong>Tags:</strong> {customer.tags}
              </p>
            )}
          </div>
        ))}
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
              <div className="form-row">
                <div className="form-group">
                  <label>E-post</label>
                  <input type="email" value={formData.email}
                    onChange={e => setFormData({...formData, email: e.target.value})} className="form-input" />
                </div>
                <div className="form-group">
                  <label>Telefon</label>
                  <input type="text" value={formData.phone}
                    onChange={e => setFormData({...formData, phone: e.target.value})} className="form-input" />
                </div>
              </div>
              <div className="form-group">
                <label>Adresse</label>
                <input type="text" value={formData.address}
                  onChange={e => setFormData({...formData, address: e.target.value})} className="form-input" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Postnummer</label>
                  <input type="text" value={formData.zip_code}
                    onChange={e => setFormData({...formData, zip_code: e.target.value})} className="form-input" />
                </div>
                <div className="form-group">
                  <label>By</label>
                  <input type="text" value={formData.city}
                    onChange={e => setFormData({...formData, city: e.target.value})} className="form-input" />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Type</label>
                  <select value={formData.type}
                    onChange={e => setFormData({...formData, type: e.target.value})} className="form-select">
                    <option value="Private">Private</option>
                    <option value="Business">Business</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select value={formData.status}
                    onChange={e => setFormData({...formData, status: e.target.value})} className="form-select">
                    {statuses.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Tags</label>
                <input type="text" value={formData.tags}
                  onChange={e => setFormData({...formData, tags: e.target.value})} 
                  className="form-input" placeholder="wellness, vip, online" />
              </div>
              <div className="form-group">
                <label>Neste steg</label>
                <input type="text" value={formData.next_step}
                  onChange={e => setFormData({...formData, next_step: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Merknad</label>
                <textarea value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})} className="form-textarea" />
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
