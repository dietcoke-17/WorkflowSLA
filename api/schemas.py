"""
WorkflowSLA: Pydantic API Schemas
Defines request and response models for bottleneck analysis and simulations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    average_order_value: float = Field(default=45.0, description="Average order value in target currency", gt=0)
    daily_transactions: int = Field(default=10000, description="Average daily transactions processed", gt=0)
    revenue_drop_per_hour_delayed: float = Field(
        default=0.005,
        description="Percentage of revenue leaked per delay hour (e.g., 0.005 = 0.5%)",
        ge=0.0,
        le=1.0
    )
    operational_cost_per_hour: float = Field(
        default=65.0,
        description="Hourly cost of blocked personnel and operational overhead",
        ge=0.0
    )
    timeframe_days: int = Field(default=90, description="Window of historical dataset in days", ge=1)
    currency: str = Field(default="USD", description="Currency code (USD, INR, EUR)")


class BottleneckHandoff(BaseModel):
    bottleneck_rank: int
    handoff_corridor: str
    from_department: str
    to_department: str
    total_transitions: int
    breach_count: int
    breach_rate_pct: float
    avg_duration_hours: float
    sla_target_hours: float
    corridor_breach_hours: float
    weekly_breach_hours: float
    delay_share_pct: float
    cumulative_delay_pct: float
    gmv_leaked: float
    weekly_gmv_leaked: float
    operational_cost: float
    weekly_operational_cost: float
    total_financial_leakage: float
    weekly_financial_leakage: float
    formatted_weekly_leakage: str
    inr_lakhs_per_week: float


class ProcessRecommendation(BaseModel):
    corridor: str
    bottleneck_rank: int
    recommendation: str
    action_item: str
    projected_reclaimed_hours_weekly: float
    projected_weekly_savings: float
    projected_annual_savings: float
    formatted_weekly_savings: str
    formatted_annual_savings: str
    inr_benchmark_savings_per_week: str
    implementation_effort: str
    confidence_score: float


class BottleneckAnalysisResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]
    worst_performing_handoffs: List[BottleneckHandoff]
    quantified_revenue_impact: Dict[str, Any]
    data_backed_recommendations: List[ProcessRecommendation]
    executive_summary: str
    enterprise_summary: Dict[str, Any]

