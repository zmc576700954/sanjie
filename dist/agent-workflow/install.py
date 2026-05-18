"""
Agent Workflow installer.
Copies skills and agent definitions to the appropriate platform directory.

Usage:
    python install.py --platform claude-code [--skills-only] [--agent-only]
    python install.py --platform cursor [--skills-only]
    python install.py --platform codex [--skills-only]
    python install.py --skill sanjian --platform claude-code
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
        "agent_src": os.path.join(SCRIPT_DIR, "platforms", "claude-code", "agents"),
    },
    "cursor": {
        "skills": os.path.expanduser("~/.cursor/skills"),
        "agents": os.path.expanduser("~/.cursor/agents"),
        "agent_src": os.path.join(SCRIPT_DIR, "platforms", "cursor", "agents"),
    },
    "codex": {
        "skills": os.path.expanduser("~/.agents/skills"),
        "agents": None,  # Codex uses root AGENTS.md, not a directory
        "agent_src": os.path.join(SCRIPT_DIR, "platforms", "codex"),
    },
    "trae": {
        "skills": os.path.join(os.getcwd(), ".trae", "skills"),
        "agents": os.path.join(os.getcwd(), ".trae", "rules"),
        "agent_src": os.path.join(SCRIPT_DIR, "platforms", "trae", "rules"),
    },
}


def install_skills(platform: str, skill_name: str = None):
    """Install skills to platform target directory."""
    target_dir = PLATFORM_TARGETS[platform]["skills"]
    os.makedirs(target_dir, exist_ok=True)

    if skill_name:
        src = os.path.join(SKILLS_SRC, skill_name)
        if not os.path.exists(src):
            print(f"Error: Skill '{skill_name}' not found in {SKILLS_SRC}")
            sys.exit(1)
        dst = os.path.join(target_dir, skill_name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Installed skill '{skill_name}' -> {dst}")
    else:
        for name in os.listdir(SKILLS_SRC):
            src = os.path.join(SKILLS_SRC, name)
            if os.path.isdir(src) and os.path.exists(os.path.join(src, "SKILL.md")):
                dst = os.path.join(target_dir, name)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"Installed skill '{name}' -> {dst}")


def install_agent(platform: str):
    """Install agent definition to platform target directory."""
    config = PLATFORM_TARGETS[platform]

    if platform == "codex":
        # Codex: copy AGENTS.md to current working directory
        src = os.path.join(config["agent_src"], "AGENTS.md")
        dst = os.path.join(os.getcwd(), "AGENTS.md")
        shutil.copy2(src, dst)
        print(f"Installed AGENTS.md -> {dst}")
    elif platform == "trae":
        # Trae: copy rules to .trae/rules/
        agent_src = config["agent_src"]
        agent_dst = config["agents"]
        os.makedirs(agent_dst, exist_ok=True)
        for name in os.listdir(agent_src):
            if name.endswith('.md'):
                src = os.path.join(agent_src, name)
                dst = os.path.join(agent_dst, name)
                shutil.copy2(src, dst)
                print(f"Installed rule '{name}' -> {dst}")
    else:
        agent_src = config["agent_src"]
        agent_dst = config["agents"]
        os.makedirs(agent_dst, exist_ok=True)
        for name in os.listdir(agent_src):
            if name.endswith('.md'):
                src = os.path.join(agent_src, name)
                dst = os.path.join(agent_dst, name)
                shutil.copy2(src, dst)
                print(f"Installed agent '{name}' -> {dst}")


def main():
    parser = argparse.ArgumentParser(description="Install Agent Workflow skills and agents")
    parser.add_argument("--platform", required=True, choices=["claude-code", "cursor", "codex", "trae"])
    parser.add_argument("--skill", help="Install a specific skill only")
    parser.add_argument("--skills-only", action="store_true", help="Install skills only, skip agent")
    parser.add_argument("--agent-only", action="store_true", help="Install agent only, skip skills")
    args = parser.parse_args()

    if args.platform not in PLATFORM_TARGETS:
        print(f"Error: Unknown platform '{args.platform}'")
        sys.exit(1)

    if args.skill:
        install_skills(args.platform, args.skill)
    elif args.agent_only:
        install_agent(args.platform)
    elif args.skills_only:
        install_skills(args.platform)
    else:
        install_skills(args.platform)
        install_agent(args.platform)
        print(f"\nInstallation complete for {args.platform}.")


if __name__ == "__main__":
    main()
