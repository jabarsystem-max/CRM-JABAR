import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const NewPurchase = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    supplier_id: '',
    product_id: '',
    quantity: 100,
    unit_cost: 0,
    status: 'Ordered',
    notes: ''
  });

  const fetchData = async () => {
    try {
      const [suppliersRes, productsRes] = await Promise.all([
        axios.get(`${API_URL}/suppliers`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Kunne ikke laste data');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
    // eslint-disable-next-line
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      
      // Auto-fill unit cost when product is selected
      if (name === 'product_id' && value) {
        const product = products.find(p => p.id === value);
        if (product) {
          newData.unit_cost = product.cost;
        }
      }
      
      return newData;
    });
  };

  const calculateTotal = () => {
    return formData.quantity * formData.unit_cost;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const purchaseData = {
        ...formData,
        quantity: parseInt(formData.quantity),
        unit_cost: parseFloat(formData.unit_cost),
        total_cost: calculateTotal(),
        date: new Date().toISOString()
      };

      await axios.post(`${API_URL}/purchases`, purchaseData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      navigate('/purchases');
    } catch (error) {
      console.error('Error creating purchase:', error);
      setError(error.response?.data?.detail || 'Feil ved opprettelse av innkjøp');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🚚 Ny innkjøp</h1>
          <p className="page-subtitle">Registrer ny produktinnkjøp</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/purchases')}>
          ← Avbryt
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </div>
      )}

      <div className="form-container">
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-column">
              <h3 className="form-section-title">Innkjøpsdetaljer</h3>
              
              <div className="form-group">
                <label className="form-label">Leverandør *</label>
                <select
                  name="supplier_id"
                  value={formData.supplier_id}
                  onChange={handleChange}
                  className="form-select"
                  required
                >
                  <option value="">Velg leverandør</option>
                  {suppliers.map(supplier => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Produkt *</label>
                <select
                  name="product_id"
                  value={formData.product_id}
                  onChange={handleChange}
                  className="form-select"
                  required
                >
                  <option value="">Velg produkt</option>
                  {products.map(product => (
                    <option key={product.id} value={product.id}>
                      {product.name} (SKU: {product.sku})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Antall *</label>
                  <input
                    type="number"
                    name="quantity"
                    value={formData.quantity}
                    onChange={handleChange}
                    className="form-input"
                    required
                    min="1"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Enhetspris (kr) *</label>
                  <input
                    type="number"
                    name="unit_cost"
                    value={formData.unit_cost}
                    onChange={handleChange}
                    className="form-input"
                    required
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Total kostnad</label>
                <div className="form-input" style={{ background: '#D1FAE5', color: '#27AE60', fontWeight: 700, fontSize: '18px' }}>
                  {calculateTotal().toFixed(2)} kr
                </div>
              </div>
            </div>

            <div className="form-column">
              <h3 className="form-section-title">Status og notater</h3>

              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="form-select"
                >
                  <option value="Ordered">Bestilt</option>
                  <option value="In_Transit">På vei</option>
                  <option value="Received">Mottatt</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Notater</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  className="form-textarea"
                  rows={8}
                  placeholder="Interne notater om innkjøpet"
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={() => navigate('/purchases')}>
              Avbryt
            </button>
            <button type="submit" className="btn-primary">
              Opprett innkjøp
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewPurchase;
