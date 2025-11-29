import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Inventory = () => {
  const { token } = useAuth();
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editItem, setEditItem] = useState(null);
  const [quantity, setQuantity] = useState('');

  const fetchInventory = async () => {
    try {
      const response = await axios.get(`${API_URL}/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInventory(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching inventory:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [token]);

  const handleUpdate = async (productId) => {
    try {
      await axios.put(
        `${API_URL}/inventory/${productId}`,
        { quantity: parseInt(quantity) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEditItem(null);
      setQuantity('');
      fetchInventory();
    } catch (error) {
      console.error('Error updating inventory:', error);
      alert('Kunne ikke oppdatere lager');
    }
  };

  if (loading) {
    return <div className="loading">Laster...</div>;
  }

  const totalValue = inventory.reduce((sum, item) => sum + (item.quantity * item.product_cost), 0);
  const totalQty = inventory.reduce((sum, item) => sum + item.quantity, 0);
  const lowStock = inventory.filter(item => item.quantity < item.min_quantity);

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📦 Lager</h1>
          <p className="page-subtitle">Administrer lagerbeholdning</p>
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
            {inventory.map(item => (
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
                      value={quantity}
                      onChange={e => setQuantity(e.target.value)}
                      className="inline-input"
                      placeholder={item.quantity}
                    />
                  ) : (
                    item.quantity
                  )}
                </td>
                <td>{item.min_quantity}</td>
                <td>
                  {item.quantity < item.min_quantity ? (
                    <span className="badge badge-warning">Lavt</span>
                  ) : (
                    <span className="badge badge-success">OK</span>
                  )}
                </td>
                <td>{Math.round(item.quantity * item.product_cost)} kr</td>
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
                        setQuantity(item.quantity);
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

export default Inventory;
