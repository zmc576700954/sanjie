---
name: celestial_registry
description: "Self-discovery tool for the Celestial Court. Scans all installed skills and outputs available tools."
tools:
  - name: check_tools
    script: "scripts/check_tools.py"
---

# Celestial Registry

This skill provides self-discovery capabilities for the Celestial Court. It scans the `skills/` directory to identify all installed skills and their associated tools by parsing their `SKILL.md` files.
