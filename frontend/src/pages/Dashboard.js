import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Dashboard = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await axios.get(`${API_URL}/dashboard`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard:', error);
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [token]);

  if (loading) return <div className="loading">Laster dashboard...</div>;
  if (!data) return <div className="loading">Kunne ikke laste dashboard</div>;

  const { top_panel, tasks, sales_profit_graphs, products, customers, channel_performance } = data;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">🏠 Dashboard</h1>
          <p className="page-subtitle">ZenVit CRM - Oversikt</p>
        </div>
      </div>

      {/* Top Panel - KPIs */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div>
            <div className="stat-value">{Math.round(top_panel.today_sales)} kr</div>
            <div className="stat-label">Salg i dag</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div>
            <div className="stat-value">{Math.round(top_panel.today_profit)} kr</div>
            <div className="stat-label">Profit i dag</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🛒</div>
          <div>
            <div className="stat-value">{top_panel.orders_today}</div>
            <div className="stat-label">Ordrer i dag</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div>
            <div className="stat-value">{top_panel.low_stock}</div>
            <div className="stat-label">Lavt lager</div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Today's Tasks */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>✓ Dagens oppgaver</h3>
            <button className="btn-small btn-secondary" onClick={() => navigate('/tasks')}>
              Se alle
            </button>
          </div>
          <div className="task-list">
            {tasks.today_top3.length === 0 ? (
              <p className="empty-message">Ingen oppgaver for i dag</p>
            ) : (
              tasks.today_top3.map(task => (
                <div key={task.id} className="task-item">
                  <div className="task-title">{task.title}</div>
                  <div className="task-meta">
                    <span className={`badge badge-${task.priority === 'High' ? 'danger' : 'warning'}`}>
                      {task.priority}
                    </span>
                    <span className="task-type">{task.type}</span>
                  </div>
                </div>
              ))
            )}
            {tasks.overdue.length > 0 && (
              <div className="task-alert">
                <strong>⚠️ {tasks.overdue.length} forfalte oppgaver</strong>
              </div>
            )}
          </div>
        </div>

        {/* Monthly Sales Graph */}
        <div className="dashboard-card">
          <h3>📊 Månedlig salg & profit (siste 6 mnd)</h3>
          <div className="chart-container">
            <div className="bar-chart">
              {sales_profit_graphs.monthly_sales.map((month, idx) => {
                const maxValue = Math.max(
                  ...sales_profit_graphs.monthly_sales.map(m => m.value),
                  ...sales_profit_graphs.monthly_profit.map(m => m.value)
                );
                const salesHeight = maxValue > 0 ? (month.value / maxValue) * 100 : 0;
                const profitHeight = maxValue > 0 ? (sales_profit_graphs.monthly_profit[idx].value / maxValue) * 100 : 0;
                
                return (
                  <div key={idx} className="bar-group">
                    <div className="bar-wrapper">
                      <div className="bar bar-sales" style={{ height: `${salesHeight}%` }} title={`Salg: ${Math.round(month.value)} kr`}></div>
                      <div className="bar bar-profit" style={{ height: `${profitHeight}%` }} title={`Profit: ${Math.round(sales_profit_graphs.monthly_profit[idx].value)} kr`}></div>
                    </div>
                    <div className="bar-label">{month.month}</div>
                  </div>
                );
              })}
            </div>
            <div className="chart-legend">
              <span><span className="legend-dot legend-sales"></span> Salg</span>
              <span><span className="legend-dot legend-profit"></span> Profit</span>
            </div>
          </div>
        </div>

        {/* Best Sellers */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>💊 Bestselgere (siste 30 dager)</h3>
            <button className="btn-small btn-secondary" onClick={() => navigate('/products')}>
              Se alle
            </button>
          </div>
          <div className="product-list">
            {products.best_sellers.length === 0 ? (
              <p className="empty-message">Ingen produktsalg ennå</p>
            ) : (
              products.best_sellers.map((product, idx) => (
                <div key={idx} className="product-item">
                  <div className="product-rank">{idx + 1}</div>
                  <div className="product-info">
                    <div className="product-name">{product.name}</div>
                    <div className="product-stats">
                      <span>{product.quantity} stk</span>
                      <span className="product-revenue">{Math.round(product.revenue)} kr</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Most Profitable */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>📈 Mest lønnsome</h3>
          </div>
          <div className="product-list">
            {products.most_profitable.length === 0 ? (
              <p className="empty-message">Ingen produktsalg ennå</p>
            ) : (
              products.most_profitable.map((product, idx) => (
                <div key={idx} className="product-item">
                  <div className="product-rank">{idx + 1}</div>
                  <div className="product-info">
                    <div className="product-name">{product.name}</div>
                    <div className="product-stats">
                      <span className="text-success">{Math.round(product.profit)} kr profit</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* VIP Customers */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>👑 VIP-kunder</h3>
            <button className="btn-small btn-secondary" onClick={() => navigate('/customers')}>
              Se alle
            </button>
          </div>
          <div className="customer-list">
            {customers.vip.length === 0 ? (
              <p className="empty-message">Ingen VIP-kunder ennå</p>
            ) : (
              customers.vip.map(customer => (
                <div key={customer.id} className="customer-item" onClick={() => navigate(`/customers/${customer.id}`)}>
                  <div className="customer-name">{customer.name}</div>
                  <div className="customer-meta">
                    <span>{Math.round(customer.total_value || 0)} kr</span>
                    <span className="customer-orders">{customer.order_count || 0} ordrer</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* New Customers */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>🆕 Nye kunder</h3>
          </div>
          <div className="customer-list">
            {customers.new_this_week.length === 0 ? (
              <p className="empty-message">Ingen nye kunder</p>
            ) : (
              customers.new_this_week.map(customer => (
                <div key={customer.id} className="customer-item" onClick={() => navigate(`/customers/${customer.id}`)}>
                  <div className="customer-name">{customer.name}</div>
                  <div className="customer-meta">
                    <span className="badge badge-omega">{customer.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Low Stock Alert */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>📦 Lavt lagernivå</h3>
            <button className="btn-small btn-secondary" onClick={() => navigate('/stock')}>
              Se lager
            </button>
          </div>
          <div className="stock-list">
            {products.low_stock.length === 0 ? (
              <p className="empty-message">Alle produkter har OK lagernivå</p>
            ) : (
              products.low_stock.map(item => (
                <div key={item.id} className="stock-item">
                  <div className="stock-info">
                    <div className="stock-name">{item.product_name}</div>
                    <div className="stock-details">
                      <span className="stock-quantity">{item.quantity} stk</span>
                      <span className={`badge badge-${item.status === 'Low' ? 'warning' : 'danger'}`}>
                        {item.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Channel Performance */}
        <div className="dashboard-card">
          <div className="dashboard-card-header">
            <h3>📢 Kanalytelse (siste 30 dager)</h3>
          </div>
          <div className="channel-list">
            {channel_performance.length === 0 ? (
              <p className="empty-message">Ingen salgsdata ennå</p>
            ) : (
              channel_performance.map(channel => (
                <div key={channel.channel} className="channel-item">
                  <div className="channel-name">{channel.channel}</div>
                  <div className="channel-stats">
                    <span>{channel.orders} ordrer</span>
                    <span className="channel-revenue">{Math.round(channel.revenue)} kr</span>
                    <span className="text-success">{Math.round(channel.profit)} kr profit</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
