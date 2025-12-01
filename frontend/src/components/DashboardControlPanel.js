import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardControlPanel.css';

const DashboardControlPanel = ({ data }) => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, []);

  const formatDateTime = (date) => {
    const days = ['Søndag', 'Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lørdag'];
    const months = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember'];
    
    const dayName = days[date.getDay()];
    const day = date.getDate();
    const month = months[date.getMonth()];
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${dayName} ${day}. ${month} – ${hours}:${minutes}`;
  };

  const handleQuickAction = (action) => {
    switch(action) {
      case 'order':
        navigate('/orders/new');
        break;
      case 'product':
        navigate('/products', { state: { openModal: true } });
        break;
      case 'purchase':
        navigate('/purchases/new');
        break;
      default:
        break;
    }
  };

  return (
    <div className="control-panel">
      <div className="control-panel-container">
        {/* Left: Time & Date */}
        <div className="cp-section cp-datetime">
          <div className="cp-icon">📅</div>
          <div className="cp-datetime-text">
            <div className="cp-datetime-main">{formatDateTime(currentTime)}</div>
            <div className="cp-datetime-sub">Dagens Kontrollpanel</div>
          </div>
        </div>

        {/* Middle: Quick Actions */}
        <div className="cp-section cp-actions">
          <button 
            className="cp-action-btn"
            onClick={() => handleQuickAction('order')}
          >
            <span className="cp-action-icon">🛒</span>
            <span className="cp-action-label">Ny ordre</span>
          </button>
          <button 
            className="cp-action-btn"
            onClick={() => handleQuickAction('product')}
          >
            <span className="cp-action-icon">📦</span>
            <span className="cp-action-label">Nytt produkt</span>
          </button>
          <button 
            className="cp-action-btn"
            onClick={() => handleQuickAction('purchase')}
          >
            <span className="cp-action-icon">🚚</span>
            <span className="cp-action-label">Ny innkjøp</span>
          </button>
        </div>

        {/* Right: Alerts & Today Stats */}
        <div className="cp-section cp-info">
          {/* Alerts */}
          <div className="cp-alerts">
            {data?.alerts?.lowStock > 0 && (
              <div 
                className="cp-alert cp-alert-warning"
                onClick={() => navigate('/products/low-stock')}
              >
                <span className="cp-alert-icon">⚠️</span>
                <span className="cp-alert-text">{data.alerts.lowStock} produkter lavt lager</span>
              </div>
            )}
            {data?.alerts?.pendingOrders > 0 && (
              <div 
                className="cp-alert cp-alert-info"
                onClick={() => navigate('/orders', { state: { filter: 'pending' } })}
              >
                <span className="cp-alert-icon">⏳</span>
                <span className="cp-alert-text">{data.alerts.pendingOrders} bestillinger venter</span>
              </div>
            )}
            {data?.alerts?.incomingPurchases > 0 && (
              <div 
                className="cp-alert cp-alert-success"
                onClick={() => navigate('/purchases', { state: { filter: 'incoming' } })}
              >
                <span className="cp-alert-icon">📥</span>
                <span className="cp-alert-text">{data.alerts.incomingPurchases} innkjøp på vei</span>
              </div>
            )}
          </div>

          {/* Today Stats */}
          <div className="cp-stats">
            <div className="cp-stat">
              <div className="cp-stat-value">{data?.todayStats?.sales?.toLocaleString('no-NO') || 0} kr</div>
              <div className="cp-stat-label">Dagens salg</div>
            </div>
            <div className="cp-stat">
              <div className="cp-stat-value">{data?.todayStats?.orders || 0}</div>
              <div className="cp-stat-label">Ordre i dag</div>
            </div>
            <div className="cp-stat">
              <div className="cp-stat-value">{data?.todayStats?.newPurchases || 0}</div>
              <div className="cp-stat-label">Nye innkjøp</div>
            </div>
            <div className="cp-stat">
              <div className={`cp-stat-value ${(data?.todayStats?.inventoryChange || 0) >= 0 ? 'positive' : 'negative'}`}>
                {(data?.todayStats?.inventoryChange || 0) >= 0 ? '+' : ''}{data?.todayStats?.inventoryChange?.toLocaleString('no-NO') || 0} kr
              </div>
              <div className="cp-stat-label">Lagerverdi endring</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardControlPanel;
