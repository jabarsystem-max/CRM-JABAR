import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './ZenVitAI.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const ZenVitAI = () => {
  const { token } = useAuth();
  const [customerContext, setCustomerContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!customerContext.trim() || customerContext.trim().length < 10) {
      setError('Vennligst gi en mer detaljert beskrivelse av kunden (minst 10 tegn)');
      return;
    }

    setLoading(true);
    setError('');
    setRecommendations(null);

    try {
      const response = await axios.post(
        `${API_URL}/ai/recommend-products`,
        { customer_context: customerContext },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (err) {
      console.error('AI recommendation error:', err);
      setError(err.response?.data?.detail || 'Kunne ikke generere anbefalinger. Prøv igjen.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setCustomerContext('');
    setRecommendations(null);
    setError('');
  };

  const exampleQueries = [
    "Kunde med lite energi og dårlig søvn",
    "Kunde som er ofte syk og har dårlig hud",
    "Kunde som ikke spiser fisk og fryser mye om vinteren",
    "Eldre kunde med leddsmerter og stivhet"
  ];

  const handleExampleClick = (query) => {
    // Pure React state update - no DOM manipulation
    setCustomerContext(query);
    setRecommendations(null);
    setError('');
  };

  return (
    <div className="ai-page">
      <div className="ai-header">
        <div className="ai-header-content">
          <h1 className="ai-title">🧠 ZenVit AI-Veileder</h1>
          <p className="ai-subtitle">Intelligent produktanbefaling basert på kundebehov (Intern bruk)</p>
        </div>
        <div className="ai-badge">Beta</div>
      </div>

      <div className="ai-container">
        {/* Left Panel - Input */}
        <div className="ai-input-panel">
          <div className="ai-card">
            <h3 className="ai-card-title">Beskriv kunden / behovet</h3>
            
            <form onSubmit={handleSubmit}>
              <textarea
                className="ai-textarea"
                value={customerContext}
                onChange={(e) => setCustomerContext(e.target.value)}
                placeholder="Eksempel: Kunde som er ofte syk og fryser mye om vinteren..."
                rows={8}
                disabled={loading}
              />

              <div className="ai-actions">
                <button 
                  type="submit" 
                  className="btn-primary btn-ai"
                  disabled={loading || !customerContext.trim()}
                >
                  {loading ? (
                    <>
                      <span className="ai-spinner"></span>
                      Genererer anbefalinger...
                    </>
                  ) : (
                    <>
                      🤖 Foreslå produkter
                    </>
                  )}
                </button>
                
                {(recommendations || error) && (
                  <button 
                    type="button" 
                    className="btn-secondary"
                    onClick={handleClear}
                  >
                    🔄 Ny forespørsel
                  </button>
                )}
              </div>
            </form>

            {/* Example Queries */}
            <div className="ai-examples">
              <p className="ai-examples-title">Eksempler (klikk for å bruke):</p>
              <div className="ai-examples-grid">
                {exampleQueries.map((query, idx) => (
                  <button
                    key={idx}
                    className="ai-example-btn"
                    onClick={() => handleExampleClick(query)}
                    disabled={loading}
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>

            {/* Disclaimer */}
            <div className="ai-disclaimer">
              <span className="ai-disclaimer-icon">⚠️</span>
              <span className="ai-disclaimer-text">
                AI-anbefalinger er generelle råd, ikke medisinske diagnoser. 
                Ved alvorlige symptomer skal kunden rådføre seg med lege.
              </span>
            </div>
          </div>
        </div>

        {/* Right Panel - Results */}
        <div className="ai-results-panel">
          {error && (
            <div className="ai-error">
              <span className="ai-error-icon">❌</span>
              <div>
                <h4>Feil</h4>
                <p>{error}</p>
              </div>
            </div>
          )}

          {recommendations && (
            <>
              {/* Quick Product Cards */}
              {recommendations.products && recommendations.products.length > 0 && (
                <div className="ai-card">
                  <h3 className="ai-card-title">🎯 Anbefalte produkter</h3>
                  <div className="ai-products-grid">
                    {recommendations.products.map((product, idx) => (
                      <div key={idx} className="ai-product-card">
                        <div className="ai-product-number">{idx + 1}</div>
                        <div className="ai-product-content">
                          <h4 className="ai-product-name">{product.name}</h4>
                          <p className="ai-product-reason">{product.reason}</p>
                          {product.dose && (
                            <div className="ai-product-dose">
                              <span className="dose-icon">📊</span>
                              <span>{product.dose}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Explanation */}
              {recommendations.explanation && (
                <div className="ai-card">
                  <h3 className="ai-card-title">📝 Detaljert begrunnelse</h3>
                  <div className="ai-explanation">
                    {recommendations.explanation.split('\n').map((line, idx) => {
                      // Check if line is a heading
                      if (line.startsWith('**') && line.endsWith('**')) {
                        const heading = line.replace(/\*\*/g, '');
                        return <h4 key={idx} className="ai-explanation-heading">{heading}</h4>;
                      }
                      // Regular line
                      if (line.trim()) {
                        return <p key={idx} className="ai-explanation-text">{line}</p>;
                      }
                      return <br key={idx} />;
                    })}
                  </div>
                </div>
              )}
            </>
          )}

          {!recommendations && !error && !loading && (
            <div className="ai-empty-state">
              <div className="ai-empty-icon">🧠</div>
              <h3>Klar til å hjelpe!</h3>
              <p>Beskriv kundens behov i tekstfeltet til venstre, så vil AI-en forslå de beste ZenVit-produktene.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ZenVitAI;
