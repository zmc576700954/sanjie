import os

from mcp.shared.exceptions import McpError
from mcp.types import INVALID_PARAMS, ErrorData

from skills.celestial_registry.skill_manifest import parse_skill_manifest


class RiskGuard:
    """Declarative risk guard layer that validates skill invocations based on
    declared rules in SKILL.md manifests.
    """

    def __init__(self):
        self._guards = {
            "scope_guardian": self._check_scope,
            "backup": self._check_backup,
            "syntax_validation": self._check_syntax_validation,
            "rollback": self._check_rollback,
            "blast_assessment": self._check_blast_assessment,
            "user_approval": self._check_user_approval,
            "destruction_logging": self._check_destruction_logging,
        }

    def validate(self, skill_name: str, invocation_context: dict) -> None:
        """Validate a skill invocation against its declared guard rules.

        Args:
            skill_name: Name of the skill to validate.
            invocation_context: Context dict passed to the skill invocation.

        Raises:
            McpError: If any required guard rule fails.
        """
        skill_md_path = f"skills/tool_{skill_name}/SKILL.md"
        if not os.path.isfile(skill_md_path):
            # Fallback for non-tool skills (agents, etc.)
            skill_md_path = f"skills/agent_{skill_name}/SKILL.md"
        if not os.path.isfile(skill_md_path):
            skill_md_path = f"skills/{skill_name}/SKILL.md"

        manifest = parse_skill_manifest(skill_md_path)
        if manifest is None:
            return

        guard_rules = manifest.get("guard_rules", [])
        for rule in guard_rules:
            if not rule.get("required", False):
                continue
            guard_name = rule.get("name")
            parameters = rule.get("parameters", {})
            guard_fn = self._guards.get(guard_name)
            if guard_fn is not None:
                guard_fn(invocation_context, parameters)

    def _check_scope(self, ctx: dict, params: dict) -> None:
        """Check that the number of target files does not exceed max_files."""
        max_files = params.get("max_files")
        if max_files is None:
            return
        target_files = ctx.get("target_files", [])
        if len(target_files) > max_files:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message=f"Scope exceeded: {len(target_files)} files (max {max_files})",
                )
            )

    def _check_backup(self, ctx: dict, params: dict) -> None:
        """Check that backup_dir exists in the invocation context."""
        if "backup_dir" not in ctx:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Missing required context: backup_dir",
                )
            )

    def _check_syntax_validation(self, ctx: dict, params: dict) -> None:
        """No-op: syntax validation is handled by the skill itself."""
        pass

    def _check_rollback(self, ctx: dict, params: dict) -> None:
        """Check that rollback_plan exists in the invocation context."""
        if "rollback_plan" not in ctx:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Missing required context: rollback_plan",
                )
            )

    def _check_blast_assessment(self, ctx: dict, params: dict) -> None:
        """Check that blast_assessment exists in the invocation context."""
        if "blast_assessment" not in ctx:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Missing required context: blast_assessment",
                )
            )

    def _check_user_approval(self, ctx: dict, params: dict) -> None:
        """Check that user_approved is True in the invocation context."""
        if not ctx.get("user_approved", False):
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Missing required context: user_approved must be True",
                )
            )

    def _check_destruction_logging(self, ctx: dict, params: dict) -> None:
        """Check that destruction_log exists in the invocation context."""
        if "destruction_log" not in ctx:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Missing required context: destruction_log",
                )
            )
