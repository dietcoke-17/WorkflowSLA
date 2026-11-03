"""
WorkflowSLA: Synthetic Dataset Generator
Generates 10,000+ synthetic workflow tickets and 30,000+ inter-departmental
transitions simulating Jira/ServiceNow ticketing logs across Operations,
Category, Supply Chain, and Central departments.

Models real-world cross-functional friction with top 3 bottleneck handoffs
responsible for ~80% of SLA breach delays:
  1. Category -> Supply Chain (Vendor specifications, manual approvals)
  2. Supply Chain -> Operations (Warehouse receiving backlogs, dock congestion)
  3. Central -> Category (Compliance KYC, legal verification stalls)
"""
import sys
import os
import random
from pathlib import Path
from datetime import datetime, timedelta

# Ensure root and vendor directory are in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

from faker import Faker
from database.connection import get_db_context, init_db, engine
from database.models import Department, Initiative, SLAPolicy, Ticket, WorkflowTransition

fake = Faker()
Faker.seed(42)
random.seed(42)

# Department definitions
DEPARTMENTS_DATA = [
    {"code": "CAT", "name": "Category Management", "description": "Vendor management, merchandising, catalog onboarding, pricing"},
    {"code": "SCM", "name": "Supply Chain & Logistics", "description": "Fulfillment centers, cross-docking, line haul, 3PL logistics"},
    {"code": "OPS", "name": "Operations", "description": "Warehouse hub operations, picking, packing, quality control & dispatch"},
    {"code": "CENTRAL", "name": "Central Operations & Compliance", "description": "Vendor KYC, legal compliance, risk audits, policies"},
    {"code": "TECH", "name": "Tech & Systems", "description": "WMS, OMS, ERP integrations, automated pipeline services"},
    {"code": "FIN", "name": "Finance & Invoicing", "description": "Commercial reconciliation, vendor payouts, credit clearing"},
]

# Strategic Initiatives
INITIATIVES_DATA = [
    {
        "code": "INIT-CAT-ONBOARD",
        "name": "Q1 Tier-1 Vendor Onboarding Acceleration",
        "initiative_type": "Catalog Onboarding",
        "priority": "P1",
        "dept_code": "CAT",
        "budget": 2500000.0,
        "target_quarter": "2024-Q1",
        "status": "ACTIVE"
    },
    {
        "code": "INIT-SCM-CROSSDOCK",
        "name": "National Cross-Docking & Linehaul Route Optimization",
        "initiative_type": "Cross-Docking Logistics",
        "priority": "P0",
        "dept_code": "SCM",
        "budget": 5000000.0,
        "target_quarter": "2024-Q1",
        "status": "ACTIVE"
    },
    {
        "code": "INIT-CENTRAL-KYC",
        "name": "Automated Vendor KYC & Compliance Verification",
        "initiative_type": "Vendor KYC & Compliance",
        "priority": "P2",
        "dept_code": "CENTRAL",
        "budget": 1200000.0,
        "target_quarter": "2024-Q2",
        "status": "ACTIVE"
    },
    {
        "code": "INIT-OPS-WMS",
        "name": "Warehouse Capacity Rebalancing & Inbound Dock SLA",
        "initiative_type": "Inventory Rebalancing",
        "priority": "P1",
        "dept_code": "OPS",
        "budget": 3400000.0,
        "target_quarter": "2024-Q2",
        "status": "ACTIVE"
    },
    {
        "code": "INIT-TECH-RETURNS",
        "name": "High-Velocity Reverse Logistics & Returns Processing",
        "initiative_type": "Returns Processing",
        "priority": "P2",
        "dept_code": "TECH",
        "budget": 1800000.0,
        "target_quarter": "2024-Q3",
        "status": "ACTIVE"
    },
    {
        "code": "INIT-OPS-SAME-DAY",
        "name": "Metro Express Same-Day Dispatch SLA Enhancement",
        "initiative_type": "Express Fulfillment",
        "priority": "P0",
        "dept_code": "OPS",
        "budget": 4200000.0,
        "target_quarter": "2024-Q3",
        "status": "ACTIVE"
    }
]

