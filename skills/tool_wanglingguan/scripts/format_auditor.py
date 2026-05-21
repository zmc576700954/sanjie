import argparse
import json
import os
import re
from typing import Dict, List, Optional

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Module-level compiled patterns for performance
_YAML_FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
_A2A_ENVELOPE_RE = re.compile(r'```json\s+A2A_ENVELOPE\s*(.*?)\s*```', re.DOTALL)
_MD_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
_MD_ANCHOR_RE = re.compile(r'^#+\s+(.+)$', re.MULTILINE)


def audit_content(content: str, check_type: str) -> dict:
    """
    Audits the content based on the requested check type.
    check_type: 'document' (requires YAML frontmatter) or 'handoff' (requires A2A_ENVELOPE block)
    Returns a dict with status and reasons.
    """
    report = {
        "status": "PASS",
        "errors": []
    }

    if check_type == 'document':
        # Check for YAML frontmatter
        match = _YAML_FRONTMATTER_RE.match(content.lstrip())
        
        if not match:
            report["status"] = "FAIL"
            report["errors"].append("Missing or malformed YAML Frontmatter (must start with ---).")
        else:
            frontmatter = match.group(1)
            required_keys = ['title:', 'date:', 'status:']
            for key in required_keys:
                if key not in frontmatter.lower():
                    report["status"] = "FAIL"
                    report["errors"].append(f"Frontmatter missing required key: {key.replace(':', '')}")

    elif check_type == 'handoff':
        # Check for A2A_ENVELOPE JSON block
        match = _A2A_ENVELOPE_RE.search(content)
        
        if not match:
            report["status"] = "FAIL"
            report["errors"].append("Missing ```json A2A_ENVELOPE block.")
        else:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                if 'target_agent' not in data:
                    report["status"] = "FAIL"
                    report["errors"].append("JSON missing required key: 'target_agent'.")
            except json.JSONDecodeError as e:
                report["status"] = "FAIL"
                report["errors"].append(f"Invalid JSON format in A2A_ENVELOPE block: {e}")

    else:
        report["status"] = "FAIL"
        report["errors"].append(f"Unknown check_type: {check_type}")

    return report


def validate_yaml_schema(content: str, schema: Optional[Dict] = None) -> Dict:
    """
    Validates YAML frontmatter against a JSON schema.

    Args:
        content: The document content containing YAML frontmatter.
        schema: Optional JSON schema dict. If None, uses default schema for
                Celestial documents (title: string, date: string, status: enum).

    Returns:
        Dict with 'valid' (bool) and 'errors' (list of strings).
    """
    result = {"valid": True, "errors": []}

    if not JSONSCHEMA_AVAILABLE:
        result["valid"] = False
        result["errors"].append("jsonschema library not available. Install with: pip install jsonschema")
        return result

    # Extract frontmatter
    match = _YAML_FRONTMATTER_RE.match(content.lstrip())
    if not match:
        result["valid"] = False
        result["errors"].append("Missing YAML frontmatter.")
        return result

    frontmatter_text = match.group(1)

    # Parse YAML-like key-value pairs (simplified, no nested structures)
    import datetime
    import yaml
    try:
        data = yaml.safe_load(frontmatter_text)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"YAML parse error: {e}")
        return result

    if not isinstance(data, dict):
        result["valid"] = False
        result["errors"].append("Frontmatter must be a YAML mapping (key: value).")
        return result

    # Convert YAML-native types (datetime, date) to strings for JSON schema validation
    def _yaml_to_json(val):
        if isinstance(val, dict):
            return {k: _yaml_to_json(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [_yaml_to_json(v) for v in val]
        elif isinstance(val, (datetime.date, datetime.datetime)):
            return val.isoformat()
        elif isinstance(val, bool):
            return val
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, str) or val is None:
            return val
        else:
            return str(val)

    data = _yaml_to_json(data)

    if schema is None:
        # Default schema for Celestial documents
        schema = {
            "type": "object",
            "required": ["title", "date", "status"],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "date": {"type": "string", "format": "date"},
                "status": {"type": "string", "enum": ["draft", "review", "published", "archived"]},
                "author": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        }

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        result["valid"] = False
        result["errors"].append(f"Schema validation error: {e.message} (path: {list(e.path)})")
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Validation error: {e}")

    return result


def check_markdown_links(content: str, base_path: str = ".") -> List[Dict]:
    """
    Checks all Markdown links in content for resolvability.

    Checks:
    - Internal file links (e.g., [text](./file.md)) exist on disk
    - Internal anchor links (e.g., [text](#section)) have matching heading
    - External URLs are not checked (assumed valid)

    Args:
        content: Markdown content to check.
        base_path: Directory to resolve relative file paths against.

    Returns:
        List of broken link reports, each with line, link_text, target, reason.
    """
    broken = []
    lines = content.split("\n")

    # Collect all headings for anchor validation
    headings = set()
    for line in lines:
        match = _MD_ANCHOR_RE.match(line)
        if match:
            heading_text = match.group(1).strip()
            # Create slug: lowercase, replace spaces with hyphens, remove special chars
            slug = re.sub(r'[^\w\s-]', '', heading_text.lower()).strip().replace(" ", "-")
            headings.add(slug)
            headings.add(heading_text.lower())

    for line_num, line in enumerate(lines, start=1):
        for match in _MD_LINK_RE.finditer(line):
            link_text = match.group(1)
            target = match.group(2)

            # Skip external URLs
            if target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue

            # Skip image links
            if line[match.start() - 1:match.start()] == "!":
                continue

            # Anchor-only link
            if target.startswith("#"):
                anchor = target[1:]
                anchor_slug = anchor.lower().replace(" ", "-")
                if anchor_slug not in headings and anchor.lower() not in headings:
                    broken.append({
                        "line": line_num,
                        "link_text": link_text,
                        "target": target,
                        "reason": f"Anchor '#{anchor}' not found in document headings",
                    })
                continue

            # Relative file link
            file_path = os.path.normpath(os.path.join(base_path, target))
            if not os.path.exists(file_path):
                broken.append({
                    "line": line_num,
                    "link_text": link_text,
                    "target": target,
                    "reason": f"File not found: {file_path}",
                })

    return broken


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wang Lingguan Format Auditor")
    parser.add_argument("--file", required=True, help="File to audit")
    parser.add_argument("--type", required=True, choices=['document', 'handoff'], help="Type of audit to perform")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found - {args.file}")
        exit(1)

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    result = audit_content(content, args.type)
    
    print(f"=== WANG LINGGUAN AUDIT REPORT ===")
    print(f"Target: {args.file}")
    print(f"Audit Type: {args.type.upper()}")
    print(f"Status: {result['status']}")
    if result['errors']:
        print("Violations:")
        for err in result['errors']:
            print(f" - {err}")
    print("==================================")
    
    # Exit with 1 if failed, so CLI tools know it failed
    if result['status'] == "FAIL":
        exit(1)
