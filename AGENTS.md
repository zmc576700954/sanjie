# Celestial Court (Agents Cluster)

A decentralized, event-driven multi-agent system for Claude Code, Codex, and Gemini CLI. 

## Architecture
- **South Heaven Gate (Native Router):** Handled natively by the CLI tool's skill routing. Agents are triggered implicitly via keyword matching in the `description` or explicitly via `@agent` / `$agent-name`.
- **Celestial Court (Specialized Agents):** 
    - **YangJian (Investigation):** Deeply researches bugs and generates actionable reports.
    - **Nezha (Execution):** Fast, atomic code modifications.
    - **Taibai Jinxing (Documentation):** Handles changelogs, READMEs, and user communication.
- **Celestial Treasure House (Shared Skills):** Reusable tools (Sanjian, Yindan, etc.) that can be invoked by any agent or the user.

## Getting Started
1. Install the cluster: `python install.py --platform claude-code` (or gemini).
2. Start using specialized agents:
   - `$... yangjian help me find the memory leak`
   - `$... nezha fix the typo in the header`

## Structure
- `skills/`: The unified repository of Agents (`agent_*`) and Tools (`tool_*`).
- `install.py`: Deployment script for platform integration.
