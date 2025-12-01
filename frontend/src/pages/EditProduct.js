import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useParams } from 'react-router-dom';
import './CRM.css';
import './ProductForm.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const EditProduct = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(null);
  const [suppliers, setSuppliers] = useState([]);
  const [error, setError] = useState('');
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    if (token && id) {
      fetchProductAndSuppliers();
    }
  }, [token, id]);

  const fetchProductAndSuppliers = async () => {
    try {
      const [productRes, suppliersRes] = await Promise.all([
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/suppliers`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      const product = productRes.data.find(p => p.id === id);
      if (!product) {
        setError('Produkt ikke funnet');
        setLoading(false);
        return;
      }

      setFormData({
        name: product.name || '',
        short_description: product.short_description || '',
        description: product.description || '',
        full_description: product.full_description || '',
        category: product.category || 'vitamin',
        subcategory: product.subcategory || '',
        brand: product.brand || '',
        health_areas: product.health_areas || [],
        ean: product.ean || '',
        packaging_type: product.packaging_type || 'flaske',
        units_per_package: product.units_per_package || 1,
        weight_grams: product.weight_grams || '',
        price: product.price || '',
        cost: product.cost || '',
        min_stock: product.min_stock || 80,
        supplier_id: product.supplier_id || '',
        color: product.color || 'omega',
        image_url: product.image_url || '',
        active: product.active !== undefined ? product.active : true,
        sku: product.sku
      });
      
      setSuppliers(suppliersRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching product:', error);
      setError('Kunne ikke laste produkt');
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const submitData = {
        ...formData,
        weight_grams: formData.weight_grams === '' ? null : parseFloat(formData.weight_grams),
        units_per_package: formData.units_per_package === '' ? 1 : parseInt(formData.units_per_package),
        cost: parseFloat(formData.cost),
        price: parseFloat(formData.price),
        min_stock: parseInt(formData.min_stock),
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

      await axios.put(`${API_URL}/products/${id}`, submitData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      navigate(`/products/${id}`);
    } catch (error) {
      console.error('Error updating product:', error);
      
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
        setError('Feil ved oppdatering av produkt');
      }
    }
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

    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Ugyldig filtype. Kun JPEG, PNG og WebP er tillatt.');
      return;
    }

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

      const imageUrl = `${process.env.REACT_APP_BACKEND_URL}${response.data.image_url}`;
      setFormData(prev => ({ ...prev, image_url: imageUrl }));
    } catch (error) {
      console.error('Error uploading image:', error);
      setError(error.response?.data?.detail || 'Feil ved opplasting av bilde');
    } finally {
      setUploadingImage(false);
    }
  };

  if (loading) return <div className="loading">Laster produkt...</div>;
  if (error && !formData) return <div className="error-state">{error}</div>;
  if (!formData) return <div className="error-state">Produkt ikke funnet</div>;

  const healthAreasOptions = ['Immun', 'Søvn', 'Energi', 'Hjerte', 'Hjerne', 'Ledd', 'Hud', 'Øyne', 'Mage'];

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">✏️ Rediger produkt</h1>
          <p className="page-subtitle">{formData.name}</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate(`/products/${id}`)}>
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
            {/* Left Column - Same as Products.js */}
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
                  placeholder="F.eks. Omega-3 500mg"
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
                  placeholder="En kort beskrivelse (valgfritt)"
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
                  placeholder="Beskriv produktet (valgfritt)"
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
                  placeholder="Detaljert beskrivelse med markdown-formatering (valgfritt)"
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
                    placeholder="F.eks. Kapsler (valgfritt)"
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
                  placeholder="Produsentens merke (valgfritt)"
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
              
              <div className="form-group">
                <label className="form-label">SKU (automatisk generert)</label>
                <input
                  type="text"
                  value={formData.sku}
                  className="form-input"
                  disabled
                />
              </div>

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
                    placeholder="F.eks. 60"
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
                  placeholder="Produktets vekt i gram (valgfritt)"
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
                    placeholder="Din innkjøpspris"
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
                    placeholder="Salgspris til kunde"
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
                  placeholder="Minimum lagerantal"
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
                      <img src={formData.image_url} alt="Preview" />
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
            <button type="button" className="btn-secondary" onClick={() => navigate(`/products/${id}`)}>
              Avbryt
            </button>
            <button type="submit" className="btn-primary">
              Lagre endringer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditProduct;
