import { useState } from "react";
import { Icon } from "../components/Icons";

function FeedbackPage({
  user,
  feedback,
  communityTips,
  onSubmitFeedback,
  onDeleteFeedback,
  onCreateCommunityTip,
  onDeleteCommunityTip,
  cultures,
  scenarios,
  t,
}) {
  const [form, setForm] = useState({ rating: 5, comment: "" });
  const [tipForm, setTipForm] = useState({ culture_id: "", scenario_id: "", title: "", tip_text: "" });
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      setError("");
      await onSubmitFeedback({ rating: Number(form.rating), comment: form.comment });
      setForm({ rating: 5, comment: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleTipSubmit(event) {
    event.preventDefault();
    try {
      setError("");
      await onCreateCommunityTip({
        culture_id: Number(tipForm.culture_id),
        scenario_id: tipForm.scenario_id ? Number(tipForm.scenario_id) : null,
        title: tipForm.title,
        tip_text: tipForm.tip_text,
      });
      setTipForm({ culture_id: "", scenario_id: "", title: "", tip_text: "" });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="page-stack">
      <div className="two-column">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Feedback</p>
            <h2>Send suggestions</h2>
          </div>
          {user ? (
            <form className="form-stack" onSubmit={handleSubmit}>
              <select value={form.rating} onChange={(event) => setForm({ ...form, rating: event.target.value })}>
                <option value="5">5 - Excellent</option>
                <option value="4">4 - Helpful</option>
                <option value="3">3 - Okay</option>
                <option value="2">2 - Needs work</option>
                <option value="1">1 - Poor</option>
              </select>
              <textarea rows="5" placeholder="Share what should improve" value={form.comment} onChange={(event) => setForm({ ...form, comment: event.target.value })} />
              <button type="submit">Submit feedback</button>
            </form>
          ) : (
            <p className="muted">Sign in to submit feedback.</p>
          )}
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{t("community_tips")}</p>
            <h2>Share real experiences</h2>
          </div>
          {user ? (
            <form className="form-stack" onSubmit={handleTipSubmit}>
              <label className="select-shell">
                <Icon name="globe" size={18} />
                <select value={tipForm.culture_id} onChange={(event) => setTipForm({ ...tipForm, culture_id: event.target.value })}>
                  <option value="">Select country</option>
                  {cultures.map((culture) => <option key={culture.id} value={culture.id}>{culture.name}</option>)}
                </select>
              </label>
              <label className="select-shell">
                <Icon name="scenario" size={18} />
                <select value={tipForm.scenario_id} onChange={(event) => setTipForm({ ...tipForm, scenario_id: event.target.value })}>
                  <option value="">Optional scenario</option>
                  {scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}
                </select>
              </label>
              <input placeholder="Tip title" value={tipForm.title} onChange={(event) => setTipForm({ ...tipForm, title: event.target.value })} />
              <textarea rows="4" placeholder="Example: In Tokyo, wait for the host to guide seating before sitting down." value={tipForm.tip_text} onChange={(event) => setTipForm({ ...tipForm, tip_text: event.target.value })} />
              <button type="submit">{t("submit_tip")}</button>
            </form>
          ) : (
            <p className="muted">Sign in to share community tips.</p>
          )}
        </article>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="two-column">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{user?.role === "admin" ? "Moderation" : "History"}</p>
            <h2>{user?.role === "admin" ? "All feedback" : "Your feedback"}</h2>
          </div>
          <div className="list-stack">
            {feedback.length ? feedback.map((item) => (
              <article key={item.id} className="list-card">
                <strong>{item.user_name}</strong>
                <span>Rating: {item.rating}/5</span>
                <small>{new Date(item.created_at).toLocaleString()}</small>
                <p className="muted">{item.comment || "No comment provided."}</p>
                {user ? <button className="ghost-button" onClick={() => onDeleteFeedback(item.id)}>Delete</button> : null}
              </article>
            )) : <p className="muted">No feedback available.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">{t("community_tips")}</p>
            <h2>User experiences and tips</h2>
          </div>
          <div className="list-stack">
            {communityTips.length ? communityTips.map((item) => (
              <article key={item.id} className="list-card">
                <strong>{item.title}</strong>
                <span>{item.culture_name}{item.scenario_name ? ` • ${item.scenario_name}` : ""}</span>
                <small>By {item.user_name}</small>
                <p className="muted">{item.tip_text}</p>
                {user && (user.role === "admin" || user.name === item.user_name) ? <button className="ghost-button" onClick={() => onDeleteCommunityTip(item.id)}>Delete</button> : null}
              </article>
            )) : <p className="muted">No community tips yet.</p>}
          </div>
        </article>
      </div>
    </section>
  );
}

export default FeedbackPage;
