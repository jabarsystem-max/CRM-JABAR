import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Orders = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    customer_id: '',
    items: [{ product_id: '', quantity: 1 }]
  });

  const fetchOrders = async () => {
    try {
      const [ordersRes, customersRes, productsRes] = await Promise.all([
        axios.get(`${API_URL}/orders`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/customers`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setOrders(ordersRes.data);
      setCustomers(customersRes.data);
      setProducts(productsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching orders:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/orders`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ customer_id: '', items: [{ product_id: '', quantity: 1 }] });
      fetchOrders();
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Kunne ikke opprette ordre');
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product_id: '', quantity: 1 }]
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = field === 'quantity' ? parseInt(value) : value;
    setFormData({ ...formData, items: newItems });
  };

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📊 Ordrer</h1>
          <p className="page-subtitle">Administrer salgsordrer</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny ordre</button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ordre-ID</th>
              <th>Kunde</th>
              <th>Produkter</th>
              <th>Totalt</th>
              <th>Status</th>
              <th>Dato</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(order => (
              <tr key={order.id}>
                <td><code>{order.id.substring(0, 8)}</code></td>
                <td><strong>{order.customer_name}</strong></td>
                <td>{order.items.length} produkt(er)</td>
                <td>{Math.round(order.total)} kr</td>
                <td>
                  <span className={`badge badge-${order.status === 'completed' ? 'success' : 'warning'}`}>
                    {order.status === 'completed' ? 'Fullført' : 'Venter'}
                  </span>
                </td>
                <td>{new Date(order.order_date).toLocaleString('nb-NO')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny ordre</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Kunde *</label>
                <select required value={formData.customer_id}
                  onChange={e => setFormData({...formData, customer_id: e.target.value})} className="form-select">
                  <option value="">Velg kunde</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              
              <label>Produkter *</label>
              {formData.items.map((item, idx) => (
                <div key={idx} className="form-row">
                  <div className="form-group" style={{flex: 2}}>
                    <select required value={item.product_id}
                      onChange={e => updateItem(idx, 'product_id', e.target.value)} className="form-select">
                      <option value="">Velg produkt</option>
                      {products.map(p => <option key={p.id} value={p.id}>{p.name} - {p.price} kr</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <input type="number" min="1" required value={item.quantity}
                      onChange={e => updateItem(idx, 'quantity', e.target.value)}
                      className="form-input" placeholder="Antall" />
                  </div>
                </div>
              ))}
              <button type="button" className="btn-secondary" onClick={addItem} style={{marginBottom: '15px'}}>
                + Legg til produkt
              </button>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Opprett ordre</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
