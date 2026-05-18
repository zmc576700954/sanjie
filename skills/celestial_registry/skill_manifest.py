import os

import yaml


def parse_skill_manifest(skill_md_path: str) -> dict:
    """Parse YAML frontmatter from a Skill definition file.

    Args:
        skill_md_path: Path to the SKILL.md file.

    Returns:
        A dict with normalized keys (name, description, tools, risk_level,
        guard_rules) or None if the file does not exist.
    """
    if not os.path.exists(skill_md_path):
        return None

    with open(skill_md_path, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}

    # Find the end of frontmatter (second ---)
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}

    frontmatter = content[3:end_idx].strip()
    data = yaml.safe_load(frontmatter) or {}

    return {
        "name": data.get("name"),
        "description": data.get("description"),
        "tools": data.get("tools", []),
        "risk_level": data.get("risk_level", "lowest"),
        "guard_rules": data.get("guard_rules", []),
    }
