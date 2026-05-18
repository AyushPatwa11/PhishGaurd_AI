const API = "";   // same origin (Flask serves both)

let history = [];

// ── Boot & Routing ────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadExamples();
  setupNavigation();
  
  // Enter key support for inputs
  document.getElementById("msg-url").addEventListener("keydown", e => {
    if (e.key === "Enter") analyze();
  });
  
  // Initial route
  const hashRoute = window.location.hash.replace('#', '');
  if (['home', 'dashboard', 'history', 'education', 'threat-map', 'settings'].includes(hashRoute)) {
    navigate(hashRoute);
  } else {
    navigate('home');
  }
});

function setupNavigation() {
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const route = e.currentTarget.getAttribute('data-route');
      navigate(route);
    });
  });
}

function navigate(route) {
  // Update URL hash without jumping
  if (history.pushState) {
    window.history.pushState(null, null, `#${route}`);
  } else {
    window.location.hash = `#${route}`;
  }

  // Update active links
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('data-route') === route) {
      link.classList.add('active');
    }
  });

  // Switch views
  document.querySelectorAll('.view-section').forEach(section => {
    section.classList.remove('active');
    // Reset animation
    section.style.animation = 'none';
    section.offsetHeight; /* trigger reflow */
    section.style.animation = null; 
  });
  document.getElementById(`view-${route}`).classList.add('active');
  
  // Scroll to top
  document.querySelector('.app-container').scrollTop = 0;
  
  if (route === 'history') {
    renderHistoryPage();
  } else if (route === 'threat-map') {
    startThreatFeed();
  } else {
    stopThreatFeed();
  }
}
window.navigate = navigate;

