from skills.celestial_registry.guard import RiskGuard
from mcp.shared.exceptions import McpError


def test_guard_blocks_scope_exceeded():
    guard = RiskGuard()
    ctx = {"target_files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py", "g.py", "h.py", "i.py", "j.py", "k.py"]}
    params = {"max_files": 10}
    try:
        guard._check_scope(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "Scope exceeded" in str(e)


def test_guard_passes_within_scope():
    guard = RiskGuard()
    ctx = {"target_files": ["a.py", "b.py"]}
    params = {"max_files": 10}
    guard._check_scope(ctx, params)  # Should not raise


def test_guard_blocks_missing_backup_dir():
    guard = RiskGuard()
    ctx = {}
    params = {}
    try:
        guard._check_backup(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "backup_dir" in str(e)


def test_guard_passes_with_backup_dir():
    guard = RiskGuard()
    ctx = {"backup_dir": "/backups"}
    params = {}
    guard._check_backup(ctx, params)  # Should not raise


def test_guard_blocks_missing_rollback_plan():
    guard = RiskGuard()
    ctx = {}
    params = {}
    try:
        guard._check_rollback(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "rollback_plan" in str(e)


def test_guard_passes_with_rollback_plan():
    guard = RiskGuard()
    ctx = {"rollback_plan": "restore from backup"}
    params = {}
    guard._check_rollback(ctx, params)  # Should not raise


def test_guard_blocks_missing_blast_assessment():
    guard = RiskGuard()
    ctx = {}
    params = {}
    try:
        guard._check_blast_assessment(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "blast_assessment" in str(e)


def test_guard_passes_with_blast_assessment():
    guard = RiskGuard()
    ctx = {"blast_assessment": "low"}
    params = {}
    guard._check_blast_assessment(ctx, params)  # Should not raise


def test_guard_blocks_user_approval_false():
    guard = RiskGuard()
    ctx = {"user_approved": False}
    params = {}
    try:
        guard._check_user_approval(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "user_approved" in str(e)


def test_guard_blocks_user_approval_missing():
    guard = RiskGuard()
    ctx = {}
    params = {}
    try:
        guard._check_user_approval(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "user_approved" in str(e)


def test_guard_passes_user_approval_true():
    guard = RiskGuard()
    ctx = {"user_approved": True}
    params = {}
    guard._check_user_approval(ctx, params)  # Should not raise


def test_guard_blocks_missing_destruction_log():
    guard = RiskGuard()
    ctx = {}
    params = {}
    try:
        guard._check_destruction_logging(ctx, params)
        assert False, "Should have raised McpError"
    except McpError as e:
        assert "destruction_log" in str(e)


def test_guard_passes_with_destruction_log():
    guard = RiskGuard()
    ctx = {"destruction_log": "log.txt"}
    params = {}
    guard._check_destruction_logging(ctx, params)  # Should not raise


def test_guard_syntax_validation_is_noop():
    guard = RiskGuard()
    ctx = {}
    params = {}
    guard._check_syntax_validation(ctx, params)  # Should not raise
