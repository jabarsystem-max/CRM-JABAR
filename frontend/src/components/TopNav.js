import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './TopNav.css';

const TopNav = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [darkMode, setDarkMode] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
    { path: '/products', label: 'Produkter', icon: '💊' },
    { path: '/orders', label: 'Ordrer', icon: '📦' },
    { path: '/stock', label: 'Lager', icon: '📊' },
    { path: '/purchases', label: 'Innkjøp', icon: '🛒' },
    { path: '/customers', label: 'Kunder', icon: '👥' },
    { path: '/ai', label: 'ZenVit AI', icon: '🧠' },
    { path: '/reports', label: 'Rapporter', icon: '📈' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
      setShowSearch(false);
    }
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark-mode');
  };

  return (
    <nav className="top-nav">
      <div className="top-nav-container">
        {/* Logo */}
        <div className="top-nav-logo">
          <Link to="/dashboard">
            <span className="logo-text">ZENVIT</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <div className="top-nav-menu">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </div>

        {/* Right Section */}
        <div className="top-nav-actions">
          {/* Date & Time */}
          <div className="top-nav-datetime">
            <span className="datetime-text">
              {currentTime.toLocaleDateString('no-NO', { day: 'numeric', month: 'short' })} {currentTime.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          
          {/* Search */}
          <div className="search-container">
            {showSearch ? (
              <form onSubmit={handleSearch} className="search-form">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Søk..."
                  className="search-input"
                  autoFocus
                  onBlur={() => {
                    setTimeout(() => setShowSearch(false), 200);
                  }}
                />
              </form>
            ) : (
              <button
                className="icon-btn"
                onClick={() => setShowSearch(true)}
                title="Søk"
              >
                🔍
              </button>
            )}
          </div>

          {/* Dark Mode Toggle */}
          <button
            className="icon-btn"
            onClick={toggleDarkMode}
            title={darkMode ? 'Lys modus' : 'Mørk modus'}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>

          {/* User Menu */}
          <div className="user-menu-container">
            <button
              className="user-menu-btn"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="user-avatar">
                {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="user-name">{user?.name || 'Bruker'}</span>
              <span className="dropdown-arrow">▼</span>
            </button>

            {showUserMenu && (
              <div className="user-dropdown">
                <div className="dropdown-item" onClick={() => { navigate('/settings'); setShowUserMenu(false); }}>
                  ⚙️ Innstillinger
                </div>
                <div className="dropdown-divider"></div>
                <div className="dropdown-item" onClick={handleLogout}>
                  🚪 Logg ut
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Hamburger */}
        <button
          className="mobile-menu-btn"
          onClick={() => setShowMobileMenu(!showMobileMenu)}
        >
          {showMobileMenu ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile Menu */}
      {showMobileMenu && (
        <div className="mobile-menu">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`mobile-nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => setShowMobileMenu(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
          <div className="mobile-divider"></div>
          <div className="mobile-nav-item" onClick={() => { navigate('/settings'); setShowMobileMenu(false); }}>
            ⚙️ Innstillinger
          </div>
          <div className="mobile-nav-item" onClick={handleLogout}>
            🚪 Logg ut
          </div>
        </div>
      )}
    </nav>
  );
};

export default TopNav;
