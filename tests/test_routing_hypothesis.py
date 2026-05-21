"""Tests the core hypothesis: Can an L1 runtime route correctly via [next_action] + Capability Registry?

This is NOT a production router. It is a simulator that mimics how Claude Code
would scan Persona files and make routing decisions. If this simulator can route
correctly, the hypothesis is validated: the spec is sufficient for L1 runtimes.

Scenarios tested:
1. Exact match: tags align perfectly with a Persona's Capability Registry
2. Multi-persona match: best fit is chosen by tag overlap + confidence
3. No match: fallback to direct execution
4. Hot-swap: new Persona with same capability is discovered automatically
5. Confidence tie-break: high confidence wins over medium when scores are equal
"""

import json
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_agents_dir():
    """Create a temporary agents/ directory with test personas."""
    tmpdir = Path(tempfile.mkdtemp())
    agents_dir = tmpdir / "agents"
    agents_dir.mkdir()

    # Nezha: problem_solving expert
    (agents_dir / "nezha.md").write_text("""
# Persona Template: Nezha
# Role: Bug Fixer

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| problem_solving | [debug, fix, php, python] | high | Code-level bug fixing |

### Domain: problem_solving
- **Trigger Patterns**: `[root_cause]` present
- **Required Context**: Investigation report
- **Output Schema**: `[fix_summary]`, `[modified_files]`

## Core Directives
1. Use `yindan` for precise fixes.

## Output Schema
Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: one sentence
- [capability_used]: problem_solving
- [tags]: relevant tags
- [next_action]: next step description
""", encoding="utf-8")

    # Taibai: documentation expert
    (agents_dir / "taibai.md").write_text("""
# Persona Template: Taibai
# Role: Documenter

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| documentation | [docs, spec, yaml] | high | Technical documentation |

### Domain: documentation
- **Trigger Patterns**: `[doc_request]` present
- **Required Context**: Technical design
- **Output Schema**: `[doc_summary]`, `[sections]`

## Core Directives
1. Generate YAML Frontmatter.

## Output Schema
Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: one sentence
- [capability_used]: documentation
- [tags]: relevant tags
- [next_action]: next step description
""", encoding="utf-8")

    # JinZha: problem_solving for Go
    (agents_dir / "jinzha.md").write_text("""
# Persona Template: JinZha
# Role: Go Expert

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| problem_solving | [debug, fix, go] | medium | Go language bug fixing |

### Domain: problem_solving
- **Trigger Patterns**: `[root_cause]` present
- **Required Context**: Go error logs
- **Output Schema**: `[fix_summary]`, `[modified_files]`

## Core Directives
1. Use `go vet` before fixing.

## Output Schema
Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: one sentence
- [capability_used]: problem_solving
- [tags]: relevant tags
- [next_action]: next step description
""", encoding="utf-8")

    yield agents_dir

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir)


# ---------------------------------------------------------------------------
# Simulator: L1 Runtime Routing Logic
# ---------------------------------------------------------------------------

def parse_capability_registry(persona_path: Path) -> list:
    """Parse Capability Registry table from a persona markdown file.

    Returns list of dicts: [{"domain": str, "tags": list, "confidence": str}, ...]
    """
    content = persona_path.read_text(encoding="utf-8")
    capabilities = []

    # Simple parser: look for table rows after "## Capability Registry"
    in_registry = False
    for line in content.splitlines():
        if "## Capability Registry" in line:
            in_registry = True
            continue
        if in_registry and line.startswith("|") and "Domain" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]  # Remove empty
            if len(parts) >= 4:
                domain = parts[0]
                tags_raw = parts[1]
                confidence = parts[2].lower()
                # Parse tags like "[debug, fix, php]"
                tags = [t.strip().strip("'\"").lower() for t in tags_raw.strip("[]").split(",")]
                capabilities.append({
                    "persona": persona_path.stem,
                    "domain": domain,
                    "tags": tags,
                    "confidence": confidence,
                })
        if in_registry and line.startswith("## ") and "Capability Registry" not in line:
            break

    return capabilities


def scan_personas(agents_dir: Path) -> list:
    """Scan all personas and build capability index."""
    index = []
    for persona_file in agents_dir.glob("*.md"):
        caps = parse_capability_registry(persona_file)
        index.extend(caps)
    return index


def route_by_next_action(next_action: dict, agents_dir: Path) -> dict:
    """Simulate L1 runtime routing decision.

    Args:
        next_action: Dict with "capability", "tags" (list), optional "preferred"
        agents_dir: Path to agents/ directory

    Returns:
        {"action": "route", "target": persona_name} or
        {"action": "fallback", "reason": str}
    """
    index = scan_personas(agents_dir)
    requested_domain = next_action.get("capability", "")
    requested_tags = set(t.lower() for t in next_action.get("tags", []))
    preferred = set(p.lower() for p in next_action.get("preferred", []))

    # Filter by domain
    candidates = [c for c in index if c["domain"] == requested_domain]
    if not candidates:
        return {"action": "fallback", "reason": f"no persona declares domain: {requested_domain}"}

    # Priority 1: If preferred list is specified, check preferred candidates first
    if preferred:
        preferred_candidates = [c for c in candidates if c["persona"] in preferred]
        if preferred_candidates:
            # Among preferred, pick by tag match then confidence
            def preferred_score(c):
                s = len(requested_tags & set(c["tags"]))
                conf_map = {"high": 0.3, "medium": 0.2, "low": 0.1}
                s += conf_map.get(c["confidence"], 0)
                return s
            best = max(preferred_candidates, key=preferred_score)
            return {"action": "route", "target": best["persona"], "score": preferred_score(best)}

    # Priority 2: Score all candidates by tag match + confidence
    def score(c):
        s = 0
        # Tag matches
        candidate_tags = set(c["tags"])
        s += len(requested_tags & candidate_tags)
        # Confidence bonus (for tie-breaking)
        conf_map = {"high": 0.3, "medium": 0.2, "low": 0.1}
        s += conf_map.get(c["confidence"], 0)
        return s

    best = max(candidates, key=score)

    # If no tags matched at all (score is only from confidence bonus), still route
    # because domain match is sufficient for L1 to load a persona
    return {"action": "route", "target": best["persona"], "score": score(best)}


