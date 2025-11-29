import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Search = () => {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const performSearch = async () => {
      if (!query) {
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`${API_URL}/search?q=${encodeURIComponent(query)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setResults(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error searching:', error);
        setLoading(false);
      }
    };

    performSearch();
  }, [query, token]);

  if (loading) return <div className="loading">Søker...</div>;
  if (!query) return <div className="crm-page"><h2>Ingen søkeord angitt</h2></div>;
  if (!results) return <div className="loading">Feil ved søk</div>;

  const totalResults = Object.values(results).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🔍 Søkeresultater</h1>
          <p className="page-subtitle">Søk etter: "{query}" - {totalResults} resultater</p>
        </div>
      </div>

      {results.products.length > 0 && (
        <div className="search-section">
          <h3>Produkter ({results.products.length})</h3>
          <div className="grid">
            {results.products.map(product => (
              <div key={product.id} className="card-item clickable" onClick={() => navigate('/products')}>
                <div className="card-title">{product.name}</div>
                <p className="card-text">SKU: {product.sku}</p>
                <p className="card-text">{product.price} kr</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.customers.length > 0 && (
        <div className="search-section">
          <h3>Kunder ({results.customers.length})</h3>
          <div className="grid">
            {results.customers.map(customer => (
              <div key={customer.id} className="card-item clickable" onClick={() => navigate(`/customers/${customer.id}`)}>
                <div className="card-title">{customer.name}</div>
                <p className="card-text">{customer.email}</p>
                <p className="card-text">Status: {customer.status}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.orders.length > 0 && (
        <div className="search-section">
          <h3>Ordrer ({results.orders.length})</h3>
          <div className="grid">
            {results.orders.map(order => (
              <div key={order.id} className="card-item clickable" onClick={() => navigate('/orders')}>
                <div className="card-title">{order.customer_name}</div>
                <p className="card-text">Ordre: {order.id.substring(0, 8)}</p>
                <p className="card-text">{Math.round(order.order_total)} kr</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.tasks.length > 0 && (
        <div className="search-section">
          <h3>Oppgaver ({results.tasks.length})</h3>
          <div className="grid">
            {results.tasks.map(task => (
              <div key={task.id} className="card-item clickable" onClick={() => navigate('/tasks')}>
                <div className="card-title">{task.title}</div>
                <p className="card-text">{task.description}</p>
                <span className={`badge badge-${task.priority === 'High' ? 'danger' : 'warning'}`}>{task.priority}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {totalResults === 0 && (
        <div className="no-results">
          <p>Ingen resultater funnet for "{query}"</p>
        </div>
      )}
    </div>
  );
};

export default Search;
