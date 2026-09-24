import axios from "axios";

const TOKEN_KEY = "lifexash_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const saveToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

// Shared axios instance: every request goes to the FastAPI backend.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor: runs before every request and attaches the JWT if we have one.
client.interceptors.request.use((config) => {
  const token = getToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// AuthContext registers a function here, so a 401 can log out and redirect via React Router.
let onUnauthorized = null;
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler;
};

// Login/register return 401/409 for wrong input — the form shows those, so don't log out.
const AUTH_FORM_URLS = ["/auth/login", "/auth/register"];

// Response interceptor: a 401 anywhere else means the token is missing, expired or invalid.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthForm = AUTH_FORM_URLS.includes(error.config?.url);
    if (error.response?.status === 401 && !isAuthForm && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  },
);

// Turns an axios error into a message we can show the user.
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (!error.response) return "Can't reach the server. Is the backend running?";
  const detail = error.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail[0].msg; // 422 validation error
  return fallback;
}

export default client;
