import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useParams, useNavigate } from 'react-router-dom';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const CustomerDetail = () => {
  const { token } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        const [customerRes, timelineRes] = await Promise.all([
          axios.get(`${API_URL}/customers`, { headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API_URL}/customers/${id}/timeline`, { headers: { Authorization: `Bearer ${token}` } })
        ]);
        const cust = customerRes.data.find(c => c.id === id);
        setCustomer(cust);
        setTimeline(timelineRes.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching customer:', error);
        setLoading(false);
      }
    };

    fetchCustomer();
  }, [id, token]);

  if (loading) return <div className="loading">Laster...</div>;
  if (!customer) return <div className="loading">Kunde ikke funnet</div>;

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">👤 {customer.name}</h1>
          <p className="page-subtitle">{customer.type} kunde - {customer.status}</p>
        </div>
        <button className="btn-secondary" onClick={() => navigate('/customers')}>← Tilbake</button>
      </div>

      <div className="customer-detail-grid">
        <div className="customer-info-card">
          <h3>Kundeinformasjon</h3>
          <div className="info-grid">
            <div><strong>E-post:</strong> {customer.email || '-'}</div>
            <div><strong>Telefon:</strong> {customer.phone || '-'}</div>
            <div><strong>Adresse:</strong> {customer.address || '-'}</div>
            <div><strong>Postnr/By:</strong> {customer.zip_code} {customer.city}</div>
            <div><strong>Type:</strong> {customer.type}</div>
            <div><strong>Status:</strong> <span className={`badge badge-${customer.status === 'VIP' ? 'success' : 'omega'}`}>{customer.status}</span></div>
            <div><strong>Total verdi:</strong> {Math.round(customer.total_value || 0)} kr</div>
            <div><strong>Antall ordrer:</strong> {customer.order_count || 0}</div>
            <div><strong>Favoritt produkt:</strong> {customer.favorite_product || '-'}</div>
            <div><strong>Siste ordre:</strong> {customer.last_order_date ? new Date(customer.last_order_date).toLocaleDateString('nb-NO') : '-'}</div>
            {customer.tags && <div><strong>Tags:</strong> {customer.tags}</div>}
            {customer.next_step && <div><strong>Neste steg:</strong> {customer.next_step}</div>}
            {customer.notes && <div style={{gridColumn: '1/-1'}}><strong>Merknad:</strong> {customer.notes}</div>}
          </div>
        </div>

        <div className="timeline-card">
          <h3>Tidslinje</h3>
          <div className="timeline">
            {timeline.length === 0 ? (
              <p>Ingen aktivitet ennå</p>
            ) : (
              timeline.map(entry => (
                <div key={entry.id} className="timeline-entry">
                  <div className="timeline-date">{new Date(entry.date).toLocaleString('nb-NO')}</div>
                  <div className="timeline-type">
                    <span className={`badge badge-${entry.type === 'Order' ? 'success' : entry.type === 'Task' ? 'warning' : 'omega'}`}>
                      {entry.type}
                    </span>
                  </div>
                  <div className="timeline-description">{entry.description}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerDetail;
