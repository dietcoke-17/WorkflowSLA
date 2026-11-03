-- ============================================================================
-- WorkflowSLA: Advanced SQL Analytics Queries
-- Features Window Functions (LAG, LEAD, RANK, PERCENT_RANK), CTEs,
-- and Timestamp Differences for Enterprise Bottleneck Analysis.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Inter-Departmental Transition Durations & Breach Rates
-- ----------------------------------------------------------------------------
-- Calculates average handoff duration, average SLA targets, total volume,
-- breach counts, and breach percentage between every department pair.
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


-- ----------------------------------------------------------------------------
-- 2. Advanced Window Analysis: LAG / LEAD Cascading Delay Correlation
-- ----------------------------------------------------------------------------
-- Leverages LAG to assess whether a breach in step N-1 causes cascading
-- delays in step N, and LEAD to project downstream handoff exposure.
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
        -- LAG: Inspect prior step's department, duration, and breach status
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
        -- LEAD: Inspect downstream receiving department and anticipated SLA
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
ORDER BY cascade_breach_dependency_pct DESC;


-- ----------------------------------------------------------------------------
-- 3. Top 3 Inter-Departmental Handoffs Responsible for 80% of Workflow Delays
-- ----------------------------------------------------------------------------
-- Pinpoints the top 3 friction points using Window Function SUM() OVER ()
-- to calculate running cumulative breach hours and verify the 80% Pareto threshold.
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
        -- Enterprise Total Breach Hours across all corridors
        SUM(corridor_breach_hours) OVER () AS total_enterprise_delay_hours,
        -- Individual share of enterprise delay
        ROUND(100.0 * corridor_breach_hours / SUM(corridor_breach_hours) OVER (), 2) AS delay_share_pct,
        -- Running cumulative delay hours
        SUM(corridor_breach_hours) OVER (
            ORDER BY corridor_breach_hours DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_cumulative_hours,
        -- Running cumulative percentage of delay
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
    cumulative_delay_pct
FROM CorridorRankings
WHERE bottleneck_rank <= 3
ORDER BY bottleneck_rank ASC;


-- ----------------------------------------------------------------------------
-- 4. SLA Breach Rates Categorized by Initiative Type & Owning Department
-- ----------------------------------------------------------------------------
SELECT 
    i.initiative_type,
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
GROUP BY i.initiative_type, d.name, d.code
ORDER BY total_breach_hours DESC;
