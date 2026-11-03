-- ============================================================================
-- WorkflowSLA: SQLite Normalized Relational Database Schema
-- Compatible with SQLite 3.25+ (Supports CTEs & Window Functions)
-- ============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS workflow_transitions;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS sla_policies;
DROP TABLE IF EXISTS initiatives;
DROP TABLE IF EXISTS departments;

-- 1. Departments Table
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_departments_code ON departments(code);

-- 2. Initiatives Table
CREATE TABLE initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    initiative_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P1',
    owner_department_id INTEGER NOT NULL REFERENCES departments(id),
    budget REAL DEFAULT 0.00,
    target_quarter TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_initiatives_type ON initiatives(initiative_type);
CREATE INDEX idx_initiatives_owner ON initiatives(owner_department_id);

-- 3. SLA Policies Table
CREATE TABLE sla_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    initiative_type TEXT,
    priority TEXT,
    from_department_id INTEGER REFERENCES departments(id),
    to_department_id INTEGER REFERENCES departments(id),
    max_duration_hours REAL NOT NULL,
    warning_threshold_hours REAL NOT NULL,
    breach_penalty_per_hour REAL DEFAULT 150.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sla_initiative_type ON sla_policies(initiative_type);

-- 4. Tickets Table
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_key TEXT NOT NULL UNIQUE,
    initiative_id INTEGER NOT NULL REFERENCES initiatives(id),
    title TEXT NOT NULL,
    ticket_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'P2',
    status TEXT NOT NULL DEFAULT 'OPEN',
    creator_department_id INTEGER NOT NULL REFERENCES departments(id),
    current_department_id INTEGER NOT NULL REFERENCES departments(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    total_duration_hours REAL,
    is_breached INTEGER NOT NULL DEFAULT 0,
    total_breach_hours REAL NOT NULL DEFAULT 0.00
);

CREATE INDEX idx_tickets_key ON tickets(ticket_key);
CREATE INDEX idx_tickets_initiative ON tickets(initiative_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_is_breached ON tickets(is_breached);

-- 5. Workflow Transitions Table
CREATE TABLE workflow_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    transition_seq INTEGER NOT NULL,
    from_department_id INTEGER NOT NULL REFERENCES departments(id),
    to_department_id INTEGER NOT NULL REFERENCES departments(id),
    transitioned_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_hours REAL,
    sla_target_hours REAL NOT NULL DEFAULT 24.00,
    is_breached INTEGER NOT NULL DEFAULT 0,
    breach_hours REAL NOT NULL DEFAULT 0.00,
    is_blocked INTEGER NOT NULL DEFAULT 0,
    blocker_reason TEXT,
    blocked_duration_hours REAL DEFAULT 0.00,
    notes TEXT
);

CREATE INDEX idx_transitions_ticket ON workflow_transitions(ticket_id);
CREATE INDEX idx_transitions_from_to ON workflow_transitions(from_department_id, to_department_id);
CREATE INDEX idx_transitions_dates ON workflow_transitions(transitioned_at, completed_at);
CREATE INDEX idx_transitions_breach ON workflow_transitions(is_breached);

