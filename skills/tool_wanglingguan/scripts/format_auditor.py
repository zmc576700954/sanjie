import argparse
import re
import json
import os

# Module-level compiled patterns for performance
_YAML_FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
_A2A_HANDOFF_RE = re.compile(r'```json\s+A2A_HANDOFF\s*(.*?)\s*```', re.DOTALL)


def audit_content(content: str, check_type: str) -> dict:
    """
    Audits the content based on the requested check type.
    check_type: 'document' (requires YAML frontmatter) or 'handoff' (requires A2A_HANDOFF block)
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
        # Check for A2A_HANDOFF JSON block
        match = _A2A_HANDOFF_RE.search(content)
        
        if not match:
            report["status"] = "FAIL"
            report["errors"].append("Missing ```json A2A_HANDOFF block.")
        else:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                if 'target_agent' not in data:
                    report["status"] = "FAIL"
                    report["errors"].append("JSON missing required key: 'target_agent'.")
            except json.JSONDecodeError as e:
                report["status"] = "FAIL"
                report["errors"].append(f"Invalid JSON format in A2A_HANDOFF block: {e}")

    else:
        report["status"] = "FAIL"
        report["errors"].append(f"Unknown check_type: {check_type}")

    return report

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
