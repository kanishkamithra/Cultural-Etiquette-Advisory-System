const API_BASE = "/api";

const state = {
  token: localStorage.getItem("ceas-token"),
  user: null,
  currentAdvice: null,
  cultures: [],
  scenarios: [],
  rules: [],
  savedAdvice: [],
  feedback: [],
};

const elements = {
  tabs: document.querySelectorAll(".tab-button"),
  tabContents: document.querySelectorAll(".tab-content"),
  sessionBanner: document.getElementById("sessionBanner"),
  logoutButton: document.getElementById("logoutButton"),
  adviceForm: document.getElementById("adviceForm"),
  countrySelect: document.getElementById("countrySelect"),
  scenarioSelect: document.getElementById("scenarioSelect"),
  ruleCultureSelect: document.getElementById("ruleCultureSelect"),
  ruleScenarioSelect: document.getElementById("ruleScenarioSelect"),
  adviceState: document.getElementById("adviceState"),
  adviceCard: document.getElementById("adviceCard"),
  adviceTitle: document.getElementById("adviceTitle"),
  doList: document.getElementById("doList"),
  dontList: document.getElementById("dontList"),
  reasonList: document.getElementById("reasonList"),
  safeAlternativeList: document.getElementById("safeAlternativeList"),
  riskLabel: document.getElementById("riskLabel"),
  meterFill: document.getElementById("meterFill"),
  saveAdviceButton: document.getElementById("saveAdviceButton"),
  exportAdviceButton: document.getElementById("exportAdviceButton"),
  loginForm: document.getElementById("loginForm"),
  registerForm: document.getElementById("registerForm"),
  guestAccessButton: document.getElementById("guestAccessButton"),
  savedAdviceList: document.getElementById("savedAdviceList"),
  feedbackForm: document.getElementById("feedbackForm"),
  feedbackList: document.getElementById("feedbackList"),
  adminFeedbackList: document.getElementById("adminFeedbackList"),
  adminPanel: document.getElementById("adminPanel"),
  cultureForm: document.getElementById("cultureForm"),
  scenarioForm: document.getElementById("scenarioForm"),
  ruleForm: document.getElementById("ruleForm"),
  ruleInventory: document.getElementById("ruleInventory"),
  heroCountries: document.getElementById("heroCountries"),
  heroScenarios: document.getElementById("heroScenarios"),
  heroRules: document.getElementById("heroRules"),
  toast: document.getElementById("toast"),
};

bootstrap();

async function bootstrap() {
  bindEvents();
  await hydrateSession();
  await refreshData();
  renderSession();
}

function bindEvents() {
  elements.tabs.forEach((button) => button.addEventListener("click", () => switchTab(button.dataset.tab)));
  elements.registerForm.addEventListener("submit", handleRegister);
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.guestAccessButton.addEventListener("click", handleGuestAccess);
  elements.logoutButton.addEventListener("click", handleLogout);
  elements.adviceForm.addEventListener("submit", handleAdviceLookup);
  elements.saveAdviceButton.addEventListener("click", saveAdviceForUser);
  elements.exportAdviceButton.addEventListener("click", exportAdvice);
  elements.feedbackForm.addEventListener("submit", submitFeedback);
  elements.cultureForm.addEventListener("submit", addCulture);
  elements.scenarioForm.addEventListener("submit", addScenario);
  elements.ruleForm.addEventListener("submit", addRule);
  elements.savedAdviceList.addEventListener("click", handleSavedAdviceDelete);
  elements.ruleInventory.addEventListener("click", handleRuleDelete);
  elements.adminFeedbackList.addEventListener("click", handleFeedbackDelete);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

async function hydrateSession() {
  if (!state.token) {
    return;
  }
  try {
    state.user = await api("/auth/me");
  } catch (_) {
    clearSession();
  }
}

async function refreshData() {
  const [stats, cultures, scenarios, rules] = await Promise.all([
    api("/stats"),
    api("/cultures"),
    api("/scenarios"),
    api("/rules"),
  ]);

  state.cultures = cultures;
  state.scenarios = scenarios;
  state.rules = rules;

  elements.heroCountries.textContent = stats.cultures;
  elements.heroScenarios.textContent = stats.scenarios;
  elements.heroRules.textContent = stats.rules;
  refreshSelects();

  if (state.user) {
    await refreshUserCollections();
  } else {
    state.savedAdvice = [];
    state.feedback = [];
    renderCollections();
  }
}

async function refreshUserCollections() {
  const calls = [api("/saved-advice"), api("/feedback")];
  const [savedAdvice, feedback] = await Promise.all(calls);
  state.savedAdvice = savedAdvice;
  state.feedback = feedback;
  renderCollections();
}

function switchTab(tabId) {
  elements.tabs.forEach((button) => button.classList.toggle("active", button.dataset.tab === tabId));
  elements.tabContents.forEach((section) => section.classList.toggle("active", section.id === tabId));
}

async function handleRegister(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const session = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name").trim(),
        email: form.get("email").trim(),
        password: form.get("password"),
      }),
    });
    applySession(session);
    event.target.reset();
    await refreshData();
    renderSession();
    showToast("Account created and signed in.");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const session = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: form.get("email").trim(),
        password: form.get("password"),
      }),
    });
    applySession(session);
    event.target.reset();
    await refreshData();
    renderSession();
    showToast(`Welcome back, ${state.user.name}.`);
  } catch (error) {
    showToast(error.message);
  }
}

