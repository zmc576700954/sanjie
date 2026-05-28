"""Review Ticket Manager - Handles CRUD operations for review tickets.

Tickets are stored as JSON files in a2a_inbox/review_tickets/.
Each ticket has a unique ID and a state lifecycle:
    open -> pending -> verified | reopened
"""

import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


TICKET_DIR = os.path.join("a2a_inbox", "review_tickets")

VALID_STATUSES = {"open", "pending", "verified", "reopened"}
VALID_SEVERITIES = {"Critical", "High", "Warning", "Note", "TODO"}

# Module-level cache for list_tickets performance
_cache: Dict = {
    "mtime": 0.0,
    "tickets": [],
    "ticket_map": {},
}


def clear_cache():
    """Manually invalidate the ticket cache."""
    _cache["mtime"] = 0.0
    _cache["tickets"] = []
    _cache["ticket_map"] = {}


def _is_cache_valid() -> bool:
    """Check if the in-memory cache is still valid based on directory mtime."""
    if not _cache["tickets"]:
        return False
    try:
        current_mtime = os.stat(TICKET_DIR).st_mtime
        return current_mtime == _cache["mtime"]
    except (OSError, FileNotFoundError):
        return False


def _refresh_cache():
    """Rebuild the in-memory cache from disk."""
    tickets = []
    ticket_map = {}
    for filename in sorted(os.listdir(TICKET_DIR)):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(TICKET_DIR, filename), "r", encoding="utf-8") as f:
                ticket = json.load(f)
                tickets.append(ticket)
                ticket_map[ticket.get("ticket_id", "")] = ticket
        except (json.JSONDecodeError, OSError):
            continue
    try:
        _cache["mtime"] = os.stat(TICKET_DIR).st_mtime
    except OSError:
        _cache["mtime"] = 0.0
    _cache["tickets"] = tickets
    _cache["ticket_map"] = ticket_map


# --- Concurrency: write lock + atomic file writes ---

_write_lock = threading.Lock()


def _atomic_write_json(filepath: str, data: Dict):
    """Write JSON atomically: write to a temp file then rename."""
    dir_name = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=dir_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


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
    """Create a new review ticket. Returns the generated ticket_id."""
    _ensure_ticket_dir()
    now = datetime.now(timezone.utc).isoformat()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
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
    with _write_lock:
        _atomic_write_json(_ticket_path(ticket_id), ticket)
        clear_cache()
    return ticket_id


def get_ticket(ticket_id: str) -> Optional[Dict]:
    """Read a ticket by ID. Uses cache for O(1) lookup when available."""
    if _is_cache_valid() and ticket_id in _cache["ticket_map"]:
        return _cache["ticket_map"][ticket_id]
    path = _ticket_path(ticket_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_ticket_status(
    ticket_id: str,
    new_status: str,
    actor: str = "wanglingguan",
    fixed_file: Optional[str] = None,
    verification_result: Optional[Dict] = None,
) -> Dict:
    """Update ticket status and append to history."""
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
    with _write_lock:
        _atomic_write_json(_ticket_path(ticket_id), ticket)
        clear_cache()
    return ticket


def list_tickets(status_filter: Optional[str] = None) -> List[Dict]:
    """List all tickets, optionally filtered by status. Uses in-memory cache."""
    _ensure_ticket_dir()
    if not _is_cache_valid():
        _refresh_cache()
    if status_filter is None:
        return list(_cache["tickets"])
    return [t for t in _cache["tickets"] if t.get("status") == status_filter]


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
        status = t.get("status", "unknown")
        severity = t.get("severity", "unknown")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
        if status == "open":
            summary["open_tickets"].append(t["ticket_id"])
    return summary
