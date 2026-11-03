"""
WorkflowSLA: Normalized Relational Database Models
Models cross-functional initiatives, departments, SLA policies,
tickets (simulating Jira/ServiceNow), and inter-departmental workflow transitions.
"""
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Numeric, Index
)
from sqlalchemy.orm import relationship
from database.connection import Base


class Department(Base):
    """
    Normalized Department table.
    Core departments: Operations, Category, Supply Chain, Central, Tech, Support.
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    owned_initiatives = relationship("Initiative", back_populates="owner_department")
    transitions_from = relationship(
        "WorkflowTransition",
        foreign_keys="WorkflowTransition.from_department_id",
        back_populates="from_department"
    )
    transitions_to = relationship(
        "WorkflowTransition",
        foreign_keys="WorkflowTransition.to_department_id",
        back_populates="to_department"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Initiative(Base):
    """
    Cross-functional business initiatives driving internal ticketing workflows.
    (e.g., Catalog Onboarding, Logistics Hub Expansion, Vendor KYC, Returns Automation)
    """
    __tablename__ = "initiatives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    initiative_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(10), default="P1", nullable=False)
    owner_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    budget = Column(Numeric(14, 2), default=0.0)
    target_quarter = Column(String(10), nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    owner_department = relationship("Department", back_populates="owned_initiatives")
    tickets = relationship("Ticket", back_populates="initiative", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "initiative_type": self.initiative_type,
            "priority": self.priority,
            "owner_department_id": self.owner_department_id,
            "budget": float(self.budget) if self.budget else 0.0,
            "target_quarter": self.target_quarter,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SLAPolicy(Base):
    """
    SLA Policies defining targeted completion thresholds and breach boundaries
    by department pair, initiative type, or ticket priority.
    """
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_name = Column(String(100), nullable=False)
    initiative_type = Column(String(50), nullable=True, index=True)
    priority = Column(String(10), nullable=True)
    from_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    max_duration_hours = Column(Float, nullable=False)  # SLA limit before breach
    warning_threshold_hours = Column(Float, nullable=False)  # Early warning
    breach_penalty_per_hour = Column(Float, default=150.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "policy_name": self.policy_name,
            "initiative_type": self.initiative_type,
            "priority": self.priority,
            "from_department_id": self.from_department_id,
            "to_department_id": self.to_department_id,
            "max_duration_hours": self.max_duration_hours,
            "warning_threshold_hours": self.warning_threshold_hours,
            "breach_penalty_per_hour": self.breach_penalty_per_hour
        }


class Ticket(Base):
    """
    Synthetic workflow support and operations tickets simulating Jira / ServiceNow records.
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_key = Column(String(32), unique=True, nullable=False, index=True)
    initiative_id = Column(Integer, ForeignKey("initiatives.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    ticket_type = Column(String(50), nullable=False)
    priority = Column(String(10), default="P2", nullable=False, index=True)
    status = Column(String(30), default="OPEN", nullable=False, index=True)
    creator_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    current_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    total_duration_hours = Column(Float, nullable=True)
    is_breached = Column(Boolean, default=False, nullable=False, index=True)
    total_breach_hours = Column(Float, default=0.0, nullable=False)

    # Relationships
    initiative = relationship("Initiative", back_populates="tickets")
    transitions = relationship(
        "WorkflowTransition",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="WorkflowTransition.transition_seq"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_key": self.ticket_key,
            "initiative_id": self.initiative_id,
            "title": self.title,
            "ticket_type": self.ticket_type,
            "priority": self.priority,
            "status": self.status,
            "creator_department_id": self.creator_department_id,
            "current_department_id": self.current_department_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "total_duration_hours": self.total_duration_hours,
            "is_breached": self.is_breached,
            "total_breach_hours": self.total_breach_hours
        }


class WorkflowTransition(Base):
    """
    Inter-departmental handoffs and transitions tracking workflow progression,
    handoff timestamps, durations, blockers, and SLA breaches.
    """
    __tablename__ = "workflow_transitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    transition_seq = Column(Integer, nullable=False)  # Handoff index (1, 2, 3...)
    from_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    transitioned_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    duration_hours = Column(Float, nullable=True)
    sla_target_hours = Column(Float, nullable=False, default=24.0)
    is_breached = Column(Boolean, default=False, nullable=False, index=True)
    breach_hours = Column(Float, default=0.0, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocker_reason = Column(String(120), nullable=True)
    blocked_duration_hours = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="transitions")
    from_department = relationship(
        "Department",
        foreign_keys=[from_department_id],
        back_populates="transitions_from"
    )
    to_department = relationship(
        "Department",
        foreign_keys=[to_department_id],
        back_populates="transitions_to"
    )

    __table_args__ = (
        Index("idx_handoff_pair", "from_department_id", "to_department_id"),
        Index("idx_ticket_seq", "ticket_id", "transition_seq"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "transition_seq": self.transition_seq,
            "from_department_id": self.from_department_id,
            "to_department_id": self.to_department_id,
            "transitioned_at": self.transitioned_at.isoformat() if self.transitioned_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_hours": self.duration_hours,
            "sla_target_hours": self.sla_target_hours,
            "is_breached": self.is_breached,
            "breach_hours": self.breach_hours,
            "is_blocked": self.is_blocked,
            "blocker_reason": self.blocker_reason,
            "blocked_duration_hours": self.blocked_duration_hours
        }

