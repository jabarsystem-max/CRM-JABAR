import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';
import './ProductForm.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Products = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    short_description: '',
    description: '',
    full_description: '',
    category: 'vitamin',
    subcategory: '',
    brand: '',
    health_areas: [],
    ean: '',
    packaging_type: 'flaske',
    units_per_package: 1,
    weight_grams: '',
    price: '',
    cost: '',
    min_stock: 80,
    supplier_id: '',
    color: 'omega',
    image_url: '',
    active: true
  });
  const [suppliers, setSuppliers] = useState([]);
  const [editingProduct, setEditingProduct] = useState(null);
  const [error, setError] = useState('');

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
    setError('');
    
    try {
      if (editingProduct) {
        await axios.put(`${API_URL}/products/${editingProduct.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await axios.post(`${API_URL}/products`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowModal(false);
      setEditingProduct(null);
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      setError(error.response?.data?.detail || 'Feil ved lagring av produkt');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      short_description: '',
      description: '',
      full_description: '',
      category: 'vitamin',
      subcategory: '',
      brand: '',
      health_areas: [],
      ean: '',
      packaging_type: 'flaske',
      units_per_package: 1,
      weight_grams: '',
      price: '',
      cost: '',
      min_stock: 80,
      supplier_id: '',
      color: 'omega',
      image_url: '',
      active: true
    });
    setError('');
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleHealthAreaToggle = (area) => {
    setFormData(prev => {
      const areas = prev.health_areas || [];
      if (areas.includes(area)) {
        return { ...prev, health_areas: areas.filter(a => a !== area) };
      } else {
        return { ...prev, health_areas: [...areas, area] };
      }
    });
  };

  const handleDelete = async (id) => {
    if (window.confirm('Er du sikker på at du vil slette dette produktet?')) {
      try {
        await axios.delete(`${API_URL}/products/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchProducts();
      } catch (error) {
        console.error('Error deleting product:', error);
        alert('Kunne ikke slette produkt');
      }
    }
  };

  if (loading) return <div className="loading">Laster produkter...</div>;

  const healthAreasOptions = ['Immun', 'Søvn', 'Energi', 'Hjerte', 'Hjerne', 'Ledd', 'Hud', 'Øyne', 'Mage'];

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">💊 Produkter</h1>
          <p className="page-subtitle">{products.length} produkter totalt</p>
        </div>
        <button className="btn-primary" onClick={() => { resetForm(); setShowModal(true); }}>
          + Nytt produkt
        </button>
      </div>

      <div className="product-grid">
        {products.map(product => (
          <div 
            key={product.id} 
            className="product-card" 
            onClick={() => navigate(`/products/${product.id}`)}
          >
            <div className="product-card-header">
              {product.image_url || product.thumbnail_url ? (
                <img 
                  src={product.thumbnail_url || product.image_url} 
                  alt={product.name}
                  className="product-card-image"
                />
              ) : (
                <div className="product-card-image-placeholder">📦</div>
              )}
              <span className={`product-badge badge-${product.category}`}>
                {product.category}
              </span>
            </div>
            
            <div className="product-card-body">
              <h3 className="product-card-title">{product.name}</h3>
              
              <div className="product-card-price">
                <span className="price-value">{product.price} kr</span>
              </div>
              
              <div className="product-card-meta">
                <div className="meta-item">
                  <span className="meta-label">SKU:</span>
                  <span className="meta-value">{product.sku}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Lager:</span>
                  <span className="meta-value">{product.stock_status || 'OK'}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for create/edit */}
      {showModal && (
        <div className="modal-overlay" onClick={(e) => {
          if (e.target.className === 'modal-overlay') {
            setShowModal(false);
            setEditingProduct(null);
            resetForm();
          }
        }}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">{editingProduct ? 'Rediger produkt' : 'Nytt produkt'}</h2>
              <button className="modal-close" onClick={() => { setShowModal(false); setEditingProduct(null); resetForm(); }}>×</button>
            </div>
            
            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                <span className="error-text">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                {/* Left Column */}
                <div className="form-column">
                  <h3 className="form-section-title">Grunnleggende informasjon</h3>
                  
                  <div className="form-group">
                    <label className="form-label">Produktnavn *</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className="form-input"
                      required
                      minLength={2}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Kort beskrivelse</label>
                    <input
                      type="text"
                      name="short_description"
                      value={formData.short_description}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="En-linje beskrivelse"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Beskrivelse</label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleChange}
                      className="form-textarea"
                      rows={3}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Full beskrivelse (Markdown)</label>
                    <textarea
                      name="full_description"
                      value={formData.full_description}
                      onChange={handleChange}
                      className="form-textarea"
                      rows={5}
                      placeholder="Støtter markdown-formatering"
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Kategori *</label>
                      <select
                        name="category"
                        value={formData.category}
                        onChange={handleChange}
                        className="form-select"
                        required
                      >
                        <option value="vitamin">Vitamin</option>
                        <option value="mineral">Mineral</option>
                        <option value="supplement">Supplement</option>
                        <option value="omega">Omega</option>
                        <option value="probiotic">Probiotic</option>
                        <option value="herbal">Herbal</option>
                        <option value="protein">Protein</option>
                        <option value="other">Annet</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Underkategori</label>
                      <input
                        type="text"
                        name="subcategory"
                        value={formData.subcategory}
                        onChange={handleChange}
                        className="form-input"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Merke</label>
                    <input
                      type="text"
                      name="brand"
                      value={formData.brand}
                      onChange={handleChange}
                      className="form-input"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Helseområder / Tags</label>
                    <div className="health-areas-grid">
                      {healthAreasOptions.map(area => (
                        <button
                          key={area}
                          type="button"
                          className={`health-area-btn ${(formData.health_areas || []).includes(area) ? 'active' : ''}`}
                          onClick={() => handleHealthAreaToggle(area)}
                        >
                          {area}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column */}
                <div className="form-column">
                  <h3 className="form-section-title">Produktdetaljer</h3>
                  
                  {editingProduct && (
                    <div className="form-group">
                      <label className="form-label">SKU (automatisk generert)</label>
                      <input
                        type="text"
                        value={editingProduct.sku}
                        className="form-input"
                        disabled
                      />
                    </div>
                  )}

                  <div className="form-group">
                    <label className="form-label">EAN / Strekkode</label>
                    <input
                      type="text"
                      name="ean"
                      value={formData.ean}
                      onChange={handleChange}
                      className="form-input"
                      pattern="[0-9]*"
                      placeholder="13 siffer"
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Pakningstype</label>
                      <select
                        name="packaging_type"
                        value={formData.packaging_type}
                        onChange={handleChange}
                        className="form-select"
                      >
                        <option value="flaske">Flaske</option>
                        <option value="glass">Glass</option>
                        <option value="boks">Boks</option>
                        <option value="pakke">Pakke</option>
                        <option value="pose">Pose</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Enheter per pakke</label>
                      <input
                        type="number"
                        name="units_per_package"
                        value={formData.units_per_package}
                        onChange={handleChange}
                        className="form-input"
                        min="1"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Vekt (gram)</label>
                    <input
                      type="number"
                      name="weight_grams"
                      value={formData.weight_grams}
                      onChange={handleChange}
                      className="form-input"
                      step="0.1"
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Innkjøpspris (kr) *</label>
                      <input
                        type="number"
                        name="cost"
                        value={formData.cost}
                        onChange={handleChange}
                        className="form-input"
                        required
                        min="0"
                        step="0.01"
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Salgspris (kr) *</label>
                      <input
                        type="number"
                        name="price"
                        value={formData.price}
                        onChange={handleChange}
                        className="form-input"
                        required
                        min="0"
                        step="0.01"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Minimum lager *</label>
                    <input
                      type="number"
                      name="min_stock"
                      value={formData.min_stock}
                      onChange={handleChange}
                      className="form-input"
                      required
                      min="0"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Leverandør</label>
                    <select
                      name="supplier_id"
                      value={formData.supplier_id}
                      onChange={handleChange}
                      className="form-select"
                    >
                      <option value="">Velg leverandør</option>
                      {suppliers.map(supplier => (
                        <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Produktbilde URL</label>
                    <input
                      type="url"
                      name="image_url"
                      value={formData.image_url}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="https://..."
                    />
                    {formData.image_url && (
                      <div className="image-preview">
                        <img src={formData.image_url} alt="Preview" />
                      </div>
                    )}
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Farge (UI)</label>
                      <select
                        name="color"
                        value={formData.color}
                        onChange={handleChange}
                        className="form-select"
                      >
                        <option value="omega">Blå</option>
                        <option value="success">Grønn</option>
                        <option value="warning">Gul</option>
                        <option value="danger">Rød</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Status</label>
                      <div className="checkbox-group">
                        <label>
                          <input
                            type="checkbox"
                            name="active"
                            checked={formData.active}
                            onChange={handleChange}
                          />
                          <span>Aktiv</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => { setShowModal(false); setEditingProduct(null); resetForm(); }}>
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
