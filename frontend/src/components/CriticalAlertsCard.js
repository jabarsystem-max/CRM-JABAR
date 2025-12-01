import React from 'react';
import { useNavigate } from 'react-router-dom';
import './CriticalAlertsCard.css';

const CriticalAlertsCard = ({ alerts }) => {
  const navigate = useNavigate();

  // Don't render if no alerts
  if (!alerts || (alerts.lowStock === 0 && alerts.pendingOrders === 0 && alerts.incomingPurchases === 0)) {
    return null;
  }

  return (
    <div className="critical-alerts-card">
      <div className="alerts-header">
        <h3 className="alerts-title">⚠️ Kritiske varsler</h3>
      </div>

      <div className="alerts-grid">
        {alerts.lowStock > 0 && (
          <div 
            className="alert-item alert-warning"
            onClick={() => navigate('/products/low-stock')}
          >
            <div className="alert-icon">⚠️</div>
            <div className="alert-content">
              <div className="alert-number">{alerts.lowStock}</div>
              <div className="alert-label">Produkter lavt lager</div>
            </div>
          </div>
        )}

        {alerts.pendingOrders > 0 && (
          <div 
            className="alert-item alert-info"
            onClick={() => navigate('/orders', { state: { filter: 'pending' } })}
          >
            <div className="alert-icon">⏳</div>
            <div className="alert-content">
              <div className="alert-number">{alerts.pendingOrders}</div>
              <div className="alert-label">Bestillinger venter</div>
            </div>
          </div>
        )}

        {alerts.incomingPurchases > 0 && (
          <div 
            className="alert-item alert-success"
            onClick={() => navigate('/purchases', { state: { filter: 'incoming' } })}
          >
            <div className="alert-icon">📥</div>
            <div className="alert-content">
              <div className="alert-number">{alerts.incomingPurchases}</div>
              <div className="alert-label">Innkjøp på vei</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CriticalAlertsCard;