# Friction profiles for department transitions
# (Breach probability, average delay hours multiplier, common blocker reasons)
FRICTION_PROFILES = {
    # TOP BOTTLENECK 1: Category -> Supply Chain (Major friction: ~44% breach probability, heavy delays)
    ("CAT", "SCM"): {
        "breach_prob": 0.44,
        "sla_target_hours": 24.0,
        "mean_delay_hours": 36.5,
        "blockers": [
            "Vendor master data incomplete",
            "Manual approval required for oversize/hazmat SKU",
            "Missing packaging specifications & barcode mapping",
            "Supplier lead time mismatch with warehouse dock calendar"
        ]
    },
    # TOP BOTTLENECK 2: Supply Chain -> Operations (Major friction: ~38% breach probability, dock delays)
    ("SCM", "OPS"): {
        "breach_prob": 0.38,
        "sla_target_hours": 18.0,
        "mean_delay_hours": 28.0,
        "blockers": [
            "Warehouse inbound receiving dock congestion",
            "Inbound pallet count discrepancy vs advance ship notice",
            "Storage zone capacity saturation in primary FC",
            "Forklift inspection & labor shift handover backlog"
        ]
    },
    # TOP BOTTLENECK 3: Central -> Category (Major friction: ~32% breach probability, compliance stalls)
    ("CENTRAL", "CAT"): {
        "breach_prob": 0.32,
        "sla_target_hours": 20.0,
        "mean_delay_hours": 26.0,
        "blockers": [
            "Vendor GST/Tax certification verification pending",
            "Legal contract clause review escalation",
            "Background audit flagged entity ownership mismatch",
            "Central policy risk sign-off delay"
        ]
    },
    # Standard smooth transitions (low breach rate ~6% - 12%)
    ("OPS", "SCM"): {
        "breach_prob": 0.08,
        "sla_target_hours": 12.0,
        "mean_delay_hours": 11.0,
        "blockers": ["Linehaul driver check-in delay", "Dispatch bay staging full"]
    },
    ("OPS", "CENTRAL"): {
        "breach_prob": 0.06,
        "sla_target_hours": 24.0,
        "mean_delay_hours": 14.0,
        "blockers": ["Periodic compliance sample audit"]
    },
    ("CAT", "CENTRAL"): {
        "breach_prob": 0.10,
        "sla_target_hours": 16.0,
        "mean_delay_hours": 12.5,
        "blockers": ["Brand authorization trademark check"]
    },
    ("SCM", "CENTRAL"): {
        "breach_prob": 0.07,
        "sla_target_hours": 18.0,
        "mean_delay_hours": 13.0,
        "blockers": ["Customs manifest document mismatch"]
    },
    ("TECH", "OPS"): {
        "breach_prob": 0.09,
        "sla_target_hours": 8.0,
        "mean_delay_hours": 7.0,
        "blockers": ["Handheld scanner firmware sync timeout"]
    },
    ("OPS", "FIN"): {
        "breach_prob": 0.08,
        "sla_target_hours": 24.0,
        "mean_delay_hours": 15.0,
        "blockers": ["Invoice amount variance vs physical received qty"]
    },
    ("FIN", "OPS"): {
        "breach_prob": 0.07,
        "sla_target_hours": 12.0,
        "mean_delay_hours": 9.5,
        "blockers": ["Credit hold release queue"]
    }
}

# Typical departmental handoff pathways for realistic tickets
HANDOFF_PATHWAYS = [
    # Pathway A: New Vendor SKU Onboarding (Central -> Cat -> SCM -> Ops)
    ["CENTRAL", "CAT", "SCM", "OPS"],
    # Pathway B: Cross-Dock Fast Track (Cat -> SCM -> Ops)
    ["CAT", "SCM", "OPS"],
    # Pathway C: Inbound Rebalancing (SCM -> Ops -> SCM)
    ["SCM", "OPS", "SCM"],
    # Pathway D: Compliance & Verification (Cat -> Central -> Cat -> SCM)
    ["CAT", "CENTRAL", "CAT", "SCM"],
    # Pathway E: Warehouse Audit & Dispatch (Ops -> SCM -> Ops)
    ["OPS", "SCM", "OPS"],
    # Pathway F: Finance Reconcile & Settlement (Ops -> FIN -> Ops)
    ["OPS", "FIN", "OPS"],
]

TICKET_TYPES = [
    "Vendor Approval Request",
    "High-Priority SKU Ingestion",
    "Linehaul Cross-Dock Transfer",
    "Inbound Receiving Discrepancy",
    "Warehouse Slotting Allocation",
    "Compliance Audit Clearance",
    "Bulk Inventory Rebalancing",
    "Express Fulfillment Escalation",
    "Return Authorization Triage",
    "Barcode Verification Review"
]


