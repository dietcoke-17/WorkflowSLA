-- ============================================================================
-- WorkflowSLA: PostgreSQL Normalized Relational Database Schema
-- Tracks cross-functional initiatives, tickets, and inter-departmental transitions
-- ============================================================================

-- Drop existing tables if rebuilding
DROP TABLE IF EXISTS workflow_transitions CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS sla_policies CASCADE;
DROP TABLE IF EXISTS initiatives CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- 1. Departments Table
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(16) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_departments_code ON departments(code);

-- 2. Initiatives Table
CREATE TABLE initiatives (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    initiative_type VARCHAR(50) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'P1',
    owner_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    budget NUMERIC(14, 2) DEFAULT 0.00,
    target_quarter VARCHAR(10) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_initiatives_type ON initiatives(initiative_type);
CREATE INDEX idx_initiatives_owner ON initiatives(owner_department_id);

-- 3. SLA Policies Table
CREATE TABLE sla_policies (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL,
    initiative_type VARCHAR(50),
    priority VARCHAR(10),
    from_department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    to_department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    max_duration_hours DOUBLE PRECISION NOT NULL,
    warning_threshold_hours DOUBLE PRECISION NOT NULL,
    breach_penalty_per_hour DOUBLE PRECISION DEFAULT 150.00,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sla_initiative_type ON sla_policies(initiative_type);

-- 4. Tickets Table (Simulating Jira / ServiceNow records)
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(32) NOT NULL UNIQUE,
    initiative_id INTEGER NOT NULL REFERENCES initiatives(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    ticket_type VARCHAR(50) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'P2',
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    creator_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    current_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITHOUT TIME ZONE,
    total_duration_hours DOUBLE PRECISION,
    is_breached BOOLEAN NOT NULL DEFAULT FALSE,
    total_breach_hours DOUBLE PRECISION NOT NULL DEFAULT 0.00
);

CREATE INDEX idx_tickets_key ON tickets(ticket_key);
CREATE INDEX idx_tickets_initiative ON tickets(initiative_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_is_breached ON tickets(is_breached);

-- 5. Workflow Transitions Table (Inter-departmental handoffs)
CREATE TABLE workflow_transitions (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    transition_seq INTEGER NOT NULL,
    from_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    to_department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    transitioned_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    duration_hours DOUBLE PRECISION,
    sla_target_hours DOUBLE PRECISION NOT NULL DEFAULT 24.00,
    is_breached BOOLEAN NOT NULL DEFAULT FALSE,
    breach_hours DOUBLE PRECISION NOT NULL DEFAULT 0.00,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    blocker_reason VARCHAR(120),
    blocked_duration_hours DOUBLE PRECISION DEFAULT 0.00,
    notes TEXT
);

CREATE INDEX idx_transitions_ticket ON workflow_transitions(ticket_id);
CREATE INDEX idx_transitions_from_to ON workflow_transitions(from_department_id, to_department_id);
CREATE INDEX idx_transitions_dates ON workflow_transitions(transitioned_at, completed_at);
CREATE INDEX idx_transitions_breach ON workflow_transitions(is_breached);
