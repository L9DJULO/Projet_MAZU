const eur = (n) => new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

fetch("/api/health").then(r => r.json()).then(h => {
  const badge = document.getElementById("mode-badge");
  badge.textContent = `CV:${h.vision} | ML:${h.ml} | LLM:${h.llm_mode}`;
});

document.getElementById("sample-btn").addEventListener("click", () => {
  const f = document.getElementById("inspect-form");
  f.make.value = "BMW"; f.model.value = "Serie 3"; f.year.value = 2014;
  f.mileage_km.value = 168000; f.vin.value = "WBA3B1C50EK123456";
  f.base_market_value.value = "";
});

const AGENT_LABELS = {};

document.getElementById("inspect-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  document.getElementById("results").classList.add("hidden");
  document.getElementById("orchestration").classList.add("hidden");
  document.getElementById("loading").classList.remove("hidden");

  const formData = new FormData(e.target);

  try {
    await runStream(formData);
  } catch (err) {
    alert("Echec de l'inspection : " + err.message);
  } finally {
    btn.disabled = false;
    document.getElementById("loading").classList.add("hidden");
  }
});

async function runStream(formData) {
  const resp = await fetch("/api/inspect/stream", { method: "POST", body: formData });
  if (!resp.ok || !resp.body) throw new Error("Erreur serveur " + resp.status);

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let doneData = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line) continue;
      const ev = JSON.parse(line);
      if (ev.event === "start") initOrchestration(ev);
      else if (ev.event === "message") pushMessage(ev);
      else if (ev.event === "done") doneData = ev;
    }
  }

  document.querySelectorAll(".agent-node").forEach(n => {
    n.classList.remove("active", "active-recv");
    n.classList.add("done");
  });

  if (doneData) render(doneData);
}

function initOrchestration(ev) {
  document.getElementById("loading").classList.add("hidden");
  const section = document.getElementById("orchestration");
  section.classList.remove("hidden");
  const nodes = document.getElementById("agent-nodes");
  const feed = document.getElementById("agent-feed");
  feed.innerHTML = "";
  nodes.innerHTML = "";
  ev.agents.forEach(a => {
    AGENT_LABELS[a.id] = a.label;
    nodes.insertAdjacentHTML("beforeend", `
      <div class="agent-node kind-${a.kind}" id="node-${a.id}">
        <span class="node-dot"></span>
        <div class="node-label">${a.label}</div>
        <div class="node-kind">${a.kind === "orchestrator" ? "orchestrateur" : a.kind === "service" ? "service" : "sous-agent"}</div>
      </div>`);
  });
  section.scrollIntoView({ behavior: "smooth" });
}

function pushMessage(ev) {
  document.querySelectorAll(".agent-node.active, .agent-node.active-recv")
    .forEach(n => n.classList.remove("active", "active-recv"));
  const fromNode = document.getElementById("node-" + ev.from);
  const toNode = document.getElementById("node-" + ev.to);
  if (fromNode) { fromNode.classList.add("active"); fromNode.classList.add("done"); }
  if (toNode) toNode.classList.add("active-recv");

  const feed = document.getElementById("agent-feed");
  const label = (id) => AGENT_LABELS[id] || id;
  const badge = ev.type === "resultat" ? "reponse" : "delegue";
  feed.insertAdjacentHTML("beforeend", `
    <div class="feed-msg type-${ev.type}">
      <div class="msg-route">${label(ev.from)}<span class="arrow">&rarr;</span>${label(ev.to)}
        <span class="msg-badge">${badge}</span>
      </div>
      <div class="msg-text">${ev.text}</div>
    </div>`);
  feed.scrollTop = feed.scrollHeight;
}

function render({ report, trace }) {
  const results = document.getElementById("results");
  results.classList.remove("hidden");

  document.getElementById("exec-summary").textContent = report.executive_summary;

  document.getElementById("kpis").innerHTML = `
    <div class="kpi"><div class="value">${report.mechanical.condition_score}/100</div><div class="label">Etat (${report.mechanical.condition_label})</div></div>
    <div class="kpi"><div class="value">${eur(report.mechanical.cost_estimate.total_repair_cost)}</div><div class="label">Reparations</div></div>
    <div class="kpi"><div class="value">${eur(report.valuation.adjusted_value)}</div><div class="label">Valeur ajustee</div></div>
    <div class="kpi"><div class="value">${eur(report.negotiation.recommended_offer)}</div><div class="label">Offre conseillee</div></div>
  `;

  document.getElementById("vision-provider").textContent = report.vision.provider;
  document.getElementById("damages-list").innerHTML = report.vision.damages.length
    ? report.vision.damages.map(d => `
      <li>
        <span><b>${d.type.replace(/_/g, " ")}</b> - ${d.location}
          <small style="color:#6b7280"> (conf. ${(d.confidence*100).toFixed(0)}%)</small>
        </span>
        <span class="sev sev-${d.severity}">${d.severity}</span>
      </li>`).join("")
    : "<li>Aucun dommage detecte.</li>";

  document.getElementById("mech-summary").textContent = report.mechanical.summary;
  document.getElementById("repair-table").innerHTML = report.mechanical.cost_estimate.repair_lines
    .map(l => `<tr><td>${l.label}</td><td>${eur(l.estimated_cost)}</td></tr>`).join("")
    + `<tr><td><b>Total</b></td><td><b>${eur(report.mechanical.cost_estimate.total_repair_cost)}</b></td></tr>`;

  const h = report.history;
  const flag = (bad) => bad ? '<span class="flag-bad">Oui</span>' : '<span class="flag-ok">Non</span>';
  document.getElementById("history-source").textContent = h.source;
  document.getElementById("history-list").innerHTML = `
    <li><span class="k">Sinistres</span><span class="v">${h.accidents}</span></li>
    <li><span class="k">Proprietaires</span><span class="v">${h.previous_owners}</span></li>
    <li><span class="k">Km coherent</span><span class="v">${h.odometer_consistent ? '<span class="flag-ok">Oui</span>' : '<span class="flag-bad">Non</span>'}</span></li>
    <li><span class="k">Vol signale</span><span class="v">${flag(h.stolen_flag)}</span></li>
    <li><span class="k">Rappels ouverts</span><span class="v">${h.open_recalls}</span></li>
    <li><span class="k">Notes</span><span class="v">${h.notes}</span></li>
  `;

  const v = report.valuation;
  document.getElementById("valuation-list").innerHTML = `
    <li><span class="k">Valeur de base</span><span class="v">${eur(v.base_value)}</span></li>
    <li><span class="k">Facteur d'etat</span><span class="v">${v.condition_factor}</span></li>
    <li><span class="k">Valeur ajustee</span><span class="v">${eur(v.adjusted_value)}</span></li>
  `;

  const n = report.negotiation;
  document.getElementById("nego-summary").innerHTML =
    `${n.summary}<br><br>
     <b>Fourchette :</b> offre ${eur(n.recommended_offer)} | juste ${eur(n.fair_value)} | max ${eur(n.walk_away_price)}`;
  document.getElementById("nego-args").innerHTML = n.arguments.map(a => `<li>${a}</li>`).join("");

  document.getElementById("trace-list").innerHTML = trace
    .map(s => `<li><b>${s.agent}</b> | ${s.action}${s.detail ? " - " + s.detail : ""}</li>`).join("");

  results.scrollIntoView({ behavior: "smooth" });
}
