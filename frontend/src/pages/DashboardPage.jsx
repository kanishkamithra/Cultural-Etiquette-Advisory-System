import { useEffect, useMemo, useState } from "react";
import { Icon } from "../components/Icons";

function DashboardPage({
  user,
  data,
  travelMode,
  t,
  onGenerateAdvice,
  onSaveAdvice,
  onDeleteSavedAdvice,
  onCreateFavorite,
  onDeleteFavorite,
  onLoadQuickGuide,
  onCompareCultures,
  onRunMistakeAlert,
  onParseAdviceQuery,
  onRunSimulation,
}) {
  const [form, setForm] = useState({
    cultureId: "",
    scenarioId: "",
    formality: "formal",
    setting: "business",
    relationship: "client",
    userNotes: "",
  });
  const [quickGuide, setQuickGuide] = useState(null);
  const [queryText, setQueryText] = useState("");
  const [compareForm, setCompareForm] = useState({ left_culture_id: "", right_culture_id: "", scenario_id: "" });
  const [compareResult, setCompareResult] = useState(null);
  const [mistakeForm, setMistakeForm] = useState({ culture_id: "", scenario_id: "", action_text: "" });
  const [mistakeResult, setMistakeResult] = useState(null);
  const [simulationForm, setSimulationForm] = useState({ step: 1, choice: "" });
  const [isOnline, setIsOnline] = useState(() => navigator.onLine);
  const [error, setError] = useState("");

  const currentFavorite = useMemo(() => {
    if (!data.currentAdvice) return null;
    return data.favorites.find(
      (item) => item.culture_id === data.currentAdvice.cultureId && item.scenario_id === data.currentAdvice.scenarioId,
    );
  }, [data.currentAdvice, data.favorites]);

  

  useEffect(() => {
    function updateStatus() {
      setIsOnline(navigator.onLine);
    }

    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);
    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
    };
  }, []);

  async function loadAdviceBundle(cultureId, scenarioId) {
    await onGenerateAdvice({
      culture_id: Number(cultureId),
      scenario_id: Number(scenarioId),
      formality: form.formality,
      setting: form.setting,
      relationship: form.relationship,
      user_notes: form.userNotes,
    });
    const guide = await onLoadQuickGuide(Number(cultureId));
    setQuickGuide(guide);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      setError("");
      if (!form.cultureId || !form.scenarioId) {
        setError("Please select both a country and a scenario.");
        return;
      }
      await loadAdviceBundle(form.cultureId, form.scenarioId);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleQueryAssist(event) {
    event.preventDefault();
    try {
      setError("");
      if (!queryText.trim()) {
        setError("Enter a short request to analyze.");
        return;
      }
      const parsed = await onParseAdviceQuery(queryText);
      if (parsed.culture) {
        setForm((previous) => ({ ...previous, cultureId: String(parsed.culture.id) }));
      }
      if (parsed.scenario) {
        setForm((previous) => ({ ...previous, scenarioId: String(parsed.scenario.id) }));
      }
      if (parsed.context) {
        setForm((previous) => ({
          ...previous,
          formality: parsed.context.formality,
          setting: parsed.context.setting,
          relationship: parsed.context.relationship,
        }));
      }
      if (parsed.ready) {
        await loadAdviceBundle(parsed.culture.id, parsed.scenario.id);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleFavorite() {
    if (!user || !data.currentAdvice) return;
    if (currentFavorite) {
      await onDeleteFavorite(currentFavorite.id);
    } else {
      await onCreateFavorite({ culture_id: data.currentAdvice.cultureId, scenario_id: data.currentAdvice.scenarioId });
    }
  }

  async function handleCompare(event) {
    event.preventDefault();
    try {
      setCompareResult(await onCompareCultures({
        left_culture_id: Number(compareForm.left_culture_id),
        right_culture_id: Number(compareForm.right_culture_id),
        scenario_id: Number(compareForm.scenario_id),
      }));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleMistakeAlert(event) {
    event.preventDefault();
    try {
      setMistakeResult(await onRunMistakeAlert({
        culture_id: Number(mistakeForm.culture_id),
        scenario_id: mistakeForm.scenario_id ? Number(mistakeForm.scenario_id) : null,
        action_text: mistakeForm.action_text,
      }));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSimulation(event) {
    event.preventDefault();
    try {
      setError("");
      if (!form.cultureId || !form.scenarioId) {
        setError("Select a country and scenario before running the simulation.");
        return;
      }
      if (!simulationForm.choice.trim()) {
        setError("Describe your action so we can evaluate it.");
        return;
      }
      const result = await onRunSimulation({
        culture_id: Number(form.cultureId),
        scenario_id: Number(form.scenarioId),
        step: simulationForm.step,
        choice: simulationForm.choice,
        formality: form.formality,
        setting: form.setting,
        relationship: form.relationship,
      });
      setSimulationForm((previous) => ({
        step: result.next_step || previous.step,
        choice: "",
      }));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page-stack">
      <article className="panel hero-panel dashboard-hero refined-hero">
        <div className="hero-copy-row">
          <div>
            <p className="kicker">Dashboard</p>
            <h2>Plan the interaction with confidence</h2>
            <p className="muted">Select a country and scenario to generate focused advice.</p>
          </div>
          <div className="hero-status-cluster">
            <span className={isOnline ? "status-chip online" : "status-chip offline"}>
              <Icon name={isOnline ? "wifi" : "wifi_off"} size={14} />
              <span>{isOnline ? "Online" : "Offline-ready"}</span>
            </span>
            {travelMode ? <span className="status-chip neutral">Travel mode on</span> : null}
          </div>
        </div>

        <div className="dashboard-focus-grid">
          <form className="panel-slab planner-card" onSubmit={handleSubmit}>
            <div className="section-heading compact">
              <p className="kicker">Advice planner</p>
              <h3>Generate tailored guidance</h3>
            </div>
            <div className="form-inline planner-inline">
              <label className="select-shell">
                <Icon name="globe" size={18} />
                <select required value={form.cultureId} onChange={(event) => setForm({ ...form, cultureId: event.target.value })}>
                  <option value="">Select country</option>
                  {data.cultures.map((culture) => <option key={culture.id} value={culture.id}>{culture.name}</option>)}
                </select>
              </label>
              <label className="select-shell">
                <Icon name="scenario" size={18} />
                <select required value={form.scenarioId} onChange={(event) => setForm({ ...form, scenarioId: event.target.value })}>
                  <option value="">Select scenario</option>
                  {data.scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}
                </select>
              </label>
              <button type="submit">Generate advice</button>
            </div>
            <div className="context-grid">
              <label>
                <span className="field-label">Formality</span>
                <select value={form.formality} onChange={(event) => setForm({ ...form, formality: event.target.value })}>
                  <option value="formal">Formal</option>
                  <option value="informal">Informal</option>
                </select>
              </label>
              <label>
                <span className="field-label">Setting</span>
                <select value={form.setting} onChange={(event) => setForm({ ...form, setting: event.target.value })}>
                  <option value="business">Business</option>
                  <option value="casual">Casual</option>
                </select>
              </label>
              <label>
                <span className="field-label">Relationship</span>
                <select value={form.relationship} onChange={(event) => setForm({ ...form, relationship: event.target.value })}>
                  <option value="client">Client</option>
                  <option value="boss">Boss</option>
                  <option value="colleague">Colleague</option>
                  <option value="host">Host</option>
                  <option value="elder">Elder</option>
                  <option value="friend">Friend</option>
                  <option value="stranger">Stranger</option>
                </select>
              </label>
            </div>
            <textarea rows="3" placeholder="Optional: mention habits or concerns to detect conflicts." value={form.userNotes} onChange={(event) => setForm({ ...form, userNotes: event.target.value })} />
          </form>
        </div>

        <form className="panel-slab query-card" onSubmit={handleQueryAssist}>
          <h3 className="mini-heading"><Icon name="search" size={16} />Describe the situation</h3>
          <textarea rows="3" placeholder='Try: "Informal dinner in Japan with a client."' value={queryText} onChange={(event) => setQueryText(event.target.value)} />
          <div className="action-row">
            <button type="submit" className="ghost-button">Analyze request</button>
            {data.parsedQuery ? <p className="muted">{data.parsedQuery.message}</p> : null}
          </div>
        </form>

        {error ? <p className="error-text">{error}</p> : null}
      </article>

      <div className="two-column dashboard-main-columns">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Advice</p>
            <h2>{data.currentAdvice ? `${data.currentAdvice.cultureName} - ${data.currentAdvice.scenarioName}` : "No advice selected yet"}</h2>
          </div>
          {data.currentAdvice ? (
            <>
              <div className="risk-summary-card">
                <div>
                  <span className="field-label">Risk level</span>
                  <strong>{data.currentAdvice.riskLabel}</strong>
                </div>
                <div>
                  <span className="field-label">Risk score</span>
                  <strong>{data.currentAdvice.riskPercent}%</strong>
                </div>
                <div>
                  <span className="field-label">Context</span>
                  <div className="tag-row compact-tags">
                    <span className="tag">{data.currentAdvice.context.formality}</span>
                    <span className="tag">{data.currentAdvice.context.setting}</span>
                    <span className="tag">{data.currentAdvice.context.relationship}</span>
                  </div>
                </div>
              </div>

              <div className="panel-slab">
                <h3 className="mini-heading"><Icon name="spark" size={16} />Why this advice fits</h3>
                <p className="muted">{data.currentAdvice.explanation}</p>
              </div>

              <div className="action-row">
                <button onClick={onSaveAdvice} disabled={!user}>Save advice</button>
                <button className="ghost-button" onClick={toggleFavorite} disabled={!user}>
                  {currentFavorite ? "Remove favorite" : "Add favorite"}
                </button>
              </div>

              <div className="advice-grid">
                <div className="content-card">
                  <h3 className="mini-heading"><Icon name="check" size={16} />Do</h3>
                  <ul>{data.currentAdvice.rules.map((rule) => <li key={`${rule.id}-do`}>{rule.do_text}</li>)}</ul>
                </div>
                <div className="content-card">
                  <h3 className="mini-heading"><Icon name="alert" size={16} />Don't</h3>
                  <ul>{data.currentAdvice.rules.map((rule) => <li key={`${rule.id}-dont`}>{rule.dont_text}</li>)}</ul>
                </div>
              </div>

              <div className="advice-grid">
                <div className="content-card">
                  <h3 className="mini-heading"><Icon name="bookmark" size={16} />Safe alternatives</h3>
                  <ul>{data.currentAdvice.rules.map((rule) => <li key={`${rule.id}-safe`}>{rule.safe_alternative}</li>)}</ul>
                </div>
                <div className="content-card">
                  <h3 className="mini-heading"><Icon name="spark" size={16} />Action plan</h3>
                  <ul>{data.currentAdvice.safeActions.map((item, index) => <li key={`safe-plan-${index}`}>{item}</li>)}</ul>
                </div>
              </div>

              {data.currentAdvice.conflicts?.length ? (
                <div className="panel-slab warning-slab">
                  <h3 className="mini-heading"><Icon name="alert" size={16} />Cultural conflict detection</h3>
                  <ul>{data.currentAdvice.conflicts.map((item, index) => <li key={`conflict-${index}`}>{item.warning}</li>)}</ul>
                </div>
              ) : null}
            </>
          ) : (
            <div className="empty-state">
              <Icon name="empty" size={44} />
              <h3>Generate your first advice card</h3>
              <p className="muted">The dashboard now keeps country context, quick rules, and tailored advice in one place.</p>
            </div>
          )}
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Saved</p>
            <h2>Bookmarks and quick return points</h2>
          </div>
          {user ? (
            <div className="list-stack">
              {data.favorites.length ? data.favorites.map((item) => (
                <article key={item.id} className="list-card interactive-card">
                  <strong className="mini-heading"><Icon name="bookmark" size={16} />{item.culture_name} - {item.scenario_name}</strong>
                  <small>{new Date(item.created_at).toLocaleString()}</small>
                  <button className="ghost-button" onClick={() => onDeleteFavorite(item.id)}>Remove</button>
                </article>
              )) : <div className="empty-state compact"><Icon name="bookmark" size={36} /><p className="muted">No favorites yet.</p></div>}

              {data.savedAdvice.length ? data.savedAdvice.map((item) => (
                <article key={item.id} className="list-card interactive-card">
                  <strong>{item.culture_name} - {item.scenario_name}</strong>
                  <span>{item.risk_label} risk</span>
                  <small>{new Date(item.generated_at).toLocaleString()}</small>
                  <button className="ghost-button" onClick={() => onDeleteSavedAdvice(item.id)}>Delete</button>
                </article>
              )) : null}
            </div>
          ) : (
            <div className="empty-state compact">
              <Icon name="user" size={36} />
              <p className="muted">Sign in to save advice and keep favorites.</p>
            </div>
          )}
        </article>
      </div>

      <div className="two-column dashboard-main-columns">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{t("quick_guide")}</p>
            <h2>Top do's and don'ts</h2>
          </div>
          {quickGuide ? (
            <div className="quick-guide-grid">
              <div className="content-card">
                <h3 className="mini-heading"><Icon name="check" size={16} />Top 5 Do's</h3>
                <ul>{quickGuide.dos.map((item, index) => <li key={`${item.text}-${index}`}>{item.text}</li>)}</ul>
              </div>
              <div className="content-card">
                <h3 className="mini-heading"><Icon name="alert" size={16} />Top 5 Don'ts</h3>
                <ul>{quickGuide.donts.map((item, index) => <li key={`${item.text}-${index}`}>{item.text}</li>)}</ul>
              </div>
            </div>
          ) : (
            <div className="empty-state compact"><Icon name="spark" size={36} /><p className="muted">Generate advice to load a compact country quick guide.</p></div>
          )}
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Simulation</p>
            <h2>Practice the situation safely</h2>
          </div>
          <form className="form-stack" onSubmit={handleSimulation}>
            <textarea rows="4" placeholder="Describe what you would do in this situation." value={simulationForm.choice} onChange={(event) => setSimulationForm({ ...simulationForm, choice: event.target.value })} />
            <button type="submit" disabled={!form.cultureId || !form.scenarioId}>Evaluate decision</button>
          </form>
          {data.simulation ? (
            <div className="panel-slab">
              <h3 className="mini-heading"><Icon name="spark" size={16} />Step {data.simulation.step}</h3>
              <p><strong>Prompt:</strong> {data.simulation.prompt}</p>
              <p><strong>{data.simulation.feedback.verdict}</strong> ({data.simulation.feedback.score}%)</p>
              <p className="muted">{data.simulation.feedback.explanation}</p>
              <p><strong>Recommended action:</strong> {data.simulation.feedback.recommended_action}</p>
            </div>
          ) : <div className="empty-state compact"><Icon name="spark" size={36} /><p className="muted">Choose a country and scenario, then test your decisions here.</p></div>}
        </article>
      </div>

      <div className="two-column dashboard-main-columns">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{t("mistake_alert")}</p>
            <h2>Evaluate an action</h2>
          </div>
          <form className="form-stack" onSubmit={handleMistakeAlert}>
            <label className="select-shell">
              <Icon name="globe" size={18} />
              <select value={mistakeForm.culture_id} onChange={(event) => setMistakeForm({ ...mistakeForm, culture_id: event.target.value })}>
                <option value="">Select country</option>
                {data.cultures.map((culture) => <option key={culture.id} value={culture.id}>{culture.name}</option>)}
              </select>
            </label>
            <label className="select-shell">
              <Icon name="scenario" size={18} />
              <select value={mistakeForm.scenario_id} onChange={(event) => setMistakeForm({ ...mistakeForm, scenario_id: event.target.value })}>
                <option value="">Any scenario</option>
                {data.scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}
              </select>
            </label>
            <textarea rows="4" placeholder="Example: I plan to start eating before the host begins." value={mistakeForm.action_text} onChange={(event) => setMistakeForm({ ...mistakeForm, action_text: event.target.value })} />
            <button type="submit">Check risk</button>
          </form>
          {mistakeResult ? (
            <div className="panel-slab">
              <h3 className="mini-heading"><Icon name="alert" size={16} />{mistakeResult.risk_label} Risk ({mistakeResult.risk_percent}%)</h3>
              <p className="muted">{mistakeResult.explanation}</p>
              <p><strong>Safer alternative:</strong> {mistakeResult.safer_alternative}</p>
            </div>
          ) : null}
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{t("compare")}</p>
            <h2>Compare etiquette between two countries</h2>
          </div>
          <form className="comparison-grid" onSubmit={handleCompare}>
            <label className="select-shell">
              <Icon name="globe" size={18} />
              <select value={compareForm.left_culture_id} onChange={(event) => setCompareForm({ ...compareForm, left_culture_id: event.target.value })}>
                <option value="">Left country</option>
                {data.cultures.map((culture) => <option key={culture.id} value={culture.id}>{culture.name}</option>)}
              </select>
            </label>
            <label className="select-shell">
              <Icon name="globe" size={18} />
              <select value={compareForm.right_culture_id} onChange={(event) => setCompareForm({ ...compareForm, right_culture_id: event.target.value })}>
                <option value="">Right country</option>
                {data.cultures.map((culture) => <option key={culture.id} value={culture.id}>{culture.name}</option>)}
              </select>
            </label>
            <label className="select-shell">
              <Icon name="scenario" size={18} />
              <select value={compareForm.scenario_id} onChange={(event) => setCompareForm({ ...compareForm, scenario_id: event.target.value })}>
                <option value="">Select scenario</option>
                {data.scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}
              </select>
            </label>
            <button type="submit">Compare</button>
          </form>
          {compareResult ? (
            <div className="comparison-table">
              <div className="comparison-header">
                <strong>{compareResult.left.name}</strong>
                <strong>{compareResult.right.name}</strong>
              </div>
              <div className="comparison-row">
                <div><h4>Do</h4>{compareResult.left_rules.map((rule, index) => <p key={`left-do-${index}`}>{rule.do_text}</p>)}</div>
                <div><h4>Do</h4>{compareResult.right_rules.map((rule, index) => <p key={`right-do-${index}`}>{rule.do_text}</p>)}</div>
              </div>
              <div className="comparison-row">
                <div><h4>Don't</h4>{compareResult.left_rules.map((rule, index) => <p key={`left-dont-${index}`}>{rule.dont_text}</p>)}</div>
                <div><h4>Don't</h4>{compareResult.right_rules.map((rule, index) => <p key={`right-dont-${index}`}>{rule.dont_text}</p>)}</div>
              </div>
            </div>
          ) : null}
        </article>
      </div>
    </section>
  );
}

export default DashboardPage;
