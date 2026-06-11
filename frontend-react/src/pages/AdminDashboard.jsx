import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats]       = useState(null);
  const [users, setUsers]       = useState([]);
  const [videos, setVideos]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState('stats');

  // Search / Filter
  const [userSearch, setUserSearch]   = useState('');
  const [videoSearch, setVideoSearch] = useState('');
  const [videoStatus, setVideoStatus] = useState('all');

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes, videosRes] = await Promise.all([
        api.get('/auth/admin/stats'),
        api.get('/auth/admin/users'),
        api.get('/video/admin/videos'),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setVideos(videosRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleUser = async (userId) => {
    try {
      const res = await api.patch(`/auth/admin/users/${userId}/toggle-active`);
setUsers(prev =>
  prev.map(u => u.id === userId ? { ...u, is_active: res.data.is_active } : u)
);
    } catch (err) { console.error(err); }
  };

  // ── Filtered data ──────────────────────────────────────────
  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.email.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredVideos = videos.filter(v => {
    const matchSearch =
      (v.original_filename || '').toLowerCase().includes(videoSearch.toLowerCase()) ||
      (`User #${v.user_id}`).toLowerCase().includes(videoSearch.toLowerCase());
    const matchStatus = videoStatus === 'all' || v.status === videoStatus;
    return matchSearch && matchStatus;
  });

  // ── Export CSV ─────────────────────────────────────────────
  const exportCSV = (data, filename, columns) => {
    const header = columns.map(c => c.label).join(',');
    const rows = data.map(row =>
      columns.map(c => `"${row[c.key] ?? ''}"`).join(',')
    );
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const exportUsers = () => exportCSV(filteredUsers, 'users.csv', [
    { key: 'id',         label: 'ID' },
    { key: 'username',   label: 'Username' },
    { key: 'email',      label: 'Email' },
    { key: 'is_admin',   label: 'Admin' },
    { key: 'is_active',  label: 'Actif' },
    { key: 'created_at', label: 'Créé le' },
  ]);

  const exportVideos = () => exportCSV(filteredVideos, 'videos.csv', [
    { key: 'id',                label: 'ID' },
    { key: 'original_filename', label: 'Fichier' },
    { key: 'user_id',           label: 'User ID' },
    { key: 'duration',          label: 'Durée (s)' },
    { key: 'file_size',         label: 'Taille (bytes)' },
    { key: 'status',            label: 'Statut' },
    { key: 'created_at',        label: 'Uploadé le' },
  ]);

  // ── Charts data ────────────────────────────────────────────
  const videosChartData = [
    { name: 'Terminé',    value: stats?.videos?.completed  ?? 0, color: '#27AE60' },
    { name: 'En cours',   value: stats?.videos?.processing ?? 0, color: '#E67E22' },
    { name: 'Échoué',     value: stats?.videos?.failed     ?? 0, color: '#E74C3C' },
    { name: 'Uploadé',    value: (stats?.videos?.total ?? 0)
                                 - (stats?.videos?.completed  ?? 0)
                                 - (stats?.videos?.processing ?? 0)
                                 - (stats?.videos?.failed     ?? 0), color: '#888' },
  ].filter(d => d.value > 0);

  const usersChartData = [
    { name: 'Actifs',   value: stats?.users?.active   ?? 0, color: '#27AE60' },
    { name: 'Inactifs', value: stats?.users?.inactive ?? 0, color: '#E74C3C' },
  ];

  const barData = [
    { name: 'Utilisateurs', total: stats?.users?.total    ?? 0 },
    { name: 'Vidéos',       total: stats?.videos?.total   ?? 0 },
    { name: 'Détections',   total: stats?.detections      ?? 0 },
    { name: 'Conversations',total: stats?.conversations   ?? 0 },
  ];

  const getStatusBadge = (status) => {
    const map = {
      completed:  { label: 'Terminé',    color: '#27AE60' },
      processing: { label: 'En cours',   color: '#E67E22' },
      pending:    { label: 'En attente', color: '#3498DB' },
      failed:     { label: 'Échoué',     color: '#E74C3C' },
      uploaded:   { label: 'Uploadé',    color: '#888888' },
    };
    const s = map[status] || { label: status, color: '#888' };
    return <span className="status-badge" style={{ background: s.color }}>{s.label}</span>;
  };

  if (loading) return (
    <div className="admin-loading">
      <div className="spinner" />
      <p>Chargement du dashboard...</p>
    </div>
  );

  return (
    <div className="admin-container">

      {/* ── Header ── */}
      <div className="admin-header">
        <div className="admin-header-left">
          <h1>⚙️ Dashboard Administrateur</h1>
          <span className="admin-badge">Admin</span>
        </div>
        <div className="admin-header-right">
          <span className="admin-username">👤 {user?.username}</span>
          <button className="btn-back" onClick={() => navigate('/video')}>← Retour</button>
          <button className="btn-logout" onClick={logout}>Déconnexion</button>
        </div>
      </div>

      {/* ── Stats Cards ── */}
      <div className="stats-grid">
        {[
          { icon: '👥', label: 'Utilisateurs', value: stats?.users?.total    ?? 0, color: '#2E5F8A' },
          { icon: '🎬', label: 'Vidéos',       value: stats?.videos?.total   ?? 0, color: '#E67E22' },
          { icon: '🔍', label: 'Détections',   value: stats?.detections      ?? 0, color: '#8E44AD' },
          { icon: '✅', label: 'Users actifs', value: stats?.users?.active   ?? 0, color: '#27AE60' },
        ].map((card, i) => (
          <div className="stat-card" key={i} style={{ borderTop: `4px solid ${card.color}` }}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-value" style={{ color: card.color }}>{card.value}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        ))}
      </div>

      {/* ── Tabs ── */}
      <div className="admin-tabs">
        {[
          { key: 'stats',  label: '📊 Statistiques' },
          { key: 'users',  label: '👥 Utilisateurs' },
          { key: 'videos', label: '🎬 Vidéos' },
        ].map(tab => (
          <button key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Charts ── */}
      {activeTab === 'stats' && (
        <div className="charts-grid">

          {/* Bar chart global */}
          <div className="chart-card">
            <h3>Vue globale</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={barData}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="total" radius={[6,6,0,0]}>
                  {barData.map((_, i) => (
                    <Cell key={i} fill={['#2E5F8A','#E67E22','#8E44AD','#27AE60'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie — Statut vidéos */}
          <div className="chart-card">
            <h3>Statut des vidéos</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={videosChartData} dataKey="value" nameKey="name"
                     cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}`}>
                  {videosChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Pie — Utilisateurs */}
          <div className="chart-card">
            <h3>Utilisateurs actifs / inactifs</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={usersChartData} dataKey="value" nameKey="name"
                     cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}`}>
                  {usersChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

        </div>
      )}

      {/* ── Tab: Users ── */}
      {activeTab === 'users' && (
        <div className="admin-table-section">
          <div className="table-toolbar">
            <input className="search-input" placeholder="🔍 Rechercher username / email..."
              value={userSearch} onChange={e => setUserSearch(e.target.value)} />
            <button className="btn-export" onClick={exportUsers}>
              ⬇️ Export CSV
            </button>
          </div>
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th><th>Username</th><th>Email</th>
                  <th>Admin</th><th>Actif</th><th>Créé le</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr><td colSpan={7} className="no-data">Aucun résultat</td></tr>
                ) : filteredUsers.map(u => (
                  <tr key={u.id} className={!u.is_active ? 'row-disabled' : ''}>
                    <td>#{u.id}</td>
                    <td><strong>{u.username}</strong></td>
                    <td>{u.email}</td>
                    <td>{u.is_admin ? '👑 Oui' : '—'}</td>
                    <td>
                      <span className={`active-badge ${u.is_active ? 'active' : 'inactive'}`}>
                        {u.is_active ? '✅ Actif' : '❌ Inactif'}
                      </span>
                    </td>
                    <td>{new Date(u.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>
                      {!u.is_admin && (
                        <button
                          className={`toggle-btn ${u.is_active ? 'btn-disable' : 'btn-enable'}`}
                          onClick={() => toggleUser(u.id)}>
                          {u.is_active ? 'Désactiver' : 'Activer'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footer">{filteredUsers.length} résultat(s)</div>
        </div>
      )}

      {/* ── Tab: Videos ── */}
      {activeTab === 'videos' && (
        <div className="admin-table-section">
          <div className="table-toolbar">
            <input className="search-input" placeholder="🔍 Rechercher fichier / utilisateur..."
              value={videoSearch} onChange={e => setVideoSearch(e.target.value)} />
            <select className="filter-select" value={videoStatus}
              onChange={e => setVideoStatus(e.target.value)}>
              <option value="all">Tous les statuts</option>
              <option value="completed">Terminé</option>
              <option value="processing">En cours</option>
              <option value="failed">Échoué</option>
              <option value="uploaded">Uploadé</option>
            </select>
            <button className="btn-export" onClick={exportVideos}>
              ⬇️ Export CSV
            </button>
          </div>
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th><th>Fichier</th><th>Utilisateur</th>
                  <th>Durée</th><th>Taille</th><th>Statut</th><th>Uploadé le</th>
                </tr>
              </thead>
              <tbody>
                {filteredVideos.length === 0 ? (
                  <tr><td colSpan={7} className="no-data">Aucun résultat</td></tr>
                ) : filteredVideos.map(v => (
                  <tr key={v.id}>
                    <td>#{v.id}</td>
                    <td className="filename">{v.original_filename}</td>
                    <td>{v.username ?? `User #${v.user_id}`}</td>
                    <td>{v.duration ? `${v.duration.toFixed(1)}s` : '—'}</td>
                    <td>{v.file_size ? `${(v.file_size/1024/1024).toFixed(1)} MB` : '—'}</td>
                    <td>{getStatusBadge(v.status)}</td>
                    <td>{new Date(v.created_at).toLocaleDateString('fr-FR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footer">{filteredVideos.length} résultat(s)</div>
        </div>
      )}

    </div>
  );
}