function handleGuestAccess() {
  clearSession();
  renderSession();
  renderCollections();
  showToast("Guest access enabled.");
}

async function handleLogout() {
  if (state.token) {
    try {
      await api("/auth/logout", { method: "POST" });
    } catch (_) {
      // Ignore invalidated sessions on logout.
    }
  }
  clearSession();
  renderSession();
  renderCollections();
  showToast("Signed out.");
}

function applySession(session) {
  state.token = session.token;
  state.user = session.user;
  localStorage.setItem("ceas-token", session.token);
}

function clearSession() {
  state.token = null;
  state.user = null;
  state.currentAdvice = null;
  state.savedAdvice = [];
  state.feedback = [];
  localStorage.removeItem("ceas-token");
  elements.adviceCard.classList.add("hidden");
  elements.adviceState.classList.remove("hidden");
  elements.adviceState.innerHTML = "<p>Select a culture and scenario to generate etiquette advice.</p>";
}

function renderSession() {
  if (state.user?.role === "admin") {
    elements.sessionBanner.textContent = `Signed in as ${state.user.name} (Admin)`;
  } else if (state.user) {
    elements.sessionBanner.textContent = `Signed in as ${state.user.name}`;
  } else {
    elements.sessionBanner.textContent = "Browsing in guest mode";
  }

  elements.logoutButton.classList.toggle("hidden", !state.user);
  elements.adminPanel.classList.toggle("hidden", state.user?.role !== "admin");
}

function refreshSelects() {
  fillSelect(elements.countrySelect, state.cultures, "Choose a culture");
  fillSelect(elements.scenarioSelect, state.scenarios, "Choose a scenario");
  fillSelect(elements.ruleCultureSelect, state.cultures, "Select culture");
  fillSelect(elements.ruleScenarioSelect, state.scenarios, "Select scenario");
}

function fillSelect(select, items, placeholder) {
  const currentValue = select.value;
  select.innerHTML = `<option value="">${placeholder}</option>` + items.map((item) => `<option value="${item.id}">${item.name}</option>`).join("");
  if (items.some((item) => String(item.id) === currentValue)) {
    select.value = currentValue;
  }
}

