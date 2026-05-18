"""Scan installed skills and extract profiles."""


def scan_skills(skill_library) -> dict:
    """
    Scan all registered skills and extract their profiles.

    Args:
        skill_library: SkillLibrary instance with get_all_skills()

    Returns:
        {total_skills, skill_profiles: [{name, description, tools}]}
    """
    all_skills = skill_library.get_all_skills()
    profiles = []

    for skill in all_skills:
        # Skip the router itself to avoid circular routing
        if "bajiu" in skill.name.lower() or "router" in skill.name.lower():
            continue
        tools = skill.get_tools()
        profiles.append({
            "name": skill.name,
            "description": skill.description,
            "tools": [t.name for t in tools],
        })

    return {
        "total_skills": len(profiles),
        "skill_profiles": profiles,
    }
