import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Products = () => {
  const { token } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'vitamin',
    sku: '',
    price: '',
    cost: '',
    color: 'omega'
  });

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_URL}/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/products`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({
        name: '',
        description: '',
        category: 'vitamin',
        sku: '',
        price: '',
        cost: '',
        color: 'omega'
      });
      fetchProducts();
    } catch (error) {
      console.error('Error creating product:', error);
      alert('Kunne ikke opprette produkt');
    }
  };

  if (loading) {
    return <div className="loading">Laster...</div>;
  }

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">💊 Produkter</h1>
          <p className="page-subtitle">Administrer alle ZenVit-produkter</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          + Nytt produkt
        </button>
      </div>

      <div className="grid">
        {products.map(product => (
          <div key={product.id} className="card-item">
            <div className="card-header">
              <h3 className="card-title">{product.name}</h3>
              <span className={`badge badge-${product.color}`}>{product.category}</span>
            </div>
            <p className="card-text">{product.description}</p>
            <div className="card-stats">
              <div className="stat">
                <span className="stat-label">SKU</span>
                <span className="stat-value">{product.sku}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Salgspris</span>
                <span className="stat-value">{product.price} kr</span>
              </div>
              <div className="stat">
                <span className="stat-label">Innkjøpspris</span>
                <span className="stat-value">{product.cost} kr</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Nytt produkt</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Produktnavn</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Beskrivelse</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  className="form-textarea"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Kategori</label>
                  <select
                    value={formData.category}
                    onChange={e => setFormData({...formData, category: e.target.value})}
                    className="form-select"
                  >
                    <option value="vitamin">Vitamin</option>
                    <option value="supplement">Supplement</option>
                    <option value="mineral">Mineral</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>SKU</label>
                  <input
                    type="text"
                    required
                    value={formData.sku}
                    onChange={e => setFormData({...formData, sku: e.target.value})}
                    className="form-input"
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Salgspris (kr)</label>
                  <input
                    type="number"
                    required
                    value={formData.price}
                    onChange={e => setFormData({...formData, price: parseFloat(e.target.value)})}
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label>Innkjøpspris (kr)</label>
                  <input
                    type="number"
                    required
                    value={formData.cost}
                    onChange={e => setFormData({...formData, cost: parseFloat(e.target.value)})}
                    className="form-input"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Farge (UI)</label>
                <select
                  value={formData.color}
                  onChange={e => setFormData({...formData, color: e.target.value})}
                  className="form-select"
                >
                  <option value="d3">D3 (Orange)</option>
                  <option value="omega">Omega (Blå)</option>
                  <option value="mag">Magnesium (Grønn)</option>
                  <option value="csink">C+Sink (Gul)</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Avbryt
                </button>
                <button type="submit" className="btn-primary">
                  Opprett produkt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products;
