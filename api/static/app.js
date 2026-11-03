/**
 * WorkflowSLA: Interactive Dashboard Client
 * Fetches bottleneck analytics from FastAPI, handles slider updates,
 * and renders recommendations and metrics.
 */

let currentCurrency = "USD";

async function fetchBottlenecks() {
  const aov = document.getElementById("input-aov").value;
  const dailyTx = document.getElementById("input-daily-tx").value;
  const revDrop = (document.getElementById("input-rev-drop").value / 100.0).toFixed(4);
  const opsCost = document.getElementById("input-ops-cost").value;

  try {
    const url = `/analyze-bottlenecks?aov=${aov}&daily_tx=${dailyTx}&rev_drop_per_hr=${revDrop}&ops_cost_per_hr=${opsCost}&currency=${currentCurrency}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load bottleneck analytics");
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error("Error fetching analysis:", err);
  }
}

async function fetchFrictionCorridors() {
  try {
    const res = await fetch("/metrics/department-friction");
    if (!res.ok) throw new Error("Failed to load friction metrics");
    const data = await res.json();
    renderCorridorsTable(data);
  } catch (err) {
    console.error("Error fetching corridors:", err);
  }
}

function renderDashboard(data) {
  const ent = data.enterprise_summary || {};
  const impact = data.quantified_revenue_impact || {};
  const topHandoffs = data.worst_performing_handoffs || [];
  const recs = data.data_backed_recommendations || [];

  // 1. KPI Cards
  document.getElementById("kpi-total-tickets").textContent = (ent.total_tickets || 10000).toLocaleString();
  document.getElementById("kpi-breach-rate").textContent = `${ent.overall_breach_rate_pct || 28.1}%`;
  document.getElementById("kpi-breached-transitions").textContent = `${(ent.total_breached_transitions || 6560).toLocaleString()} Transitions Delayed`;
  document.getElementById("kpi-delay-hours").textContent = `${Math.round(ent.total_breach_hours || impact.total_delay_hours).toLocaleString()} hrs`;
  document.getElementById("kpi-weekly-leakage").textContent = impact.formatted_weekly_leakage || "$1.30M";
  document.getElementById("kpi-inr-benchmark").textContent = `Benchmark: ${impact.inr_benchmark_weekly_leakage || '800 Lakh/week'}`;

  // 2. Top 3 Bottlenecks
  const container = document.getElementById("bottlenecks-container");
  container.innerHTML = "";

  let cumulativeDelayShare = 0;
  topHandoffs.forEach(bn => {
    cumulativeDelayShare += bn.delay_share_pct;
    const card = document.createElement("div");
    card.className = "bottleneck-card";
    card.innerHTML = `
      <div class="bn-header">
        <span class="bn-rank">#${bn.bottleneck_rank} BOTTLENECK</span>
        <span class="bn-delay-share">${bn.delay_share_pct}% Delay Share</span>
      </div>
      <div class="bn-title">${bn.handoff_corridor} (${bn.from_department} → ${bn.to_department})</div>
      <div class="bn-progress-bar">
        <div class="bn-progress-fill" style="width: ${bn.delay_share_pct}%;"></div>
      </div>
      <div class="bn-metrics-row">
        <div class="bn-metric">Breach Rate: <span>${bn.breach_rate_pct}%</span></div>
        <div class="bn-metric">Avg Time: <span>${bn.avg_duration_hours}h</span> (SLA: ${bn.sla_target_hours}h)</div>
        <div class="bn-metric">Weekly Leakage: <span>${bn.formatted_weekly_leakage}</span></div>
      </div>
    `;
    container.appendChild(card);
  });

  const paretoBadge = document.getElementById("pareto-badge");
  if (paretoBadge) {
    paretoBadge.textContent = `${cumulativeDelayShare.toFixed(1)}% Combined Delay Share`;
  }

  // 3. Recommendations
  const recContainer = document.getElementById("recommendations-container");
  recContainer.innerHTML = "";
  recs.forEach(rec => {
    const card = document.createElement("div");
    card.className = "recommendation-card";
    card.innerHTML = `
      <div class="rec-title">${rec.recommendation}</div>
      <div class="rec-action">${rec.action_item}</div>
      <div class="rec-impact-badge">
        <span class="rec-reclaim">⚡ Reclaim ${rec.projected_reclaimed_hours_weekly} hrs/week</span>
        <span>Est. Savings: ${rec.formatted_weekly_savings}/wk (${rec.inr_benchmark_savings_per_week})</span>
      </div>
    `;
    recContainer.appendChild(card);
  });

  // 4. Simulation Results Box
  document.getElementById("res-weekly-gmv").textContent = formatVal(impact.weekly_gmv_leaked);
  document.getElementById("res-weekly-ops").textContent = formatVal(impact.weekly_operational_cost);
  document.getElementById("res-weekly-total").textContent = impact.formatted_weekly_leakage;

  // 5. Scenarios
  const sc = impact.sensitivity_scenarios || {};
  if (sc.conservative) document.getElementById("sc-conservative").textContent = sc.conservative.formatted_weekly_leakage;
  if (sc.baseline) document.getElementById("sc-baseline").textContent = sc.baseline.formatted_weekly_leakage;
  if (sc.aggressive) document.getElementById("sc-aggressive").textContent = sc.aggressive.formatted_weekly_leakage;
}

function renderCorridorsTable(corridors) {
  const tbody = document.getElementById("table-corridors-body");
  if (!tbody) return;
  tbody.innerHTML = "";

  corridors.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${c.from_code} → ${c.to_code}</strong> <br><small style="color:#64748b;">${c.from_department} → ${c.to_department}</small></td>
      <td>${c.total_transitions.toLocaleString()}</td>
      <td>${c.avg_duration_hours} hrs</td>
      <td>${c.avg_sla_target_hours} hrs</td>
      <td><span style="color:${c.breach_rate_pct > 25 ? '#f87171' : '#10b981'}; font-weight:600;">${c.breach_rate_pct}%</span> (${c.breach_count})</td>
      <td><strong>${Math.round(c.total_breach_hours).toLocaleString()} hrs</strong></td>
      <td>${c.total_blockers} incidents</td>
    `;
    tbody.appendChild(tr);
  });
}

