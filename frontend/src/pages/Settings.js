import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const Settings = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [accentColor, setAccentColor] = useState(() => localStorage.getItem('accentColor') || 'blue');
  const [notifications, setNotifications] = useState({
    lowStock: localStorage.getItem('notify_lowStock') !== 'false',
    newOrders: localStorage.getItem('notify_newOrders') !== 'false',
    taskDeadlines: localStorage.getItem('notify_taskDeadlines') !== 'false'
  });

  useEffect(() => {
    // Apply theme to body
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    // Apply accent color
    document.documentElement.style.setProperty('--accent-color', 
      accentColor === 'blue' ? '#3b82f6' : 
      accentColor === 'green' ? '#10b981' : 
      accentColor === 'purple' ? '#8b5cf6' : '#3b82f6'
    );
    localStorage.setItem('accentColor', accentColor);
  }, [accentColor]);

  const handleNotificationChange = (key) => {
    const newValue = !notifications[key];
    setNotifications(prev => ({
      ...prev,
      [key]: newValue
    }));
    localStorage.setItem(`notify_${key}`, newValue);
  };

  const handleExportData = () => {
    alert('Eksportfunksjonalitet kommer snart! Dette vil eksportere alle data til CSV/JSON.');
  };

  const handleResetSettings = () => {
    if (window.confirm('Er du sikker på at du vil tilbakestille alle innstillinger?')) {
      localStorage.removeItem('theme');
      localStorage.removeItem('accentColor');
      localStorage.removeItem('notify_lowStock');
      localStorage.removeItem('notify_newOrders');
      localStorage.removeItem('notify_taskDeadlines');
      setTheme('light');
      setAccentColor('blue');
      setNotifications({
        lowStock: true,
        newOrders: true,
        taskDeadlines: true
      });
      alert('Innstillinger tilbakestilt!');
    }
  };

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">⚙️ Innstillinger</h1>
          <p className="page-subtitle">Administrer kontoen og preferanser</p>
        </div>
      </div>

      <div className="settings-container">
        <div className="settings-sidebar">
          <button 
            className={`settings-tab ${activeTab === 'profile' ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            👤 Profil
          </button>
          <button 
            className={`settings-tab ${activeTab === 'appearance' ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab('appearance')}
          >
            🎨 Utseende
          </button>
          <button 
            className={`settings-tab ${activeTab === 'notifications' ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            🔔 Varsler
          </button>
          <button 
            className={`settings-tab ${activeTab === 'automation' ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab('automation')}
          >
            🤖 Automatisering
          </button>
          <button 
            className={`settings-tab ${activeTab === 'data' ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            💾 Data & Eksport
          </button>
        </div>

        <div className="settings-content">
          {activeTab === 'profile' && (
            <div className="settings-section">
              <h2>Profilinformasjon</h2>
              <div className="settings-group">
                <label className="settings-label">Fullt navn</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={user?.full_name || 'Admin User'}
                  readOnly
                />
              </div>
              <div className="settings-group">
                <label className="settings-label">E-post</label>
                <input 
                  type="email" 
                  className="form-input" 
                  value={user?.email || 'admin@zenvit.no'}
                  readOnly
                />
              </div>
              <div className="settings-group">
                <label className="settings-label">Rolle</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={user?.role || 'admin'}
                  readOnly
                />
              </div>
              <p className="settings-note">
                💡 For å endre profilinformasjon, kontakt systemadministrator.
              </p>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="settings-section">
              <h2>Utseende og tema</h2>
              
              <div className="settings-group">
                <label className="settings-label">Tema</label>
                <div className="theme-selector">
                  <button 
                    className={`theme-option ${theme === 'light' ? 'theme-option--active' : ''}`}
                    onClick={() => setTheme('light')}
                  >
                    ☀️ Lyst
                  </button>
                  <button 
                    className={`theme-option ${theme === 'dark' ? 'theme-option--active' : ''}`}
                    onClick={() => setTheme('dark')}
                  >
                    🌙 Mørkt
                  </button>
                </div>
                <p className="settings-note">
                  ℹ️ Mørkt tema kommer snart! For nå er kun lyst tema tilgjengelig.
                </p>
              </div>

              <div className="settings-group">
                <label className="settings-label">Aksentfarge</label>
                <div className="color-selector">
                  <button 
                    className={`color-option color-blue ${accentColor === 'blue' ? 'color-option--active' : ''}`}
                    onClick={() => setAccentColor('blue')}
                  >
                    Blå
                  </button>
                  <button 
                    className={`color-option color-green ${accentColor === 'green' ? 'color-option--active' : ''}`}
                    onClick={() => setAccentColor('green')}
                  >
                    Grønn
                  </button>
                  <button 
                    className={`color-option color-purple ${accentColor === 'purple' ? 'color-option--active' : ''}`}
                    onClick={() => setAccentColor('purple')}
                  >
                    Lilla
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="settings-section">
              <h2>Varslingsinnstillinger</h2>
              
              <div className="settings-group">
                <div className="settings-toggle">
                  <div>
                    <strong>Lavt lagernivå</strong>
                    <p className="settings-description">Få varsler når produkter har lavt lagernivå</p>
                  </div>
                  <label className="toggle-switch">
                    <input 
                      type="checkbox" 
                      checked={notifications.lowStock}
                      onChange={() => handleNotificationChange('lowStock')}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div className="settings-group">
                <div className="settings-toggle">
                  <div>
                    <strong>Nye ordrer</strong>
                    <p className="settings-description">Få varsler når det kommer inn nye ordrer</p>
                  </div>
                  <label className="toggle-switch">
                    <input 
                      type="checkbox" 
                      checked={notifications.newOrders}
                      onChange={() => handleNotificationChange('newOrders')}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div className="settings-group">
                <div className="settings-toggle">
                  <div>
                    <strong>Oppgavefrister</strong>
                    <p className="settings-description">Få varsler om kommende oppgavefrister</p>
                  </div>
                  <label className="toggle-switch">
                    <input 
                      type="checkbox" 
                      checked={notifications.taskDeadlines}
                      onChange={() => handleNotificationChange('taskDeadlines')}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <p className="settings-note">
                ℹ️ Varslinger er foreløpig kun for lokal lagring. Sanntidsvarsler kommer i neste versjon.
              </p>
            </div>
          )}

          {activeTab === 'automation' && (
            <div className="settings-section">
              <h2>Automatiseringsregler</h2>
              
              <div className="automation-card">
                <div className="automation-header">
                  <h3>🤖 Aktive automatiseringer</h3>
                  <span className="badge badge-success">Aktiv</span>
                </div>
                <ul className="automation-list">
                  <li>✅ Opprett oppgave ved lavt lagernivå</li>
                  <li>✅ Oppdater kundestatistikk ved nye ordrer</li>
                  <li>✅ Fullfør lageroppgaver ved påfyll</li>
                  <li>✅ Generer daglige og månedlige rapporter</li>
                </ul>
              </div>

              <div className="automation-card automation-card--disabled">
                <div className="automation-header">
                  <h3>⏳ Kommende automatiseringer</h3>
                  <span className="badge badge-omega">Planlagt</span>
                </div>
                <ul className="automation-list">
                  <li>⏳ E-postvarsler ved viktige hendelser</li>
                  <li>⏳ Automatisk kundeoppfølging</li>
                  <li>⏳ Prognose for lagerbehov</li>
                  <li>⏳ Automatiske innkjøpsforslag</li>
                </ul>
              </div>

              <p className="settings-note">
                💡 Alle automatiseringer kjører i bakgrunnen uten brukerhandling.
              </p>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="settings-section">
              <h2>Data og eksport</h2>
              
              <div className="settings-group">
                <h3>Eksporter data</h3>
                <p className="settings-description">
                  Last ned alle dine CRM-data i CSV eller JSON format
                </p>
                <button className="btn-primary" onClick={handleExportData}>
                  📥 Eksporter data
                </button>
              </div>

              <div className="settings-group">
                <h3>Tilbakestill innstillinger</h3>
                <p className="settings-description">
                  Dette vil tilbakestille alle preferanser til standardverdier
                </p>
                <button className="btn-danger" onClick={handleResetSettings}>
                  🔄 Tilbakestill innstillinger
                </button>
              </div>

              <div className="settings-group">
                <h3>Lagringsinformasjon</h3>
                <div className="storage-info">
                  <div className="storage-item">
                    <span className="storage-label">Database:</span>
                    <span className="storage-value">MongoDB</span>
                  </div>
                  <div className="storage-item">
                    <span className="storage-label">Lokale innstillinger:</span>
                    <span className="storage-value">Browser LocalStorage</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
