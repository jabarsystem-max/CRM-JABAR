import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const NewOrder = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    customer_id: '',
    status: 'Pending',
    shipping_address: '',
    notes: ''
  });

  const [orderItems, setOrderItems] = useState([
    { product_id: '', quantity: 1, price: 0 }
  ]);

  const fetchData = async () => {
    try {
      const [customersRes, productsRes] = await Promise.all([
        axios.get(`${API_URL}/customers`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API_URL}/products`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setCustomers(customersRes.data);
      setProducts(productsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Kunne ikke laste data');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
    // eslint-disable-next-line
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddProduct = () => {
    setOrderItems([...orderItems, { product_id: '', quantity: 1, price: 0 }]);
  };

  const handleRemoveProduct = (index) => {
    const newItems = orderItems.filter((_, i) => i !== index);
    setOrderItems(newItems.length > 0 ? newItems : [{ product_id: '', quantity: 1, price: 0 }]);
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...orderItems];
    newItems[index][field] = value;
    
    // Auto-fill price when product is selected
    if (field === 'product_id' && value) {
      const product = products.find(p => p.id === value);
      if (product) {
        // Use sale_price (new model) or fallback to price (legacy)
        const productPrice = product.sale_price || product.price || 0;
        newItems[index].price = parseFloat(productPrice);
      }
    }
    
    // Ensure quantity is a number
    if (field === 'quantity') {
      newItems[index].quantity = parseInt(value) || 1;
    }
    
    setOrderItems(newItems);
  };

  const calculateTotal = () => {
    return orderItems.reduce((total, item) => {
      const quantity = parseInt(item.quantity) || 0;
      const price = parseFloat(item.price) || 0;
      return total + (quantity * price);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate
    if (!formData.customer_id) {
      setError('Vennligst velg en kunde');
      return;
    }

    const validItems = orderItems
      .filter(item => item.product_id && item.quantity > 0)
      .map(item => ({
        ...item,
        quantity: parseInt(item.quantity) || 1,
        price: parseFloat(item.price) || 0
      }));
    
    if (validItems.length === 0) {
      setError('Legg til minst ett produkt');
      return;
    }
    
    const totalPrice = calculateTotal();
    if (totalPrice <= 0) {
      setError('Totalpris må være større enn 0. Sjekk at produktene har pris.');
      return;
    }

    try {
      const orderData = {
        ...formData,
        items: validItems,
        order_total: totalPrice,
        date: new Date().toISOString()
      };

      await axios.post(`${API_URL}/orders`, orderData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      navigate('/orders');
    } catch (error) {
      console.error('Error creating order:', error);
      setError(error.response?.data?.detail || 'Feil ved opprettelse av ordre');
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🛒 Ny bestilling</h1>
          <p className="page-subtitle">Opprett en ny kundeordre</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/orders')}>
          ← Avbryt
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </div>
      )}

      <div className="form-container">
        <form onSubmit={handleSubmit}>
          <div className="form-section">
            <h3 className="form-section-title">Kundeinformasjon</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Kunde *</label>
                <select
                  name="customer_id"
                  value={formData.customer_id}
                  onChange={handleChange}
                  className="form-select"
                  required
                >
                  <option value="">Velg kunde</option>
                  {customers.map(customer => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name} - {customer.email}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="form-select"
                >
                  <option value="Pending">Pending</option>
                  <option value="Processing">Processing</option>
                  <option value="Packed">Packed</option>
                  <option value="Shipped">Shipped</option>
                  <option value="Delivered">Delivered</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Leveringsadresse</label>
              <input
                type="text"
                name="shipping_address"
                value={formData.shipping_address}
                onChange={handleChange}
                className="form-input"
                placeholder="Gate, postnummer, by"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Notater</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                className="form-textarea"
                rows={3}
                placeholder="Interne notater om ordren"
              />
            </div>
          </div>

          <div className="form-section">
            <div className="form-section-header">
              <h3 className="form-section-title">Produkter</h3>
              <button 
                type="button" 
                className="btn-secondary"
                onClick={handleAddProduct}
              >
                + Legg til produkt
              </button>
            </div>

            <div className="order-items-list">
              {orderItems.map((item, index) => (
                <div key={index} className="order-item-row">
                  <div className="order-item-number">{index + 1}</div>
                  
                  <div className="order-item-field">
                    <label className="form-label-small">Produkt *</label>
                    <select
                      value={item.product_id}
                      onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                      className="form-select"
                      required
                    >
                      <option value="">Velg produkt</option>
                      {products.map(product => (
                        <option key={product.id} value={product.id}>
                          {product.name} - {product.sale_price || product.price || 0} kr
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="order-item-field-small">
                    <label className="form-label-small">Antall *</label>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 1)}
                      className="form-input"
                      min="1"
                      required
                    />
                  </div>

                  <div className="order-item-field-small">
                    <label className="form-label-small">Pris (kr) *</label>
                    <input
                      type="number"
                      value={item.price}
                      onChange={(e) => handleItemChange(index, 'price', parseFloat(e.target.value) || 0)}
                      className="form-input"
                      step="0.01"
                      min="0"
                      required
                    />
                  </div>

                  <div className="order-item-total">
                    <label className="form-label-small">Total</label>
                    <div className="item-total-value">
                      {((parseInt(item.quantity) || 0) * (parseFloat(item.price) || 0)).toFixed(2)} kr
                    </div>
                  </div>

                  {orderItems.length > 1 && (
                    <button
                      type="button"
                      className="btn-remove"
                      onClick={() => handleRemoveProduct(index)}
                      title="Fjern produkt"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>

            <div className="order-summary">
              <div className="order-summary-row">
                <span className="order-summary-label">Totalt antall produkter:</span>
                <span className="order-summary-value">{orderItems.filter(i => i.product_id).length}</span>
              </div>
              <div className="order-summary-row order-summary-total">
                <span className="order-summary-label">Totalpris:</span>
                <span className="order-summary-value">{calculateTotal().toFixed(2)} kr</span>
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={() => navigate('/orders')}>
              Avbryt
            </button>
            <button type="submit" className="btn-primary">
              Opprett ordre
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewOrder;
