import { Link, NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="brand">LifeXash</Link>
      <NavLink to="/" end>Dashboard</NavLink>
      <NavLink to="/planner">Planner</NavLink>
      <NavLink to="/notes">Notes</NavLink>
      <NavLink to="/journal">Journal</NavLink>
      <NavLink to="/profile">Profile</NavLink>
    </nav>
  );
}