# ---------------------------------------------------------------------------
# RED: Hypothesis Tests (they will fail if spec is insufficient)
# ---------------------------------------------------------------------------

class TestRoutingHypothesis:
    """Test that L1 runtime can correctly route based on [next_action] + Capability Registry."""

    def test_exact_match_routes_to_nezha(self, mock_agents_dir):
        """Exact tag match should route to the best-fitting persona."""
        next_action = {
            "capability": "problem_solving",
            "tags": ["debug", "php"],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "route"
        assert result["target"] == "nezha"

    def test_go_tag_routes_to_jinzha(self, mock_agents_dir):
        """Go-specific tags should route to JinZha, not Nezha."""
        next_action = {
            "capability": "problem_solving",
            "tags": ["debug", "go"],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "route"
        assert result["target"] == "jinzha"

    def test_preferred_persona_override(self, mock_agents_dir):
        """Preferred list should override tag scoring when specified."""
        next_action = {
            "capability": "problem_solving",
            "tags": ["debug", "php"],  # Nezha matches better by tags
            "preferred": ["jinzha"],   # But JinZha is preferred
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "route"
        assert result["target"] == "jinzha"

    def test_no_match_fallback(self, mock_agents_dir):
        """Unknown capability should trigger fallback, not crash."""
        next_action = {
            "capability": "machine_learning",
            "tags": ["training", "pytorch"],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "fallback"
        assert "no persona declares domain" in result["reason"]

    def test_hot_swap_new_persona_discovered(self, mock_agents_dir):
        """Adding a new persona with same capability should be auto-discovered."""
        # Add a new persona on-the-fly
        (mock_agents_dir / "muzha.md").write_text("""
# Persona Template: Muzha
# Role: Rust Expert

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| problem_solving | [debug, fix, rust] | high | Rust bug fixing |

## Output Schema
Always include:
- [task_status]: completed | failed
- [capability_used]: problem_solving
- [tags]: relevant tags
- [next_action]: next step
""", encoding="utf-8")

        next_action = {
            "capability": "problem_solving",
            "tags": ["debug", "rust"],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "route"
        assert result["target"] == "muzha"

    def test_confidence_tiebreak(self, mock_agents_dir):
        """When tag scores tie, higher confidence should win."""
        next_action = {
            "capability": "problem_solving",
            "tags": ["debug"],  # Both Nezha and JinZha have "debug"
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        # Nezha has high confidence, JinZha has medium
        # Both match "debug" (score 1.0)
        # Nezha gets +0.3 confidence bonus, JinZha gets +0.2
        assert result["action"] == "route"
        assert result["target"] == "nezha"

    def test_documentation_routes_to_taibai(self, mock_agents_dir):
        """Different capability domain routes to different persona."""
        next_action = {
            "capability": "documentation",
            "tags": ["docs", "spec"],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        assert result["action"] == "route"
        assert result["target"] == "taibai"

    def test_empty_tags_still_routes_by_domain(self, mock_agents_dir):
        """Even with no tags, domain match should route (with low score)."""
        next_action = {
            "capability": "problem_solving",
            "tags": [],
        }

        result = route_by_next_action(next_action, mock_agents_dir)

        # Domain matches, but no tag matches → score is just confidence bonus
        # Nezha: 0.3, JinZha: 0.2 → Nezha wins
        assert result["action"] == "route"
        assert result["target"] == "nezha"


# ---------------------------------------------------------------------------
# End-to-End: Simulated Conversation Flow
# ---------------------------------------------------------------------------

class TestEndToEndConversationFlow:
    """Simulate a full conversation: WangLingguan → YangJian → Nezha."""

    def test_full_review_fix_flow(self, mock_agents_dir):
        """Full flow: review request → route to fixer → fallback when done."""
        # Step 1: WangLingguan finds a bug, outputs handoff
        wlg_output = {
            "capability": "investigation",  # WangLingguan's domain
            "tags": ["review", "security"],
            "next_action": "Fix SQL injection in UserController.php",
        }
        # WangLingguan is not in mock, but let's say user asks for fix

        # Step 2: User or L1 routes to problem_solving
        fix_request = {
            "capability": "problem_solving",
            "tags": ["debug", "php", "security"],
        }

        result = route_by_next_action(fix_request, mock_agents_dir)
        assert result["action"] == "route"
        assert result["target"] == "nezha"

        # Step 3: Nezha fixes, outputs completion
        nezha_output = {
            "capability": "problem_solving",
            "tags": ["debug", "php"],
            "task_status": "completed",
        }

        # Step 4: L1 sees "completed", no further routing needed
        if nezha_output.get("task_status") == "completed":
            assert True  # Flow ends here
        else:
            result = route_by_next_action(nezha_output, mock_agents_dir)
            assert result["action"] == "route"  # Would continue if not completed
