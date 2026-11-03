/**
 * WorkflowSLA: Aceternity UI Dynamic Controller
 * Features Interactive Spotlight Hover, Dynamic Bento Grid Updates,
 * Real-Time Financial Guesstimations, and Table Filtering.
 */

let currentCurrency = "USD";
let cachedCorridors = [];

// DOM References
const dom = {
  // Tabs
  tabButtons: document.querySelectorAll(".tab-pill"),
  tabPanes: document.querySelectorAll(".tab-pane"),

  // KPIs
  kpiTotalTickets: document.getElementById("kpi-total-tickets"),
  kpiTotalTransitions: document.getElementById("kpi-total-transitions"),
  kpiBreachRate: document.getElementById("kpi-breach-rate"),
  kpiBreachedCount: document.getElementById("kpi-breached-count"),
  kpiTotalDelay: document.getElementById("kpi-total-delay"),
  kpiAvgDuration: document.getElementById("kpi-avg-duration"),
  kpiWeeklyLeakage: document.getElementById("kpi-weekly-leakage"),
  kpiInrBenchmark: document.getElementById("kpi-inr-benchmark"),
  syncStamp: document.getElementById("sync-stamp"),

  // Corridors & Playbook
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
  opsBoundMin: document.getElementById("ops-bound-min"),
  opsBoundMax: document.getElementById("ops-bound-max"),

  // Simulator Outputs
  simOutWeeklyTotal: document.getElementById("sim-out-weekly-total"),
  simOutInrBenchmark: document.getElementById("sim-out-inr-benchmark"),
  simOutWeeklyGmv: document.getElementById("sim-out-weekly-gmv"),
  simOutWeeklyOps: document.getElementById("sim-out-weekly-ops"),

  // Scenarios Table
  scValConsWeekly: document.getElementById("sc-val-cons-weekly"),
  scValConsTotal: document.getElementById("sc-val-cons-total"),
  scValBaseWeekly: document.getElementById("sc-val-base-weekly"),
  scValBaseTotal: document.getElementById("sc-val-base-total"),
  scValAggrWeekly: document.getElementById("sc-val-aggr-weekly"),
  scValAggrTotal: document.getElementById("sc-val-aggr-total"),

  // Table & Search
  corridorSearch: document.getElementById("corridor-search"),
  corridorsTableBody: document.getElementById("corridors-table-body"),

  // Action Buttons
  btnRefresh: document.getElementById("btn-refresh"),
  btnReseed: document.getElementById("btn-reseed"),
  btnCopySql: document.getElementById("btn-copy-sql"),
};

/** Aceternity Mouse Spotlight Effect */
function initAceternitySpotlight() {
  document.querySelectorAll(".bento-card, .corridor-glass-card, .rfc-bento-card").forEach(card => {
    card.addEventListener("mousemove", e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });
}

/** Segmented Tab Navigation Controller */
function initTabNavigation() {
  dom.tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      dom.tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      dom.tabPanes.forEach(p => {
        p.classList.remove("active");
        p.hidden = true;
      });

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add("active");
        targetPane.hidden = false;
        initAceternitySpotlight();
      }
    });
  });
}

