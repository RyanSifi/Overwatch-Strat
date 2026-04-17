/**
 * Client Axios configuré pour l'API OW Coach.
 * Injecte automatiquement le token d'auth si présent dans localStorage.
 */
import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

// Injecte le token dans chaque requête si disponible
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ow_token");
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

export default client;
