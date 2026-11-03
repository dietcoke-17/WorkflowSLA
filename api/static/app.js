/**
 * WorkflowSLA: Enterprise Dashboard Client
 * Production B2B interface controller implementing tab management,
 * synchronized slider/numeric inputs, real-time recalculations,
 * search filters, and dual-currency formatting.
 */

let currentCurrency = "USD";
let cachedCorridors = [];
let lastSyncTimestamp = new Date();

// DOM Elements
const elements = {
  // Tabs
  tabButtons: document.querySelectorAll(".tab-btn"),
  tabPanels: document.querySelectorAll(".tab-content"),

  // KPIs
  kpiTotalTickets: document.getElementById("kpi-total-tickets"),
  kpiTotalTransitions: document.getElementById("kpi-total-transitions"),
  kpiBreachRate: document.getElementById("kpi-breach-rate"),
  kpiBreachedCount: document.getElementById("kpi-breached-count"),
  kpiTotalDelay: document.getElementById("kpi-total-delay"),
  kpiAvgDuration: document.getElementById("kpi-avg-duration"),
  kpiWeeklyLeakage: document.getElementById("kpi-weekly-leakage"),
  kpiInrBenchmark: document.getElementById("kpi-inr-benchmark"),

  // Bottlenecks & Recommendations
  topBottlenecksList: document.getElementById("top-bottlenecks-list"),
  paretoSummaryPill: document.getElementById("pareto-summary-pill"),
  rfcsContainer: document.getElementById("rfcs-container"),

  // Simulator Inputs
  currencySelect: document.getElementById("currency-select"),
  sliderAov: document.getElementById("slider-aov"),
  numAov: document.getElementById("num-aov"),
  sliderDailyTx: document.getElementById("slider-daily-tx"),
  numDailyTx: document.getElementById("num-daily-tx"),
  sliderRevDrop: document.getElementById("slider-rev-drop"),
  numRevDrop: document.getElementById("num-rev-drop"),
  sliderOpsCost: document.getElementById("slider-ops-cost"),
  numOpsCost: document.getElementById("num-ops-cost"),

  // Currency Labels
  currSym1: document.getElementById("currency-sym-1"),
  currSym2: document.getElementById("currency-sym-2"),
  aovBoundMin: document.getElementById("aov-bound-min"),
  aovBoundMax: document.getElementById("aov-bound-max"),

  // Simulator Outputs
  simOutWeeklyTotal: document.getElementById("sim-out-weekly-total"),
  simOutInrBenchmark: document.getElementById("sim-out-inr-benchmark"),
  simOutWeeklyGmv: document.getElementById("sim-out-weekly-gmv"),
  simOutWeeklyOps: document.getElementById("sim-out-weekly-ops"),

  // Scenarios
  scValConsWeekly: document.getElementById("sc-val-cons-weekly"),
  scValConsTotal: document.getElementById("sc-val-cons-total"),
  scValBaseWeekly: document.getElementById("sc-val-base-weekly"),
  scValBaseTotal: document.getElementById("sc-val-base-total"),
  scValAggrWeekly: document.getElementById("sc-val-aggr-weekly"),
  scValAggrTotal: document.getElementById("sc-val-aggr-total"),

  // Corridor Table & Search
  corridorSearch: document.getElementById("corridor-search"),
  corridorsTableBody: document.getElementById("corridors-table-body"),

  // Actions
  btnRefresh: document.getElementById("btn-refresh"),
  btnReseed: document.getElementById("btn-reseed"),
  btnCopySql: document.getElementById("btn-copy-sql"),
  lastSyncTime: document.getElementById("last-sync-time"),
};

/** Tab Navigation Controller */
function initTabs() {
  elements.tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      elements.tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      elements.tabPanels.forEach(p => {
        p.classList.remove("active");
        p.hidden = true;
      });

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
        targetPanel.hidden = false;
      }
    });
  });
}

