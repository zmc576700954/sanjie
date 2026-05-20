---
name: wanglingguan
description: >
  Compliance and auditing toolset. Use this to verify if generated documents 
  or agent outputs adhere strictly to the Celestial Architecture formatting rules 
  (YAML Frontmatter for docs, A2A JSON for agent handoffs).
tools:
  - name: format_auditor
    script: "scripts/format_auditor.py"
    parameters:
      file: "Path to the file to audit."
      type: "'document' (checks for YAML frontmatter) or 'handoff' (checks for A2A_ENVELOPE json)."
---

# Compliance & Auditing

You have access to the `format_auditor` tool.
Use this tool to mechanically verify the output of other agents without relying on your own visual estimation.

## Available Audit Types:
- **document**: Ensures the file starts with `---` and contains `title`, `date`, and `status`.
- **handoff**: Ensures the file contains a ````json A2A_ENVELOPE` block that parses as valid JSON and includes `target_agent`.