// ── Load example buttons ──────────────────────────────────────────────────────
async function loadExamples() {
  try {
    const res  = await fetch(API + "/api/examples");
    const list = await res.json();
    const row  = document.getElementById("examples-row");
    list.forEach((ex, idx) => {
      const btn = document.createElement("button");
      btn.className   = "example-btn slide-up";
      btn.style.animationDelay = `${0.2 + (idx * 0.1)}s`;
      btn.textContent = ex.label;
      btn.onclick = () => {
        document.getElementById("msg-text").value = ex.text;
        document.getElementById("msg-url").value  = ex.url;
        showToast("Template loaded. Ready to scan.");
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
    window.latestReportData = { data, text, url }; // Save for export
    renderResults(data, text, url);
    addHistory(data, text, url);
    document.getElementById('export-dashboard-btn').disabled = false;
    showToast("Scan complete.");
  } catch (e) {
    document.getElementById("score-content").innerHTML = `
      <div class="empty-state" style="color:var(--red)">
        <div style="font-size:32px; animation: pulseDot 2s infinite">⚠️</div>
        <div>Connection Lost</div>
        <div style="font-size:12px; color:var(--text-muted)">Ensure Flask backend is active.</div>
      </div>`;
  } finally {
    setLoading(false);
    setTimeout(() => {
      const scoreCard = document.getElementById('score-content').closest('.card');
      if (scoreCard) scoreCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 150);
  }
}
window.analyze = analyze;

// ── Render results ────────────────────────────────────────────────────────────
function renderResults(d, text, url) {
  const { verdict, level, risk_score, probability, top_features, reasons, tactics } = d;
  const color = riskColor(risk_score);
  const r = 60, circ = 2 * Math.PI * r;
  const offset = circ - (risk_score / 100) * circ;

  // Score ring
  document.getElementById("score-content").innerHTML = `
    <div class="score-ring-wrap slide-up">
      <svg class="ring-svg" viewBox="0 0 160 160">
        <circle class="ring-track" cx="80" cy="80" r="${r}"/>
        <circle class="ring-fill" cx="80" cy="80" r="${r}"
          stroke="${color}"
          stroke-dasharray="${circ.toFixed(2)}"
          stroke-dashoffset="${offset.toFixed(2)}"/>
        <text class="ring-score" x="80" y="75">${risk_score}</text>
        <text class="ring-label" x="80" y="98">Risk / 100</text>
      </svg>
      <div class="verdict-badge ${level}" style="box-shadow: 0 0 20px ${color}40">${verdict}</div>
      <div style="margin-top: 10px; font-size: 12px; color: var(--text-muted);">Confidence: ${Math.round(probability * 100)}%</div>
    </div>`;

  // Tactics
  document.getElementById("tactics-content").innerHTML = tactics.length
    ? `<div class="tactics-wrap slide-up">${tactics.map((t, i) => `
        <div class="tactic-pill" style="color:${t.color};border-color:${t.color}50;background:${t.color}15;animation-delay:${i*0.1}s">
          ${t.name}
        </div>`).join("")}</div>
        <p style="margin-top:16px; font-size:12px; color:var(--text-muted)">Hovering disabled. See education tab for details on tactics.</p>`
    : `<div class="empty-state slide-up"><div style="font-size:24px;opacity:0.5">✅</div><div>No psychological manipulation tactics detected.</div></div>`;

  // Feature bars
  const maxW = Math.max(...top_features.map(f => f.weight), 0.001);
  document.getElementById("features-content").innerHTML = `
    <div class="feature-list slide-up">
      ${top_features.map((f, i) => {
        const pct = Math.round((f.weight / maxW) * 100);
        const col = f.direction === "phishing" ? color : "var(--green)";
        return `<div class="feature-row" style="animation-delay:${i*0.1}s">
          <span class="feature-name">${f.feature}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${col};box-shadow:0 0 10px ${col}40"></div></div>
          <span class="feature-val">${Math.round(f.value * 100)}%</span>
        </div>`;
      }).join("")}
    </div>`;

  // Reasons
  const bColor = level === "high" ? "var(--red)" : level === "medium" ? "var(--amber)" : "var(--green)";
  const icon   = level === "high" ? "🚨" : level === "medium" ? "⚠️" : "✅";
  let reasonsHTML = reasons.length
    ? `<div class="reasons-list slide-up">${reasons.map((r, i) =>
        `<div class="reason-item" style="border-left-color:${bColor};animation-delay:${i*0.1}s">${icon} ${r}</div>`
      ).join("")}</div>`
    : `<div class="reason-item slide-up" style="border-left-color:var(--green)">✅ Payload appears clean. No significant threat vectors identified.</div>`;

  if (d.server_info) {
     reasonsHTML += `
      <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border);" class="slide-up">
         <h4 style="margin-bottom: 8px; color: var(--text-dark); font-size: 14px;"><span class="icon">📍</span> Server Geolocation</h4>
         <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 4px;"><strong>IP Address:</strong> ${d.server_info.ip}</p>
         <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;"><strong>Origin:</strong> ${d.server_info.city}, ${d.server_info.country}</p>
         <button class="secondary-btn pulse-btn" style="padding: 6px 12px; font-size: 12px; width: 100%" onclick="viewThreatOnMap(${d.server_info.lat}, ${d.server_info.lon}, '${d.server_info.ip}')">Track on Live Map 🎯</button>
      </div>`;
  }
  document.getElementById("reasons-content").innerHTML = reasonsHTML;
}

window.targetThreatLoc = null;
function viewThreatOnMap(lat, lon, ip) {
  window.targetThreatLoc = { lat, lon, ip };
  navigate('threat-map');
}
window.viewThreatOnMap = viewThreatOnMap;

// ── History ───────────────────────────────────────────────────────────────────
function addHistory(d, text, url) {
  history.unshift({
    id:      Math.random().toString(36).substr(2, 9),
    time:    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    date:    new Date().toLocaleDateString(),
    preview: (text || url).substring(0, 60) + ((text || url).length > 60 ? "..." : ""),
    score:   d.risk_score,
    level:   d.level,
    verdict: d.verdict,
  });
  if (history.length > 50) history.pop();
  
  if (document.getElementById('view-history').classList.contains('active')) {
    renderHistoryPage();
  }
}

function renderHistoryPage() {
  const el = document.getElementById("history-page-content");
  if (!history.length) {
    el.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon float-anim">📁</div>
        <div>Your historical scans will be recorded here.</div>
        <button class="primary-btn pulse-btn" style="margin-top:20px" onclick="navigate('dashboard')">Run First Scan</button>
      </div>`;
    return;
  }
  
  el.innerHTML = `
    <table class="history-table">
      <thead><tr>
        <th>ID</th><th>Date & Time</th><th>Payload Preview</th><th>Score</th><th>Verdict</th>
      </tr></thead>
      <tbody>${history.map(h => `
        <tr>
          <td style="color:var(--text-dark);font-family:monospace">${h.id}</td>
          <td style="color:var(--text-muted);white-space:nowrap">${h.date} <span style="margin-left:8px">${h.time}</span></td>
          <td>${h.preview || '<span style="opacity:0.5">Empty Payload</span>'}</td>
          <td><span style="font-weight:700;font-size:16px;color:${riskColor(h.score)}">${h.score}</span></td>
          <td><span class="pill ${h.level}" style="box-shadow: 0 0 10px ${riskColor(h.score)}40">${h.verdict}</span></td>
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
    ? `<div class="spinner"></div> Running Deep Scan...`
    : "Run Security Scan";
    
  if (on) {
    btn.style.background = "var(--bg-dark)";
    btn.style.boxShadow = "none";
    btn.style.border = "1px solid var(--primary)";
  } else {
    btn.style.background = "";
    btn.style.boxShadow = "";
    btn.style.border = "";
  }
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

// ── Export Features ──────────────────────────────────────────────────────────
function exportLatestReport() {
  if (!window.latestReportData) return;
  const { data, text, url } = window.latestReportData;
  const report = `PhishGuard AI Threat Report\n\nTarget: ${url || 'N/A'}\nPayload: ${text || 'N/A'}\n\nVerdict: ${data.verdict} (${data.level})\nRisk Score: ${data.risk_score}/100\nConfidence: ${Math.round(data.probability*100)}%\n\nReasons:\n${data.reasons.map(r => '- ' + r).join('\n')}`;
  
  const blob = new Blob([report], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `PhishGuard_Report_${Date.now()}.txt`;
  a.click();
  showToast("Report exported successfully.");
}
window.exportLatestReport = exportLatestReport;

function exportHistoryCSV() {
  if (!history.length) {
    showToast("No history to export.");
    return;
  }
  const headers = ["ID", "Date", "Time", "Verdict", "Score", "Preview"];
  const rows = history.map(h => [h.id, h.date, h.time, h.verdict, h.score, `"${h.preview.replace(/"/g, '""')}"`].join(","));
  const csv = [headers.join(","), ...rows].join("\n");
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `PhishGuard_History_${Date.now()}.csv`;
  a.click();
  showToast("History exported as CSV.");
}
window.exportHistoryCSV = exportHistoryCSV;

// ── Settings Features ────────────────────────────────────────────────────────
function generateApiKey() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let token = 'phish_v2_';
  for (let i = 0; i < 24; i++) {
    token += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  document.getElementById('mock-api-key').textContent = token;
  showToast("New API Key generated.");
}
window.generateApiKey = generateApiKey;

// ── Live Threat Map (Real Data) ──────────────────────────────────────────────
let threatFeedInterval = null;
let leafletMap = null;
let currentScope = 'global';

function updateThreatScope() {
  currentScope = document.getElementById('threat-scope-select').value;
  const logList = document.getElementById('threat-log-list');
  logList.innerHTML = `<li style="color:var(--text-muted);font-style:italic">Re-calibrating targeting sensors for ${currentScope}...</li>`;
  
  // Clear map markers immediately
  leafletMap.eachLayer((layer) => {
    if (layer instanceof L.Marker) leafletMap.removeLayer(layer);
  });
  
  // Force immediate refresh
  stopThreatFeed();
  startThreatFeed();
}
window.updateThreatScope = updateThreatScope;

function startThreatFeed() {
  if (!leafletMap) {
    leafletMap = L.map('real-threat-map').setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors & CartoDB'
    }).addTo(leafletMap);
  } else {
    setTimeout(() => leafletMap.invalidateSize(), 200);
  }
  
  if (threatFeedInterval) return;
  
  const logList = document.getElementById('threat-log-list');
  if (!logList.innerHTML.includes('Re-calibrating')) {
    logList.innerHTML = '<li style="color:var(--text-muted);font-style:italic">Connected to Threat Intel Node. Parsing live feed...</li>';
  }
  
  const customIcon = L.divIcon({
    className: 'custom-blip',
    html: "<div class='blip' style='position:relative; transform:none;'></div>",
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  const fetchThreats = async () => {
    try {
      const res = await fetch(API + "/api/live-threats?scope=" + currentScope);
      const threats = await res.json();
      
      if (!threats || !threats.length) return;
      
      if (logList.innerHTML.includes("Threat Intel Node") || logList.innerHTML.includes("Re-calibrating")) {
        logList.innerHTML = ''; // clear loading msg
      }
      
      // If we have scoped coordinates from backend, center map to user area initially
      if (window.targetThreatLoc) {
        const { lat, lon, ip } = window.targetThreatLoc;
        leafletMap.flyTo([lat, lon], 7, { duration: 2 });
        L.marker([lat, lon], { icon: customIcon })
          .addTo(leafletMap)
          .bindPopup(`<b style="color:var(--red)">Analyzed Threat Target</b><br>IP: ${ip}`).openPopup();
        window.targetThreatLoc = null; // Clear so it doesn't stay locked
      } else if (currentScope !== 'global' && threats[0] && threats[0].user_lat) {
        leafletMap.flyTo([threats[0].user_lat, threats[0].user_lon], threats[0].scope_zoom || 6, { duration: 1.5 });
      } else if (currentScope === 'global') {
        leafletMap.flyTo([20, 0], 2, { duration: 1.5 });
      }
      
      threats.forEach((t, i) => {
        setTimeout(() => {
          // Map Marker
          const marker = L.marker([t.lat, t.lon], { icon: customIcon }).addTo(leafletMap);
          marker.bindPopup(`<b>${t.type}</b><br>IP: ${t.ip}<br>${t.city}, ${t.country}`);
          
          // Remove marker after 8 seconds to keep map clean
          setTimeout(() => { if (leafletMap.hasLayer(marker)) leafletMap.removeLayer(marker); }, 8000);
          
          // Log List Entry
          const logItem = document.createElement('li');
          logItem.className = 'threat-log-item slide-up';
          logItem.innerHTML = `<div><span class="ip">${t.ip}</span> <span style="color:#fff;margin-left:8px;font-weight:600">${t.type}</span></div><div class="loc">${t.city}, ${t.country}</div>`;
          logList.prepend(logItem);
          if (logList.children.length > 25) logList.removeChild(logList.lastChild);
          
          // Pan map to threat occasionally if global
          if (currentScope === 'global' && (i === 0 || Math.random() > 0.8)) {
            leafletMap.flyTo([t.lat, t.lon], Math.floor(Math.random() * 3) + 3, { 
              duration: 2.5, 
              easeLinearity: 0.1 
            });
          }
        }, i * 1200); // Stagger appearances every 1.2s
      });
    } catch (e) {
      console.error("Error fetching live threats:", e);
    }
  };
  
  fetchThreats();
  threatFeedInterval = setInterval(fetchThreats, 20000); // Fetch new batch every 20s
}

function stopThreatFeed() {
  if (threatFeedInterval) {
    clearInterval(threatFeedInterval);
    threatFeedInterval = null;
  }
}