/** Fetch Bottleneck Analytics from REST API */
async function fetchBottlenecks() {
  const aov = dom.numAov.value;
  const dailyTx = dom.numDailyTx.value;
  const revDrop = (parseFloat(dom.numRevDrop.value) / 100.0).toFixed(4);
  const opsCost = dom.numOpsCost.value;

  try {
    const url = `/analyze-bottlenecks?aov=${aov}&daily_tx=${dailyTx}&rev_drop_per_hr=${revDrop}&ops_cost_per_hr=${opsCost}&currency=${currentCurrency}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("API call failed");
    const data = await res.json();
    renderDashboard(data);
    updateSyncTime();
  } catch (err) {
    console.error("fetchBottlenecks error:", err);
  }
}

/** Fetch All Corridor Friction Data */
async function fetchCorridors() {
  try {
    const res = await fetch("/metrics/department-friction");
    if (!res.ok) throw new Error("Failed to load friction data");
    cachedCorridors = await res.json();
    renderCorridorsTable(cachedCorridors);
  } catch (err) {
    console.error("fetchCorridors error:", err);
  }
}

/** Render Overview KPIs, Bottlenecks, and RFCs */
function renderDashboard(data) {
  const ent = data.enterprise_summary || {};
  const impact = data.quantified_revenue_impact || {};
  const worstHandoffs = data.worst_performing_handoffs || [];
  const recs = data.data_backed_recommendations || [];

  // 1. Metric Bento Grid
  if (dom.kpiTotalTickets) dom.kpiTotalTickets.textContent = Number(ent.total_tickets || 10000).toLocaleString();
  if (dom.kpiTotalTransitions) dom.kpiTotalTransitions.textContent = Number(ent.total_transitions || 23356).toLocaleString();
  if (dom.kpiBreachRate) dom.kpiBreachRate.textContent = `${ent.overall_breach_rate_pct || 28.09}%`;
  if (dom.kpiBreachedCount) dom.kpiBreachedCount.textContent = Number(ent.total_breached_transitions || 6560).toLocaleString();
  if (dom.kpiTotalDelay) dom.kpiTotalDelay.textContent = `${Math.round(ent.total_breach_hours || impact.total_delay_hours).toLocaleString()}h`;
  if (dom.kpiAvgDuration) dom.kpiAvgDuration.textContent = `${ent.avg_transition_hours || 16.7}h`;
  if (dom.kpiWeeklyLeakage) dom.kpiWeeklyLeakage.textContent = impact.formatted_weekly_leakage || "$1.30M";
  if (dom.kpiInrBenchmark) dom.kpiInrBenchmark.innerHTML = `Benchmark equivalent: <strong class="text-rose">${impact.inr_benchmark_weekly_leakage || '800.71 Lakh / week'}</strong>`;

  // 2. Critical Bottlenecks Stream (Aceternity Glass Cards)
  if (dom.topBottlenecksList) {
    dom.topBottlenecksList.innerHTML = "";
    let cumulative = 0;

    worstHandoffs.forEach(bn => {
      cumulative += bn.delay_share_pct;
      const card = document.createElement("div");
      card.className = "corridor-glass-card";
      card.innerHTML = `
        <div class="cgc-top">
          <div class="cgc-left">
            <span class="cgc-rank-tag">RANK #${bn.bottleneck_rank}</span>
            <span class="cgc-title">${bn.handoff_corridor} (${bn.from_department} &rarr; ${bn.to_department})</span>
          </div>
          <span class="cgc-delay-pct">${bn.delay_share_pct}% Enterprise Delay</span>
        </div>
        <div class="cgc-meter-track">
          <div class="cgc-meter-fill" style="width: ${bn.delay_share_pct}%;"></div>
        </div>
        <div class="cgc-metrics-grid">
          <div class="cgc-metric-item">
            <span class="cgc-label">Breach Frequency</span>
            <span class="cgc-val text-amber">${bn.breach_rate_pct}% (${Number(bn.breach_count).toLocaleString()} breaches)</span>
          </div>
          <div class="cgc-metric-item">
            <span class="cgc-label">Mean Duration</span>
            <span class="cgc-val">${bn.avg_duration_hours}h <small style="color:var(--text-muted); font-weight:400;">(Target: ${bn.sla_target_hours}h)</small></span>
          </div>
          <div class="cgc-metric-item">
            <span class="cgc-label">Weekly Leakage</span>
            <span class="cgc-val text-rose">${bn.formatted_weekly_leakage} / wk</span>
          </div>
          <div class="cgc-metric-item">
            <span class="cgc-label">INR Equivalent</span>
            <span class="cgc-val">₹${bn.inr_lakhs_per_week} L/wk</span>
          </div>
        </div>
      `;
      dom.topBottlenecksList.appendChild(card);
    });

    if (dom.paretoSummaryPill) {
      dom.paretoSummaryPill.textContent = `${cumulative.toFixed(1)}% Combined Delay Share`;
    }
  }

  // 3. Process RFCs (Tab 3 Bento Deck)
  if (dom.rfcsContainer) {
    dom.rfcsContainer.innerHTML = "";
    recs.forEach((rec, idx) => {
      const tile = document.createElement("div");
      tile.className = "rfc-bento-card";
      tile.innerHTML = `
        <div class="rfc-top-row">
          <span class="rfc-number-chip">RFC-0${idx + 1} &bull; ${rec.corridor}</span>
          <span class="rfc-confidence-pill">${Math.round(rec.confidence_score * 100)}% Confidence</span>
        </div>
        <h3 class="rfc-title-text">${rec.recommendation}</h3>
        <p class="rfc-action-box">${rec.action_item}</p>
        <div class="rfc-metrics-bar">
          <div class="rfc-met-item">
            <span class="rfc-met-lbl">Reclaimed Hours</span>
            <span class="rfc-met-val emerald">&darr; ${rec.projected_reclaimed_hours_weekly} hrs / week</span>
          </div>
          <div class="rfc-met-item">
            <span class="rfc-met-lbl">Weekly ROI Savings</span>
            <span class="rfc-met-val emerald">${rec.formatted_weekly_savings} / wk</span>
          </div>
          <div class="rfc-met-item">
            <span class="rfc-met-lbl">Annual Value</span>
            <span class="rfc-met-val">${rec.formatted_annual_savings}</span>
          </div>
          <div class="rfc-met-item">
            <span class="rfc-met-lbl">Implementation Effort</span>
            <span class="rfc-met-val">${rec.implementation_effort}</span>
          </div>
        </div>
      `;
      dom.rfcsContainer.appendChild(tile);
    });
  }

  // 4. Simulator Output Column
  if (dom.simOutWeeklyTotal) dom.simOutWeeklyTotal.textContent = impact.formatted_weekly_leakage || "$1,298,168";
  if (dom.simOutInrBenchmark) dom.simOutInrBenchmark.textContent = `Equivalent: ${impact.inr_benchmark_weekly_leakage || '800.71 Lakh / week'}`;
  if (dom.simOutWeeklyGmv) dom.simOutWeeklyGmv.textContent = formatCurrency(impact.weekly_gmv_leaked);
  if (dom.simOutWeeklyOps) dom.simOutWeeklyOps.textContent = formatCurrency(impact.weekly_operational_cost);

  // 5. Sensitivity Scenarios
  const sc = impact.sensitivity_scenarios || {};
  if (sc.conservative) {
    if (dom.scValConsWeekly) dom.scValConsWeekly.textContent = sc.conservative.formatted_weekly_leakage;
    if (dom.scValConsTotal) dom.scValConsTotal.textContent = formatCurrency(sc.conservative.weekly_leakage * (90 / 7));
  }
  if (sc.baseline) {
    if (dom.scValBaseWeekly) dom.scValBaseWeekly.textContent = sc.baseline.formatted_weekly_leakage;
    if (dom.scValBaseTotal) dom.scValBaseTotal.textContent = impact.formatted_total_leakage;
  }
  if (sc.aggressive) {
    if (dom.scValAggrWeekly) dom.scValAggrWeekly.textContent = sc.aggressive.formatted_weekly_leakage;
    if (dom.scValAggrTotal) dom.scValAggrTotal.textContent = formatCurrency(sc.aggressive.weekly_leakage * (90 / 7));
  }

  initAceternitySpotlight();
}

/** Render Table of Department Corridors */
function renderCorridorsTable(corridors) {
  if (!dom.corridorsTableBody) return;
  dom.corridorsTableBody.innerHTML = "";

  corridors.forEach(c => {
    const tr = document.createElement("tr");
    const isHigh = c.breach_rate_pct > 25.0;
    tr.innerHTML = `
      <td><strong>${c.from_code} &rarr; ${c.to_code}</strong></td>
      <td>${c.from_department}</td>
      <td>${c.to_department}</td>
      <td class="text-right font-mono">${Number(c.total_transitions).toLocaleString()}</td>
      <td class="text-right font-mono">${c.avg_duration_hours}h</td>
      <td class="text-right font-mono">${c.avg_sla_target_hours}h</td>
      <td class="text-right">
        <span class="breach-pill ${isHigh ? 'high' : 'low'}">
          ${c.breach_rate_pct}%
        </span>
      </td>
      <td class="text-right font-mono"><strong>${Math.round(c.total_breach_hours).toLocaleString()}h</strong></td>
      <td class="text-right font-mono">${c.total_blockers}</td>
    `;
    dom.corridorsTableBody.appendChild(tr);
  });
}

/** Currency Formatter */
function formatCurrency(amount) {
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

/** Sync Time Updater */
function updateSyncTime() {
  if (dom.syncStamp) {
    dom.syncStamp.textContent = "Synced just now";
  }
}

/** Event Listeners Setup */
function setupEventHandlers() {
  // AOV Synchronized Inputs
  dom.sliderAov.addEventListener("input", () => {
    dom.numAov.value = dom.sliderAov.value;
    fetchBottlenecks();
  });
  dom.numAov.addEventListener("input", () => {
    dom.sliderAov.value = dom.numAov.value;
    fetchBottlenecks();
  });

  // Daily Tx Synchronized Inputs
  dom.sliderDailyTx.addEventListener("input", () => {
    dom.numDailyTx.value = dom.sliderDailyTx.value;
    fetchBottlenecks();
  });
  dom.numDailyTx.addEventListener("input", () => {
    dom.sliderDailyTx.value = dom.numDailyTx.value;
    fetchBottlenecks();
  });

  // Rev Drop Synchronized Inputs
  dom.sliderRevDrop.addEventListener("input", () => {
    dom.numRevDrop.value = dom.sliderRevDrop.value;
    fetchBottlenecks();
  });
  dom.numRevDrop.addEventListener("input", () => {
    dom.sliderRevDrop.value = dom.numRevDrop.value;
    fetchBottlenecks();
  });

  // Ops Cost Synchronized Inputs
  dom.sliderOpsCost.addEventListener("input", () => {
    dom.numOpsCost.value = dom.sliderOpsCost.value;
    fetchBottlenecks();
  });
  dom.numOpsCost.addEventListener("input", () => {
    dom.sliderOpsCost.value = dom.numOpsCost.value;
    fetchBottlenecks();
  });

  // Currency Selector
  dom.currencySelect.addEventListener("change", (e) => {
    currentCurrency = e.target.value;
    const sym = currentCurrency === "INR" ? "₹" : (currentCurrency === "EUR" ? "€" : "$");
    if (dom.currSym1) dom.currSym1.textContent = sym;
    if (dom.currSym2) dom.currSym2.textContent = sym;

    if (currentCurrency === "INR") {
      dom.sliderAov.min = 500;
      dom.sliderAov.max = 15000;
      dom.sliderAov.step = 250;
      dom.sliderAov.value = 3500;
      dom.numAov.value = 3500;
      dom.aovBoundMin.textContent = "₹500";
      dom.aovBoundMax.textContent = "₹15,000";

      dom.sliderOpsCost.min = 500;
      dom.sliderOpsCost.max = 10000;
      dom.sliderOpsCost.step = 250;
      dom.sliderOpsCost.value = 2500;
      dom.numOpsCost.value = 2500;
      dom.opsBoundMin.textContent = "₹500/hr";
      dom.opsBoundMax.textContent = "₹10,000/hr";
    } else {
      dom.sliderAov.min = 10;
      dom.sliderAov.max = 250;
      dom.sliderAov.step = 5;
      dom.sliderAov.value = 45;
      dom.numAov.value = 45;
      dom.aovBoundMin.textContent = "$10";
      dom.aovBoundMax.textContent = "$250";

      dom.sliderOpsCost.min = 20;
      dom.sliderOpsCost.max = 200;
      dom.sliderOpsCost.step = 5;
      dom.sliderOpsCost.value = 65;
      dom.numOpsCost.value = 65;
      dom.opsBoundMin.textContent = "$20/hr";
      dom.opsBoundMax.textContent = "$200/hr";
    }
    fetchBottlenecks();
  });

  // Corridor Search Filter
  if (dom.corridorSearch) {
    dom.corridorSearch.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        renderCorridorsTable(cachedCorridors);
        return;
      }
      const filtered = cachedCorridors.filter(c =>
        c.from_code.toLowerCase().includes(q) ||
        c.to_code.toLowerCase().includes(q) ||
        c.from_department.toLowerCase().includes(q) ||
        c.to_department.toLowerCase().includes(q)
      );
      renderCorridorsTable(filtered);
    });
  }

  // Refresh Button
  if (dom.btnRefresh) {
    dom.btnRefresh.addEventListener("click", () => {
      fetchBottlenecks();
      fetchCorridors();
    });
  }

  // Reseed Dataset Button
  if (dom.btnReseed) {
    dom.btnReseed.addEventListener("click", async () => {
      const confirmed = confirm("Reseed 10,000+ workflow tickets & 23,000+ transitions?");
      if (!confirmed) return;

      dom.btnReseed.textContent = "Reseeding...";
      dom.btnReseed.disabled = true;

      try {
        const res = await fetch("/seed-database?ticket_count=10000", { method: "POST" });
        const data = await res.json();
        alert(`Success: Regenerated ${data.total_tickets.toLocaleString()} tickets and ${data.total_transitions.toLocaleString()} transitions.`);
        fetchBottlenecks();
        fetchCorridors();
      } catch (err) {
        alert("Error reseeding dataset: " + err);
      } finally {
        dom.btnReseed.textContent = "Reseed 10k";
        dom.btnReseed.disabled = false;
      }
    });
  }

  // Copy SQL Button
  if (dom.btnCopySql) {
    dom.btnCopySql.addEventListener("click", () => {
      const code = document.getElementById("sql-code-display")?.innerText;
      if (code) {
        navigator.clipboard.writeText(code).then(() => {
          dom.btnCopySql.textContent = "Copied!";
          setTimeout(() => {
            dom.btnCopySql.textContent = "Copy SQL";
          }, 2000);
        });
      }
    });
  }
}

// Initial Boot
window.addEventListener("DOMContentLoaded", () => {
  initTabNavigation();
  setupEventHandlers();
  fetchBottlenecks();
  fetchCorridors();
  initAceternitySpotlight();
});
