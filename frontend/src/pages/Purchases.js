import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Purchases = () => {
  const { token } = useAuth();
  const [purchases, setPurchases] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    supplier_id: '',
    items: [{ product_id: '', quantity: 1 }],
    notes: ''
  });

  const fetchPurchases = async () => {
    try {
      const [purchasesRes, suppliersRes, productsRes] = await Promise.all([
        axios.get(`${API_URL}/purchases`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/suppliers`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setPurchases(purchasesRes.data);
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching purchases:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/purchases`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ supplier_id: '', items: [{ product_id: '', quantity: 1 }], notes: '' });
      fetchPurchases();
    } catch (error) {
      console.error('Error creating purchase:', error);
      alert('Kunne ikke opprette innkjøpsordre');
    }
  };

  const handleReceive = async (purchaseId) => {
    if (!window.confirm('Bekreft mottak av innkjøp?')) return;
    try {
      await axios.put(`${API_URL}/purchases/${purchaseId}/receive`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchPurchases();
    } catch (error) {
      console.error('Error receiving purchase:', error);
      alert('Kunne ikke motta innkjøp');
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
          <h1 className="page-title">📥 Innkjøp</h1>
          <p className="page-subtitle">Administrer innkjøpsordrer og mottak</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny innkjøpsordre</button>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Ordre-ID</th>
              <th>Leverandør</th>
              <th>Produkter</th>
              <th>Totalt</th>
              <th>Status</th>
              <th>Betaling</th>
              <th>Dato</th>
              <th>Handling</th>
            </tr>
          </thead>
          <tbody>
            {purchases.map(purchase => (
              <tr key={purchase.id}>
                <td><code>{purchase.id.substring(0, 8)}</code></td>
                <td><strong>{purchase.supplier_name}</strong></td>
                <td>{purchase.lines?.length || 0} produkt(er)</td>
                <td>{Math.round(purchase.total_amount)} kr</td>
                <td>
                  <span className={`badge badge-${purchase.status === 'Received' ? 'success' : purchase.status === 'Ordered' ? 'warning' : 'danger'}`}>
                    {purchase.status}
                  </span>
                </td>
                <td>
                  <span className={`badge badge-${purchase.payment_status === 'Paid' ? 'success' : 'warning'}`}>
                    {purchase.payment_status}
                  </span>
                </td>
                <td>{new Date(purchase.date).toLocaleDateString('nb-NO')}</td>
                <td>
                  {purchase.status === 'Ordered' && (
                    <button className="btn-small btn-primary" onClick={() => handleReceive(purchase.id)}>
                      Motta
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny innkjøpsordre</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Leverandør *</label>
                <select required value={formData.supplier_id}
                  onChange={e => setFormData({...formData, supplier_id: e.target.value})} className="form-select">
                  <option value="">Velg leverandør</option>
                  {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              
              <label>Produkter *</label>
              {formData.items.map((item, idx) => (
                <div key={idx} className="form-row">
                  <div className="form-group" style={{flex: 2}}>
                    <select required value={item.product_id}
                      onChange={e => updateItem(idx, 'product_id', e.target.value)} className="form-select">
                      <option value="">Velg produkt</option>
                      {products.map(p => <option key={p.id} value={p.id}>{p.name} - {p.cost} kr</option>)}
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

              <div className="form-group">
                <label>Merknad</label>
                <textarea value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})} className="form-textarea" />
              </div>

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

export default Purchases;
