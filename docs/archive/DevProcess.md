---
title: Celestial Court Development Process Summary
date: 2025-05-18
status: completed
author: Taibai
---

# Development Process: Celestial Court Architecture

1. **Initial Assessment**: Evaluated the legacy Python-based orchestration (Workflow) and identified it as overly centralized and inflexible.
2. **Architecture Pivot**: Shifted to an Event-Driven/Blackboard Multi-Agent System (MAS). Separated the "Soul" (Agents/Personas like YangJian, Nezha) from the "Body" (Skills/Tools like TianYan, SanJian).
3. **Advanced Integrations**:
   - Researched Xiaohongshu API scraping, leading to the creation of the **Dual-Domain Verification** (Plan A + C Fallback) for TianYan.
   - Researched open-source projects like `hello-agents` to extract advanced principles.
4. **Core Protocols Established**:
   - **GSSC Pipeline**: Formalized memory management.
   - **A2A Handoff**: Standardized JSON-based inter-agent communication.
   - **Evaluator Role**: Added Wang Lingguan for LLM-as-a-Judge formatting audits.
5. **MCP Migration**: Migrated CLI Python scripts to the Model Context Protocol (MCP) using `FastMCP`, starting with Taibai Jinxing. The project is now natively compatible with Claude Code, Cursor, and Gemini CLI.