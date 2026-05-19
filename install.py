"""
Agent Workflow installer.
Copies skills and agent definitions to the appropriate platform directory.

Usage:
    python install.py --platform claude-code
    python install.py --platform gemini
    python install.py --skill tool_sanjian --platform claude-code
"""
import argparse
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_SRC = os.path.join(SCRIPT_DIR, "skills")

PLATFORM_TARGETS = {
    "claude-code": {
        "skills": os.path.expanduser("~/.claude/skills"),
        "agents": os.path.expanduser("~/.claude/agents"),
    },
    "cursor": {
        "skills": os.path.expanduser("~/.cursor/skills"),
        "agents": os.path.expanduser("~/.cursor/agents"),
    },
    "codex": {
        "skills": os.path.expanduser("~/.agents/skills"),
        "agents": None,
    },
    "gemini": {
        "skills": os.path.expanduser("~/.agents/skills"),
        "agents": None,
    },
    "trae": {
        "skills": os.path.join(os.getcwd(), ".trae", "skills"),
        "agents": os.path.join(os.getcwd(), ".trae", "rules"),
    },
}


def install_skills(platform: str, skill_name: str | None = None):
    """Install skills and agents to platform target directory."""
    config = PLATFORM_TARGETS[platform]
    skills_target = config["skills"]
    os.makedirs(skills_target, exist_ok=True)

    # 1. Install skills from skills/ directory
    if skill_name:
        src = os.path.join(SKILLS_SRC, skill_name)
        if not os.path.exists(src):
            print(f"Error: Skill '{skill_name}' not found in {SKILLS_SRC}")
            sys.exit(1)
        dst = os.path.join(skills_target, skill_name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Installed skill '{skill_name}' -> {dst}")
    else:
        # Install all skills in the skills directory
        for name in os.listdir(SKILLS_SRC):
            src = os.path.join(SKILLS_SRC, name)
            if os.path.isdir(src) and os.path.exists(os.path.join(src, "SKILL.md")):
                dst = os.path.join(skills_target, name)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"Installed skill package '{name}' -> {dst}")

    # 2. Install agent personas from root agents/ directory
    if config["agents"]:
        agents_src = os.path.join(SCRIPT_DIR, "agents")
        if os.path.exists(agents_src):
            agents_target = config["agents"]
            os.makedirs(agents_target, exist_ok=True)
            for name in os.listdir(agents_src):
                if name.endswith(".md"):
                    src = os.path.join(agents_src, name)
                    dst = os.path.join(agents_target, name)
                    shutil.copy2(src, dst)
                    print(f"Installed agent persona '{name}' -> {dst}")


def main():
    parser = argparse.ArgumentParser(description="Install Agent Workflow skills and agents")
    parser.add_argument("--platform", required=True, choices=["claude-code", "cursor", "codex", "gemini", "trae"])
    parser.add_argument("--skill", help="Install a specific skill only")
    args = parser.parse_args()

    if args.skill:
        install_skills(args.platform, args.skill)
    else:
        install_skills(args.platform)
        print(f"\nInstallation complete for {args.platform}.")


if __name__ == "__main__":
    main()