async function handleAdviceLookup(event) {
  event.preventDefault();
  const cultureId = Number(elements.countrySelect.value);
  const scenarioId = Number(elements.scenarioSelect.value);
  if (!cultureId || !scenarioId) {
    return showToast("Please select both a culture and a scenario.");
  }

  try {
    const result = await api("/advice/generate", {
      method: "POST",
      body: JSON.stringify({ culture_id: cultureId, scenario_id: scenarioId }),
    });
    state.currentAdvice = {
      cultureId,
      scenarioId,
      cultureName: result.culture.name,
      scenarioName: result.scenario.name,
      generatedAt: new Date().toISOString(),
      riskLabel: result.risk_label,
      riskPercent: result.risk_percent,
      rules: result.rules,
    };
    renderAdvice();
  } catch (error) {
    state.currentAdvice = null;
    elements.adviceCard.classList.add("hidden");
    elements.adviceState.classList.remove("hidden");
    elements.adviceState.innerHTML = `<p>${error.message}</p>`;
  }
}

function renderAdvice() {
  const advice = state.currentAdvice;
  if (!advice) {
    return;
  }

  elements.adviceState.classList.add("hidden");
  elements.adviceCard.classList.remove("hidden");
  elements.adviceTitle.textContent = `${advice.cultureName} - ${advice.scenarioName}`;
  elements.riskLabel.textContent = `${advice.riskLabel} (${advice.riskPercent}%)`;
  elements.meterFill.style.width = `${advice.riskPercent}%`;
  elements.doList.innerHTML = advice.rules.map((rule) => `<li>${rule.do_text} <small>(${rule.severity})</small></li>`).join("");
  elements.dontList.innerHTML = advice.rules.map((rule) => `<li>${rule.dont_text}</li>`).join("");
  elements.reasonList.innerHTML = advice.rules.map((rule) => `<span>${rule.reason}</span>`).join("");
  elements.safeAlternativeList.innerHTML = advice.rules.map((rule) => `<li>${rule.safe_alternative}</li>`).join("");
}

async function saveAdviceForUser() {
  if (!state.currentAdvice) {
    return showToast("Generate advice before saving.");
  }
  if (!state.user) {
    return showToast("Sign in to save advice to your profile.");
  }

  try {
    await api("/saved-advice", {
      method: "POST",
      body: JSON.stringify({
        culture_id: state.currentAdvice.cultureId,
        scenario_id: state.currentAdvice.scenarioId,
        culture_name: state.currentAdvice.cultureName,
        scenario_name: state.currentAdvice.scenarioName,
        risk_label: state.currentAdvice.riskLabel,
        risk_percent: state.currentAdvice.riskPercent,
        generated_at: state.currentAdvice.generatedAt,
      }),
    });
    await refreshUserCollections();
    showToast("Advice saved.");
  } catch (error) {
    showToast(error.message);
  }
}

