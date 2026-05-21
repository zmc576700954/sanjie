import json
import os
import tempfile

import pytest

from skills.tool_wanglingguan.scripts.ticket_manager import (
    create_ticket,
    get_ticket,
    update_ticket_status,
    list_tickets,
    get_ticket_summary,
    TICKET_DIR,
)


class TestTicketManager:
    def setup_method(self):
        # Use a temp directory for tickets during tests
        self.original_dir = TICKET_DIR

    def teardown_method(self):
        # Cleanup temp tickets
        if os.path.exists(TICKET_DIR):
            for f in os.listdir(TICKET_DIR):
                if f.endswith('.json'):
                    os.remove(os.path.join(TICKET_DIR, f))

    def test_create_ticket(self):
        ticket_id = create_ticket(
            target_agent="yangjian",
            target_file="src/controller.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="Missing null check",
            evidence={"file": "src/controller.py", "line": 42},
            fix_suggestion="Add if (x === null) check",
        )
        assert ticket_id.startswith("WLG-")
        assert os.path.exists(os.path.join(TICKET_DIR, f"{ticket_id}.json"))

    def test_get_ticket(self):
        ticket_id = create_ticket(
            target_agent="taibai",
            target_file="docs/spec.md",
            assertion_type="INFO_EXPOSURE",
            severity="High",
            description="Sensitive data in error message",
            evidence={},
            fix_suggestion="Remove internal URLs from user-facing errors",
        )
        ticket = get_ticket(ticket_id)
        assert ticket is not None
        assert ticket["target_agent"] == "taibai"
        assert ticket["assertion_type"] == "INFO_EXPOSURE"
        assert ticket["status"] == "open"
        assert len(ticket["status_history"]) == 1

    def test_get_ticket_not_found(self):
        ticket = get_ticket("WLG-99999999-999")
        assert ticket is None

    def test_update_ticket_status(self):
        ticket_id = create_ticket(
            target_agent="yangjian",
            target_file="src/app.py",
            assertion_type="INPUT_VALIDATION",
            severity="Warning",
            description="Missing validation",
            evidence={},
            fix_suggestion="Add validation",
        )
        result = update_ticket_status(ticket_id, "pending", actor="yangjian", fixed_file="src/app.py")
        assert result["status"] == "pending"
        assert result["fixed_file"] == "src/app.py"
        assert len(result["status_history"]) == 2

    def test_update_ticket_verified(self):
        ticket_id = create_ticket(
            target_agent="yangjian",
            target_file="src/app.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="Null issue",
            evidence={},
            fix_suggestion="Fix it",
        )
        update_ticket_status(ticket_id, "pending", actor="yangjian")
        result = update_ticket_status(
            ticket_id,
            "verified",
            actor="wanglingguan",
            verification_result={"passed": True, "checks": ["null_handling"]},
        )
        assert result["status"] == "verified"
        assert result["verified_by"] == "wanglingguan"
        assert result["verification_result"]["passed"] is True

    def test_update_ticket_not_found(self):
        result = update_ticket_status("WLG-99999999-999", "verified")
        assert "error" in result

    def test_list_tickets(self):
        create_ticket(
            target_agent="a",
            target_file="f1.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="d1",
            evidence={},
            fix_suggestion="f1",
        )
        create_ticket(
            target_agent="b",
            target_file="f2.py",
            assertion_type="DATA_FLOW",
            severity="High",
            description="d2",
            evidence={},
            fix_suggestion="f2",
        )
        all_tickets = list_tickets()
        assert len(all_tickets) >= 2

    def test_list_tickets_filtered(self):
        tid = create_ticket(
            target_agent="a",
            target_file="f1.py",
            assertion_type="NULL_PATH",
            severity="Critical",
            description="d1",
            evidence={},
            fix_suggestion="f1",
        )
        update_ticket_status(tid, "verified")
        open_tickets = list_tickets(status_filter="open")
        verified_tickets = list_tickets(status_filter="verified")
        assert all(t["status"] == "open" for t in open_tickets)
        assert all(t["status"] == "verified" for t in verified_tickets)

    def test_get_ticket_summary(self):
        # Clear existing tickets first
        if os.path.exists(TICKET_DIR):
            for f in os.listdir(TICKET_DIR):
                if f.endswith('.json'):
                    os.remove(os.path.join(TICKET_DIR, f))

        t1 = create_ticket(
            target_agent="a", target_file="f1.py",
            assertion_type="NULL_PATH", severity="Critical",
            description="d1", evidence={}, fix_suggestion="f1",
        )
        t2 = create_ticket(
            target_agent="b", target_file="f2.py",
            assertion_type="DATA_FLOW", severity="High",
            description="d2", evidence={}, fix_suggestion="f2",
        )
        update_ticket_status(t1, "verified")

        summary = get_ticket_summary()
        assert summary["total"] == 2
        assert summary["by_status"].get("verified", 0) == 1
        assert summary["by_status"].get("open", 0) == 1
        assert summary["by_severity"].get("Critical", 0) == 1
        assert summary["by_severity"].get("High", 0) == 1
        assert len(summary["open_tickets"]) == 1
