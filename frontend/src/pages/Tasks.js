import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import './CRM.css';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Tasks = () => {
  const { token } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState('All');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 'Medium',
    type: 'Admin'
  });

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API_URL}/tasks`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTasks(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/tasks`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ title: '', description: '', due_date: '', priority: 'Medium', type: 'Admin' });
      fetchTasks();
    } catch (error) {
      console.error('Error creating task:', error);
      alert('Kunne ikke opprette oppgave');
    }
  };

  const updateStatus = async (taskId, newStatus) => {
    try {
      await axios.put(
        `${API_URL}/tasks/${taskId}/status?status=${newStatus}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchTasks();
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  if (loading) return <div className="loading">Laster...</div>;

  const statuses = ['Planned', 'InProgress', 'Done'];
  const priorities = ['High', 'Medium', 'Low'];
  const types = ['Customer', 'Order', 'Product', 'Stock', 'Supplier', 'Admin'];

  const filteredTasks = filter === 'All' ? tasks : tasks.filter(t => t.status === filter);
  const todayTasks = filteredTasks.filter(t => t.due_date && new Date(t.due_date).toDateString() === new Date().toDateString());
  const overdueTasks = filteredTasks.filter(t => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'Done');

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">✓ Oppgaver</h1>
          <p className="page-subtitle">Administrer oppgaver og oppfølging</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ny oppgave</button>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">📅</div>
          <div>
            <div className="stat-value">{todayTasks.length}</div>
            <div className="stat-label">I dag</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div>
            <div className="stat-value">{overdueTasks.length}</div>
            <div className="stat-label">Forfalt</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✓</div>
          <div>
            <div className="stat-value">{tasks.filter(t => t.status === 'Done').length}</div>
            <div className="stat-label">Fullført</div>
          </div>
        </div>
      </div>

      <div className="filter-bar">
        <button className={`filter-btn ${filter === 'All' ? 'active' : ''}`} onClick={() => setFilter('All')}>Alle ({tasks.length})</button>
        {statuses.map(s => (
          <button key={s} className={`filter-btn ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
            {s} ({tasks.filter(t => t.status === s).length})
          </button>
        ))}
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Tittel</th>
              <th>Type</th>
              <th>Prioritet</th>
              <th>Frist</th>
              <th>Status</th>
              <th>Tildelt</th>
              <th>Handling</th>
            </tr>
          </thead>
          <tbody>
            {filteredTasks.map(task => {
              const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'Done';
              return (
                <tr key={task.id} className={isOverdue ? 'overdue-row' : ''}>
                  <td><strong>{task.title}</strong>{task.description && <div style={{fontSize: '12px', color: '#7b8794'}}>{task.description}</div>}</td>
                  <td><span className="badge badge-omega">{task.type}</span></td>
                  <td>
                    <span className={`badge badge-${task.priority === 'High' ? 'danger' : task.priority === 'Medium' ? 'warning' : 'success'}`}>
                      {task.priority}
                    </span>
                  </td>
                  <td>{task.due_date ? new Date(task.due_date).toLocaleDateString('nb-NO') : '-'}</td>
                  <td>
                    <select
                      value={task.status}
                      onChange={(e) => updateStatus(task.id, e.target.value)}
                      className="status-select"
                    >
                      {statuses.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td>{task.assigned_to}</td>
                  <td>
                    {task.status !== 'Done' && (
                      <button 
                        className="btn-small btn-primary"
                        onClick={() => updateStatus(task.id, 'Done')}
                      >
                        Fullfør
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">Ny oppgave</h2>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Tittel *</label>
                <input type="text" required value={formData.title}
                  onChange={e => setFormData({...formData, title: e.target.value})} className="form-input" />
              </div>
              <div className="form-group">
                <label>Beskrivelse</label>
                <textarea value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})} className="form-textarea" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Type</label>
                  <select value={formData.type}
                    onChange={e => setFormData({...formData, type: e.target.value})} className="form-select">
                    {types.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Prioritet</label>
                  <select value={formData.priority}
                    onChange={e => setFormData({...formData, priority: e.target.value})} className="form-select">
                    {priorities.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Frist</label>
                <input type="datetime-local" value={formData.due_date}
                  onChange={e => setFormData({...formData, due_date: e.target.value})} className="form-input" />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>Avbryt</button>
                <button type="submit" className="btn-primary">Opprett oppgave</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
