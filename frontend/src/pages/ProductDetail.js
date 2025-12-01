import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import './ProductDetail.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ProductDetail = () => {
  const { id } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [stock, setStock] = useState(null);
  const [movements, setMovements] = useState([]);
  const [supplier, setSupplier] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProductDetails();
  }, [id]);

  const fetchProductDetails = async () => {
    try {
      // Fetch product
      const productRes = await axios.get(`${API_URL}/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const foundProduct = productRes.data.find(p => p.id === id);
      setProduct(foundProduct);

      // Fetch stock
      const stockRes = await axios.get(`${API_URL}/stock`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const foundStock = stockRes.data.find(s => s.product_id === id);
      setStock(foundStock);

      // Fetch stock movements
      const movementsRes = await axios.get(`${API_URL}/stock/movements?product_id=${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMovements(movementsRes.data);

      // Fetch supplier if exists
      if (foundProduct?.supplier_id) {
        const supplierRes = await axios.get(`${API_URL}/suppliers`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const foundSupplier = supplierRes.data.find(s => s.id === foundProduct.supplier_id);
        setSupplier(foundSupplier);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching product details:', error);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Laster produktdetaljer...</div>;
  if (!product) return <div className="loading">Produkt ikke funnet</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <button className="btn-secondary" onClick={() => navigate('/products')}>
          ← Tilbake
        </button>
        <button className="btn-primary" onClick={() => navigate(`/products/${id}/edit`)}>
          ✏️ Rediger produkt
        </button>
      </div>

      <div className="product-detail-container">
        {/* Left Column - Product Info */}
        <div className="product-detail-main">
          {/* Product Header */}
          <div className="product-detail-header">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} className="product-detail-image" />
            ) : (
              <div className="product-detail-image-placeholder">📦</div>
            )}
            <div className="product-detail-header-info">
              <span className={`category-badge badge-${product.category}`}>
                {product.category}
              </span>
              <h1>{product.name}</h1>
              {product.brand && <p className="product-brand">Merke: {product.brand}</p>}
              <p className="product-sku">SKU: {product.sku}</p>
            </div>
          </div>

          {/* Short Description */}
          {product.short_description && (
            <div className="product-section">
              <h3>Kort beskrivelse</h3>
              <p>{product.short_description}</p>
            </div>
          )}

          {/* Full Description */}
          {product.full_description && (
            <div className="product-section">
              <h3>Full beskrivelse</h3>
              <div className="product-description" dangerouslySetInnerHTML={{ __html: product.full_description }} />
            </div>
          )}

          {/* Health Areas / Tags */}
          {product.health_areas && product.health_areas.length > 0 && (
            <div className="product-section">
              <h3>Helseområder</h3>
              <div className="health-tags">
                {product.health_areas.map((area, idx) => (
                  <span key={idx} className="health-tag">{area}</span>
                ))}
              </div>
            </div>
          )}

          {/* Stock Movements */}
          <div className="product-section">
            <h3>Lagerbevegelser (siste 10)</h3>
            {movements.length === 0 ? (
              <p className="empty-message">Ingen lagerbevegelser ennå</p>
            ) : (
              <div className="movements-table">
                <table>
                  <thead>
                    <tr>
                      <th>Dato</th>
                      <th>Type</th>
                      <th>Mengde</th>
                      <th>Merknad</th>
                    </tr>
                  </thead>
                  <tbody>
                    {movements.slice(0, 10).map((movement, idx) => (
                      <tr key={idx}>
                        <td>{new Date(movement.date).toLocaleDateString('no-NO')}</td>
                        <td>
                          <span className={`movement-type movement-${movement.type.toLowerCase()}`}>
                            {movement.type}
                          </span>
                        </td>
                        <td>{movement.quantity} stk</td>
                        <td>{movement.note || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Sidebar */}
        <div className="product-detail-sidebar">
          {/* Pricing Card */}
          <div className="sidebar-card">
            <h3>Prising</h3>
            <div className="price-row">
              <span className="price-label">Salgspris:</span>
              <span className="price-value">{product.price} kr</span>
            </div>
            <div className="price-row">
              <span className="price-label">Innkjøpspris:</span>
              <span className="price-value">{product.cost} kr</span>
            </div>
            <div className="price-row">
              <span className="price-label">Margin:</span>
              <span className="price-value price-profit">
                {((product.price - product.cost) / product.price * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Stock Card */}
          <div className="sidebar-card">
            <h3>Lagerstatus</h3>
            <div className="stock-status">
              <span className={`status-badge status-${stock?.status?.toLowerCase() || 'ok'}`}>
                {stock?.status || 'OK'}
              </span>
              <span className="stock-quantity">{stock?.quantity || 0} stk</span>
            </div>
            <div className="stock-info-row">
              <span>Minimum lager:</span>
              <span>{product.min_stock || 80} stk</span>
            </div>
          </div>

          {/* Product Details Card */}
          <div className="sidebar-card">
            <h3>Produktdetaljer</h3>
            {product.ean && (
              <div className="detail-row">
                <span className="detail-label">EAN:</span>
                <span className="detail-value">{product.ean}</span>
              </div>
            )}
            {product.packaging_type && (
              <div className="detail-row">
                <span className="detail-label">Pakning:</span>
                <span className="detail-value">{product.packaging_type}</span>
              </div>
            )}
            {product.units_per_package && (
              <div className="detail-row">
                <span className="detail-label">Enheter per pakke:</span>
                <span className="detail-value">{product.units_per_package}</span>
              </div>
            )}
            {product.weight_grams && (
              <div className="detail-row">
                <span className="detail-label">Vekt:</span>
                <span className="detail-value">{product.weight_grams}g</span>
              </div>
            )}
            {product.subcategory && (
              <div className="detail-row">
                <span className="detail-label">Underkategori:</span>
                <span className="detail-value">{product.subcategory}</span>
              </div>
            )}
          </div>

          {/* Supplier Card */}
          {supplier && (
            <div className="sidebar-card">
              <h3>Leverandør</h3>
              <p className="supplier-name">{supplier.name}</p>
              {supplier.contact_person && <p className="supplier-contact">{supplier.contact_person}</p>}
              {supplier.email && <p className="supplier-email">{supplier.email}</p>}
              {supplier.phone && <p className="supplier-phone">{supplier.phone}</p>}
            </div>
          )}

          {/* Status Card */}
          <div className="sidebar-card">
            <h3>Status</h3>
            <div className="detail-row">
              <span className="detail-label">Aktiv:</span>
              <span className="detail-value">
                {product.active ? '✅ Ja' : '❌ Nei'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Opprettet:</span>
              <span className="detail-value">
                {new Date(product.created_at).toLocaleDateString('no-NO')}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;
