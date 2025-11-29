import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Suppliers = () => {
  const { token } = useAuth();
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: ''
  });

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get(`${API_URL}/suppliers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuppliers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/suppliers`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ name: '', contact_person: '', email: '', phone: '', address: '' });
      fetchSuppliers();
    } catch (error) {
      console.error('Error creating supplier:', error);
      alert('Kunne ikke opprette leverandør');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🤝 Leverandører</h1>
          <p className="page-subtitle">Administrer leverandører</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny leverandør</button>
      </div>

      <div className="grid">
        {suppliers.map(supplier => (
          <div key={supplier.id} className="card-item">
            <div className="card-header">
              <h3 className="card-title">{supplier.name}</h3>
            </div>
            <div className="card-stats">
              <div className="stat">
                <span className="stat-label">Kontaktperson</span>
                <span className="stat-value">{supplier.contact_person || '-'}</span>
              </div>
              <div className="stat">
                <span className="stat-label">E-post</span>
                <span className="stat-value">{supplier.email || '-'}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Telefon</span>
                <span className="stat-value">{supplier.phone || '-'}</span>
              </div>
            </div>
            <p className="card-text" style={{marginTop: '10px', fontSize: '13px', color: '#7b8794'}}>
              {supplier.address || 'Ingen adresse registrert'}
            </p>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny leverandør</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Leverandørnavn *</label>
                <input type="text" required value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Kontaktperson</label>
                <input type="text" value={formData.contact_person}
                  onChange={e => setFormData({...formData, contact_person: e.target.value})} className="form-input" />
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
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Opprett leverandør</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Suppliers;
