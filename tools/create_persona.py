#!/usr/bin/env python3
"""Creator tool for generating new Persona files compliant with Three Realms Protocol.

Usage:
    python tools/create_persona.py --name jinzha --role "Go Expert" --domain problem_solving --tags "debug,fix,go" --confidence high

Output:
    agents/jinzha.md — a new Persona template with standard sections.
"""

import argparse
import sys
from pathlib import Path


PERSONA_TEMPLATE = """# Persona Template: {name}
# Role: {role}

## Capability Registry

| Domain | Tags | Confidence | Description |
|--------|------|------------|-------------|
| {domain} | [{tags}] | {confidence} | {description} |

### Domain: {domain}
- **Trigger Patterns**: {{describe what input signals activate this persona}}
- **Required Context**: {{what data is needed to execute}}
- **Output Schema**: `[task_status]`, `[output_summary]`, `[next_action]`

## Core Directives

1. {{Directive 1: what to value}}
2. {{Directive 2: what to avoid}}
3. {{Directive 3: preferred skills}}

## Output Schema

Always include:
- [task_status]: completed | failed | needs_clarification
- [output_summary]: {{one sentence summary}}
- [capability_used]: {domain}
- [tags]: {{relevant tags from this execution}}

Include when applicable:
- [next_action]: {{description of next step for L1 routing}}
- [deliverables]: {{files modified or created}}
- [tool_calls]: {{skills invoked}}
"""


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Persona template for the Three Realms Protocol."
    )
    parser.add_argument("--name", required=True, help="Persona identifier (lowercase snake_case)")
    parser.add_argument("--role", required=True, help="Human-readable role description")
    parser.add_argument("--domain", required=True, help="Capability domain (e.g., problem_solving)")
    parser.add_argument("--tags", required=True, help="Comma-separated capability tags")
    parser.add_argument(
        "--confidence",
        choices=["high", "medium", "low"],
        default="medium",
        help="Capability confidence level",
    )
    parser.add_argument(
        "--description",
        default="",
        help="One-line capability description (defaults to role)",
    )
    parser.add_argument(
        "--output-dir",
        default="agents",
        help="Output directory for the Persona file (default: agents)",
    )

    args = parser.parse_args()

    # Validate name
    if not args.name.replace("_", "").isalnum():
        print("Error: --name must be lowercase snake_case (alphanumeric + underscores)", file=sys.stderr)
        sys.exit(1)

    # Build description
    description = args.description or args.role

    # Generate content
    content = PERSONA_TEMPLATE.format(
        name=args.name.replace("_", " ").title(),
        role=args.role,
        domain=args.domain,
        tags=", ".join(t.strip() for t in args.tags.split(",")),
        confidence=args.confidence,
        description=description,
    )

    # Write file
    output_path = Path(args.output_dir) / f"{args.name}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"Warning: {output_path} already exists. Overwrite? [y/N]", file=sys.stderr)
        response = input().strip().lower()
        if response != "y":
            print("Aborted.", file=sys.stderr)
            sys.exit(0)

    output_path.write_text(content, encoding="utf-8")
    print(f"Created: {output_path}")
    print(f"\nNext steps:")
    print(f"  1. Edit {output_path} to fill in Core Directives")
    print(f"  2. Add Trigger Patterns and Required Context")
    print(f"  3. Commit the new Persona")


if __name__ == "__main__":
    main()
