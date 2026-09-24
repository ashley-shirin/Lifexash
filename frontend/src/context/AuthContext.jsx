import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import client, { clearToken, getErrorMessage, getToken, saveToken, setUnauthorizedHandler } from "../api/client.js";

// Context = a way to share state (token, user) with every component without passing props down.
const AuthContext = createContext(null);

// Token lives in localStorage so you stay logged in after a refresh; the trade-off is that any
// JavaScript on the page (e.g. an XSS bug) could read it, unlike an httpOnly cookie.
export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [token, setToken] = useState(getToken);
  const [user, setUser] = useState(null);
  const [userError, setUserError] = useState("");

  const logout = useCallback(
    (message) => {
      clearToken();
      setToken(null);
      setUser(null);
      navigate("/login", { replace: true, state: message ? { message } : undefined });
    },
    [navigate],
  );

  // Any 401 from the API (expired/invalid token) logs the user out.
  useEffect(() => {
    setUnauthorizedHandler(() => logout("Your session has expired. Please log in again."));
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  // After a page refresh we only have the token, so fetch the user it belongs to.
  useEffect(() => {
    if (!token || user) return;
    let cancelled = false;
    setUserError("");
    client
      .get("/auth/me")
      .then((res) => !cancelled && setUser(res.data))
      .catch((err) => {
        // A 401 is already handled by the interceptor (logout); show anything else.
        if (!cancelled && err.response?.status !== 401) setUserError(getErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [token, user]);

  const login = async (email, password) => {
    const { data } = await client.post("/auth/login", { email, password });
    // Fetch the user with the new token before saving anything, so state updates together.
    const me = await client.get("/auth/me", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    saveToken(data.access_token);
    setToken(data.access_token);
    setUser(me.data);
  };

  const register = async (name, email, password) => {
    await client.post("/auth/register", { name, email, password });
    await login(email, password); // sign straight in after creating the account
  };

  const value = { token, user, userError, login, register, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
