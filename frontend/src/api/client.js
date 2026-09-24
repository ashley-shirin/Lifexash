import axios from "axios";

// Shared axios instance: every request goes to the FastAPI backend.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
});

export default client;
