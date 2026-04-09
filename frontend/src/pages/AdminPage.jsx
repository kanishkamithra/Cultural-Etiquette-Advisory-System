import { Icon } from "../components/Icons";

function AdminPage({ users, feedback, analytics }) {
  return (
    <section className="page-stack">
      <article className="panel dashboard-hero">
        <div>
          <p className="kicker">Admin Overview</p>
          <h2>Users, feedback, and product analytics</h2>
          <p className="muted">Monitor platform usage, discover which countries are searched most often, and review common etiquette mistakes users are checking.</p>
        </div>
      </article>

      <div className="three-grid">
        <article className="panel">
          <h3 className="mini-heading"><Icon name="globe" size={16} />Most searched countries</h3>
          <div className="list-stack">
            {analytics.most_searched_countries?.length ? analytics.most_searched_countries.map((item) => (
              <article key={item.culture_name} className="list-card">
                <strong>{item.culture_name}</strong>
                <small>{item.search_count} searches</small>
              </article>
            )) : <p className="muted">No search analytics yet.</p>}
          </div>
        </article>
        <article className="panel">
          <h3 className="mini-heading"><Icon name="alert" size={16} />Common mistakes</h3>
          <div className="list-stack">
            {analytics.common_mistakes?.length ? analytics.common_mistakes.map((item, index) => (
              <article key={`${item.action_text}-${index}`} className="list-card">
                <strong>{item.action_text}</strong>
                <small>{item.attempts} evaluations</small>
              </article>
            )) : <p className="muted">No mistake alerts yet.</p>}
          </div>
        </article>
        <article className="panel">
          <h3 className="mini-heading"><Icon name="feedback" size={16} />Feedback trends</h3>
          <div className="list-stack">
            {analytics.feedback_trends?.length ? analytics.feedback_trends.map((item) => (
              <article key={item.month} className="list-card">
                <strong>{item.month}</strong>
                <small>{item.average_rating}/5 average from {item.entries} entries</small>
              </article>
            )) : <p className="muted">No feedback trend data yet.</p>}
          </div>
        </article>
      </div>

      <div className="two-column">
        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Users</p>
            <h2>Registered users</h2>
          </div>
          <div className="list-stack wide-list">
            {users.length ? users.map((item) => (
              <article key={item.id} className="list-card">
                <strong>{item.name}</strong>
                <span>{item.email}</span>
                <small>{item.role} | Saved advice: {item.saved_advice_count} | Feedback: {item.feedback_count}</small>
              </article>
            )) : <p className="muted">No users found.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="section-heading">
            <p className="kicker">Feedback</p>
            <h2>Latest submissions</h2>
          </div>
          <div className="list-stack wide-list">
            {feedback.length ? feedback.map((item) => (
              <article key={item.id} className="list-card">
                <strong>{item.user_name}</strong>
                <span>Rating: {item.rating}/5</span>
                <small>{new Date(item.created_at).toLocaleString()}</small>
                <p className="muted">{item.comment || "No comment provided."}</p>
              </article>
            )) : <p className="muted">No feedback available.</p>}
          </div>
        </article>
      </div>
    </section>
  );
}

export default AdminPage;
