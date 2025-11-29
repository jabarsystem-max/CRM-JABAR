import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Dashboard = () => {
  const { user, token } = useAuth();
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');
  const [stats, setStats] = useState(null);
  const [monthly, setMonthly] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const pad = (n) => String(n).padStart(2, '0');

      const hours = pad(now.getHours());
      const minutes = pad(now.getMinutes());
      setTimeStr(`${hours}:${minutes}`);

      const weekdays = [
        'Søndag',
        'Mandag',
        'Tirsdag',
        'Onsdag',
        'Torsdag',
        'Fredag',
        'Lørdag',
      ];
      const months = [
        'januar',
        'februar',
        'mars',
        'april',
        'mai',
        'juni',
        'juli',
        'august',
        'september',
        'oktober',
        'november',
        'desember',
      ];

      const w = weekdays[now.getDay()];
      const d = now.getDate();
      const m = months[now.getMonth()];
      const y = now.getFullYear();

      setDateStr(`${w}, ${d}. ${m} ${y}`);
    };

    updateClock();
    const id = setInterval(updateClock, 15000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, monthlyRes] = await Promise.all([
          axios.get(`${API_URL}/dashboard/stats`, {
            headers: { Authorization: `Bearer ${token}` }
          }),
          axios.get(`${API_URL}/dashboard/monthly`, {
            headers: { Authorization: `Bearer ${token}` }
          })
        ]);
        setStats(statsRes.data);
        setMonthly(monthlyRes.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setLoading(false);
      }
    };

    fetchData();
    // Refresh every 5 minutes
    const interval = setInterval(fetchData, 300000);
    return () => clearInterval(interval);
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500"></div>
      </div>
    );
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat('nb-NO').format(Math.round(num));
  };

  return (
    <div className="dashboard-container">
      <div className="main-left">
        {/* HEADER */}
        <header className="main-header">
          <div className="header-left">
            <div className="header-greeting">{dateStr}</div>
            <div className="header-title">God morgen, {user?.full_name?.split(' ')[0] || 'Admin'} 👋</div>
            <div className="header-sub">
              ZenVit-oversikt for innkjøp, lager og salg i dag.
            </div>
          </div>
          <div className="header-right">
            <div className="time-badge">
              <span className="time-dot" />
              <span>{timeStr}</span>
            </div>
            <div className="user-pill">
              <div className="user-avatar">{user?.full_name?.charAt(0) || 'A'}</div>
              <span className="user-name">{user?.full_name || 'Admin'}</span>
            </div>
          </div>
        </header>

        {/* KPI CARDS */}
        <section className="kpi-row">
          <article className="kpi-card kpi-omega">
            <div className="kpi-top">
              <div className="kpi-label">Dagens salg</div>
              <div className="kpi-icon">🛒</div>
            </div>
            <div className="kpi-value">{stats?.today?.orders || 0}&nbsp;ordrer</div>
            <div className="kpi-sub">Oms. i dag: {formatNumber(stats?.today?.revenue || 0)} kr</div>
          </article>

          <article className="kpi-card kpi-d3">
            <div className="kpi-top">
              <div className="kpi-label">Dagens profit (est.)</div>
              <div className="kpi-icon">💰</div>
            </div>
            <div className="kpi-value">{formatNumber(stats?.today?.profit || 0)} kr</div>
            <div className="kpi-sub">Etter varekost, før faste kostn.</div>
          </article>

          <article className="kpi-card kpi-mag">
            <div className="kpi-top">
              <div className="kpi-label">Lagerverdi</div>
              <div className="kpi-icon">📦</div>
            </div>
            <div className="kpi-value">{formatNumber(stats?.inventory?.total_value || 0)} kr</div>
            <div className="kpi-sub">Basert på innkjøpspris.</div>
          </article>

          <article className="kpi-card kpi-csink">
            <div className="kpi-top">
              <div className="kpi-label">Lavt lager</div>
              <div className="kpi-icon">⚠️</div>
            </div>
            <div className="kpi-value">{stats?.inventory?.low_stock_count || 0} produkter</div>
            <div className="kpi-sub">Trenger innkjøp i løpet av uken.</div>
          </article>
        </section>

        {/* MID CARDS */}
        <section className="mid-grid">
          {/* Lagerkort */}
          <article className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Lagerstatus – ZenVit</div>
                <div className="card-subtitle">
                  Rask oversikt over hovedproduktene.
                </div>
              </div>
              <div className="pill">Oppdatert nå</div>
            </div>

            <div className="stat-row">
              <span className="stat-label">Totalt antall på lager</span>
              <span className="stat-value">
                {formatNumber(
                  stats?.inventory?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0
                )} stk
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">
                Totalt antall aktive produkter
              </span>
              <span className="stat-value">{stats?.inventory?.items?.length || 0}</span>
            </div>

            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '62%' }} />
            </div>
            <div className="card-subtitle">
              62&nbsp;% av ønsket lagerkapasitet er fylt.
            </div>

            <div className="product-list">
              {stats?.inventory?.items?.map((item, idx) => (
                <div key={idx} className="product-pill">
                  <div className="product-pill-label">
                    <span className={`dot dot-${item.color || 'omega'}`} />
                    <span>{item.product_name}</span>
                  </div>
                  <span>{item.quantity} stk</span>
                </div>
              ))}
            </div>
          </article>

          {/* Månedskort */}
          <article className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Månedstall – ZenVit</div>
                <div className="card-subtitle">
                  Tidsrom: inneværende måned.
                </div>
              </div>
              <div className="pill">Måned</div>
            </div>

            <div className="stat-row">
              <span className="stat-label">Omsetning</span>
              <span className="stat-value">{formatNumber(monthly?.revenue || 0)} kr</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Varekost (COGS)</span>
              <span className="stat-value">{formatNumber(monthly?.cogs || 0)} kr</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Andre kostnader</span>
              <span className="stat-value">{formatNumber(monthly?.other_costs || 0)} kr</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Estimert netto</span>
              <span className="stat-value">{formatNumber(monthly?.profit || 0)} kr</span>
            </div>

            <div className="card-subtitle">Bestselgere denne måneden:</div>
            <div className="product-list">
              {monthly?.top_products?.map((product, idx) => (
                <div key={idx} className="product-pill">
                  <div className="product-pill-label">
                    <span className={`dot dot-${product.color || 'omega'}`} />
                    <span>{product.name}</span>
                  </div>
                  <span>{product.percentage} % av salget</span>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>

      {/* RIGHT SIDE */}
      <section className="main-right">
        {/* STATUS CARD */}
        <article className="status-card">
          <div className="status-header">
            <div>
              <div className="status-title">ZenVit status – i dag</div>
              <div className="status-sub">
                Live-oversikt for nettbutikken.
              </div>
            </div>
            <div className="status-chip">Kun internt · CRM</div>
          </div>
          <div className="status-main">
            <div className="status-value">{formatNumber(stats?.today?.profit || 0)} kr</div>
            <div className="status-caption">
              Estimert profit så langt i dag (oppdatert hvert 10. minutt).
            </div>
            <div className="status-grid">
              <div className="status-item">
                <span className="status-item-label">Ordre i dag</span>
                <span className="status-item-value">{stats?.today?.orders || 0}</span>
              </div>
              <div className="status-item">
                <span className="status-item-label">Snittordre</span>
                <span className="status-item-value">{formatNumber(stats?.today?.avg_order || 0)} kr</span>
              </div>
              <div className="status-item">
                <span className="status-item-label">Returer</span>
                <span className="status-item-value">0</span>
              </div>
            </div>
          </div>
        </article>

        {/* MINI CARDS */}
        <section className="mini-status-grid">
          {stats?.inventory?.items?.slice(0, 4).map((item, idx) => {
            const cardClasses = ['mini-imm', 'mini-vinter', 'mini-omega', 'mini-mag'];
            return (
              <article key={idx} className={`mini-card ${cardClasses[idx] || 'mini-omega'}`}>
                <div className="mini-main">
                  <div className="mini-title">{item.product_name}</div>
                  <div className="mini-sub">ZenVit produkt</div>
                  <div className="mini-meta">
                    Lager: {item.quantity} stk
                  </div>
                </div>
                <div className="mini-value">{item.quantity}</div>
              </article>
            );
          })}
        </section>
      </section>
    </div>
  );
};

export default Dashboard;
