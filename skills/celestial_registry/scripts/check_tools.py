import os
import yaml
import json
from typing import List, Dict

def check_tools(skills_dir: str = None) -> str:
    """
    Scan the skills directory and extract tool metadata from SKILL.md files.
    
    Args:
        skills_dir: Path to the skills directory. Defaults to the parent of this script's directory.
        
    Returns:
        JSON string containing the list of all available tools across all skills.
    """
    if not skills_dir:
        # Assume we are in skills/celestial_registry/scripts/
        skills_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    registry = []
    
    if not os.path.exists(skills_dir):
        return json.dumps({"error": f"Skills directory not found: {skills_dir}"})

    for item in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, item)
        if os.path.isdir(skill_path):
            skill_md_path = os.path.join(skill_path, "SKILL.md")
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract frontmatter
                        if content.startswith('---'):
                            parts = content.split('---')
                            if len(parts) >= 3:
                                metadata = yaml.safe_load(parts[1])
                                if metadata:
                                    registry.append({
                                        "skill_name": metadata.get("name"),
                                        "description": metadata.get("description"),
                                        "tools": metadata.get("tools", [])
                                    })
                except Exception as e:
                    # Skip files that can't be parsed
                    continue
                    
    return json.dumps(registry, indent=2)

if __name__ == "__main__":
    print(check_tools())
