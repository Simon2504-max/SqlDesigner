import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE, errorMessage, saveSession } from '../session';

export default function Auth({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [login, setLogin] = useState({ username: '', password: '' });
  const [register, setRegister] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await axios.post(`${API_BASE}/login`, login);
      // Le serveur renvoie le jeton et l'utilisateur : on les garde dans le navigateur
      saveSession(res.data.access_token, res.data.user);
      onAuth(res.data.user.id);
    } catch (err) {
      setError(errorMessage(err, 'Login failed.'));
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_BASE}/register`, register);
      setSuccess('Account created: you can now log in.');
      setRegister({ username: '', email: '', password: '' });
      setMode('login');
    } catch (err) {
      setError(errorMessage(err, 'Sign-up failed.'));
    }
  };

  return (
    <div className="auth-card">
      <div className="auth-header">
        <h1>SqlDesigner</h1>
        <p className="subtitle">Design your database visually and export it to SQL</p>
      </div>

      <div className="auth-tabs">
        <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(''); setSuccess(''); }}>Login</button>
        <button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(''); setSuccess(''); }}>Sign up</button>
      </div>

      {error && <div className="auth-error">{error}</div>}
      {success && <div className="auth-success">{success}</div>}

      {mode === 'login' ? (
        <form onSubmit={handleLogin} className="auth-form">
          <label>Username</label>
          <input value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })} />
          <label>Password</label>
          <input type="password" value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} />
          <button className="primary">Log in</button>
        </form>
      ) : (
        <form onSubmit={handleRegister} className="auth-form">
          <label>Username</label>
          <input value={register.username} onChange={(e) => setRegister({ ...register, username: e.target.value })} />
          <label>Email</label>
          <input value={register.email} onChange={(e) => setRegister({ ...register, email: e.target.value })} />
          <label>Password</label>
          <input type="password" value={register.password} onChange={(e) => setRegister({ ...register, password: e.target.value })} />
          <button className="primary">Create account</button>
        </form>
      )}

      <div className="auth-footnote">By continuing you agree to the terms of use.</div>
    </div>
  );
}