def seed_departments_and_policies(db):
    """Inserts initial normalized departments, initiatives, and SLA policies."""
    print("-> Seeding Departments...")
    dept_map = {}
    for data in DEPARTMENTS_DATA:
        existing = db.query(Department).filter_by(code=data["code"]).first()
        if not existing:
            dept = Department(
                code=data["code"],
                name=data["name"],
                description=data["description"],
                active=True
            )
            db.add(dept)
            db.flush()
            dept_map[data["code"]] = dept.id
        else:
            dept_map[data["code"]] = existing.id

    print("-> Seeding Initiatives...")
    init_map = {}
    for idata in INITIATIVES_DATA:
        existing = db.query(Initiative).filter_by(code=idata["code"]).first()
        if not existing:
            init = Initiative(
                code=idata["code"],
                name=idata["name"],
                initiative_type=idata["initiative_type"],
                priority=idata["priority"],
                owner_department_id=dept_map[idata["dept_code"]],
                budget=idata["budget"],
                target_quarter=idata["target_quarter"],
                status=idata["status"]
            )
            db.add(init)
            db.flush()
            init_map[idata["code"]] = init.id
        else:
            init_map[idata["code"]] = existing.id

    print("-> Seeding SLA Policies...")
    for (from_code, to_code), profile in FRICTION_PROFILES.items():
        if from_code in dept_map and to_code in dept_map:
            policy_name = f"SLA-{from_code}->{to_code}"
            existing = db.query(SLAPolicy).filter_by(policy_name=policy_name).first()
            if not existing:
                sla = SLAPolicy(
                    policy_name=policy_name,
                    from_department_id=dept_map[from_code],
                    to_department_id=dept_map[to_code],
                    max_duration_hours=profile["sla_target_hours"],
                    warning_threshold_hours=profile["sla_target_hours"] * 0.75,
                    breach_penalty_per_hour=175.0
                )
                db.add(sla)

    db.commit()
    return dept_map, init_map


