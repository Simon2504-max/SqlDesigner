import React, { useEffect, useState } from 'react';
import './App.css';
import Auth from './pages/Auth';
import Home from './pages/Home';
import ProfileDetail from './pages/ProfileDetail';
import { clearSession, getSavedUser, getToken, setUnauthorizedHandler } from './session';

function App() {
  // Au démarrage : si un jeton est enregistré, on est déjà connecté
  const savedUser = getToken() ? getSavedUser() : null;
  const [userId, setUserId] = useState(savedUser?.id ?? null);
  const [view, setView] = useState(savedUser ? 'home' : 'auth'); // auth | home | profile

  const handleLogout = () => {
    clearSession();
    setUserId(null);
    setView('auth');
  };

  // Si le serveur répond 401 (jeton expiré…), retour à l'écran de connexion
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUserId(null);
      setView('auth');
    });
  }, []);

  const handleAuth = (id) => {
    setUserId(id);
    setView('home');
  };

  return (
    <div className="App-root">
      {view === 'auth' && <Auth onAuth={handleAuth} />}
      {view === 'home' && (
        <Home userId={userId} onOpenProfile={() => setView('profile')} onLogout={handleLogout} />
      )}
      {view === 'profile' && (
        <ProfileDetail onBack={() => setView('home')} onAccountDeleted={handleLogout} />
      )}
    </div>
  );
}

export default App;