/** Fetch Bottleneck Analytics from API */
async function fetchBottlenecks() {
  const aov = elements.numAov.value;
  const dailyTx = elements.numDailyTx.value;
  const revDrop = (parseFloat(elements.numRevDrop.value) / 100.0).toFixed(4);
  const opsCost = elements.numOpsCost.value;

  try {
    const url = `/analyze-bottlenecks?aov=${aov}&daily_tx=${dailyTx}&rev_drop_per_hr=${revDrop}&ops_cost_per_hr=${opsCost}&currency=${currentCurrency}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load analysis");
    const data = await res.json();
    renderAnalysis(data);
    updateSyncTimestamp();
  } catch (err) {
    console.error("API Error in fetchBottlenecks:", err);
  }
}

/** Fetch All Corridor Friction Metrics */
async function fetchCorridors() {
  try {
    const res = await fetch("/metrics/department-friction");
    if (!res.ok) throw new Error("Failed to load corridors");
    cachedCorridors = await res.json();
    renderCorridors(cachedCorridors);
  } catch (err) {
    console.error("API Error in fetchCorridors:", err);
  }
}

/** Render Overview KPIs, Bottlenecks, and Proposals */
function renderAnalysis(data) {
  const ent = data.enterprise_summary || {};
  const impact = data.quantified_revenue_impact || {};
  const worstHandoffs = data.worst_performing_handoffs || [];
  const recs = data.data_backed_recommendations || [];

  // 1. Executive KPIs
  if (elements.kpiTotalTickets) elements.kpiTotalTickets.textContent = Number(ent.total_tickets || 10000).toLocaleString();
  if (elements.kpiTotalTransitions) elements.kpiTotalTransitions.textContent = Number(ent.total_transitions || 23356).toLocaleString();
  if (elements.kpiBreachRate) elements.kpiBreachRate.textContent = `${ent.overall_breach_rate_pct || 28.09}%`;
  if (elements.kpiBreachedCount) elements.kpiBreachedCount.textContent = Number(ent.total_breached_transitions || 6560).toLocaleString();
  if (elements.kpiTotalDelay) elements.kpiTotalDelay.textContent = `${Math.round(ent.total_breach_hours || impact.total_delay_hours).toLocaleString()} hrs`;
  if (elements.kpiAvgDuration) elements.kpiAvgDuration.textContent = `${ent.avg_transition_hours || 16.7} hrs`;
  if (elements.kpiWeeklyLeakage) elements.kpiWeeklyLeakage.textContent = `${impact.formatted_weekly_leakage || "$1.30M"} / wk`;
  if (elements.kpiInrBenchmark) elements.kpiInrBenchmark.textContent = impact.inr_benchmark_weekly_leakage || "800.71 Lakh / week";

  // 2. Top Bottlenecks Cards
  if (elements.topBottlenecksList) {
    elements.topBottlenecksList.innerHTML = "";
    let cumulative = 0;

    worstHandoffs.forEach(bn => {
      cumulative += bn.delay_share_pct;
      const card = document.createElement("div");
      card.className = "corridor-card";
      card.innerHTML = `
        <div class="cc-header">
          <div class="cc-left">
            <span class="cc-rank">RANK #${bn.bottleneck_rank}</span>
            <span class="cc-corridor-title">${bn.handoff_corridor} (${bn.from_department} &rarr; ${bn.to_department})</span>
          </div>
          <span class="cc-share-badge">${bn.delay_share_pct}% Enterprise Delay</span>
        </div>
        <div class="cc-bar-wrap">
          <div class="cc-bar-fill" style="width: ${bn.delay_share_pct}%;"></div>
        </div>
        <div class="cc-metrics-grid">
          <div class="cc-metric-col">
            <span class="label">SLA Breach Rate</span>
            <span class="val text-alert">${bn.breach_rate_pct}% (${Number(bn.breach_count).toLocaleString()})</span>
          </div>
          <div class="cc-metric-col">
            <span class="label">Average Duration</span>
            <span class="val">${bn.avg_duration_hours}h <small style="color:var(--text-muted);">(SLA: ${bn.sla_target_hours}h)</small></span>
          </div>
          <div class="cc-metric-col">
            <span class="label">Weekly Leakage</span>
            <span class="val text-danger">${bn.formatted_weekly_leakage}</span>
          </div>
          <div class="cc-metric-col">
            <span class="label">INR Benchmark</span>
            <span class="val">₹${bn.inr_lakhs_per_week} L/wk</span>
          </div>
        </div>
      `;
      elements.topBottlenecksList.appendChild(card);
    });

    if (elements.paretoSummaryPill) {
      elements.paretoSummaryPill.textContent = `${cumulative.toFixed(1)}% Combined Delay Share`;
    }
  }

  // 3. Process RFCs (Tab 3)
  if (elements.rfcsContainer) {
    elements.rfcsContainer.innerHTML = "";
    recs.forEach((rec, idx) => {
      const rfc = document.createElement("div");
      rfc.className = "rfc-card";
      rfc.innerHTML = `
        <div class="rfc-top">
          <span class="rfc-id">RFC-OPS-${100 + idx} &bull; ${rec.corridor}</span>
          <span class="rfc-confidence">${Math.round(rec.confidence_score * 100)}% Confidence</span>
        </div>
        <div class="rfc-title">${rec.recommendation}</div>
        <div class="rfc-action">${rec.action_item}</div>
        <div class="rfc-metrics-grid">
          <div class="rfc-metric">
            <span class="label">Reclaimable Hours</span>
            <span class="val success">&darr; ${rec.projected_reclaimed_hours_weekly} hrs / week</span>
          </div>
          <div class="rfc-metric">
            <span class="label">Weekly ROI Savings</span>
            <span class="val success">${rec.formatted_weekly_savings} / wk</span>
          </div>
          <div class="rfc-metric">
            <span class="label">Annual Projected Value</span>
            <span class="val">${rec.formatted_annual_savings}</span>
          </div>
          <div class="rfc-metric">
            <span class="label">Implementation Effort</span>
            <span class="val">${rec.implementation_effort}</span>
          </div>
        </div>
      `;
      elements.rfcsContainer.appendChild(rfc);
    });
  }

  // 4. Simulator Output Column
  if (elements.simOutWeeklyTotal) elements.simOutWeeklyTotal.textContent = impact.formatted_weekly_leakage || "$1,298,168";
  if (elements.simOutInrBenchmark) elements.simOutInrBenchmark.textContent = `Equivalent: ${impact.inr_benchmark_weekly_leakage || '800.71 Lakh / week'}`;
  if (elements.simOutWeeklyGmv) elements.simOutWeeklyGmv.textContent = formatCurrencyAmount(impact.weekly_gmv_leaked);
  if (elements.simOutWeeklyOps) elements.simOutWeeklyOps.textContent = formatCurrencyAmount(impact.weekly_operational_cost);

  // 5. Sensitivity Scenarios
  const sc = impact.sensitivity_scenarios || {};
  if (sc.conservative) {
    if (elements.scValConsWeekly) elements.scValConsWeekly.textContent = sc.conservative.formatted_weekly_leakage;
    if (elements.scValConsTotal) elements.scValConsTotal.textContent = formatCurrencyAmount(sc.conservative.weekly_leakage * (90 / 7));
  }
  if (sc.baseline) {
    if (elements.scValBaseWeekly) elements.scValBaseWeekly.textContent = sc.baseline.formatted_weekly_leakage;
    if (elements.scValBaseTotal) elements.scValBaseTotal.textContent = impact.formatted_total_leakage;
  }
  if (sc.aggressive) {
    if (elements.scValAggrWeekly) elements.scValAggrWeekly.textContent = sc.aggressive.formatted_weekly_leakage;
    if (elements.scValAggrTotal) elements.scValAggrTotal.textContent = formatCurrencyAmount(sc.aggressive.weekly_leakage * (90 / 7));
  }
}

/** Render Table of All Department Corridors */
function renderCorridors(corridors) {
  if (!elements.corridorsTableBody) return;
  elements.corridorsTableBody.innerHTML = "";

  corridors.forEach(c => {
    const tr = document.createElement("tr");
    const isBreachHigh = c.breach_rate_pct > 25.0;
    tr.innerHTML = `
      <td><strong>${c.from_code} &rarr; ${c.to_code}</strong></td>
      <td>${c.from_department}</td>
      <td>${c.to_department}</td>
      <td class="num-col">${Number(c.total_transitions).toLocaleString()}</td>
      <td class="num-col">${c.avg_duration_hours}h</td>
      <td class="num-col">${c.avg_sla_target_hours}h</td>
      <td class="num-col">
        <span class="status-badge ${isBreachHigh ? 'breach-high' : 'breach-low'}">
          ${c.breach_rate_pct}%
        </span>
      </td>
      <td class="num-col"><strong>${Math.round(c.total_breach_hours).toLocaleString()}h</strong></td>
      <td class="num-col">${c.total_blockers}</td>
    `;
    elements.corridorsTableBody.appendChild(tr);
  });
}

/** Currency Formatter */
function formatCurrencyAmount(amount) {
  if (!amount) return "$0";
  if (currentCurrency === "INR") {
    if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} Lakh`;
    return `₹${Number(amount).toLocaleString()}`;
  }
  if (currentCurrency === "EUR") {
    if (amount >= 1000000) return `€${(amount / 1000000).toFixed(2)}M`;
    if (amount >= 1000) return `€${(amount / 1000).toFixed(1)}k`;
    return `€${Number(amount).toLocaleString()}`;
  }
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(2)}M`;
  if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}k`;
  return `$${Number(amount).toLocaleString()}`;
}

