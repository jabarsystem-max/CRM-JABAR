import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import './StockAdjustment.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const StockAdjustment = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [adjustment, setAdjustment] = useState({
    product_id: '',
    change: 0,
    reason: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [adjustmentHistory, setAdjustmentHistory] = useState([]);

  useEffect(() => {
    fetchProducts();
    fetchAdjustmentHistory();
  }, []);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/stock`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const fetchAdjustmentHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/stock/adjustments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAdjustmentHistory(response.data);
    } catch (error) {
      console.error('Error fetching adjustment history:', error);
    }
  };

  const handleProductSelect = (e) => {
    const productId = e.target.value;
    const product = products.find(p => p.product_id === productId);
    setSelectedProduct(product);
    setAdjustment(prev => ({ ...prev, product_id: productId }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!adjustment.product_id) {
      setMessage({ type: 'error', text: 'Vennligst velg et produkt' });
      return;
    }
    
    if (adjustment.change === 0) {
      setMessage({ type: 'error', text: 'Endring kan ikke være 0' });
      return;
    }
    
    if (!adjustment.reason.trim()) {
      setMessage({ type: 'error', text: 'Vennligst oppgi årsak for justeringen' });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/stock/adjust`,
        adjustment,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setMessage({ 
        type: 'success', 
        text: `${response.data.message}. Nytt antall: ${response.data.new_quantity}` 
      });
      
      // Reset form
      setAdjustment({ product_id: '', change: 0, reason: '' });
      setSelectedProduct(null);
      
      // Refresh data
      fetchProducts();
      fetchAdjustmentHistory();
      
      // Clear message after 5 seconds
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.detail || 'Feil ved lagerjustering' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="stock-adjustment-container">
        <div className="page-header">
          <h1>Lagerjustering</h1>
          <p className="page-description">
            Juster lagerbeholdning manuelt for korrigeringer, svinn, skade eller andre årsaker
          </p>
        </div>

        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="adjustment-section">
          <h2>Ny justering</h2>
          <form onSubmit={handleSubmit} className="adjustment-form">
            <div className="form-row">
              <div className="form-group">
                <label>Produkt *</label>
                <select 
                  value={adjustment.product_id}
                  onChange={handleProductSelect}
                  required
                >
                  <option value="">Velg produkt...</option>
                  {products.map(product => (
                    <option key={product.product_id} value={product.product_id}>
                      {product.product_name} (Nåværende: {product.quantity} stk)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedProduct && (
              <div className="current-stock-info">
                <div className="info-item">
                  <span className="label">Produkt:</span>
                  <span className="value">{selectedProduct.product_name}</span>
                </div>
                <div className="info-item">
                  <span className="label">Nåværende lagerbeholdning:</span>
                  <span className="value">{selectedProduct.quantity} stk</span>
                </div>
                <div className="info-item">
                  <span className="label">Minimum lagernivå:</span>
                  <span className="value">{selectedProduct.min_stock} stk</span>
                </div>
                <div className="info-item">
                  <span className="label">Status:</span>
                  <span className={`value status-${selectedProduct.status.toLowerCase()}`}>
                    {selectedProduct.status === 'OK' ? '✅ OK' : 
                     selectedProduct.status === 'Low' ? '⚠️ Lavt' : 
                     '❌ Tomt'}
                  </span>
                </div>
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label>Endring (antall) *</label>
                <div className="adjustment-input-group">
                  <button 
                    type="button" 
                    className="qty-btn minus"
                    onClick={() => setAdjustment(prev => ({ ...prev, change: prev.change - 1 }))}
                  >
                    -
                  </button>
                  <input 
                    type="number"
                    value={adjustment.change}
                    onChange={(e) => setAdjustment(prev => ({ ...prev, change: parseInt(e.target.value) || 0 }))}
                    placeholder="0"
                    required
                  />
                  <button 
                    type="button" 
                    className="qty-btn plus"
                    onClick={() => setAdjustment(prev => ({ ...prev, change: prev.change + 1 }))}
                  >
                    +
                  </button>
                </div>
                <small>Bruk positivt tall for økning, negativt for reduksjon</small>
              </div>
            </div>

            {selectedProduct && adjustment.change !== 0 && (
              <div className="preview-result">
                <span>Nytt lagernivå vil være:</span>
                <strong className={selectedProduct.quantity + adjustment.change < 0 ? 'negative' : ''}>
                  {selectedProduct.quantity + adjustment.change} stk
                </strong>
                {selectedProduct.quantity + adjustment.change < 0 && (
                  <span className="error-text">⚠️ Kan ikke gå under 0</span>
                )}
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label>Årsak *</label>
                <textarea 
                  value={adjustment.reason}
                  onChange={(e) => setAdjustment(prev => ({ ...prev, reason: e.target.value }))}
                  placeholder="Beskriv årsaken til justeringen (f.eks. 'Fysisk telling', 'Skade', 'Svinn')"
                  rows="3"
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="button" className="btn-secondary" onClick={() => navigate('/stock')}>
                Avbryt
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Justerer...' : 'Juster lager'}
              </button>
            </div>
          </form>
        </div>

        <div className="history-section">
          <h2>Siste justeringer</h2>
          <div className="adjustment-history">
            {adjustmentHistory.length === 0 ? (
              <p className="no-data">Ingen justeringer ennå</p>
            ) : (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Dato</th>
                    <th>Produkt</th>
                    <th>Endring</th>
                    <th>Årsak</th>
                    <th>Utført av</th>
                  </tr>
                </thead>
                <tbody>
                  {adjustmentHistory.map((adj) => (
                    <tr key={adj.id}>
                      <td>{new Date(adj.created_at).toLocaleString('no-NO')}</td>
                      <td>{adj.product_name}</td>
                      <td className={adj.change >= 0 ? 'positive' : 'negative'}>
                        {adj.change >= 0 ? '+' : ''}{adj.change}
                      </td>
                      <td>{adj.reason}</td>
                      <td>{adj.created_by || 'Ukjent'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default StockAdjustment;
