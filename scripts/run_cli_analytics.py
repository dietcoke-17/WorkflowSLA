"""
WorkflowSLA: Terminal Executive Analytics Report
Runs the SQL Analytics Engine and Financial Impact Simulation,
printing an executive-ready terminal report with tabulate.
"""
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from analytics.sql_engine import SQLAnalyticsEngine
from simulation.financial_engine import FinancialSimulationEngine


def print_executive_report():
    sql = SQLAnalyticsEngine()
    sim = FinancialSimulationEngine(sql)

    summary = sql.get_overall_summary_metrics()
    results = sim.simulate()

    print("\n" + "=" * 80)
    print(" WORKFLOWSLA: CROSS-FUNCTIONAL OPERATIONS & BLOCKAGE TRACKER")
    print(" Enterprise Executive Report & Financial Impact Assessment")
    print("=" * 80)

    print(f"\n[1] ENTERPRISE WORKFLOW HEALTH")
    print(f"  • Total Workflow Tickets:       {summary.get('total_tickets', 0):,}")
    print(f"  • Total Handoff Transitions:    {summary.get('total_transitions', 0):,}")
    print(f"  • Breached Transitions:         {summary.get('total_breached_transitions', 0):,} ({summary.get('overall_breach_rate_pct', 0)}%)")
    print(f"  • Total Enterprise Delay Hours: {summary.get('total_breach_hours', 0):,.1f} hrs")
    print(f"  • Average Transition Duration:  {summary.get('avg_transition_hours', 0):.1f} hrs")

    print(f"\n[2] TOP 3 BOTTLENECKS (PARETO 80% DELAY CORRIDORS)")
    for bn in results["top_three_bottlenecks"]:
        print(f"  Rank #{bn['bottleneck_rank']}: {bn['handoff_corridor']} ({bn['from_department']} -> {bn['to_department']})")
        print(f"     Delay Share:     {bn['delay_share_pct']}% of Enterprise Delay (Cumulative: {bn['cumulative_delay_pct']}%)")
        print(f"     Breach Rate:     {bn['breach_rate_pct']}% ({bn['breach_count']:,} breaches)")
        print(f"     Avg Time Taken:  {bn['avg_duration_hours']} hrs (SLA Target: {bn['sla_target_hours']} hrs)")
        print(f"     Weekly Leakage:  {bn['formatted_weekly_leakage']} / week (INR: ₹{bn['inr_lakhs_per_week']} Lakh/wk)")
        print()

    impact = results["enterprise_totals"]
    print(f"[3] QUANTIFIED FINANCIAL LEAKAGE IMPACT")
    print(f"  • Weekly GMV Leaked:            ${impact['weekly_gmv_leaked']:,.2f}")
    print(f"  • Weekly Ops Overhead:          ${impact['weekly_operational_cost']:,.2f}")
    print(f"  • Total Weekly Leakage:         {impact['formatted_weekly_leakage']} ({impact['inr_benchmark_weekly_leakage']})")
    print(f"  • Total 90-Day Enterprise Loss: {impact['formatted_total_leakage']}")

    print(f"\n[4] DATA-BACKED PROCESS AUTOMATION PROPOSALS")
    for idx, rec in enumerate(results["recommendations"], start=1):
        print(f"  Proposal #{idx} [{rec['corridor']}]: {rec['recommendation']}")
        print(f"     Action:              {rec['action_item']}")
        print(f"     Projected Reclaimed: {rec['projected_reclaimed_hours_weekly']} hours/week")
        print(f"     Weekly Savings:      {rec['formatted_weekly_savings']} / week ({rec['inr_benchmark_savings_per_week']})")
        print(f"     Annual Value:        {rec['formatted_annual_savings']} / year")
        print(f"     Effort / Confidence: {rec['implementation_effort']} | Confidence: {int(rec['confidence_score'] * 100)}%")
        print()

    print("=" * 80)
    print(" Executive Takeaway:")
    print(f" {results['executive_takeaway']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    print_executive_report()