/** Update Live Sync Timestamp */
function updateSyncTimestamp() {
  lastSyncTimestamp = new Date();
  if (elements.lastSyncTime) {
    elements.lastSyncTime.textContent = "Synced just now";
  }
}

/** Setup Event Listeners for Simulator & Table Filters */
function setupEventListeners() {
  // Synchronize Slider <-> Numeric Input for AOV
  elements.sliderAov.addEventListener("input", () => {
    elements.numAov.value = elements.sliderAov.value;
    fetchBottlenecks();
  });
  elements.numAov.addEventListener("input", () => {
    elements.sliderAov.value = elements.numAov.value;
    fetchBottlenecks();
  });

  // Synchronize Slider <-> Numeric Input for Daily Tx
  elements.sliderDailyTx.addEventListener("input", () => {
    elements.numDailyTx.value = elements.sliderDailyTx.value;
    fetchBottlenecks();
  });
  elements.numDailyTx.addEventListener("input", () => {
    elements.sliderDailyTx.value = elements.numDailyTx.value;
    fetchBottlenecks();
  });

  // Synchronize Slider <-> Numeric Input for Rev Drop
  elements.sliderRevDrop.addEventListener("input", () => {
    elements.numRevDrop.value = elements.sliderRevDrop.value;
    fetchBottlenecks();
  });
  elements.numRevDrop.addEventListener("input", () => {
    elements.sliderRevDrop.value = elements.numRevDrop.value;
    fetchBottlenecks();
  });

  // Synchronize Slider <-> Numeric Input for Ops Cost
  elements.sliderOpsCost.addEventListener("input", () => {
    elements.numOpsCost.value = elements.sliderOpsCost.value;
    fetchBottlenecks();
  });
  elements.numOpsCost.addEventListener("input", () => {
    elements.sliderOpsCost.value = elements.numOpsCost.value;
    fetchBottlenecks();
  });

  // Currency Switcher
  elements.currencySelect.addEventListener("change", (e) => {
    currentCurrency = e.target.value;
    const sym = currentCurrency === "INR" ? "₹" : (currentCurrency === "EUR" ? "€" : "$");
    if (elements.currSym1) elements.currSym1.textContent = sym;
    if (elements.currSym2) elements.currSym2.textContent = sym;

    if (currentCurrency === "INR") {
      elements.sliderAov.min = 500;
      elements.sliderAov.max = 15000;
      elements.sliderAov.step = 250;
      elements.sliderAov.value = 3500;
      elements.numAov.value = 3500;
      elements.aovBoundMin.textContent = "₹500";
      elements.aovBoundMax.textContent = "₹15,000";

      elements.sliderOpsCost.min = 500;
      elements.sliderOpsCost.max = 10000;
      elements.sliderOpsCost.step = 250;
      elements.sliderOpsCost.value = 2500;
      elements.numOpsCost.value = 2500;
    } else {
      elements.sliderAov.min = 10;
      elements.sliderAov.max = 250;
      elements.sliderAov.step = 5;
      elements.sliderAov.value = 45;
      elements.numAov.value = 45;
      elements.aovBoundMin.textContent = "$10";
      elements.aovBoundMax.textContent = "$250";

      elements.sliderOpsCost.min = 20;
      elements.sliderOpsCost.max = 200;
      elements.sliderOpsCost.step = 5;
      elements.sliderOpsCost.value = 65;
      elements.numOpsCost.value = 65;
    }
    fetchBottlenecks();
  });

  // Search Filter on Table
  if (elements.corridorSearch) {
    elements.corridorSearch.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        renderCorridors(cachedCorridors);
        return;
      }
      const filtered = cachedCorridors.filter(c =>
        c.from_code.toLowerCase().includes(q) ||
        c.to_code.toLowerCase().includes(q) ||
        c.from_department.toLowerCase().includes(q) ||
        c.to_department.toLowerCase().includes(q)
      );
      renderCorridors(filtered);
    });
  }

  // Refresh Button
  if (elements.btnRefresh) {
    elements.btnRefresh.addEventListener("click", () => {
      fetchBottlenecks();
      fetchCorridors();
    });
  }

  // Reseed Dataset Button
  if (elements.btnReseed) {
    elements.btnReseed.addEventListener("click", async () => {
      const confirmed = confirm("Reseed 10,000+ workflow tickets & 23,000+ transitions?");
      if (!confirmed) return;

      elements.btnReseed.textContent = "Reseeding (10k)...";
      elements.btnReseed.disabled = true;

      try {
        const res = await fetch("/seed-database?ticket_count=10000", { method: "POST" });
        const data = await res.json();
        alert(`Success: Regenerated ${data.total_tickets.toLocaleString()} tickets and ${data.total_transitions.toLocaleString()} transitions.`);
        fetchBottlenecks();
        fetchCorridors();
      } catch (err) {
        alert("Error reseeding dataset: " + err);
      } finally {
        elements.btnReseed.textContent = "Reseed 10k Dataset";
        elements.btnReseed.disabled = false;
      }
    });
  }

  // Copy SQL Button
  if (elements.btnCopySql) {
    elements.btnCopySql.addEventListener("click", () => {
      const code = document.getElementById("sql-code-display")?.innerText;
      if (code) {
        navigator.clipboard.writeText(code).then(() => {
          elements.btnCopySql.textContent = "Copied!";
          setTimeout(() => {
            elements.btnCopySql.textContent = "Copy SQL";
          }, 2000);
        });
      }
    });
  }
}

// Initial Boot
window.addEventListener("DOMContentLoaded", () => {
  initTabs();
  setupEventListeners();
  fetchBottlenecks();
  fetchCorridors();
});
