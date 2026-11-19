/**
 * session.js — Gestion de la connexion côté interface.
 *
 * - Garde le jeton JWT dans le localStorage du navigateur.
 * - Ajoute automatiquement "Authorization: Bearer <jeton>" à TOUTES les
 *   requêtes axios de l'application (grâce à un "intercepteur").
 * - Si le serveur répond 401 (jeton absent, faux ou expiré), déconnecte.
 */
import axios from "axios";

const TOKEN_KEY = "sd_token";
const USER_KEY = "sd_user";

// Adresse du serveur : variable VITE_API_URL du fichier .env (Vite ne lit que les variables VITE_…)
export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getSavedUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify({ id: user.id, username: user.username }));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// Fonction appelée quand le serveur nous dit "non connecté" (définie par App.js)
let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

// Avant chaque requête : on ajoute le jeton
axios.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Après chaque réponse : si 401 alors qu'on croyait être connecté, on se déconnecte
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && getToken()) {
      clearSession();
      onUnauthorized();
    }
    return Promise.reject(error);
  }
);

/** Transforme une erreur axios en message lisible pour l'utilisateur. */
export function errorMessage(error, fallback = "Something went wrong.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (!error?.response) return "Cannot reach the server. Is it running?";
  return fallback;
}
