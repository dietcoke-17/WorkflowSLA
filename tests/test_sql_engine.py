"""
Unit Tests for SQL Analytics Engine & Window Function Queries
"""
import pytest
from analytics.sql_engine import SQLAnalyticsEngine


@pytest.fixture(scope="module")
def engine():
    return SQLAnalyticsEngine()


def test_department_transition_metrics(engine):
    """Verify department transition metrics calculate averages and breach rates."""
    metrics = engine.get_department_transition_metrics()
    assert len(metrics) > 0

    first = metrics[0]
    assert "from_code" in first
    assert "to_code" in first
    assert "avg_duration_hours" in first
    assert "breach_rate_pct" in first
    assert "total_breach_hours" in first
    assert first["total_transitions"] > 0


def test_top_three_bottlenecks_pareto_window(engine):
    """Verify that the top 3 bottlenecks account for ~80%+ of all workflow delays."""
    result = engine.get_top_three_bottlenecks()
    top_three = result["top_bottlenecks"]
    assert len(top_three) == 3

    # Check ranks 1, 2, 3
    ranks = [b["bottleneck_rank"] for b in top_three]
    assert ranks == [1, 2, 3]

    # Verify cumulative delay share meets or exceeds 75-80%
    assert result["top_three_delay_share_pct"] >= 75.0, (
        f"Top 3 corridors should account for >= 75% of delays, got {result['top_three_delay_share_pct']}%"
    )

    # Verify core departments involved
    corridors = {b["handoff_corridor"] for b in top_three}
    assert any("CAT" in c for c in corridors)
    assert any("SCM" in c for c in corridors)
    assert any("OPS" in c for c in corridors)


def test_lag_lead_window_analysis(engine):
    """Verify LAG and LEAD window calculations for cascading delay correlation."""
    window_data = engine.get_lag_lead_window_analysis(limit=10)
    assert len(window_data) > 0
    row = window_data[0]
    assert "cascade_breach_dependency_pct" in row
    assert "avg_prior_step_duration" in row


def test_sla_breach_rates_by_initiative(engine):
    """Verify breach rates aggregated by initiative type."""
    initiatives = engine.get_sla_breach_rates_by_initiative()
    assert len(initiatives) > 0
    first = initiatives[0]
    assert "initiative_type" in first
    assert "breach_rate_pct" in first
    assert "total_breach_hours" in first

