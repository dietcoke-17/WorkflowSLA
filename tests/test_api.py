"""
Integration Tests for FastAPI Endpoints and Analytics Handlers
"""
import pytest
from database.connection import get_db_context
from api.schemas import SimulationRequest
from api.main import (
    analyze_bottlenecks,
    simulate_leakage,
    get_department_friction,
    get_sla_by_initiative,
    get_window_analysis,
    health_check
)


def test_health_endpoint():
    """Verify health endpoint reports healthy database status."""
    with get_db_context() as db:
        res = health_check(db=db)
        assert res["status"] == "HEALTHY"
        assert res["database"]["tickets_count"] >= 10000


def test_analyze_bottlenecks_endpoint():
    """Verify /analyze-bottlenecks returns structured payload matching specs."""
    data = analyze_bottlenecks(aov=45.0, daily_tx=10000, rev_drop_per_hr=0.005, ops_cost_per_hr=65.0)

    assert data["status"] == "SUCCESS"
    assert "worst_performing_handoffs" in data
    assert len(data["worst_performing_handoffs"]) == 3
    assert "quantified_revenue_impact" in data
    assert "data_backed_recommendations" in data
    assert len(data["data_backed_recommendations"]) >= 3
    assert "executive_summary" in data

    # Check top recommendation for 120 hrs/week
    recs = data["data_backed_recommendations"]
    cat_scm = next((r for r in recs if "Supply Chain" in r["recommendation"]), None)
    assert cat_scm is not None
    assert cat_scm["projected_reclaimed_hours_weekly"] == 120.0


def test_simulate_leakage_post_endpoint():
    """Verify POST /simulate-leakage handles custom business parameters."""
    payload = SimulationRequest(
        average_order_value=55.0,
        daily_transactions=15000,
        revenue_drop_per_hour_delayed=0.006,
        operational_cost_per_hour=75.0,
        timeframe_days=90,
        currency="USD"
    )
    data = simulate_leakage(payload=payload)
    assert "enterprise_totals" in data
    assert "sensitivity_scenarios" in data


def test_department_friction_endpoint():
    """Verify /metrics/department-friction endpoint."""
    data = get_department_friction()
    assert isinstance(data, list)
    assert len(data) > 0


def test_sla_by_initiative_endpoint():
    """Verify /metrics/sla-by-initiative endpoint."""
    data = get_sla_by_initiative()
    assert isinstance(data, list)
    assert len(data) > 0
