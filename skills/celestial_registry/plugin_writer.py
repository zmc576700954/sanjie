import os
import json

from skills.celestial_registry.loader import discover_skills


def generate_plugin_json(project_root: str = None) -> dict:
    """Generate plugin.json from discovered agents and skills."""
    if project_root is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Discover agents: all .md files in agents/
    agents_dir = os.path.join(project_root, "agents")
    agents = []
    if os.path.isdir(agents_dir):
        for filename in sorted(os.listdir(agents_dir)):
            if filename.endswith(".md"):
                name = filename[:-3]  # strip .md
                agents.append({"name": name, "path": f"agents/{filename}"})

    # Discover skills
    skills_dir = os.path.join(project_root, "skills")
    skill_names = discover_skills(skills_dir)

    # Build mcpServers
    mcp_servers = []
    mcp_servers_dir = os.path.join(project_root, "mcp-servers")
    for skill_name in skill_names:
        server_file = f"{skill_name}_server.py"
        server_path = os.path.join(mcp_servers_dir, server_file)
        if os.path.isfile(server_path):
            args_path = f"mcp-servers/{server_file}"
        else:
            args_path = "mcp-servers/auto_server.py"
        mcp_servers.append({
            "name": f"{skill_name}-server",
            "command": "python",
            "args": [args_path]
        })

    plugin = {
        "name": "sanjie",
        "version": "1.1.0",
        "description": "三界 (Three Realms): A decentralized AI-Native Agent Cluster based on MCP.",
        "agents": agents,
        "mcpServers": mcp_servers,
        "autoDiscover": True,
    }
    return plugin


def write_plugin_json(project_root: str = None) -> None:
    """Write generated plugin.json to the project root."""
    if project_root is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    plugin = generate_plugin_json(project_root)
    output_path = os.path.join(project_root, "plugin.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plugin, f, indent=2, ensure_ascii=False)
