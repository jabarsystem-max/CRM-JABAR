import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();

  const menuItems = [
    { id: 'dashboard', icon: '🏠', label: 'Dashboard', path: '/dashboard' },
    { id: 'products', icon: '💊', label: 'Produkter', path: '/products' },
    { id: 'inventory', icon: '📦', label: 'Lager', path: '/inventory' },
    { id: 'purchases', icon: '📥', label: 'Innkjøp', path: '/purchases' },
    { id: 'suppliers', icon: '🤝', label: 'Leverandører', path: '/suppliers' },
    { id: 'customers', icon: '👥', label: 'Kunder', path: '/customers' },
    { id: 'orders', icon: '📊', label: 'Ordrer', path: '/orders' },
    { id: 'costs', icon: '💸', label: 'Kostnader', path: '/costs' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
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
            title="Logg ut"
            onClick={handleLogout}
          >
            <span>🚪</span>
          </button>
        </div>
      </aside>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