function formatVal(amount) {
  if (!amount) return "$0";
  if (currentCurrency === "INR") {
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} Lakh`;
    return `₹${amount.toLocaleString()}`;
  }
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(2)}M`;
  if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}k`;
  return `$${amount.toFixed(2)}`;
}

// Event Listeners for Sliders
function setupControls() {
  const inputAov = document.getElementById("input-aov");
  const inputDailyTx = document.getElementById("input-daily-tx");
  const inputRevDrop = document.getElementById("input-rev-drop");
  const inputOpsCost = document.getElementById("input-ops-cost");
  const selectCurrency = document.getElementById("sim-currency");
  const btnReseed = document.getElementById("btn-reseed");

  inputAov.addEventListener("input", () => {
    document.getElementById("val-aov").textContent = `${currentCurrency === "INR" ? "₹" : "$"}${inputAov.value}`;
    fetchBottlenecks();
  });

  inputDailyTx.addEventListener("input", () => {
    document.getElementById("val-daily-tx").textContent = Number(inputDailyTx.value).toLocaleString();
    fetchBottlenecks();
  });

  inputRevDrop.addEventListener("input", () => {
    document.getElementById("val-rev-drop").textContent = `${Number(inputRevDrop.value).toFixed(2)}%`;
    fetchBottlenecks();
  });

  inputOpsCost.addEventListener("input", () => {
    document.getElementById("val-ops-cost").textContent = `${currentCurrency === "INR" ? "₹" : "$"}${inputOpsCost.value}`;
    fetchBottlenecks();
  });

  selectCurrency.addEventListener("change", (e) => {
    currentCurrency = e.target.value;
    if (currentCurrency === "INR") {
      inputAov.min = 500;
      inputAov.max = 15000;
      inputAov.step = 500;
      inputAov.value = 3500;
      document.getElementById("val-aov").textContent = "₹3,500";
    } else {
      inputAov.min = 10;
      inputAov.max = 250;
      inputAov.step = 5;
      inputAov.value = 45;
      document.getElementById("val-aov").textContent = "$45.00";
    }
    fetchBottlenecks();
  });

  btnReseed.addEventListener("click", async () => {
    btnReseed.textContent = "Reseeding (10k)...";
    btnReseed.disabled = true;
    try {
      const res = await fetch("/seed-database?ticket_count=10000", { method: "POST" });
      const data = await res.json();
      alert(`Success! Generated ${data.total_tickets} tickets.`);
      fetchBottlenecks();
      fetchFrictionCorridors();
    } catch (e) {
      alert("Error reseeding dataset: " + e);
    } finally {
      btnReseed.textContent = "Reseed Data";
      btnReseed.disabled = false;
    }
  });
}

// Initial Boot
window.addEventListener("DOMContentLoaded", () => {
  setupControls();
  fetchBottlenecks();
  fetchFrictionCorridors();
});

