import { Outlet } from "react-router-dom";

// Placeholder: once auth exists, this will redirect to /login when there is no valid token.
export default function ProtectedRoute() {
  return <Outlet />;
}