def generate_synthetic_dataset(target_ticket_count=10000, days_back=90):
    """
    Generates target_ticket_count (default 10,000+) tickets and corresponding
    inter-departmental transitions.
    """
    init_db()
    with get_db_context() as db:
        dept_map, init_map = seed_departments_and_policies(db)

        # Clear existing tickets & transitions for fresh seed if requested
        print(f"-> Generating {target_ticket_count:,} tickets & ~30,000+ transitions...")

        initiative_ids = list(init_map.values())
        base_start_time = datetime.utcnow() - timedelta(days=days_back)

        tickets_to_insert = []
        transitions_to_insert = []

        ticket_id_counter = 1
        # Check existing max id if any
        max_ticket_id = db.query(Ticket.id).order_by(Ticket.id.desc()).first()
        if max_ticket_id:
            ticket_id_counter = max_ticket_id[0] + 1

        priorities = ["P0", "P1", "P2", "P3"]
        priority_weights = [0.15, 0.40, 0.35, 0.10]

        for i in range(target_ticket_count):
            ticket_id = ticket_id_counter + i
            ticket_key = f"WSLA-{100000 + ticket_id}"
            init_id = random.choice(initiative_ids)
            priority = random.choices(priorities, weights=priority_weights)[0]
            ticket_type = random.choice(TICKET_TYPES)

            # Ticket creation time randomly spread over past days_back days
            created_offset_hours = random.uniform(0, days_back * 24 - 48)
            created_at = base_start_time + timedelta(hours=created_offset_hours)

            # Choose handoff pathway
            pathway = random.choice(HANDOFF_PATHWAYS)
            creator_dept_code = pathway[0]
            creator_dept_id = dept_map[creator_dept_code]

            current_cursor_time = created_at
            ticket_transitions = []
            ticket_is_breached = False
            total_ticket_breach_hours = 0.0

            # Build transitions along the pathway
            for seq, (from_code, to_code) in enumerate(zip(pathway[:-1], pathway[1:]), start=1):
                from_id = dept_map[from_code]
                to_id = dept_map[to_code]

                pair_key = (from_code, to_code)
                profile = FRICTION_PROFILES.get(
                    pair_key,
                    {
                        "breach_prob": 0.10,
                        "sla_target_hours": 24.0,
                        "mean_delay_hours": 15.0,
                        "blockers": ["Generic coordination delay", "Awaiting stakeholder input"]
                    }
                )

                sla_target = profile["sla_target_hours"]
                # Determine if this transition breaches
                will_breach = random.random() < profile["breach_prob"]

                if will_breach:
                    # Duration exceeds SLA
                    excess_hours = random.expovariate(1.0 / max(profile["mean_delay_hours"] - sla_target, 4.0))
                    duration_hours = round(sla_target + excess_hours + random.uniform(1.0, 12.0), 2)
                    is_breached = True
                    breach_hours = round(duration_hours - sla_target, 2)
                    ticket_is_breached = True
                    total_ticket_breach_hours += breach_hours
                    is_blocked = True
                    blocker_reason = random.choice(profile["blockers"])
                    blocked_duration_hours = round(breach_hours * random.uniform(0.6, 0.95), 2)
                else:
                    # Completed comfortably within SLA
                    duration_hours = round(random.uniform(2.0, sla_target * 0.90), 2)
                    is_breached = False
                    breach_hours = 0.0
                    is_blocked = random.random() < 0.05
                    blocker_reason = "Brief verification queue" if is_blocked else None
                    blocked_duration_hours = round(random.uniform(0.5, 2.0), 2) if is_blocked else 0.0

                trans_start = current_cursor_time
                trans_end = trans_start + timedelta(hours=duration_hours)
                current_cursor_time = trans_end

                transitions_to_insert.append({
                    "ticket_id": ticket_id,
                    "transition_seq": seq,
                    "from_department_id": from_id,
                    "to_department_id": to_id,
                    "transitioned_at": trans_start,
                    "completed_at": trans_end,
                    "duration_hours": duration_hours,
                    "sla_target_hours": sla_target,
                    "is_breached": is_breached,
                    "breach_hours": breach_hours,
                    "is_blocked": is_blocked,
                    "blocker_reason": blocker_reason,
                    "blocked_duration_hours": blocked_duration_hours,
                    "notes": f"Automated workflow audit log for transition {from_code} -> {to_code}."
                })

            resolved_at = current_cursor_time
            total_duration_hours = round((resolved_at - created_at).total_seconds() / 3600.0, 2)
            current_dept_id = dept_map[pathway[-1]]

            # Determine ticket status
            status = "RESOLVED" if random.random() < 0.92 else "IN_PROGRESS"
            if status == "IN_PROGRESS":
                resolved_at = None

            tickets_to_insert.append({
                "id": ticket_id,
                "ticket_key": ticket_key,
                "initiative_id": init_id,
                "title": f"[{priority}] {ticket_type} #{ticket_id} ({creator_dept_code}->{pathway[-1]})",
                "ticket_type": ticket_type,
                "priority": priority,
                "status": status,
                "creator_department_id": creator_dept_id,
                "current_department_id": current_dept_id,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "total_duration_hours": total_duration_hours if resolved_at else None,
                "is_breached": ticket_is_breached,
                "total_breach_hours": round(total_ticket_breach_hours, 2)
            })

            # Batch insert every 2,500 tickets to keep memory low and performance blazing fast
            if len(tickets_to_insert) >= 2500:
                print(f"   ...committing batch of {len(tickets_to_insert)} tickets and {len(transitions_to_insert)} transitions...")
                db.bulk_insert_mappings(Ticket, tickets_to_insert)
                db.bulk_insert_mappings(WorkflowTransition, transitions_to_insert)
                db.commit()
                tickets_to_insert = []
                transitions_to_insert = []

        # Flush any remaining items
        if tickets_to_insert:
            print(f"   ...committing final batch of {len(tickets_to_insert)} tickets and {len(transitions_to_insert)} transitions...")
            db.bulk_insert_mappings(Ticket, tickets_to_insert)
            db.bulk_insert_mappings(WorkflowTransition, transitions_to_insert)
            db.commit()

        # Count total records in database
        total_tickets = db.query(Ticket).count()
        total_transitions = db.query(WorkflowTransition).count()
        total_breaches = db.query(WorkflowTransition).filter_by(is_breached=True).count()
        print(f"\n=======================================================")
        print(f" Synthetic Dataset Generation Complete!")
        print(f"  Total Tickets:      {total_tickets:,}")
        print(f"  Total Transitions:  {total_transitions:,}")
        print(f"  Total SLA Breaches: {total_breaches:,}")
        print(f"=======================================================\n")
        return total_tickets, total_transitions


if __name__ == "__main__":
    generate_synthetic_dataset(target_ticket_count=10000)
