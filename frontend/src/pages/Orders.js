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
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: '',
    items: [{ product_id: '', quantity: 1, sale_price: '', discount: 0 }],
    channel: 'Direct',
    shipping_paid_by_customer: 0,
    shipping_cost: 0,
    payment_method: 'Card',
    notes: ''
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
      resetForm();
      fetchOrders();
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Kunne ikke opprette ordre');
    }
  };

  const updateStatus = async (orderId, newStatus) => {
    try {
      await axios.put(
        `${API_URL}/orders/${orderId}/status?status=${newStatus}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchOrders();
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      items: [{ product_id: '', quantity: 1, sale_price: '', discount: 0 }],
      channel: 'Direct',
      shipping_paid_by_customer: 0,
      shipping_cost: 0,
      payment_method: 'Card',
      notes: ''
    });
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product_id: '', quantity: 1, sale_price: '', discount: 0 }]
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = field === 'quantity' || field === 'discount' ? parseInt(value) || 0 : value;
    
    // Auto-fill sale price when product is selected
    if (field === 'product_id' && value) {
      const product = products.find(p => p.id === value);
      if (product) {
        newItems[index].sale_price = product.price;
      }
    }
    
    setFormData({ ...formData, items: newItems });
  };

  const removeItem = (index) => {
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems.length > 0 ? newItems : [{ product_id: '', quantity: 1, sale_price: '', discount: 0 }] });
  };

  if (loading) return <div className="loading">Laster...</div>;

  const channels = ['Shopify', 'TikTok', 'Instagram', 'Direct', 'Campaign'];
  const statuses = ['New', 'Processing', 'Packed', 'Shipped', 'Delivered', 'Cancelled', 'Refund'];
  const paymentMethods = ['Card', 'Vipps', 'Klarna', 'TikTokPay'];

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🛒 Ordrer</h1>
          <p className="page-subtitle">Administrer salgsordrer med profit-sporing</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny ordre</button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ordre-ID</th>
              <th>Kunde</th>
              <th>Kanal</th>
              <th>Produkter</th>
              <th>Totalt</th>
              <th>Profit</th>
              <th>Status</th>
              <th>Betaling</th>
              <th>Dato</th>
              <th>Handling</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(order => (
              <tr key={order.id}>
                <td>
                  <code className="cursor-pointer" onClick={() => setSelectedOrder(order)}>
                    {order.id.substring(0, 8)}
                  </code>
                </td>
                <td><strong>{order.customer_name}</strong></td>
                <td>
                  <span className="badge badge-omega">{order.channel}</span>
                </td>
                <td>{order.lines?.length || 0} produkt(er)</td>
                <td>{Math.round(order.order_total)} kr</td>
                <td>
                  <span className={order.profit >= 0 ? 'text-success' : 'text-danger'}>
                    {Math.round(order.profit)} kr ({order.profit_percent?.toFixed(1)}%)
                  </span>
                </td>
                <td>
                  <select
                    value={order.status}
                    onChange={(e) => updateStatus(order.id, e.target.value)}
                    className="status-select"
                  >
                    {statuses.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </td>
                <td>
                  <span className={`badge badge-${order.payment_status === 'Paid' ? 'success' : 'warning'}`}>
                    {order.payment_status}
                  </span>
                </td>
                <td>{new Date(order.date).toLocaleDateString('nb-NO')}</td>
                <td>
                  <button 
                    className="btn-small btn-secondary"
                    onClick={() => setSelectedOrder(order)}
                  >
                    Detaljer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Order Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content modal-large" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny ordre</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Kunde *</label>
                  <select required value={formData.customer_id}
                    onChange={e => setFormData({...formData, customer_id: e.target.value})} className="form-select">
                    <option value="">Velg kunde</option>
                    {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Kanal</label>
                  <select value={formData.channel}
                    onChange={e => setFormData({...formData, channel: e.target.value})} className="form-select">
                    {channels.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>

              <label>Produkter *</label>
              {formData.items.map((item, idx) => (
                <div key={idx} className="order-line">
                  <div className="form-row">
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
                    <div className="form-group">
                      <input type="number" step="0.01" required value={item.sale_price}
                        onChange={e => updateItem(idx, 'sale_price', e.target.value)}
                        className="form-input" placeholder="Pris" />
                    </div>
                    <div className="form-group">
                      <input type="number" step="0.01" value={item.discount}
                        onChange={e => updateItem(idx, 'discount', e.target.value)}
                        className="form-input" placeholder="Rabatt" />
                    </div>
                    <button type="button" className="btn-small btn-danger" onClick={() => removeItem(idx)}>
                      ✕
                    </button>
                  </div>
                </div>
              ))}
              <button type="button" className="btn-secondary" onClick={addItem} style={{marginBottom: '15px'}}>
                + Legg til produkt
              </button>

              <div className="form-row">
                <div className="form-group">
                  <label>Frakt betalt av kunde</label>
                  <input type="number" step="0.01" value={formData.shipping_paid_by_customer}
                    onChange={e => setFormData({...formData, shipping_paid_by_customer: parseFloat(e.target.value) || 0})}
                    className="form-input" />
                </div>
                <div className="form-group">
                  <label>Frakt kostnad</label>
                  <input type="number" step="0.01" value={formData.shipping_cost}
                    onChange={e => setFormData({...formData, shipping_cost: parseFloat(e.target.value) || 0})}
                    className="form-input" />
                </div>
                <div className="form-group">
                  <label>Betalingsmetode</label>
                  <select value={formData.payment_method}
                    onChange={e => setFormData({...formData, payment_method: e.target.value})} className="form-select">
                    {paymentMethods.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Merknad</label>
                <textarea value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})}
                  className="form-textarea" />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Opprett ordre</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ordredetaljer</h2>
            <div className="order-details">
              <p><strong>Ordre-ID:</strong> {selectedOrder.id}</p>
              <p><strong>Kunde:</strong> {selectedOrder.customer_name}</p>
              <p><strong>Kanal:</strong> {selectedOrder.channel}</p>
              <p><strong>Status:</strong> {selectedOrder.status}</p>
              <p><strong>Dato:</strong> {new Date(selectedOrder.date).toLocaleString('nb-NO')}</p>
              
              <h3 style={{marginTop: '20px'}}>Produkter:</h3>
              <table className="details-table">
                <thead>
                  <tr>
                    <th>Produkt</th>
                    <th>Antall</th>
                    <th>Pris</th>
                    <th>Rabatt</th>
                    <th>Total</th>
                    <th>Profit</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedOrder.lines?.map(line => (
                    <tr key={line.id}>
                      <td>{line.product_name}</td>
                      <td>{line.quantity}</td>
                      <td>{line.sale_price} kr</td>
                      <td>{line.discount} kr</td>
                      <td>{Math.round(line.line_total)} kr</td>
                      <td className={line.line_profit >= 0 ? 'text-success' : 'text-danger'}>
                        {Math.round(line.line_profit)} kr
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{marginTop: '20px'}}>
                <p><strong>Frakt (betalt):</strong> {selectedOrder.shipping_paid_by_customer} kr</p>
                <p><strong>Frakt (kostnad):</strong> {selectedOrder.shipping_cost} kr</p>
                <p><strong>Ordre total:</strong> {Math.round(selectedOrder.order_total)} kr</p>
                <p><strong>Kostnad total:</strong> {Math.round(selectedOrder.cost_total)} kr</p>
                <p><strong>Profit:</strong> <span className={selectedOrder.profit >= 0 ? 'text-success' : 'text-danger'}>
                  {Math.round(selectedOrder.profit)} kr ({selectedOrder.profit_percent?.toFixed(1)}%)
                </span></p>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={() => setSelectedOrder(null)}>Lukk</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
