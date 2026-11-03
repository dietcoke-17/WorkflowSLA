"""
Unit Tests for Database Models and Schema Integrity
"""
import pytest
from database.connection import get_db_context, init_db
from database.models import Department, Initiative, SLAPolicy, Ticket, WorkflowTransition


def test_database_initialization():
    """Verify that tables can be initialized without errors."""
    init_db()
    with get_db_context() as db:
        # Check departments exist
        depts = db.query(Department).all()
        assert len(depts) >= 4
        dept_codes = {d.code for d in depts}
        assert "OPS" in dept_codes
        assert "CAT" in dept_codes
        assert "SCM" in dept_codes
        assert "CENTRAL" in dept_codes


def test_initiatives_and_sla_policies():
    """Verify initiatives and SLA policies are seeded correctly."""
    with get_db_context() as db:
        inits = db.query(Initiative).all()
        assert len(inits) >= 5
        policies = db.query(SLAPolicy).all()
        assert len(policies) >= 3


def test_ticket_and_transition_counts():
    """Verify that synthetic dataset contains 10,000+ tickets and transitions."""
    with get_db_context() as db:
        ticket_count = db.query(Ticket).count()
        trans_count = db.query(WorkflowTransition).count()
        assert ticket_count >= 10000, f"Expected >= 10,000 tickets, found {ticket_count}"
        assert trans_count >= 20000, f"Expected >= 20,000 transitions, found {trans_count}"

