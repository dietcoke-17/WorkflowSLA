"""
WorkflowSLA: SQL Analytics Engine
Executes advanced SQL queries featuring window functions (LAG, LEAD, RANK),
cumulative sums, and timestamp differences on PostgreSQL and SQLite.
"""
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from sqlalchemy import text
from database.connection import engine, SessionLocal


class SQLAnalyticsEngine:
    """
    Advanced SQL execution engine analyzing inter-departmental handoffs,
    SLA breaches, cascading window dependencies, and enterprise friction points.
    """

    def __init__(self, db_engine=None):
        self.engine = db_engine or engine

    def execute_query(self, query_sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes raw SQL query and returns list of dictionaries."""
        with self.engine.connect() as conn:
            result = conn.execute(text(query_sql), params or {})
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows

    def get_department_transition_metrics(self) -> List[Dict[str, Any]]:
        """
        Calculates average transition time, SLA targets, breach rate,
        and total delay hours between specific departments.
        """
        sql = """
        WITH DepartmentPairs AS (
            SELECT 
                d_from.name AS from_department,
                d_from.code AS from_code,
                d_to.name AS to_department,
                d_to.code AS to_code,
                wt.duration_hours,
                wt.sla_target_hours,
                wt.is_breached,
                wt.breach_hours,
                wt.is_blocked
            FROM workflow_transitions wt
            JOIN departments d_from ON wt.from_department_id = d_from.id
            JOIN departments d_to ON wt.to_department_id = d_to.id
        )
        SELECT 
            from_code,
            from_department,
            to_code,
            to_department,
            COUNT(*) AS total_transitions,
            ROUND(AVG(duration_hours), 2) AS avg_duration_hours,
            ROUND(AVG(sla_target_hours), 2) AS avg_sla_target_hours,
            SUM(CASE WHEN is_breached = 1 OR is_breached = TRUE THEN 1 ELSE 0 END) AS breach_count,
            ROUND(
                100.0 * SUM(CASE WHEN is_breached = 1 OR is_breached = TRUE THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS breach_rate_pct,
            ROUND(SUM(breach_hours), 2) AS total_breach_hours,
            ROUND(AVG(CASE WHEN breach_hours > 0 THEN breach_hours ELSE NULL END), 2) AS avg_breach_hours_when_delayed,
            SUM(CASE WHEN is_blocked = 1 OR is_blocked = TRUE THEN 1 ELSE 0 END) AS total_blockers
        FROM DepartmentPairs
        GROUP BY from_code, from_department, to_code, to_department
        ORDER BY total_breach_hours DESC;
        """
        return self.execute_query(sql)

    def get_top_three_bottlenecks(self) -> Dict[str, Any]:
        """
        Pinpoints the top 3 inter-departmental handoffs responsible for ~80%
        of workflow delays using window functions (SUM OVER and DENSE_RANK).
        """
        sql = """
        WITH TransitionSummary AS (
            SELECT 
                d_from.code || ' -> ' || d_to.code AS handoff_corridor,
                d_from.name AS from_department_name,
                d_to.name AS to_department_name,
                COUNT(*) AS total_volume,
                SUM(CASE WHEN wt.is_breached = 1 OR wt.is_breached = TRUE THEN 1 ELSE 0 END) AS breach_volume,
                ROUND(AVG(wt.duration_hours), 2) AS avg_duration_hours,
                ROUND(AVG(wt.sla_target_hours), 2) AS sla_target_hours,
                ROUND(SUM(wt.breach_hours), 2) AS corridor_breach_hours,
                SUM(CASE WHEN wt.is_blocked = 1 OR wt.is_blocked = TRUE THEN 1 ELSE 0 END) AS blocker_count
            FROM workflow_transitions wt
            JOIN departments d_from ON wt.from_department_id = d_from.id
            JOIN departments d_to ON wt.to_department_id = d_to.id
            GROUP BY d_from.code, d_from.name, d_to.code, d_to.name
        ),
        CorridorRankings AS (
            SELECT 
                handoff_corridor,
                from_department_name,
                to_department_name,
                total_volume,
                breach_volume,
                avg_duration_hours,
                sla_target_hours,
                corridor_breach_hours,
                blocker_count,
                ROUND(100.0 * breach_volume / total_volume, 2) AS breach_rate_pct,
                SUM(corridor_breach_hours) OVER () AS total_enterprise_delay_hours,
                ROUND(100.0 * corridor_breach_hours / SUM(corridor_breach_hours) OVER (), 2) AS delay_share_pct,
                SUM(corridor_breach_hours) OVER (
                    ORDER BY corridor_breach_hours DESC 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ) AS running_cumulative_hours,
                ROUND(
                    100.0 * SUM(corridor_breach_hours) OVER (
                        ORDER BY corridor_breach_hours DESC 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) / SUM(corridor_breach_hours) OVER (),
                    2
                ) AS cumulative_delay_pct,
                DENSE_RANK() OVER (ORDER BY corridor_breach_hours DESC) AS bottleneck_rank
            FROM TransitionSummary
        )
        SELECT 
            bottleneck_rank,
            handoff_corridor,
            from_department_name,
            to_department_name,
            total_volume,
            breach_volume,
            breach_rate_pct,
            avg_duration_hours,
            sla_target_hours,
            corridor_breach_hours,
            blocker_count,
            delay_share_pct,
            cumulative_delay_pct,
            total_enterprise_delay_hours
        FROM CorridorRankings
        ORDER BY bottleneck_rank ASC;
        """
        rows = self.execute_query(sql)
        top_three = [r for r in rows if r["bottleneck_rank"] <= 3]
        total_enterprise_delay = rows[0]["total_enterprise_delay_hours"] if rows else 0.0
        top_three_cumulative_pct = top_three[-1]["cumulative_delay_pct"] if top_three else 0.0
        top_three_delay_hours = sum(r["corridor_breach_hours"] for r in top_three)

        return {
            "top_bottlenecks": top_three,
            "all_ranked_corridors": rows,
            "total_enterprise_delay_hours": round(total_enterprise_delay, 2),
            "top_three_delay_hours": round(top_three_delay_hours, 2),
            "top_three_delay_share_pct": round(top_three_cumulative_pct, 2),
            "pareto_threshold_met": top_three_cumulative_pct >= 75.0
        }

    def get_lag_lead_window_analysis(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Executes window function query with LAG (prior department breach status)
        and LEAD (subsequent handoff impact) to identify cascading delay propagation.
        """
        sql = f"""
        WITH StepSequencing AS (
            SELECT 
                wt.id AS transition_id,
                wt.ticket_id,
                t.ticket_key,
                t.priority AS ticket_priority,
                wt.transition_seq,
                d_from.code AS from_code,
                d_to.code AS to_code,
                wt.duration_hours,
                wt.sla_target_hours,
                wt.is_breached,
                wt.breach_hours,
                wt.blocker_reason,
                LAG(d_from.code) OVER (
                    PARTITION BY wt.ticket_id 
                    ORDER BY wt.transition_seq
                ) AS prev_dept_code,
                LAG(wt.duration_hours) OVER (
                    PARTITION BY wt.ticket_id 
                    ORDER BY wt.transition_seq
                ) AS prev_duration_hours,
                LAG(wt.is_breached) OVER (
                    PARTITION BY wt.ticket_id 
                    ORDER BY wt.transition_seq
                ) AS prev_is_breached,
                LEAD(d_to.code) OVER (
                    PARTITION BY wt.ticket_id 
                    ORDER BY wt.transition_seq
                ) AS next_dept_code,
                LEAD(wt.duration_hours) OVER (
                    PARTITION BY wt.ticket_id 
                    ORDER BY wt.transition_seq
                ) AS next_duration_hours
            FROM workflow_transitions wt
            JOIN tickets t ON wt.ticket_id = t.id
            JOIN departments d_from ON wt.from_department_id = d_from.id
            JOIN departments d_to ON wt.to_department_id = d_to.id
        )
        SELECT 
            from_code,
            to_code,
            COUNT(*) AS handoff_count,
            ROUND(AVG(duration_hours), 2) AS avg_current_duration,
            ROUND(AVG(prev_duration_hours), 2) AS avg_prior_step_duration,
            SUM(CASE WHEN prev_is_breached = 1 OR prev_is_breached = TRUE THEN 1 ELSE 0 END) AS count_prior_step_breached,
            ROUND(
                100.0 * SUM(CASE WHEN prev_is_breached = 1 OR prev_is_breached = TRUE THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS cascade_breach_dependency_pct
        FROM StepSequencing
        GROUP BY from_code, to_code
        HAVING COUNT(*) > 50
        ORDER BY cascade_breach_dependency_pct DESC
        LIMIT {limit};
        """
        return self.execute_query(sql)

    def get_sla_breach_rates_by_initiative(self) -> List[Dict[str, Any]]:
        """
        Aggregates SLA breach rates and total delayed hours categorized
        by strategic initiative type and owning department.
        """
        sql = """
        SELECT 
            i.initiative_type,
            i.name AS initiative_name,
            d.name AS owning_department,
            d.code AS owning_dept_code,
            COUNT(t.id) AS total_tickets,
            SUM(CASE WHEN t.is_breached = 1 OR t.is_breached = TRUE THEN 1 ELSE 0 END) AS breached_tickets,
            ROUND(
                100.0 * SUM(CASE WHEN t.is_breached = 1 OR t.is_breached = TRUE THEN 1 ELSE 0 END) / COUNT(t.id),
                2
            ) AS breach_rate_pct,
            ROUND(SUM(t.total_breach_hours), 2) AS total_breach_hours,
            ROUND(AVG(t.total_duration_hours), 2) AS avg_duration_hours,
            ROUND(AVG(CASE WHEN t.is_breached = 1 OR t.is_breached = TRUE THEN t.total_breach_hours ELSE NULL END), 2) AS avg_breach_hours_per_breached_ticket
        FROM tickets t
        JOIN initiatives i ON t.initiative_id = i.id
        JOIN departments d ON i.owner_department_id = d.id
        GROUP BY i.initiative_type, i.name, d.name, d.code
        ORDER BY total_breach_hours DESC;
        """
        return self.execute_query(sql)

    def get_top_blocker_reasons(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Extracts top blocker root causes ranked by occurrence and blocked hours."""
        sql = f"""
        SELECT 
            blocker_reason,
            d_from.code || ' -> ' || d_to.code AS handoff_corridor,
            COUNT(*) AS incident_count,
            ROUND(SUM(blocked_duration_hours), 2) AS total_blocked_hours,
            ROUND(AVG(blocked_duration_hours), 2) AS avg_hours_per_incident
        FROM workflow_transitions wt
        JOIN departments d_from ON wt.from_department_id = d_from.id
        JOIN departments d_to ON wt.to_department_id = d_to.id
        WHERE blocker_reason IS NOT NULL AND blocker_reason != ''
        GROUP BY blocker_reason, handoff_corridor
        ORDER BY incident_count DESC
        LIMIT {limit};
        """
        return self.execute_query(sql)

    def get_overall_summary_metrics(self) -> Dict[str, Any]:
        """Returns enterprise-wide workflow health metrics."""
        sql = """
        SELECT 
            COUNT(DISTINCT t.id) AS total_tickets,
            COUNT(wt.id) AS total_transitions,
            SUM(CASE WHEN wt.is_breached = 1 OR wt.is_breached = TRUE THEN 1 ELSE 0 END) AS total_breached_transitions,
            ROUND(
                100.0 * SUM(CASE WHEN wt.is_breached = 1 OR wt.is_breached = TRUE THEN 1 ELSE 0 END) / COUNT(wt.id),
                2
            ) AS overall_breach_rate_pct,
            ROUND(SUM(wt.breach_hours), 2) AS total_breach_hours,
            ROUND(AVG(wt.duration_hours), 2) AS avg_transition_hours,
            COUNT(DISTINCT wt.ticket_id) AS tickets_with_transitions
        FROM workflow_transitions wt
        LEFT JOIN tickets t ON wt.ticket_id = t.id;
        """
        rows = self.execute_query(sql)
        return rows[0] if rows else {}

