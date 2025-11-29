import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Reports = () => {
  const { token } = useAuth();
  const [dailyReport, setDailyReport] = useState(null);
  const [monthlyReport, setMonthlyReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const [dailyRes, monthlyRes] = await Promise.all([
          axios.get(`${API_URL}/reports/daily`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API_URL}/reports/monthly`, { headers: { Authorization: `Bearer ${token}` } })
        ]);
        setDailyReport(dailyRes.data);
        setMonthlyReport(monthlyRes.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching reports:', error);
        setLoading(false);
      }
    };

    fetchReports();
  }, [token]);

  if (loading) return <div className="loading">Laster...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📊 Rapporter</h1>
          <p className="page-subtitle">Salgsrapporter og analytics</p>
        </div>
      </div>

      <div className="reports-grid">
        <div className="report-card">
          <h2>Dagens rapport</h2>
          <div className="report-stats">
            <div className="report-stat">
              <span className="report-label">Salg</span>
              <span className="report-value">{dailyReport?.daily_sales?.toFixed(0) || 0} kr</span>
            </div>
            <div className="report-stat">
              <span className="report-label">Profit</span>
              <span className="report-value">{dailyReport?.daily_profit?.toFixed(0) || 0} kr</span>
            </div>
            <div className="report-stat">
              <span className="report-label">Ordrer</span>
              <span className="report-value">{dailyReport?.orders_today || 0}</span>
            </div>
            <div className="report-stat">
              <span className="report-label">Lavt lager</span>
              <span className="report-value">{dailyReport?.low_stock_count || 0}</span>
            </div>
          </div>
        </div>

        <div className="report-card">
          <h2>Månedlig rapport</h2>
          <div className="report-stats">
            <div className="report-stat">
              <span className="report-label">Salg</span>
              <span className="report-value">{monthlyReport?.monthly_sales?.toFixed(0) || 0} kr</span>
            </div>
            <div className="report-stat">
              <span className="report-label">Profit</span>
              <span className="report-value">{monthlyReport?.monthly_profit?.toFixed(0) || 0} kr</span>
            </div>
            <div className="report-stat">
              <span className="report-label">Ordrer</span>
              <span className="report-value">{monthlyReport?.orders_count || 0}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="reports-tables">
        <div className="report-table-card">
          <h3>Top 10 Produkter</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Produkt</th>
                <th>Antall</th>
                <th>Omsetning</th>
              </tr>
            </thead>
            <tbody>
              {monthlyReport?.top_products?.map((product, idx) => (
                <tr key={idx}>
                  <td>{product.name}</td>
                  <td>{product.quantity}</td>
                  <td>{Math.round(product.revenue)} kr</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="report-table-card">
          <h3>Top 10 Kunder</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Kunde</th>
                <th>Ordrer</th>
                <th>Omsetning</th>
              </tr>
            </thead>
            <tbody>
              {monthlyReport?.top_customers?.map((customer, idx) => (
                <tr key={idx}>
                  <td>{customer.name}</td>
                  <td>{customer.orders}</td>
                  <td>{Math.round(customer.revenue)} kr</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Reports;
