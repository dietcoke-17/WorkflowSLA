"""
WorkflowSLA: Cross-Functional Operations & Blockage Tracker
FastAPI REST API Application

Core Endpoints:
  - GET  /analyze-bottlenecks : Primary workflow analysis & quantified financial leakage
  - POST /simulate-leakage    : Dynamic top-down business variable simulation
  - GET  /metrics/*           : Granular department friction, window functions, and SLA rates
  - POST /seed-database       : Reseeds 10,000+ realistic synthetic tickets & transitions
  - GET  /health              : System & database health probe
"""
import sys
import os
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from database.connection import get_db, init_db, engine
from database.models import Ticket, WorkflowTransition, Department, Initiative
from analytics.sql_engine import SQLAnalyticsEngine
from simulation.financial_engine import FinancialSimulationEngine
from api.schemas import SimulationRequest, BottleneckAnalysisResponse
from scripts.generate_synthetic_data import generate_synthetic_dataset
from config import (
    DEFAULT_AVERAGE_ORDER_VALUE,
    DEFAULT_DAILY_TRANSACTIONS,
    DEFAULT_REVENUE_DROP_PER_HOUR,
    DEFAULT_OPERATIONAL_COST_PER_HOUR,
    DEFAULT_CURRENCY,
    ENVIRONMENT
)

