import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { token } = useAuth();

  return (
    <nav className="navbar">
      <Link to={token ? "/dashboard" : "/login"} className="brand">LifeXash</Link>
      {token ? (
        <>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/planner">Planner</NavLink>
          <NavLink to="/notes">Notes</NavLink>
          <NavLink to="/journal">Journal</NavLink>
          <NavLink to="/profile">Profile</NavLink>
        </>
      ) : (
        <>
          <NavLink to="/login">Log in</NavLink>
          <NavLink to="/register">Register</NavLink>
        </>
      )}
    </nav>
  );
}
