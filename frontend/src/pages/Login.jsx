import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;

function validate({ email, password }) {
  const errors = {};
  if (!email.trim()) errors.email = "Email is required.";
  else if (!EMAIL_PATTERN.test(email.trim())) errors.email = "Enter a valid email address.";
  if (!password) errors.password = "Password is required.";
  return errors;
}

export default function Login() {
  const { token, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token) return <Navigate to="/dashboard" replace />;

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const found = validate(form);
    setErrors(found);
    setServerError("");
    if (Object.keys(found).length > 0) return;

    setLoading(true);
    try {
      await login(form.email.trim(), form.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setServerError(getErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Log in</h1>
      {location.state?.message && <p className="form-info">{location.state.message}</p>}
      {serverError && <p className="form-error" role="alert">{serverError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" value={form.email} onChange={handleChange} />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </label>

        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={handleChange}
          />
          {errors.password && <span className="field-error">{errors.password}</span>}
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p>
        No account yet? <Link to="/register">Create one</Link>
      </p>
    </section>
  );
}
