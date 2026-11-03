"""
Unit Tests for Financial Simulation Engine & Guesstimate Algorithm
"""
import pytest
from simulation.financial_engine import FinancialSimulationEngine, format_currency


@pytest.fixture(scope="module")
def sim():
    return FinancialSimulationEngine()


def test_simulation_default_calculation(sim):
    """Verify simulation calculates GMV leakage and operational overhead."""
    res = sim.simulate(
        average_order_value=45.0,
        daily_transactions=10000,
        revenue_drop_per_hour_delayed=0.005,
        operational_cost_per_hour=65.0
    )

    totals = res["enterprise_totals"]
    assert totals["weekly_delay_hours"] > 0
    assert totals["weekly_gmv_leaked"] > 0
    assert totals["weekly_operational_cost"] > 0
    assert totals["weekly_financial_leakage"] == pytest.approx(
        totals["weekly_gmv_leaked"] + totals["weekly_operational_cost"], rel=1e-2
    )


def test_recommendations_and_hour_reclamation(sim):
    """Verify data-backed recommendations propose automations (e.g. 120 hrs/wk)."""
    res = sim.simulate()
    recs = res["recommendations"]
    assert len(recs) >= 3

    # Check for the Supply Chain approval recommendation
    scm_rec = next((r for r in recs if "CAT -> SCM" in r["corridor"] or "Supply Chain" in r["recommendation"]), None)
    assert scm_rec is not None
    assert scm_rec["projected_reclaimed_hours_weekly"] == 120.0
    assert scm_rec["projected_weekly_savings"] > 0


def test_sensitivity_scenarios(sim):
    """Verify conservative, baseline, and aggressive scenarios."""
    res = sim.simulate()
    sc = res["sensitivity_scenarios"]
    assert "conservative" in sc
    assert "baseline" in sc
    assert "aggressive" in sc
    assert sc["conservative"]["weekly_leakage"] < sc["baseline"]["weekly_leakage"]
    assert sc["baseline"]["weekly_leakage"] < sc["aggressive"]["weekly_leakage"]


def test_format_currency():
    """Verify currency formatting in USD and INR Lakhs."""
    assert "$" in format_currency(1500000, "USD")
    assert "Lakh" in format_currency(1200000, "INR")
