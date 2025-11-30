import React, { useEffect, useState, useCallback } from 'react';
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
    min_stock: 80,
    supplier_id: '',
    color: 'omega'
  });
  const [suppliers, setSuppliers] = useState([]);
  const [editingProduct, setEditingProduct] = useState(null);

  const fetchProducts = useCallback(async () => {
    try {
      const [productsRes, suppliersRes] = await Promise.all([
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/suppliers`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setProducts(productsRes.data);
      setSuppliers(suppliersRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching products:', error);
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchProducts();
    }
  }, [token, fetchProducts]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingProduct) {
        // Update existing product
        await axios.put(`${API_URL}/products/${editingProduct.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        // Create new product
        await axios.post(`${API_URL}/products`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowModal(false);
      setEditingProduct(null);
      setFormData({
        name: '',
        description: '',
        category: 'vitamin',
        sku: '',
        price: '',
        cost: '',
        min_stock: 80,
        supplier_id: '',
        color: 'omega'
      });
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      alert(editingProduct ? 'Kunne ikke oppdatere produkt' : 'Kunne ikke opprette produkt');
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
        <button className="btn-primary" onClick={() => {
          setEditingProduct(null);
          setFormData({
            name: '',
            description: '',
            category: 'vitamin',
            sku: '',
            price: '',
            cost: '',
            min_stock: 80,
            supplier_id: '',
            color: 'omega'
          });
          setShowModal(true);
        }}>
          + Nytt produkt
        </button>
      </div>

      <div className="product-grid">
        {products.map(product => (
          <div 
            key={product.id} 
            className="product-card" 
            onClick={() => {
              setEditingProduct(product);
              setFormData({
                name: product.name,
                sku: product.sku,
                category: product.category,
                price: product.price,
                cost: product.cost,
                description: product.description || '',
                min_stock: product.min_stock || 80,
                supplier_id: product.supplier_id || ''
              });
              setShowModal(true);
            }}
          >
            <div className="product-card-header">
              <h3 className="product-card-title">{product.name}</h3>
              <span className={`product-badge badge-${product.category === 'vitamin' ? 'success' : product.category === 'mineral' ? 'warning' : 'omega'}`}>
                {product.category}
              </span>
            </div>
            
            <div className="product-card-body">
              <div className="product-card-price">
                <span className="price-label">Salgspris</span>
                <span className="price-value">{product.price} kr</span>
              </div>
              
              <div className="product-card-meta">
                <div className="meta-item">
                  <span className="meta-label">SKU:</span>
                  <span className="meta-value">{product.sku}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Kostpris:</span>
                  <span className="meta-value">{product.cost} kr</span>
                </div>
              </div>
              
              <div className="product-card-footer">
                <span className={`status-badge status-${product.stock_status === 'OK' ? 'ok' : product.stock_status === 'Low' ? 'low' : 'out'}`}>
                  {product.stock_status || 'OK'}
                </span>
                <span className="stock-info">Min: {product.min_stock || 80} stk</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => {
          setShowModal(false);
          setEditingProduct(null);
        }}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">{editingProduct ? 'Rediger produkt' : 'Nytt produkt'}</h2>
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
              <div className="form-row">
                <div className="form-group">
                  <label>Min. lagernivå</label>
                  <input
                    type="number"
                    required
                    value={formData.min_stock}
                    onChange={e => setFormData({...formData, min_stock: parseInt(e.target.value)})}
                    className="form-input"
                  />
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
              </div>
              <div className="form-group">
                <label>Leverandør</label>
                <select
                  value={formData.supplier_id}
                  onChange={e => setFormData({...formData, supplier_id: e.target.value})}
                  className="form-select"
                >
                  <option value="">Ingen leverandør valgt</option>
                  {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => {
                  setShowModal(false);
                  setEditingProduct(null);
                }}>
                  Avbryt
                </button>
                <button type="submit" className="btn-primary">
                  {editingProduct ? 'Oppdater produkt' : 'Opprett produkt'}
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
