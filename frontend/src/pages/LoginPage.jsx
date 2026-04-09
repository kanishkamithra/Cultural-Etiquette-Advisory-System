import { useState } from "react";
import { Icon } from "../components/Icons";

function LoginPage({ onLogin, onRegister, onGuest }) {
  const [mode, setMode] = useState("login");
  const [login, setLogin] = useState({ email: "", password: "" });
  const [register, setRegister] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    try {
      setError("");
      if (mode === "login") {
        await onLogin(login);
      } else {
        await onRegister(register);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth-shell single-auth">
      <section className="auth-hero">
        <div className="logo-mark large">
          <Icon name="logo" size={28} />
          <div className="logo-stack">
            <span className="logo-text">CEAS</span>
            <span className="logo-subtitle">Cultural Etiquette Advisory System</span>
          </div>
        </div>
        <div className="auth-copy">
          <p className="eyebrow">Modern guidance platform</p>
          <h1>Respect every culture with confidence.</h1>
          <p className="lede">
            Get scenario-based etiquette guidance, save important advice, and explore cultural expectations through a cleaner, calmer interface.
          </p>
        </div>
        <div className="auth-feature-grid">
          <article className="auth-feature-card">
            <span className="status-dot" />
            <div>
              <strong>Scenario intelligence</strong>
              <p className="muted">Country-specific etiquette guidance shaped by context, role, and formality.</p>
            </div>
          </article>
          <article className="auth-feature-card">
            <span className="status-dot amber" />
            <div>
              <strong>Professional workflow</strong>
              <p className="muted">Save advice, compare cultures, and surface risks before meetings or travel.</p>
            </div>
          </article>
        </div>
      </section>

      <section className="auth-panel-wrap single-card-wrap">
        <article className="auth-panel single-card">
          <div className="auth-title-row">
            <div>
              <p className="kicker">{mode === "login" ? "Welcome back" : "Create account"}</p>
              <h2>{mode === "login" ? "Sign in to continue" : "Join the workspace"}</h2>
            </div>
            <div className="mode-switch">
              <button type="button" className={mode === "login" ? "switch-tab active" : "switch-tab"} onClick={() => setMode("login")}>Login</button>
              <button type="button" className={mode === "register" ? "switch-tab active" : "switch-tab"} onClick={() => setMode("register")}>Sign up</button>
            </div>
          </div>

          <form className="form-stack" onSubmit={submit}>
            {mode === "register" ? (
              <label className="field-group">
                <span className="field-label">Full name</span>
                <span className="field-shell">
                  <Icon name="user" size={18} />
                  <input placeholder="Enter your full name" value={register.name} onChange={(event) => setRegister({ ...register, name: event.target.value })} />
                </span>
              </label>
            ) : null}
            <label className="field-group">
              <span className="field-label">Email address</span>
                <span className="field-shell">
                  <Icon name="mail" size={18} />
                <input
                  placeholder="name@example.com"
                  type="email"
                  value={mode === "login" ? login.email : register.email}
                  onChange={(event) => mode === "login"
                    ? setLogin({ ...login, email: event.target.value })
                    : setRegister({ ...register, email: event.target.value })}
                />
              </span>
            </label>
            <label className="field-group">
              <span className="field-label">Password</span>
              <span className="field-shell">
                <Icon name="lock" size={18} />
                <input
                  placeholder="Enter password"
                  type="password"
                  value={mode === "login" ? login.password : register.password}
                  onChange={(event) => mode === "login"
                    ? setLogin({ ...login, password: event.target.value })
                    : setRegister({ ...register, password: event.target.value })}
                />
              </span>
            </label>
            {mode === "register" ? <p className="helper-text">Use at least 6 characters for a secure password.</p> : null}
            <button type="submit">{mode === "login" ? "Login" : "Create account"}</button>
          </form>

          <div className="auth-footer">
            <p className="muted">
              {mode === "login" ? "New here?" : "Already have an account?"}
              {" "}
              <button type="button" className="inline-link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
                {mode === "login" ? "Sign up" : "Login"}
              </button>
            </p>
            <button className="ghost-button full-width" onClick={onGuest}>Continue as guest</button>
          </div>

          {error ? <p className="error-text">{error}</p> : null}
        </article>
      </section>
    </div>
  );
}

export default LoginPage;
