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

document.getElementById("inspect-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  document.getElementById("results").classList.add("hidden");
  document.getElementById("loading").classList.remove("hidden");

  const formData = new FormData(e.target);

  try {
    const resp = await fetch("/api/inspect", { method: "POST", body: formData });
    if (!resp.ok) throw new Error("Erreur serveur " + resp.status);
    const data = await resp.json();
    render(data);
  } catch (err) {
    alert("Echec de l'inspection : " + err.message);
  } finally {
    btn.disabled = false;
    document.getElementById("loading").classList.add("hidden");
  }
});

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
