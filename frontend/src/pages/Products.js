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
  const [uploadingImage, setUploadingImage] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

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
      // Prepare data with proper type conversions
      const submitData = {
        ...formData,
        // Convert empty strings to null for optional number fields
        weight_grams: formData.weight_grams === '' ? null : parseFloat(formData.weight_grams),
        units_per_package: formData.units_per_package === '' ? 1 : parseInt(formData.units_per_package),
        // Required fields - keep as numbers
        cost: parseFloat(formData.cost),
        price: parseFloat(formData.price),
        min_stock: parseInt(formData.min_stock),
        // Convert empty string to null for optional fields
        ean: formData.ean === '' ? null : formData.ean,
        supplier_id: formData.supplier_id === '' ? null : formData.supplier_id,
        subcategory: formData.subcategory === '' ? null : formData.subcategory,
        brand: formData.brand === '' ? null : formData.brand,
        short_description: formData.short_description === '' ? null : formData.short_description,
        description: formData.description === '' ? null : formData.description,
        full_description: formData.full_description === '' ? null : formData.full_description,
        packaging_type: formData.packaging_type === '' ? null : formData.packaging_type,
        color: formData.color === '' ? null : formData.color,
        image_url: formData.image_url === '' ? null : formData.image_url
      };

      if (editingProduct) {
        await axios.put(`${API_URL}/products/${editingProduct.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await axios.post(`${API_URL}/products`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setShowModal(false);
      setEditingProduct(null);
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error('Error saving product:', error);
      
      // Handle Pydantic validation errors (array of error objects)
      if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
        const errors = error.response.data.detail;
        const errorMessages = errors.map(err => {
          const field = err.loc[err.loc.length - 1];
          return `${field}: ${err.msg}`;
        }).join(', ');
        setError(errorMessages);
      } else if (typeof error.response?.data?.detail === 'string') {
        setError(error.response.data.detail);
      } else {
        setError('Feil ved lagring av produkt');
      }
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
    setSelectedFile(null);
    setUploadingImage(false);
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

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Ugyldig filtype. Kun JPEG, PNG og WebP er tillatt.');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Filen er for stor. Maksimal størrelse er 5MB.');
      return;
    }

    setUploadingImage(true);
    setError('');
    
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', file);

      const response = await axios.post(`${API_URL}/upload-image`, formDataUpload, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      // Update form data with the uploaded image URL (backend returns relative path)
      const imageUrl = response.data.image_url;
      setFormData(prev => ({ ...prev, image_url: imageUrl }));
      setSelectedFile(file);
    } catch (error) {
      console.error('Error uploading image:', error);
      setError(error.response?.data?.detail || 'Feil ved opplasting av bilde');
    } finally {
      setUploadingImage(false);
    }
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
        {products.map(product => {
          // Calculate stock status and color
          const currentStock = product.current_stock || 0;
          const minStock = product.min_stock || 0;
          let stockStatus = 'normal';
          let stockColor = '#10b981'; // green
          
          if (currentStock === 0) {
            stockStatus = 'critical';
            stockColor = '#dc2626'; // red
          } else if (currentStock <= minStock) {
            stockStatus = 'low';
            stockColor = '#f59e0b'; // yellow/orange
          }
          
          return (
            <div 
              key={product.id} 
              className="product-card-modern" 
              onClick={() => navigate(`/products/${product.id}`)}
            >
              {/* Product Image */}
              <div className="product-image-container">
                {product.image_url || product.thumbnail_url ? (
                  <img 
                    src={`${process.env.REACT_APP_BACKEND_URL}${product.image_url || product.thumbnail_url}`} 
                    alt={product.name}
                    className="product-image"
                    loading="lazy"
                  />
                ) : (
                  <div className="product-image-placeholder">
                    <span className="placeholder-icon">📦</span>
                  </div>
                )}
              </div>
              
              {/* Product Info */}
              <div className="product-info">
                <h3 className="product-title">{product.name}</h3>
                
                {product.short_description && (
                  <p className="product-description">{product.short_description}</p>
                )}
                
                {/* Price */}
                <div className="product-price">
                  <span className="price-amount">{product.price} kr</span>
                </div>
                
                {/* Stock Status */}
                <div className="product-stock">
                  <span 
                    className="stock-indicator" 
                    style={{ backgroundColor: stockColor }}
                  ></span>
                  <span className="stock-text">
                    {currentStock === 0 ? 'Utsolgt' : 
                     currentStock <= minStock ? `Lav (${currentStock} stk)` : 
                     `På lager (${currentStock} stk)`}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
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
                      placeholder="13 siffer (valgfritt)"
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
                      placeholder="Valgfritt"
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
                      <option value="">Velg leverandør (valgfritt)</option>
                      {suppliers.map(supplier => (
                        <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Produktbilde</label>
                    <div className="file-upload-container">
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/jpg,image/webp"
                        onChange={handleImageUpload}
                        className="form-input"
                        id="image-upload"
                        disabled={uploadingImage}
                      />
                      {uploadingImage && <p className="upload-status">Laster opp bilde...</p>}
                      {formData.image_url && (
                        <div className="image-preview">
                          <img 
                            src={formData.image_url.startsWith('/') 
                              ? `${process.env.REACT_APP_BACKEND_URL}${formData.image_url}` 
                              : formData.image_url} 
                            alt="Preview" 
                          />
                        </div>
                      )}
                    </div>
                    <small className="form-help-text">Maks 5MB. Tillatte formater: JPEG, PNG, WebP</small>
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
