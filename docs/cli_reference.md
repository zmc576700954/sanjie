# CLI Reference

## agents-dev

Multi-tool agent/skill development environment.

```
agents-dev [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help and exit |

### Commands

| Command | Description |
|---------|-------------|
| `create` | Create a new component scaffold |
| `generate` | Generate format files for a component |
| `export` | Export a component to target tool formats |
| `validate` | Validate generated format files |
| `list` | List all components |

---

## create

Create a new component scaffold with directory structure, manifest, and skeleton code.

```
agents-dev create COMPONENT_TYPE NAME [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| COMPONENT_TYPE | Yes | One of: agent, skill, tool, mcp_server |
| NAME | Yes | Component identifier (will be converted to snake_case) |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--description` | `-d` | Auto-generated | Component description |
| `--tools` | `-t` | claude,zcode,cursor,reasionix,mcp | Comma-separated supported tools |
| `--tags` | | (none) | Comma-separated tags |

### Examples

```bash
# Create a basic skill
agents-dev create skill data_analysis

# Create with description
agents-dev create skill data_analysis --description "Data analysis skill"

# Create with custom tools and tags
agents-dev create tool file_utils --tools claude,mcp --tags "files,utils"

# Create an agent
agents-dev create agent code_reviewer --description "Automated code reviewer"

# Create an MCP server
agents-dev create mcp_server search_server
```

### Output

Creates the following structure under `components/<name>/`:

```
<name>/
├── core/
│   ├── __init__.py
│   └── <name>.py      # Skeleton with appropriate base class
├── formats/            # Empty directory
└── manifest.json       # Pre-filled metadata
```

---

## generate

Generate format files for a component using the migration generators.

```
agents-dev generate NAME [TOOLS]...
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | Yes | Component identifier |
| TOOLS | No | Target tools (default: all from manifest) |

### Examples

```bash
# Generate for all supported tools
agents-dev generate my_skill

# Generate for specific tools
agents-dev generate my_skill claude mcp
```

### Output

Writes generated files to `components/<name>/formats/<tool>/` and displays
a results table showing pass/fail status per tool.

---

## export

Export a component to target tool formats (generate + validate + write).

```
agents-dev export NAME [TOOLS]... [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | Yes | Component identifier |
| TOOLS | No | Target tools (default: all from manifest) |

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | Component directory | Output directory |
| `--all` | | False | Export to all supported tools |

### Examples

```bash
# Export to Claude
agents-dev export my_skill claude

# Export to multiple tools
agents-dev export my_skill claude zcode mcp

# Export to a specific directory
agents-dev export my_skill claude --output /path/to/claude/project

# Export to all supported tools
agents-dev export my_skill --all
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All exports passed validation |
| 1 | One or more exports had errors |

---

## validate

Validate existing generated format files for a component.

```
agents-dev validate NAME [TOOLS]...
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| NAME | Yes | Component identifier |
| TOOLS | No | Target tools (default: all from manifest) |

### Examples

```bash
# Validate all formats
agents-dev validate my_skill

# Validate specific tools
agents-dev validate my_skill claude mcp
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | One or more validations failed |

---

## list

List all components in the components/ directory.

```
agents-dev list [COMPONENT_TYPE]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| COMPONENT_TYPE | No | Filter by type: agent, skill, tool, mcp_server |

### Examples

```bash
# List all components
agents-dev list

# List only skills
agents-dev list skill

# List only agents
agents-dev list agent
```

### Output

Displays a formatted table with columns: Name, Type, Version, Description,
Supported Tools.

---

## Common Workflows

### Create and Deploy a Skill

```bash
# 1. Create the component
agents-dev create skill my_skill --description "My custom skill"

# 2. Edit the core implementation
# Edit components/my_skill/core/my_skill.py

# 3. Generate formats
agents-dev generate my_skill

# 4. Validate formats
agents-dev validate my_skill

# 5. Export to Claude
agents-dev export my_skill claude --output ~/.claude/skills/
```

### Create and Deploy an MCP Server

```bash
# 1. Create the component
agents-dev create mcp_server my_server

# 2. Edit the core implementation
# Edit components/my_server/core/my_server.py

# 3. Generate and export MCP format
agents-dev export my_server mcp --output /path/to/mcp/servers/
```

### Migrate a Skill to Multiple Tools

```bash
# 1. Create the skill with multiple tool support
agents-dev create skill universal_skill --tools claude,zcode,mcp

# 2. Implement and generate
agents-dev generate universal_skill

# 3. Validate across all tools
agents-dev validate universal_skill

# 4. Export to each tool separately
agents-dev export universal_skill claude --output /path/to/claude/
agents-dev export universal_skill zcode --output /path/to/zcode/
agents-dev export universal_skill mcp --output /path/to/mcp/
```
