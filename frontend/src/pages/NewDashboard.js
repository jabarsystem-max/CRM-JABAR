import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './NewDashboard.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const NewDashboard = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [timeFilter, setTimeFilter] = useState('month');

  const fetchDashboardData = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/dashboard/kpis`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchDashboardData();
    }
  }, [token, fetchDashboardData]);

  const handleKPIClick = (destination, filter = null) => {
    if (filter) {
      navigate(destination, { state: { filter } });
    } else {
      navigate(destination);
    }
  };

  if (loading) {
    return <div className="loading">Laster dashboard...</div>;
  }

  if (!dashboardData) {
    return <div className="loading">Kunne ikke laste dashboarddata</div>;
  }

  const { kpis, chart_data, tables } = dashboardData;

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Dashboard</h1>
        <p className="dashboard-subtitle">Oversikt over din virksomhet</p>
      </div>

      {/* KPI Cards - 2 rows x 3 columns */}
      <div className="kpi-grid">
        {/* Row 1 */}
        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/products')}
        >
          <div className="kpi-icon green">📦</div>
          <h3 className="kpi-title">Produkter totalt</h3>
          <p className="kpi-value">{kpis.total_products}</p>
          <p className="kpi-subtitle">Aktive produkter i systemet</p>
        </div>

        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/products', { lowStock: true })}
        >
          <div className="kpi-icon red">⚠️</div>
          <h3 className="kpi-title">Lavt lager</h3>
          <p className="kpi-value">{kpis.low_stock}</p>
          <p className="kpi-subtitle">Produkter under minimum</p>
        </div>

        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/orders', { thisMonth: true })}
        >
          <div className="kpi-icon blue">📊</div>
          <h3 className="kpi-title">Salg denne måneden</h3>
          <p className="kpi-value">{kpis.sales_this_month.count}</p>
          <p className="kpi-subtitle">{kpis.sales_this_month.revenue.toLocaleString('no-NO')} kr omsetning</p>
        </div>

        {/* Row 2 */}
        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/purchases', { incoming: true })}
        >
          <div className="kpi-icon purple">🚚</div>
          <h3 className="kpi-title">Innkjøp på vei</h3>
          <p className="kpi-value">{kpis.incoming_purchases}</p>
          <p className="kpi-subtitle">Bestillinger underveis</p>
        </div>

        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/stock')}
        >
          <div className="kpi-icon yellow">💰</div>
          <h3 className="kpi-title">Lagerverdi totalt</h3>
          <p className="kpi-value">{Math.round(kpis.inventory_value / 1000)}k</p>
          <p className="kpi-subtitle">{kpis.inventory_value.toLocaleString('no-NO')} kr</p>
        </div>

        <div 
          className="kpi-card" 
          onClick={() => handleKPIClick('/customers', { active: true })}
        >
          <div className="kpi-icon orange">👥</div>
          <h3 className="kpi-title">Aktive kunder (mnd.)</h3>
          <p className="kpi-value">{kpis.active_customers}</p>
          <p className="kpi-subtitle">Kunder med ordre denne måneden</p>
        </div>
      </div>

      {/* Charts and Tables */}
      <div className="dashboard-content">
        {/* Left: Chart */}
        <div className="chart-card">
          <div className="card-header">
            <h2 className="card-title">Siste 30 dager</h2>
            <div className="time-filters">
              <button 
                className={`time-filter-btn ${timeFilter === 'week' ? 'active' : ''}`}
                onClick={() => setTimeFilter('week')}
              >
                Uke
              </button>
              <button 
                className={`time-filter-btn ${timeFilter === 'month' ? 'active' : ''}`}
                onClick={() => setTimeFilter('month')}
              >
                Måned
              </button>
              <button 
                className={`time-filter-btn ${timeFilter === 'year' ? 'active' : ''}`}
                onClick={() => setTimeFilter('year')}
              >
                År
              </button>
            </div>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chart_data.last_30_days}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                  dataKey="date" 
                  stroke="#6B7280"
                  style={{ fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getDate()}/${date.getMonth() + 1}`;
                  }}
                />
                <YAxis 
                  yAxisId="left"
                  stroke="#6B7280"
                  style={{ fontSize: 12 }}
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right"
                  stroke="#6B7280"
                  style={{ fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="orders" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  name="Antall ordre"
                  dot={{ r: 3 }}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#27AE60" 
                  strokeWidth={2}
                  name="Omsetning (kr)"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Tables */}
        <div className="tables-grid">
          {/* Low Stock Table */}
          <div className="table-card">
            <div className="card-header">
              <h2 className="card-title">Lavt lager (topp 5)</h2>
            </div>
            
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Produkt</th>
                  <th>Lager</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {tables.low_stock.length > 0 ? (
                  tables.low_stock.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.product_name}</td>
                      <td>{item.current_stock} / {item.min_stock}</td>
                      <td>
                        <span className={`status-badge ${item.status.toLowerCase()}`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" style={{ textAlign: 'center', padding: '20px', color: '#9CA3AF' }}>
                      Ingen produkter med lavt lager
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Recent Orders Table */}
          <div className="table-card">
            <div className="card-header">
              <h2 className="card-title">Siste ordrer (5 stk)</h2>
            </div>
            
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Dato</th>
                  <th>Kunde</th>
                  <th>Sum</th>
                </tr>
              </thead>
              <tbody>
                {tables.recent_orders.length > 0 ? (
                  tables.recent_orders.map((order) => (
                    <tr key={order.id}>
                      <td>{order.date}</td>
                      <td>{order.customer}</td>
                      <td>{order.total} kr</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" style={{ textAlign: 'center', padding: '20px', color: '#9CA3AF' }}>
                      Ingen ordrer ennå
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewDashboard;
