const API = "";   // same origin (Flask serves both)

let history = [];

// ── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
  document.getElementById("msg-url").addEventListener("keydown", e => {
    if (e.key === "Enter") analyze();
  });
});

// ── Load example buttons ──────────────────────────────────────────────────────
async function loadExamples() {
  try {
    const res  = await fetch(API + "/api/examples");
    const list = await res.json();
    const row  = document.getElementById("examples-row");
    list.forEach(ex => {
      const btn = document.createElement("button");
      btn.className   = "example-btn";
      btn.textContent = ex.label;
      btn.onclick = () => {
        document.getElementById("msg-text").value = ex.text;
        document.getElementById("msg-url").value  = ex.url;
      };
      row.appendChild(btn);
    });
  } catch { /* backend not up yet */ }
}

// ── Analyze ───────────────────────────────────────────────────────────────────
async function analyze() {
  const text = document.getElementById("msg-text").value.trim();
  const url  = document.getElementById("msg-url").value.trim();
  if (!text && !url) { showToast("Enter a message or URL first."); return; }

  setLoading(true);
  try {
    const res  = await fetch(API + "/api/predict", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, url }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderResults(data, text, url);
    addHistory(data, text, url);
  } catch (e) {
    document.getElementById("score-content").innerHTML = `
      <div class="empty-state" style="color:var(--red)">
        <div style="font-size:22px">⚠️</div>
        <div>Could not reach backend</div>
        <div style="font-size:12px">Make sure Flask is running: <code>python backend/app.py</code></div>
      </div>`;
  } finally {
    setLoading(false);
  }
}
window.analyze = analyze;

// ── Render results ────────────────────────────────────────────────────────────
function renderResults(d, text, url) {
  const { verdict, level, risk_score, probability, top_features, reasons, tactics } = d;
  const color = riskColor(risk_score);
  const r = 54, circ = 2 * Math.PI * r;
  const offset = circ - (risk_score / 100) * circ;

  // Score ring
  document.getElementById("score-content").innerHTML = `
    <div class="score-ring-wrap">
      <svg class="ring-svg" viewBox="0 0 148 148">
        <circle class="ring-track" cx="74" cy="74" r="${r}"/>
        <circle class="ring-fill" cx="74" cy="74" r="${r}"
          stroke="${color}"
          stroke-dasharray="${circ.toFixed(2)}"
          stroke-dashoffset="${offset.toFixed(2)}"/>
        <text class="ring-score" x="74" y="70">${risk_score}</text>
        <text class="ring-label" x="74" y="89">/ 100</text>
      </svg>
      <div class="verdict-badge ${level}">${verdict}</div>
      <div class="confidence-text">Confidence: ${Math.round(probability * 100)}%</div>
    </div>`;

  // Tactics
  document.getElementById("tactics-content").innerHTML = tactics.length
    ? `<div class="tactics-wrap">${tactics.map(t => `
        <div class="tactic-pill" style="color:${t.color};border-color:${t.color}33;background:${t.color}18">
          ${t.name}<div class="tactic-desc">${t.desc}</div>
        </div>`).join("")}</div>`
    : `<div style="color:var(--text3);font-size:13px;padding:6px 0">No manipulation tactics detected.</div>`;

  // Feature bars
  const maxW = Math.max(...top_features.map(f => f.weight), 0.001);
  document.getElementById("features-content").innerHTML = `
    <div class="feature-list">
      ${top_features.map(f => {
        const pct = Math.round((f.weight / maxW) * 100);
        const col = f.direction === "phishing" ? color : "var(--green)";
        return `<div class="feature-row">
          <span class="feature-name">${f.feature}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${col}"></div></div>
          <span class="feature-val">${Math.round(f.value * 100)}%</span>
        </div>`;
      }).join("")}
    </div>`;

  // Reasons
  const bColor = level === "high" ? "var(--red)" : level === "medium" ? "var(--amber)" : "var(--green)";
  const icon   = level === "high" ? "🚨" : level === "medium" ? "⚠️" : "✅";
  document.getElementById("reasons-content").innerHTML = reasons.length
    ? `<div class="reasons-list">${reasons.map(r =>
        `<div class="reason-item" style="border-left-color:${bColor}">${icon} ${r}</div>`
      ).join("")}</div>`
    : `<div class="reason-item" style="border-left-color:var(--green)">✅ No significant phishing signals detected.</div>`;
}

// ── History ───────────────────────────────────────────────────────────────────
function addHistory(d, text, url) {
  history.unshift({
    time:    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    preview: (text || url).substring(0, 48) + ((text || url).length > 48 ? "…" : ""),
    score:   d.risk_score,
    level:   d.level,
    verdict: d.verdict,
  });
  if (history.length > 10) history.pop();
  renderHistory();
}

function renderHistory() {
  const el = document.getElementById("history-content");
  if (!history.length) {
    el.innerHTML = `<div class="empty-state" style="height:80px"><div style="font-size:12px;color:var(--text3)">Analyses will appear here.</div></div>`;
    return;
  }
  el.innerHTML = `
    <table class="history-table">
      <thead><tr>
        <th>Time</th><th>Preview</th><th>Score</th><th>Verdict</th>
      </tr></thead>
      <tbody>${history.map(h => `
        <tr>
          <td style="color:var(--text3);white-space:nowrap">${h.time}</td>
          <td>${h.preview}</td>
          <td><span style="font-weight:600;color:${riskColor(h.score)}">${h.score}</span></td>
          <td><span class="pill ${h.level}">${h.verdict}</span></td>
        </tr>`).join("")}
      </tbody>
    </table>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function riskColor(score) {
  if (score >= 75) return "var(--red)";
  if (score >= 45) return "var(--amber)";
  return "var(--green)";
}

function setLoading(on) {
  const btn = document.getElementById("analyze-btn");
  const lbl = document.getElementById("btn-label");
  btn.disabled  = on;
  lbl.innerHTML = on
    ? `<div class="spinner"></div> Analyzing…`
    : "Analyze for Phishing";
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2800);
}