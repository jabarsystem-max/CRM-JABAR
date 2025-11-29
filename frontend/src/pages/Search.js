import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Search = () => {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchInput, setSearchInput] = useState(query || '');

  useEffect(() => {
    const performSearch = async () => {
      if (!query) {
        setLoading(false);
        return;
      }

      setLoading(true);
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

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ q: searchInput.trim() });
    }
  };

  const totalResults = results ? Object.values(results).reduce((sum, arr) => sum + arr.length, 0) : 0;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🔍 Søk</h1>
          <p className="page-subtitle">Søk på tvers av produkter, kunder, ordrer og oppgaver</p>
        </div>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Søk etter produkter, kunder, ordrer..."
          className="search-input-large"
        />
        <button type="submit" className="btn-primary">
          🔍 Søk
        </button>
      </form>

      {loading && <div className="loading">Søker...</div>}
      
      {!loading && query && results && (
        <>
          <div className="search-results-header">
            <p className="page-subtitle">Søkeresultater for: "{query}" - {totalResults} treff</p>
          </div>

          {results.products && results.products.length > 0 && (
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
        </>
      )}
    </div>
  );
};

export default Search;
