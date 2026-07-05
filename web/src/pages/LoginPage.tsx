import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, token, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && token) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={onSubmit}>
        <div className="brand brand-large">
          <span className="brand-mark">TS</span>
          <div>
            <strong>TheSecond</strong>
            <small>Management Console</small>
          </div>
        </div>
        <p className="login-copy">
          Sign in with your website admin account. This is separate from Telegram — field staff use the bot,
          you use this console for dashboard and payroll.
        </p>
        <div className="login-help">
          <strong>Your admin login</strong>
          <p>
            Email: <code>admin@example.com</code>
            <br />
            Password: <code>admin12345</code>
          </p>
          <small>
            To set your own email/password later, run in terminal:
            <code>python -m app.db.manage_admin --email you@email.com --password YourPassword123</code>
          </small>
        </div>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error-banner">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