# Initialize FastAPI application
app = FastAPI(
    title="WorkflowSLA: Cross-Functional Operations & Blockage Tracker",
    description=(
        "Enterprise analytics engine tracking internal business initiatives and support tickets. "
        "Calculates SLA breaches using advanced SQL window functions (LAG, LEAD) and dynamically "
        "guesstimates financial leakage and GMV impact caused by cross-departmental bottlenecks."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for dashboard
static_path = ROOT_DIR / "api" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Shared singletons
sql_engine = SQLAnalyticsEngine()
sim_engine = FinancialSimulationEngine(sql_engine)


@app.on_event("startup")
def startup_event():
    """Ensure database schema is created and populated on startup."""
    init_db()
    try:
        from database.connection import get_db_context
        with get_db_context() as db:
            if db.query(Ticket).count() == 0:
                generate_synthetic_dataset(db, ticket_count=10000)
    except Exception as e:
        print(f"Startup data check: {e}")


@app.get("/", tags=["Dashboard"])
def serve_dashboard():
    """Serves the interactive web dashboard."""
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={
            "app": "WorkflowSLA: Cross-Functional Operations & Blockage Tracker",
            "documentation": "/docs",
            "analyze_endpoint": "/analyze-bottlenecks"
        }
    )


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """System health check and database statistics."""
    try:
        tickets_count = db.query(Ticket).count()
        transitions_count = db.query(WorkflowTransition).count()
        depts_count = db.query(Department).count()
        initiatives_count = db.query(Initiative).count()
        return {
            "status": "HEALTHY",
            "environment": ENVIRONMENT,
            "database": {
                "dialect": engine.dialect.name,
                "tickets_count": tickets_count,
                "transitions_count": transitions_count,
                "departments_count": depts_count,
                "initiatives_count": initiatives_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


@app.get("/analyze-bottlenecks", response_model=BottleneckAnalysisResponse, tags=["Analytics & Guesstimate"])
def analyze_bottlenecks(
    aov: float = Query(DEFAULT_AVERAGE_ORDER_VALUE, description="Average Order Value (e.g. $45 or ₹3500)", gt=0),
    daily_tx: int = Query(DEFAULT_DAILY_TRANSACTIONS, description="Average daily transactions processed", gt=0),
    rev_drop_per_hr: float = Query(
        DEFAULT_REVENUE_DROP_PER_HOUR,
        description="Revenue drop per hour delayed (0.005 = 0.5%)",
        ge=0.0,
        le=1.0
    ),
    ops_cost_per_hr: float = Query(
        DEFAULT_OPERATIONAL_COST_PER_HOUR,
        description="Hourly cost of blocked operations personnel",
        ge=0.0
    ),
    timeframe_days: int = Query(90, description="Dataset observation window in days", ge=1),
    currency: str = Query(DEFAULT_CURRENCY, description="Currency code (USD, INR, EUR)")
):
    """
    Core Required Endpoint:
    Executes advanced workflow analytics to pinpoint the worst-performing departmental
    handoffs, calculates quantified financial leakage using top-down business variables,
    and returns data-backed process automation recommendations (e.g. reclaiming 120 hrs/week).
    """
    # Unpack default values if called directly as a function in Python
    _aov = getattr(aov, "default", aov)
    _daily_tx = getattr(daily_tx, "default", daily_tx)
    _rev_drop = getattr(rev_drop_per_hr, "default", rev_drop_per_hr)
    _ops_cost = getattr(ops_cost_per_hr, "default", ops_cost_per_hr)
    _timeframe = getattr(timeframe_days, "default", timeframe_days)
    _currency = getattr(currency, "default", currency)

    try:
        sim_results = sim_engine.simulate(
            average_order_value=_aov,
            daily_transactions=_daily_tx,
            revenue_drop_per_hour_delayed=_rev_drop,
            operational_cost_per_hour=_ops_cost,
            timeframe_days=_timeframe,
            currency=_currency
        )

        overall_metrics = sql_engine.get_overall_summary_metrics()

        return {
            "status": "SUCCESS",
            "metadata": {
                "generated_at": sim_results["input_variables"],
                "analysis_scope": "Operations, Category Management, Supply Chain, and Central compliance"
            },
            "worst_performing_handoffs": sim_results["top_three_bottlenecks"],
            "quantified_revenue_impact": sim_results["enterprise_totals"],
            "data_backed_recommendations": sim_results["recommendations"],
            "executive_summary": sim_results["executive_takeaway"],
            "enterprise_summary": overall_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis calculation error: {str(e)}")


@app.post("/simulate-leakage", tags=["Analytics & Guesstimate"])
def simulate_leakage(payload: SimulationRequest):
    """
    Dynamic scenario simulation endpoint.
    Accepts customized top-down business variables to calculate real-time GMV leakage
    and sensitivity scenarios (Conservative, Baseline, Aggressive).
    """
    try:
        results = sim_engine.simulate(
            average_order_value=payload.average_order_value,
            daily_transactions=payload.daily_transactions,
            revenue_drop_per_hour_delayed=payload.revenue_drop_per_hour_delayed,
            operational_cost_per_hour=payload.operational_cost_per_hour,
            timeframe_days=payload.timeframe_days,
            currency=payload.currency
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@app.get("/metrics/department-friction", tags=["Granular Metrics"])
def get_department_friction():
    """Returns granular transition durations and breach rates between all departmental pairs."""
    return sql_engine.get_department_transition_metrics()


@app.get("/metrics/sla-by-initiative", tags=["Granular Metrics"])
def get_sla_by_initiative():
    """Returns SLA breach rates broken down by strategic initiative type and owning department."""
    return sql_engine.get_sla_breach_rates_by_initiative()


@app.get("/metrics/window-analysis", tags=["Granular Metrics"])
def get_window_analysis(limit: int = Query(20, ge=1, le=100)):
    """
    Returns LAG/LEAD window function analysis identifying cascading
    delay dependencies across preceding and downstream workflow steps.
    """
    return sql_engine.get_lag_lead_window_analysis(limit=limit)


@app.get("/metrics/blockers", tags=["Granular Metrics"])
def get_blocker_reasons(limit: int = Query(10, ge=1, le=50)):
    """Returns top blocker reasons ranked by volume and total blocked duration hours."""
    return sql_engine.get_top_blocker_reasons(limit=limit)


@app.post("/seed-database", tags=["Administration"])
def seed_database(ticket_count: int = Query(10000, ge=500, le=50000)):
    """
    Generates a realistic synthetic dataset of 10,000+ tickets and 20,000-35,000+
    transitions simulating Jira/ServiceNow workflow logs.
    """
    try:
        total_tickets, total_transitions = generate_synthetic_dataset(target_ticket_count=ticket_count)
        return {
            "status": "SUCCESS",
            "message": f"Successfully generated {total_tickets:,} tickets and {total_transitions:,} transitions.",
            "total_tickets": total_tickets,
            "total_transitions": total_transitions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed database: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("api.main:app", host=HOST, port=PORT, reload=True)
