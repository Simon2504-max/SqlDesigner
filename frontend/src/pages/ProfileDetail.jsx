import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE, errorMessage } from '../session';

export default function ProfileDetail({ onBack, onAccountDeleted }) {
  const [form, setForm] = useState({ full_name: '', email: '', phone: '' });
  const [username, setUsername] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');

  // Au chargement : on récupère le profil de l'utilisateur connecté
  useEffect(() => {
    axios
      .get(`${API_BASE}/me`)
      .then((res) => {
        setUsername(res.data.username);
        setForm({
          full_name: res.data.full_name || '',
          email: res.data.email || '',
          phone: res.data.phone || '',
        });
      })
      .catch((e) => setErr(errorMessage(e, 'Could not load your profile.')));
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMsg('');
    setErr('');
    try {
      await axios.put(`${API_BASE}/me`, form);
      setMsg('Profile updated.');
    } catch (e) {
      setErr(errorMessage(e, 'Update failed.'));
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete your account? All your schemas will be lost.')) return;
    try {
      await axios.delete(`${API_BASE}/me`);
      onAccountDeleted();
    } catch (e) {
      setErr(errorMessage(e, 'Delete failed.'));
    }
  };

  return (
    <div className="profile-card">
      <button className="back" onClick={onBack}>← Back</button>
      <h3>Profile {username && `· ${username}`}</h3>
      {err && <div className="auth-error">{err}</div>}
      {msg && <div className="auth-success">{msg}</div>}

      <form onSubmit={handleUpdate} className="profile-form">
        <label>Full name</label>
        <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <label>Email</label>
        <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label>Phone</label>
        <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <div className="profile-actions">
          <button className="primary">Save</button>
          <button type="button" className="danger" onClick={handleDelete}>Delete account</button>
        </div>
      </form>
    </div>
  );
}
