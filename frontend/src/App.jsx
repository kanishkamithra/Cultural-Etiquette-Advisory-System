import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { apiRequest } from "./services/api";
import { Icon } from "./components/Icons";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import FeedbackPage from "./pages/FeedbackPage";
import LoginPage from "./pages/LoginPage";

const emptyData = {
  currentAdvice: null,
  cultures: [],
  scenarios: [],
  rules: [],
  stats: { cultures: 0, scenarios: 0, rules: 0, users: 0, feedback: 0 },
  savedAdvice: [],
  favorites: [],
  feedback: [],
  recommendations: { headline: "", based_on: "", items: [] },
  dailyTip: null,
  communityTips: [],
  adminUsers: [],
  analytics: { most_searched_countries: [], common_mistakes: [], feedback_trends: [] },
  parsedQuery: null,
  simulation: null,
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("ceas-token"));
  const [guestMode, setGuestMode] = useState(() => localStorage.getItem("ceas-guest-mode") === "true");
  const [travelMode, setTravelMode] = useState(() => localStorage.getItem("ceas-travel-mode") === "true");
  const [user, setUser] = useState(null);
  const [data, setData] = useState(emptyData);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    bootstrap();
  }, []);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }
    const timer = window.setTimeout(() => setToast(""), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function bootstrap() {
    setBusy(true);
    try {
      let currentUser = null;
      if (token) {
        currentUser = await apiRequest("/auth/me", {}, token);
        setUser(currentUser);
      }
      await refreshData(currentUser, token);
    } catch (_) {
      clearSession();
      await refreshData(null, null);
    } finally {
      setBusy(false);
      setLoading(false);
    }
  }

  async function refreshData(currentUser = user, currentToken = token) {
    const [stats, cultures, scenarios, rules, dailyTip, communityTips] = await Promise.all([
      apiRequest("/stats"),
      apiRequest("/cultures"),
      apiRequest("/scenarios"),
      apiRequest("/rules"),
      apiRequest("/travel-mode/daily-tip", {}, currentToken),
      apiRequest("/community-tips"),
    ]);

    const next = {
      ...emptyData,
      stats,
      cultures,
      scenarios,
      rules,
      dailyTip,
      communityTips,
      currentAdvice: data.currentAdvice,
    };

    if (currentUser && currentToken) {
      const tasks = [
        apiRequest("/saved-advice", {}, currentToken),
        apiRequest("/feedback", {}, currentToken),
        apiRequest("/favorites", {}, currentToken),
        apiRequest("/recommendations", {}, currentToken),
      ];
      if (currentUser.role === "admin") {
        tasks.push(apiRequest("/users", {}, currentToken), apiRequest("/analytics", {}, currentToken));
      }
      const [savedAdvice, feedback, favorites, recommendations, adminUsers = [], analytics = emptyData.analytics] = await Promise.all(tasks);
      next.savedAdvice = savedAdvice;
      next.feedback = feedback;
      next.favorites = favorites;
      next.recommendations = recommendations;
      next.adminUsers = adminUsers;
      next.analytics = analytics;
    }

    setData(next);
  }

  function clearSession() {
    localStorage.removeItem("ceas-token");
    localStorage.removeItem("ceas-guest-mode");
    setToken(null);
    setGuestMode(false);
    setUser(null);
    setData((previous) => ({ ...previous, currentAdvice: null, savedAdvice: [], favorites: [], feedback: [], adminUsers: [], analytics: emptyData.analytics }));
  }

  function enableGuestMode() {
    localStorage.setItem("ceas-guest-mode", "true");
    setGuestMode(true);
    navigate("/dashboard");
  }

  function toggleTravelMode() {
    const next = !travelMode;
    setTravelMode(next);
    localStorage.setItem("ceas-travel-mode", String(next));
  }

  async function withBusy(action, successMessage) {
    setBusy(true);
    try {
      const result = await action();
      if (successMessage) {
        setToast(successMessage);
      }
      return result;
    } finally {
      setBusy(false);
    }
  }

  async function handleRegister(payload) {
    return withBusy(async () => {
      const session = await apiRequest("/auth/register", { method: "POST", body: JSON.stringify(payload) });
      localStorage.setItem("ceas-token", session.token);
      localStorage.removeItem("ceas-guest-mode");
      setToken(session.token);
      setUser(session.user);
      setGuestMode(false);
      await refreshData(session.user, session.token);
      navigate("/dashboard");
    }, "Account created.");
  }

  async function handleLogin(payload) {
    return withBusy(async () => {
      const session = await apiRequest("/auth/login", { method: "POST", body: JSON.stringify(payload) });
      localStorage.setItem("ceas-token", session.token);
      localStorage.removeItem("ceas-guest-mode");
      setToken(session.token);
      setUser(session.user);
      setGuestMode(false);
      await refreshData(session.user, session.token);
      navigate("/dashboard");
    }, "Signed in successfully.");
  }

  async function handleLogout() {
    await withBusy(async () => {
      if (token) {
        try {
          await apiRequest("/auth/logout", { method: "POST" }, token);
        } catch (_) {
          // Ignore stale logout tokens.
        }
      }
      clearSession();
      navigate("/login");
    }, "Signed out.");
  }

  async function generateAdvice(cultureId, scenarioId) {
    const payload = typeof cultureId === "object"
      ? cultureId
      : { culture_id: cultureId, scenario_id: scenarioId };
    return withBusy(async () => {
      const advice = await apiRequest("/advice/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setData((previous) => ({
        ...previous,
        currentAdvice: {
          cultureId: advice.culture.id,
          scenarioId: advice.scenario.id,
          cultureName: advice.culture.name,
          scenarioName: advice.scenario.name,
          riskLabel: advice.risk_label,
          riskPercent: advice.risk_percent,
          generatedAt: new Date().toISOString(),
          rules: advice.rules,
          context: advice.context,
          safeActions: advice.safe_actions,
          conflicts: advice.conflicts,
          explanation: advice.explanation,
          personalization: advice.personalization,
        },
      }));
      return advice;
    });
  }

  async function saveAdvice() {
    if (!token || !data.currentAdvice) {
      throw new Error("Sign in and generate advice first.");
    }
    return withBusy(async () => {
      await apiRequest(
        "/saved-advice",
        {
          method: "POST",
          body: JSON.stringify({
            culture_id: data.currentAdvice.cultureId,
            scenario_id: data.currentAdvice.scenarioId,
            culture_name: data.currentAdvice.cultureName,
            scenario_name: data.currentAdvice.scenarioName,
            risk_label: data.currentAdvice.riskLabel,
            risk_percent: data.currentAdvice.riskPercent,
            generated_at: data.currentAdvice.generatedAt,
          }),
        },
        token,
      );
      await refreshData(user, token);
    }, "Advice saved.");
  }

  async function deleteSavedAdvice(id) {
    return withBusy(async () => {
      await apiRequest(`/saved-advice/${id}`, { method: "DELETE" }, token);
      await refreshData(user, token);
    }, "Saved advice removed.");
  }

  async function createFavorite(payload) {
    return withBusy(async () => {
      await apiRequest("/favorites", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Added to favorites.");
  }

  async function deleteFavorite(id) {
    return withBusy(async () => {
      await apiRequest(`/favorites/${id}`, { method: "DELETE" }, token);
      await refreshData(user, token);
    }, "Favorite removed.");
  }

  async function submitFeedback(payload) {
    return withBusy(async () => {
      await apiRequest("/feedback", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Feedback submitted.");
  }

  async function deleteFeedback(id) {
    return withBusy(async () => {
      await apiRequest(`/feedback/${id}`, { method: "DELETE" }, token);
      await refreshData(user, token);
    }, "Feedback removed.");
  }

  async function createCommunityTip(payload) {
    return withBusy(async () => {
      await apiRequest("/community-tips", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Community tip shared.");
  }

  async function deleteCommunityTip(id) {
    return withBusy(async () => {
      await apiRequest(`/community-tips/${id}`, { method: "DELETE" }, token);
      await refreshData(user, token);
    }, "Community tip removed.");
  }

  async function createCulture(payload) {
    return withBusy(async () => {
      await apiRequest("/cultures", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Culture added.");
  }

  async function createScenario(payload) {
    return withBusy(async () => {
      await apiRequest("/scenarios", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Scenario added.");
  }

  async function createRule(payload) {
    return withBusy(async () => {
      await apiRequest("/rules", { method: "POST", body: JSON.stringify(payload) }, token);
      await refreshData(user, token);
    }, "Rule added.");
  }

  async function deleteRule(id) {
    return withBusy(async () => {
      await apiRequest(`/rules/${id}`, { method: "DELETE" }, token);
      await refreshData(user, token);
    }, "Rule deleted.");
  }

  async function loadQuickGuide(cultureId) {
    return apiRequest(`/quick-guide/${cultureId}`);
  }

  async function compareCultures(payload) {
    return apiRequest("/compare", { method: "POST", body: JSON.stringify(payload) });
  }

  async function runMistakeAlert(payload) {
    return apiRequest("/mistake-alert", { method: "POST", body: JSON.stringify(payload) }, token);
  }

  async function parseAdviceQuery(query) {
    const parsed = await apiRequest("/advice/parse", { method: "POST", body: JSON.stringify({ query }) }, token);
    setData((previous) => ({ ...previous, parsedQuery: parsed }));
    return parsed;
  }

  async function runSimulation(payload) {
    const simulation = await apiRequest("/simulation", { method: "POST", body: JSON.stringify(payload) }, token);
    setData((previous) => ({ ...previous, simulation }));
    return simulation;
  }

  if (loading) {
    return <div className="screen-center">Loading application...</div>;
  }

  const showAuthLayout = !user && !guestMode && location.pathname === "/login";
  const t = (key) => ({
    dashboard: "Dashboard",
    feedback: "Feedback",
    admin: "Admin",
    logout: "Logout",
    travel_mode: "Travel Mode",
    recommended_for_you: "Recommended for you",
    daily_tip: "Daily etiquette tip",
    community_tips: "Community Tips",
    compare: "Compare",
    quick_guide: "Emergency Quick Guide",
    mistake_alert: "Cultural Mistake Alert",
  }[key] || key);

  if (showAuthLayout) {
    return (
      <>
        <LoginPage onLogin={handleLogin} onRegister={handleRegister} onGuest={enableGuestMode} t={t} />
        {toast ? <div className="toast">{toast}</div> : null}
      </>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="logo-mark brand-logo">
            <Icon name="logo" size={26} />
            <div className="logo-stack">
              <span className="logo-text">CEAS</span>
              <span className="logo-subtitle">Cultural Etiquette Advisory System</span>
            </div>
          </div>
          <h1>Clarity for cross-cultural moments.</h1>
          <p className="lede">Plan quickly, act respectfully, and stay confident.</p>
        </div>

        <div className="sidebar-note">
          <span className="sidebar-note-label">Live workspace</span>
          <strong>Advice, feedback, and admin insights in one streamlined console</strong>
        </div>

        <div className="stat-grid">
          <StatCard label="Countries" value={data.stats.cultures} />
          <StatCard label="Rules" value={data.stats.rules} />
          <StatCard label="Users" value={data.stats.users} />
          <StatCard label="Feedback" value={data.stats.feedback} />
        </div>

        <nav className="nav-stack">
          <SidebarLink to="/dashboard" icon="dashboard" label={t("dashboard")} />
          <SidebarLink to="/feedback" icon="feedback" label={t("feedback")} />
          {user?.role === "admin" ? <SidebarLink to="/admin" icon="admin" label={t("admin")} /> : null}
        </nav>

        <div className="utility-panel">
          <label className="toggle-row">
            <span>{t("travel_mode")}</span>
            <button type="button" className={travelMode ? "toggle-pill active" : "toggle-pill"} onClick={toggleTravelMode}>
              <span className="toggle-dot" />
            </button>
          </label>
        </div>

        <div className="session-card">
          <div className="profile-head">
            <div className="avatar-badge">{user ? user.name.charAt(0).toUpperCase() : "G"}</div>
            <div>
              <strong>{user ? user.name : "Guest mode"}</strong>
              <span>{user ? user.role : guestMode ? "Exploring without an account" : location.pathname}</span>
            </div>
          </div>
          {user || guestMode ? (
            <button className="logout-button" onClick={handleLogout}>
              <Icon name="logout" size={16} />
              <span>{user ? t("logout") : "Exit guest mode"}</span>
            </button>
          ) : null}
        </div>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to={user || guestMode ? "/dashboard" : "/login"} replace />} />
          <Route path="/login" element={user || guestMode ? <Navigate to="/dashboard" replace /> : <LoginPage onLogin={handleLogin} onRegister={handleRegister} onGuest={enableGuestMode} t={t} />} />
          <Route path="/dashboard" element={user || guestMode ? <DashboardPage user={user} data={data} travelMode={travelMode} t={t} onGenerateAdvice={generateAdvice} onSaveAdvice={saveAdvice} onDeleteSavedAdvice={deleteSavedAdvice} onCreateFavorite={createFavorite} onDeleteFavorite={deleteFavorite} onLoadQuickGuide={loadQuickGuide} onCompareCultures={compareCultures} onRunMistakeAlert={runMistakeAlert} onParseAdviceQuery={parseAdviceQuery} onRunSimulation={runSimulation} /> : <Navigate to="/login" replace />} />
          <Route path="/feedback" element={user || guestMode ? <FeedbackPage user={user} feedback={data.feedback} communityTips={data.communityTips} onSubmitFeedback={submitFeedback} onDeleteFeedback={deleteFeedback} onCreateCommunityTip={createCommunityTip} onDeleteCommunityTip={deleteCommunityTip} cultures={data.cultures} scenarios={data.scenarios} t={t} /> : <Navigate to="/login" replace />} />
          <Route path="/admin" element={user?.role === "admin" ? <AdminPage users={data.adminUsers} feedback={data.feedback} analytics={data.analytics} /> : <Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to={user || guestMode ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </main>

      <aside className="right-panel">
        <div className="panel">
          <h3>Insights</h3>
          <div className="list-stack">
            <div className="list-card">
              <strong>Daily tip</strong>
              <span>{travelMode && data.dailyTip ? `${data.dailyTip.culture_name} · ${data.dailyTip.scenario_name}` : "Turn on travel mode"}</span>
              <small>{travelMode && data.dailyTip ? data.dailyTip.tip : "Get a fresh etiquette tip each day."}</small>
            </div>
            <div className="list-card">
              <strong>Recommendations</strong>
              <span>{data.recommendations.items.length ? data.recommendations.items[0].culture_name : "No suggestions yet"}</span>
              <small>{data.recommendations.items.length ? data.recommendations.items[0].scenario_name : "Save advice to personalize."}</small>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Saved</h3>
          <div className="list-stack">
            <div className="list-card">
              <strong>Favorites</strong>
              <span>{data.favorites.length} items</span>
              <small>Quick access for frequent scenarios.</small>
            </div>
            <div className="list-card">
              <strong>Saved advice</strong>
              <span>{data.savedAdvice.length} items</span>
              <small>Review past guidance anytime.</small>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Preview</h3>
          {data.currentAdvice ? (
            <div className="list-card">
              <strong>{data.currentAdvice.cultureName}</strong>
              <span>{data.currentAdvice.scenarioName}</span>
              <small>Risk: {data.currentAdvice.riskLabel}</small>
            </div>
          ) : (
            <div className="empty-state compact">
              <p className="muted">Generate advice to see a quick preview.</p>
            </div>
          )}
        </div>
      </aside>

      {toast ? <div className="toast">{toast}</div> : null}
    </div>
  );
}

function SidebarLink({ to, icon, label }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
      <span className="nav-indicator" />
      <Icon name={icon} size={18} className="nav-icon" />
      <span>{label}</span>
    </NavLink>
  );
}

function StatCard({ label, value }) {
  return (
    <article className="stat-card">
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}

export default App;
