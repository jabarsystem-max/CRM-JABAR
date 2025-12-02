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
                  <strong>{item.quantity}</strong>
                </td>
                <td>{item.min_stock}</td>
                <td>
                  <span className={`badge badge-${item.status === 'OK' ? 'success' : item.status === 'Low' ? 'warning' : 'danger'}`}>
                    {item.status}
                  </span>
                </td>
                <td>{Math.round(item.quantity * (item.product_cost || 0))} kr</td>
                <td>
                  <button
                    className="btn-small btn-secondary"
                    onClick={() => navigate('/stock/adjust')}
                  >
                    Juster
                  </button>
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
