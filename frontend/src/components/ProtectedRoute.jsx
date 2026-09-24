import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

// Wraps every private page: no token → /login; token but user not loaded yet → wait.
export default function ProtectedRoute() {
  const { token, user, userError } = useAuth();

  if (!token) return <Navigate to="/login" replace />;
  if (userError) return <p className="form-error">{userError}</p>;
  if (!user) return <p>Loading…</p>;
  return <Outlet />;
}
