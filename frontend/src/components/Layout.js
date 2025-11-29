import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const menuItems = [
    { id: 'dashboard', icon: '🏠', label: 'Dashboard', path: '/dashboard' },
    { id: 'products', icon: '💊', label: 'Produkter', path: '/products' },
    { id: 'stock', icon: '📦', label: 'Lager', path: '/stock' },
    { id: 'orders', icon: '🛒', label: 'Ordrer', path: '/orders' },
    { id: 'customers', icon: '👥', label: 'Kunder', path: '/customers' },
    { id: 'purchases', icon: '📥', label: 'Innkjøp', path: '/purchases' },
    { id: 'suppliers', icon: '🤝', label: 'Leverandører', path: '/suppliers' },
    { id: 'tasks', icon: '✓', label: 'Oppgaver', path: '/tasks' },
    { id: 'expenses', icon: '💸', label: 'Utgifter', path: '/expenses' },
    { id: 'reports', icon: '📊', label: 'Rapporter', path: '/reports' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setShowSearch(false);
      setSearchQuery('');
    }
  };

  return (
    <div className="layout-container">
      <aside className="sidebar">
        <div className="sidebar-logo" onClick={() => navigate('/dashboard')}>
          Z
        </div>
        <div className="sidebar-nav">
          {menuItems.map(item => (
            <button
              key={item.id}
              className={`sidebar-btn ${location.pathname === item.path ? 'sidebar-btn--active' : ''}`}
              title={item.label}
              onClick={() => navigate(item.path)}
            >
              <span>{item.icon}</span>
            </button>
          ))}
        </div>
        <div className="sidebar-spacer" />
        <div className="sidebar-settings">
          <button
            className="sidebar-btn"
            title="Søk"
            onClick={() => setShowSearch(!showSearch)}
          >
            <span>🔍</span>
          </button>
          <button
            className="sidebar-btn"
            title="Logg ut"
            onClick={handleLogout}
          >
            <span>🚪</span>
          </button>
        </div>
      </aside>
      
      <main className="main-content">
        {showSearch && (
          <div className="search-bar">
            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="Søk i produkter, kunder, ordrer..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                autoFocus
                className="search-input"
              />
            </form>
          </div>
        )}
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
