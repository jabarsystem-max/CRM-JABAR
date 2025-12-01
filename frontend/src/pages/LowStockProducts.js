import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';
import './ProductForm.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const LowStockProducts = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [lowStockProducts, setLowStockProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLowStockProducts = async () => {
    try {
      // Get all stock items with Low or Out status
      const stockResponse = await axios.get(`${API_URL}/stock`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const lowStockItems = stockResponse.data.filter(
        item => item.status === 'Low' || item.status === 'Out'
      );

      // Get product details for each low stock item
      const productsResponse = await axios.get(`${API_URL}/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const productsWithLowStock = lowStockItems.map(stockItem => {
        const product = productsResponse.data.find(p => p.id === stockItem.product_id);
        return {
          ...product,
          currentStock: stockItem.quantity,
          minStock: stockItem.min_stock,
          status: stockItem.status
        };
      }).filter(p => p.id); // Filter out any null products

      setLowStockProducts(productsWithLowStock);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching low stock products:', error);
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Laster produkter med lavt lager...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">⚠️ Lavt lager</h1>
          <p className="page-subtitle">{lowStockProducts.length} produkter under minimum</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/products')}>
          ← Tilbake til produkter
        </button>
      </div>

      {lowStockProducts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h3>Ingen produkter med lavt lager</h3>
          <p>Alle produkter har tilfredsstillende lagernivå</p>
        </div>
      ) : (
        <div className="product-grid">
          {lowStockProducts.map(product => (
            <div 
              key={product.id} 
              className="product-card low-stock-card" 
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
                <span className={`product-badge badge-${product.status === 'Out' ? 'danger' : 'warning'}`}>
                  {product.status === 'Out' ? 'Tomt' : 'Lavt lager'}
                </span>
                <div className="warning-overlay">
                  <span className="warning-icon">⚠️</span>
                </div>
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
                  <div className="meta-item meta-warning">
                    <span className="meta-label">Lager:</span>
                    <span className="meta-value">{product.currentStock} / {product.minStock}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LowStockProducts;
