"""
WorkflowSLA: Standard Library Test Runner
Executes all unit, SQL, simulation, and API tests using python's built-in unittest module.
Requires zero external network or HTTP test client packages.
"""
import sys
import os
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from database.connection import get_db_context, init_db
from database.models import Department, Initiative, SLAPolicy, Ticket, WorkflowTransition
from analytics.sql_engine import SQLAnalyticsEngine
from simulation.financial_engine import FinancialSimulationEngine, format_currency
from api.schemas import SimulationRequest
from api.main import (
    analyze_bottlenecks,
    simulate_leakage,
    get_department_friction,
    get_sla_by_initiative,
    get_window_analysis,
    health_check
)


class TestDatabaseSchema(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_departments_and_initiatives(self):
        with get_db_context() as db:
            depts = db.query(Department).all()
            self.assertGreaterEqual(len(depts), 4)
            dept_codes = {d.code for d in depts}
            self.assertIn("OPS", dept_codes)
            self.assertIn("CAT", dept_codes)
            self.assertIn("SCM", dept_codes)
            self.assertIn("CENTRAL", dept_codes)

            inits = db.query(Initiative).all()
            self.assertGreaterEqual(len(inits), 5)

    def test_synthetic_record_counts(self):
        with get_db_context() as db:
            ticket_count = db.query(Ticket).count()
            trans_count = db.query(WorkflowTransition).count()
            self.assertGreaterEqual(ticket_count, 10000, f"Expected >= 10,000 tickets, got {ticket_count}")
            self.assertGreaterEqual(trans_count, 20000, f"Expected >= 20,000 transitions, got {trans_count}")


class TestSQLAnalyticsEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SQLAnalyticsEngine()

    def test_department_transition_metrics(self):
        metrics = self.engine.get_department_transition_metrics()
        self.assertGreater(len(metrics), 0)
        first = metrics[0]
        self.assertIn("from_code", first)
        self.assertIn("to_code", first)
        self.assertIn("avg_duration_hours", first)
        self.assertIn("breach_rate_pct", first)
        self.assertIn("total_breach_hours", first)

    def test_top_three_bottlenecks_pareto_window(self):
        result = self.engine.get_top_three_bottlenecks()
        top_three = result["top_bottlenecks"]
        self.assertEqual(len(top_three), 3)

        ranks = [b["bottleneck_rank"] for b in top_three]
        self.assertEqual(ranks, [1, 2, 3])

        self.assertGreaterEqual(
            result["top_three_delay_share_pct"], 75.0,
            f"Top 3 should account for >= 75% of delays, got {result['top_three_delay_share_pct']}%"
        )

    def test_window_analysis_lag_lead(self):
        rows = self.engine.get_lag_lead_window_analysis(limit=5)
        self.assertGreater(len(rows), 0)
        self.assertIn("cascade_breach_dependency_pct", rows[0])


class TestFinancialSimulationEngine(unittest.TestCase):
    def setUp(self):
        self.sim = FinancialSimulationEngine()

    def test_simulation_calculations(self):
        res = self.sim.simulate(
            average_order_value=45.0,
            daily_transactions=10000,
            revenue_drop_per_hour_delayed=0.005,
            operational_cost_per_hour=65.0
        )
        totals = res["enterprise_totals"]
        self.assertGreater(totals["weekly_delay_hours"], 0)
        self.assertGreater(totals["weekly_gmv_leaked"], 0)
        self.assertGreater(totals["weekly_financial_leakage"], 0)

    def test_recommendation_and_reclaim_hours(self):
        res = self.sim.simulate()
        recs = res["recommendations"]
        self.assertGreaterEqual(len(recs), 3)

        scm_rec = next((r for r in recs if "CAT -> SCM" in r["corridor"] or "Supply Chain" in r["recommendation"]), None)
        self.assertIsNotNone(scm_rec)
        self.assertEqual(scm_rec["projected_reclaimed_hours_weekly"], 120.0)

    def test_currency_formatting(self):
        self.assertIn("$", format_currency(1500000, "USD"))
        self.assertIn("Lakh", format_currency(1200000, "INR"))


class TestFastAPIFunctions(unittest.TestCase):
    def test_health_check(self):
        with get_db_context() as db:
            res = health_check(db=db)
            self.assertEqual(res["status"], "HEALTHY")
            self.assertGreaterEqual(res["database"]["tickets_count"], 10000)

    def test_analyze_bottlenecks_endpoint(self):
        data = analyze_bottlenecks(aov=45.0, daily_tx=10000, rev_drop_per_hr=0.005, ops_cost_per_hr=65.0)
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(len(data["worst_performing_handoffs"]), 3)
        self.assertIn("quantified_revenue_impact", data)
        self.assertIn("data_backed_recommendations", data)

        recs = data["data_backed_recommendations"]
        scm_rec = next((r for r in recs if "Supply Chain" in r["recommendation"]), None)
        self.assertIsNotNone(scm_rec)
        self.assertEqual(scm_rec["projected_reclaimed_hours_weekly"], 120.0)

    def test_simulate_leakage_endpoint(self):
        payload = SimulationRequest(
            average_order_value=50.0,
            daily_transactions=12000,
            revenue_drop_per_hour_delayed=0.005,
            operational_cost_per_hour=70.0,
            timeframe_days=90,
            currency="USD"
        )
        data = simulate_leakage(payload=payload)
        self.assertIn("enterprise_totals", data)
        self.assertIn("sensitivity_scenarios", data)

    def test_metrics_functions(self):
        r1 = get_department_friction()
        self.assertIsInstance(r1, list)
        self.assertGreater(len(r1), 0)

        r2 = get_sla_by_initiative()
        self.assertIsInstance(r2, list)
        self.assertGreater(len(r2), 0)

        r3 = get_window_analysis(limit=5)
        self.assertIsInstance(r3, list)
        self.assertGreater(len(r3), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
