"""Review Ticket Manager - Handles CRUD operations for review tickets.

Tickets are stored as JSON files in a2a_inbox/review_tickets/.
Each ticket has a unique ID and a state lifecycle:
    open -> pending -> verified | reopened
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


TICKET_DIR = os.path.join('a2a_inbox', 'review_tickets')

VALID_STATUSES = {"open", "pending", "verified", "reopened"}
VALID_SEVERITIES = {"Critical", "High", "Warning", "Note", "TODO"}


def _ensure_ticket_dir():
    os.makedirs(TICKET_DIR, exist_ok=True)


def _ticket_path(ticket_id: str) -> str:
    return os.path.join(TICKET_DIR, f"{ticket_id}.json")


def create_ticket(
    target_agent: str,
    target_file: str,
    assertion_type: str,
    severity: str,
    description: str,
    evidence: Dict,
    fix_suggestion: str,
    due_date: Optional[str] = None,
) -> str:
    """
    Create a new review ticket.

    Returns:
        The generated ticket_id.
    """
    _ensure_ticket_dir()

    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime('%Y%m%d')

    # Generate unique ID with UUID suffix to avoid race conditions
    ticket_id = f"WLG-{date_str}-{uuid.uuid4().hex[:8].upper()}"

    ticket = {
        "ticket_id": ticket_id,
        "created_at": now,
        "target_agent": target_agent,
        "target_file": target_file,
        "assertion_type": assertion_type,
        "severity": severity,
        "description": description,
        "evidence": evidence,
        "status": "open",
        "status_history": [
            {"status": "open", "timestamp": now, "actor": "wanglingguan"}
        ],
        "fix_suggestion": fix_suggestion,
        "fixed_file": None,
        "verified_by": None,
        "verification_result": None,
        "due_date": due_date,
    }

    with open(_ticket_path(ticket_id), 'w', encoding='utf-8') as f:
        json.dump(ticket, f, indent=2, ensure_ascii=False)

    return ticket_id


def get_ticket(ticket_id: str) -> Optional[Dict]:
    """Read a ticket by ID."""
    path = _ticket_path(ticket_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    actor: str = "wanglingguan",
    fixed_file: Optional[str] = None,
    verification_result: Optional[Dict] = None,
) -> Dict:
    """
    Update ticket status and append to history.

    Args:
        ticket_id: The ticket ID.
        new_status: One of 'open', 'pending', 'verified', 'reopened'.
        actor: Who made the status change.
        fixed_file: Path to the fixed file (for pending status).
        verification_result: Result dict from verification (for verified/reopened).

    Returns:
        Updated ticket dict, or {'error': ...} if not found.
    """
    if new_status not in VALID_STATUSES:
        return {"error": f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}"}

    ticket = get_ticket(ticket_id)
    if ticket is None:
        return {"error": f"Ticket not found: {ticket_id}"}

    now = datetime.now(timezone.utc).isoformat()
    ticket["status"] = new_status
    ticket["status_history"].append({
        "status": new_status,
        "timestamp": now,
        "actor": actor,
    })

    if fixed_file:
        ticket["fixed_file"] = fixed_file

    if verification_result:
        ticket["verification_result"] = verification_result
        ticket["verified_by"] = actor

    with open(_ticket_path(ticket_id), 'w', encoding='utf-8') as f:
        json.dump(ticket, f, indent=2, ensure_ascii=False)

    return ticket


def list_tickets(status_filter: Optional[str] = None) -> List[Dict]:
    """List all tickets, optionally filtered by status."""
    _ensure_ticket_dir()
    tickets = []
    for filename in sorted(os.listdir(TICKET_DIR)):
        if not filename.endswith('.json'):
            continue
        with open(os.path.join(TICKET_DIR, filename), 'r', encoding='utf-8') as f:
            ticket = json.load(f)
            if status_filter is None or ticket.get('status') == status_filter:
                tickets.append(ticket)
    return tickets


def get_ticket_summary() -> Dict:
    """Get aggregate statistics of all tickets."""
    tickets = list_tickets()
    summary = {
        "total": len(tickets),
        "by_status": {},
        "by_severity": {},
        "open_tickets": [],
    }
    for t in tickets:
        status = t.get('status', 'unknown')
        severity = t.get('severity', 'unknown')
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        if status == 'open':
            summary["open_tickets"].append(t["ticket_id"])
    return summary
