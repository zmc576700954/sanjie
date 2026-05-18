import os

import yaml


def parse_skill_manifest(skill_md_path: str) -> dict:
    """Parse YAML frontmatter from a Skill definition file.

    Args:
        skill_md_path: Path to the SKILL.md file.

    Returns:
        A dict with normalized keys, or None if the file does not exist.
    """
    if not os.path.isfile(skill_md_path):
        return None

    with open(skill_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None

    # Find the closing --- after the opening one
    end_marker = content.find("---", 3)
    if end_marker == -1:
        return None

    frontmatter = content[3:end_marker].strip()
    data = yaml.safe_load(frontmatter) or {}

    return {
        "name": data.get("name"),
        "description": data.get("description"),
        "tools": data.get("tools", []),
        "risk_level": data.get("risk_level", "lowest"),
        "guard_rules": data.get("guard_rules", []),
    }
