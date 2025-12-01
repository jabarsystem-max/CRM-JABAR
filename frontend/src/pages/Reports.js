import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';
import './Reports.css';

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

  if (loading) return <div className="loading">Laster rapporter...</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">📈 Rapporter</h1>
          <p className="page-subtitle">Salgsrapporter og analytics</p>
        </div>
      </div>

      {/* Dagens rapport */}
      <div className="report-section">
        <div className="report-section-header">
          <h2 className="report-section-title">📅 Dagens rapport</h2>
          <span className="report-date">{new Date().toLocaleDateString('no-NO')}</span>
        </div>
        
        <div className="report-cards-grid">
          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #D1FAE5 0%, #27AE60 100%)' }}>💰</div>
            <div className="metric-content">
              <div className="metric-label">Salg i dag</div>
              <div className="metric-value">{dailyReport?.daily_sales?.toFixed(0) || 0} kr</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #DBEAFE 0%, #3B82F6 100%)' }}>📦</div>
            <div className="metric-content">
              <div className="metric-label">Ordre i dag</div>
              <div className="metric-value">{dailyReport?.daily_orders || 0}</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #FEF3C7 0%, #F59E0B 100%)' }}>📈</div>
            <div className="metric-content">
              <div className="metric-label">Fortjeneste i dag</div>
              <div className="metric-value">{dailyReport?.daily_profit?.toFixed(0) || 0} kr</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #E9D5FF 0%, #8B5CF6 100%)' }}>👥</div>
            <div className="metric-content">
              <div className="metric-label">Unike kunder</div>
              <div className="metric-value">{dailyReport?.unique_customers || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Månedsrapport */}
      <div className="report-section">
        <div className="report-section-header">
          <h2 className="report-section-title">📆 Månedsrapport</h2>
          <span className="report-date">{new Date().toLocaleDateString('no-NO', { month: 'long', year: 'numeric' })}</span>
        </div>
        
        <div className="report-cards-grid">
          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #D1FAE5 0%, #27AE60 100%)' }}>💵</div>
            <div className="metric-content">
              <div className="metric-label">Total omsetning</div>
              <div className="metric-value">{monthlyReport?.monthly_sales?.toFixed(0) || 0} kr</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #DBEAFE 0%, #3B82F6 100%)' }}>📊</div>
            <div className="metric-content">
              <div className="metric-label">Totale ordre</div>
              <div className="metric-value">{monthlyReport?.monthly_orders || 0}</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #FEF3C7 0%, #F59E0B 100%)' }}>🎯</div>
            <div className="metric-content">
              <div className="metric-label">Total fortjeneste</div>
              <div className="metric-value">{monthlyReport?.monthly_profit?.toFixed(0) || 0} kr</div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #E9D5FF 0%, #8B5CF6 100%)' }}>👑</div>
            <div className="metric-content">
              <div className="metric-label">Aktive kunder</div>
              <div className="metric-value">{monthlyReport?.unique_customers || 0}</div>
            </div>
          </div>
        </div>

        {/* Gjennomsnitt */}
        <div className="report-cards-grid" style={{ marginTop: '16px' }}>
          <div className="report-metric-card">
            <div className="metric-content" style={{ textAlign: 'center' }}>
              <div className="metric-label">Gj.snitt ordre</div>
              <div className="metric-value" style={{ fontSize: '20px' }}>
                {monthlyReport?.monthly_orders > 0 
                  ? (monthlyReport.monthly_sales / monthlyReport.monthly_orders).toFixed(0) 
                  : 0} kr
              </div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-content" style={{ textAlign: 'center' }}>
              <div className="metric-label">Margin %</div>
              <div className="metric-value" style={{ fontSize: '20px' }}>
                {monthlyReport?.monthly_sales > 0 
                  ? ((monthlyReport.monthly_profit / monthlyReport.monthly_sales) * 100).toFixed(1) 
                  : 0}%
              </div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-content" style={{ textAlign: 'center' }}>
              <div className="metric-label">Ordre per dag (gj.snitt)</div>
              <div className="metric-value" style={{ fontSize: '20px' }}>
                {(monthlyReport?.monthly_orders / new Date().getDate()).toFixed(1) || 0}
              </div>
            </div>
          </div>

          <div className="report-metric-card">
            <div className="metric-content" style={{ textAlign: 'center' }}>
              <div className="metric-label">Salg per dag (gj.snitt)</div>
              <div className="metric-value" style={{ fontSize: '20px' }}>
                {(monthlyReport?.monthly_sales / new Date().getDate()).toFixed(0) || 0} kr
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Toppselgere */}
      {monthlyReport?.top_products && monthlyReport.top_products.length > 0 && (
        <div className="report-section">
          <div className="report-section-header">
            <h2 className="report-section-title">🏆 Toppselgere denne måneden</h2>
          </div>
          
          <div className="top-products-grid">
            {monthlyReport.top_products.slice(0, 5).map((product, index) => (
              <div key={product.product_name} className="top-product-card">
                <div className="top-product-rank">#{index + 1}</div>
                <div className="top-product-content">
                  <div className="top-product-name">{product.product_name}</div>
                  <div className="top-product-stats">
                    <span className="top-product-sold">{product.quantity_sold} solgt</span>
                    <span className="top-product-revenue">{product.revenue?.toFixed(0)} kr</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
