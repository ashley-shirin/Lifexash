import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

// Simple line icons (24 × 24), drawn with the text colour so they follow the active/inactive colour.
const ICONS = {
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  planner: (
    <>
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M3 9h18M8 2v4M16 2v4M9 15l2 2 4-4" />
    </>
  ),
  notes: (
    <>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
      <path d="M14 3v6h6M8 13h8M8 17h5" />
    </>
  ),
  journal: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9.5h.01M15 9.5h.01" />
    </>
  ),
  profile: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
};

const LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { to: "/planner", label: "Planner", icon: "planner" },
  { to: "/notes", label: "Notes", icon: "notes" },
  { to: "/journal", label: "Journal", icon: "journal" },
  { to: "/profile", label: "Profile", icon: "profile" },
];

export default function Navbar() {
  const { token } = useAuth();

  return (
    <>
      <nav className="navbar" aria-label="Main">
        <Link to={token ? "/dashboard" : "/login"} className="brand">LifeXash</Link>
        {token ? (
          // On phones these top links are hidden by CSS and the bottom bar below is shown instead.
          LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className="top-link">
              {link.label}
            </NavLink>
          ))
        ) : (
          <>
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/register">Register</NavLink>
          </>
        )}
      </nav>

      {token && (
        <nav className="bottom-nav" aria-label="Main">
          {LINKS.map((link) => (
            <NavLink key={link.to} to={link.to}>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                {ICONS[link.icon]}
              </svg>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </>
  );
}
