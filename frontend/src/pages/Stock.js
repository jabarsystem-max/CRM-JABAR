import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Stock = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [stock, setStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({ quantity: '', min_stock: '' });

  const fetchStock = async () => {
    try {
      const response = await axios.get(`${API_URL}/stock`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStock(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stock:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStock();
  }, [token]);

  const handleUpdate = async (productId) => {
    try {
      await axios.put(
        `${API_URL}/stock/${productId}`,
        { 
          quantity: parseInt(formData.quantity),
          min_stock: parseInt(formData.min_stock)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEditItem(null);
      setFormData({ quantity: '', min_stock: '' });
      fetchStock();
    } catch (error) {
      console.error('Error updating stock:', error);
      alert('Kunne ikke oppdatere lager');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  const totalValue = stock.reduce((sum, item) => sum + (item.quantity * (item.product_cost || 0)), 0);
  const totalQty = stock.reduce((sum, item) => sum + item.quantity, 0);
  const lowStock = stock.filter(item => item.status === 'Low' || item.status === 'Out');

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📦 Lageroversikt</h1>
          <p className="page-subtitle">Administrer lagerbeholdning og lagergrenser</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-secondary" onClick={() => navigate('/stock-movements')}>
            📊 Bevegelser
          </button>
          <button className="btn-primary" onClick={() => navigate('/stock/adjust')}>
            ✏️ Juster lager
          </button>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div>
            <div className="stat-value">{totalQty}</div>
            <div className="stat-label">Totalt på lager</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div>
            <div className="stat-value">{Math.round(totalValue)} kr</div>
            <div className="stat-label">Total lagerverdi</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div>
            <div className="stat-value">{lowStock.length}</div>
            <div className="stat-label">Lavt lager</div>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Produkt</th>
              <th>SKU</th>
              <th>Beholdning</th>
              <th>Min. nivå</th>
              <th>Status</th>
              <th>Verdi</th>
              <th>Handling</th>
            </tr>
          </thead>
          <tbody>
            {stock.map(item => (
              <tr key={item.id}>
                <td>
                  <div className="product-cell">
                    <span className={`dot dot-${item.product_color || 'omega'}`}></span>
                    {item.product_name}
                  </div>
                </td>
                <td>{item.product_sku}</td>
                <td>
                  {editItem === item.product_id ? (
                    <input
                      type="number"
                      value={formData.quantity}
                      onChange={e => setFormData({...formData, quantity: e.target.value})}
                      className="inline-input"
                    />
                  ) : (
                    item.quantity
                  )}
                </td>
                <td>
                  {editItem === item.product_id ? (
                    <input
                      type="number"
                      value={formData.min_stock}
                      onChange={e => setFormData({...formData, min_stock: e.target.value})}
                      className="inline-input"
                    />
                  ) : (
                    item.min_stock
                  )}
                </td>
                <td>
                  <span className={`badge badge-${item.status === 'OK' ? 'success' : item.status === 'Low' ? 'warning' : 'danger'}`}>
                    {item.status}
                  </span>
                </td>
                <td>{Math.round(item.quantity * (item.product_cost || 0))} kr</td>
                <td>
                  {editItem === item.product_id ? (
                    <div className="action-buttons">
                      <button className="btn-small btn-primary" onClick={() => handleUpdate(item.product_id)}>
                        Lagre
                      </button>
                      <button className="btn-small btn-secondary" onClick={() => setEditItem(null)}>
                        Avbryt
                      </button>
                    </div>
                  ) : (
                    <button
                      className="btn-small btn-secondary"
                      onClick={() => {
                        setEditItem(item.product_id);
                        setFormData({ quantity: item.quantity, min_stock: item.min_stock });
                      }}
                    >
                      Juster
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Stock;
