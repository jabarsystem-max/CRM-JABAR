import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const StockMovements = () => {
  const { token } = useAuth();
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMovements = async () => {
    try {
      const response = await axios.get(`${API_URL}/stock-movements`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMovements(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching movements:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMovements();
  }, [token]);

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📊 Lagerbevegelser</h1>
          <p className="page-subtitle">Komplett historikk over alle lagerendringer</p>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Dato</th>
              <th>Produkt</th>
              <th>Type</th>
              <th>Antall</th>
              <th>Referanse</th>
              <th>Merknad</th>
            </tr>
          </thead>
          <tbody>
            {movements.map(mov => (
              <tr key={mov.id}>
                <td>{new Date(mov.date).toLocaleString('nb-NO')}</td>
                <td>{mov.product_name}</td>
                <td>
                  <span className={`badge badge-${mov.type === 'IN' ? 'success' : 'warning'}`}>
                    {mov.type === 'IN' ? 'Inn' : 'Ut'}
                  </span>
                </td>
                <td>{mov.quantity}</td>
                <td>
                  {mov.order_id && <span>Ordre: {mov.order_id.substring(0, 8)}</span>}
                  {mov.purchase_id && <span>Innkjøp: {mov.purchase_id.substring(0, 8)}</span>}
                </td>
                <td>{mov.note || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StockMovements;
