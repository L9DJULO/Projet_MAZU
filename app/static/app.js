const eur = (n) => new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);

fetch("/api/health").then(r => r.json()).then(h => {
  const badge = document.getElementById("mode-badge");
  badge.textContent = `CV:${h.vision} | ML:${h.ml} | LLM:${h.llm_mode}`;
});

document.getElementById("sample-btn").addEventListener("click", () => {
  const f = document.getElementById("inspect-form");
  f.make.value = "BMW"; f.model.value = "Serie 3"; f.year.value = 2014;
  f.mileage_km.value = 168000;
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

  const val = report.valuation;
  const nego = report.negotiation;
  const kpis = [
    `<div class="kpi ${report.mechanical.total_loss ? "kpi-bad" : ""}"><div class="value">${report.mechanical.condition_score}/100</div><div class="label">Etat (${report.mechanical.condition_label})</div></div>`,
    `<div class="kpi"><div class="value">${eur(report.mechanical.cost_estimate.total_repair_cost)}</div><div class="label">Reparations</div></div>`,
  ];
  if (val) kpis.push(`<div class="kpi"><div class="value">${eur(val.adjusted_value)}</div><div class="label">Valeur ajustee</div></div>`);
  if (nego) kpis.push(`<div class="kpi"><div class="value">${eur(nego.recommended_offer)}</div><div class="label">Offre conseillee</div></div>`);
  document.getElementById("kpis").innerHTML = kpis.join("");

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

  const valuationCard = document.getElementById("valuation-card");
  const negotiationCard = document.getElementById("negotiation-card");
  if (val) {
    valuationCard.classList.remove("hidden");
    document.getElementById("valuation-list").innerHTML = `
      <li><span class="k">Valeur de base</span><span class="v">${eur(val.base_value)}</span></li>
      <li><span class="k">Facteur d'etat</span><span class="v">${val.condition_factor}</span></li>
      <li><span class="k">Valeur ajustee</span><span class="v">${eur(val.adjusted_value)}</span></li>
    `;
  } else {
    valuationCard.classList.add("hidden");
  }

  if (nego) {
    negotiationCard.classList.remove("hidden");
    document.getElementById("nego-summary").innerHTML =
      `${nego.summary}<br><br>
       <b>Fourchette :</b> offre ${eur(nego.recommended_offer)} | juste ${eur(nego.fair_value)} | max ${eur(nego.walk_away_price)}`;
    document.getElementById("nego-args").innerHTML = nego.arguments.map(a => `<li>${a}</li>`).join("");
  } else {
    negotiationCard.classList.add("hidden");
  }

  document.getElementById("trace-list").innerHTML = trace
    .map(s => `<li><b>${s.agent}</b> | ${s.action}${s.detail ? " - " + s.detail : ""}</li>`).join("");

  results.scrollIntoView({ behavior: "smooth" });
}