function exportAdvice() {
  if (!state.currentAdvice) {
    return showToast("Generate advice before exporting.");
  }

  const lines = [
    "Cultural Etiquette Advisory System",
    `${state.currentAdvice.cultureName} - ${state.currentAdvice.scenarioName}`,
    `Risk: ${state.currentAdvice.riskLabel} (${state.currentAdvice.riskPercent}%)`,
    "",
    "DO",
    ...state.currentAdvice.rules.map((rule) => `- ${rule.do_text} [${rule.severity}]`),
    "",
    "DON'T",
    ...state.currentAdvice.rules.map((rule) => `- ${rule.dont_text}`),
    "",
    "SAFE ALTERNATIVES",
    ...state.currentAdvice.rules.map((rule) => `- ${rule.safe_alternative}`),
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${state.currentAdvice.cultureName}-${state.currentAdvice.scenarioName}.txt`.replace(/\s+/g, "-").toLowerCase();
  link.click();
  URL.revokeObjectURL(link.href);
}

async function submitFeedback(event) {
  event.preventDefault();
  if (!state.user) {
    return showToast("Sign in to submit feedback.");
  }

  const form = new FormData(event.target);
  try {
    await api("/feedback", {
      method: "POST",
      body: JSON.stringify({
        rating: Number(form.get("rating")),
        comment: form.get("comment").trim(),
      }),
    });
    event.target.reset();
    await refreshUserCollections();
    showToast("Feedback submitted.");
  } catch (error) {
    showToast(error.message);
  }
}

async function addCulture(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/cultures", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name").trim(),
        summary: form.get("summary").trim(),
      }),
    });
    event.target.reset();
    await refreshData();
    showToast("Culture added.");
  } catch (error) {
    showToast(error.message);
  }
}

async function addScenario(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/scenarios", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name").trim(),
        description: form.get("description").trim(),
      }),
    });
    event.target.reset();
    await refreshData();
    showToast("Scenario added.");
  } catch (error) {
    showToast(error.message);
  }
}

async function addRule(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api("/rules", {
      method: "POST",
      body: JSON.stringify({
        culture_id: Number(form.get("cultureId")),
        scenario_id: Number(form.get("scenarioId")),
        do_text: form.get("doText").trim(),
        dont_text: form.get("dontText").trim(),
        reason: form.get("reason").trim(),
        safe_alternative: form.get("safeAlternative").trim(),
        severity: form.get("severity"),
      }),
    });
    event.target.reset();
    await refreshData();
    showToast("Rule added.");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleSavedAdviceDelete(event) {
  const button = event.target.closest("[data-delete-saved]");
  if (!button) {
    return;
  }
  try {
    await api(`/saved-advice/${button.dataset.deleteSaved}`, { method: "DELETE" });
    await refreshUserCollections();
    showToast("Saved advice removed.");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleRuleDelete(event) {
  const button = event.target.closest("[data-delete-rule]");
  if (!button) {
    return;
  }
  try {
    await api(`/rules/${button.dataset.deleteRule}`, { method: "DELETE" });
    await refreshData();
    showToast("Rule deleted.");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleFeedbackDelete(event) {
  const button = event.target.closest("[data-delete-feedback]");
  if (!button) {
    return;
  }
  try {
    await api(`/feedback/${button.dataset.deleteFeedback}`, { method: "DELETE" });
    await refreshUserCollections();
    showToast("Feedback deleted.");
  } catch (error) {
    showToast(error.message);
  }
}

function renderCollections() {
  elements.savedAdviceList.innerHTML = state.savedAdvice.length
    ? state.savedAdvice.map((item) => `
        <article class="collection-item">
          <strong>${item.culture_name} - ${item.scenario_name}</strong>
          <span>${item.risk_label} risk</span>
          <small>${formatDate(item.generated_at)}</small>
          <button class="mini-action" data-delete-saved="${item.id}" type="button">Delete</button>
        </article>
      `).join("")
    : `<article class="collection-item"><span>No saved advice yet.</span></article>`;

  elements.feedbackList.innerHTML = state.feedback.length
    ? state.feedback.slice(0, 4).map((item) => `
        <article class="collection-item">
          <strong>${item.user_name}</strong>
          <span>Rating: ${item.rating}/5</span>
          <small>${item.comment || "No comment provided."}</small>
        </article>
      `).join("")
    : `<article class="collection-item"><span>No feedback submitted yet.</span></article>`;

  elements.adminFeedbackList.innerHTML = state.user?.role === "admin"
    ? (state.feedback.length
      ? state.feedback.map((item) => `
          <article class="collection-item">
            <strong>${item.user_name}</strong>
            <span>Rating: ${item.rating}/5</span>
            <small>${formatDate(item.created_at)} | ${item.comment || "No comment provided."}</small>
            <button class="mini-action" data-delete-feedback="${item.id}" type="button">Delete</button>
          </article>
        `).join("")
      : `<article class="collection-item"><span>No feedback available.</span></article>`)
    : `<article class="collection-item"><span>Admin review is available after admin login.</span></article>`;

  elements.ruleInventory.innerHTML = state.rules.length
    ? state.rules.map((rule) => `
        <article class="collection-item">
          <strong>${rule.culture_name} - ${rule.scenario_name}</strong>
          <span>${rule.do_text}</span>
          <small>${rule.severity} | Avoid: ${rule.dont_text}</small>
          ${state.user?.role === "admin" ? `<button class="mini-action" data-delete-rule="${rule.id}" type="button">Delete</button>` : ""}
        </article>
      `).join("")
    : `<article class="collection-item"><span>No rules added yet.</span></article>`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

let toastTimer;
function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden");
  toastTimer = setTimeout(() => elements.toast.classList.add("hidden"), 2600);
}
