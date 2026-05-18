import os

from skills.celestial_registry.skill_manifest import parse_skill_manifest


def discover_skills(skills_dir: str = "skills") -> list[str]:
    """Discover all skill packages by scanning for SKILL.md files."""
    skill_names = []
    if not os.path.isdir(skills_dir):
        return []

    for entry in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, entry)
        skill_md = os.path.join(skill_path, "SKILL.md")
        if os.path.isdir(skill_path) and os.path.isfile(skill_md):
            manifest = parse_skill_manifest(skill_md)
            if manifest and manifest.get("name"):
                skill_names.append(manifest["name"])

    return sorted(skill_names)


def _find_skill_folder(skill_name: str, skills_dir: str = "skills") -> str | None:
    """Find the folder name for a skill by matching its manifest name."""
    if not os.path.isdir(skills_dir):
        return None

    for entry in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, entry)
        skill_md = os.path.join(skill_path, "SKILL.md")
        if os.path.isdir(skill_path) and os.path.isfile(skill_md):
            manifest = parse_skill_manifest(skill_md)
            if manifest and manifest.get("name") == skill_name:
                return entry
    return None


def load_skill_tools(skill_name: str, skills_dir: str = "skills") -> list[dict]:
    """Load tool definitions for a specific skill."""
    folder = _find_skill_folder(skill_name, skills_dir)
    if folder is None:
        return []
    skill_md_path = os.path.join(skills_dir, folder, "SKILL.md")
    manifest = parse_skill_manifest(skill_md_path)
    if manifest is None:
        return []
    return manifest.get("tools", [])
