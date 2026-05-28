import re
import argparse
import sys
import os

def _extract_signatures(text):
    result = {"functions": [], "params": [], "endpoints": [], "http_methods": [], "return_hints": [], "error_codes": []}
    for m in re.finditer(r'(?:def\s+)?(\w+)\s*\(([^)]*)\)', text):
        result["functions"].append(m.group(1))
        for p in re.split(r'[,/]\s*', m.group(2)):
            p = p.strip().strip("'\"")
            if p and len(p) < 60: result["params"].append(p)
    for m in re.finditer(r'((?:GET|POST|PUT|PATCH|DELETE)\s+)?(/\w[\w/\-]*)', text, re.I):
        method = (m.group(1) or "").strip().upper()
        path = m.group(2)
        if len(path) > 2:
            result["endpoints"].append(path)
            if method: result["http_methods"].append(method)
    for m in re.finditer(r'returns?\s+(\w[\w\s]*)', text, re.I):
        result["return_hints"].append(m.group(1).strip()[:40])
    result["error_codes"] = list(set(re.findall(r'\b([3-5]\d{2})\b', text)))
    return result

def _format_signature(label, sig):
    lines = ["  %s:" % label]
    for key in ("functions", "params", "endpoints", "http_methods", "return_hints", "error_codes"):
        vals = sorted(set(sig[key]))
        if vals: lines.append("    %s: %s" % (key, ", ".join(vals)))
    return "\n".join(lines)

def _gap_analysis(local_sig, spec_sig):
    gaps = []
    for key in ("params", "functions", "endpoints", "error_codes"):
        local_set = set(local_sig[key])
        spec_set = set(spec_sig[key])
        missing_local = spec_set - local_set
        missing_spec = local_set - spec_set
        if missing_local: gaps.append("  [GAP] In spec but NOT in local (%s): %s" % (key, ", ".join(sorted(missing_local))))
        if missing_spec: gaps.append("  [NOTE] In local but NOT in spec (%s): %s" % (key, ", ".join(sorted(missing_spec))))
    return "\n".join(gaps) if gaps else "  No structural gaps detected."

def verify_logic(local_logic, official_spec):
    if "ERROR_AUTH_BLOCKED" in official_spec:
        return "[VERIFICATION FAILED]\nOfficial Spec is missing due to authentication barriers.\nAction Required: Execute Anti-Auth Fallback Protocol (Plan C: Community Search, or Plan A: Request User Assist)."
    local_sig = _extract_signatures(local_logic)
    spec_sig = _extract_signatures(official_spec)
    gap_report = _gap_analysis(local_sig, spec_sig)
    return ("=== DUAL-DOMAIN VERIFICATION REQUEST ===\n\n"
        "--- LOCAL IMPLEMENTATION ---\n%s\n\n"
        "--- OFFICIAL SPECIFICATION ---\n%s\n\n"
        "--- PRE-PROCESSED SIGNATURES ---\n%s\n%s\n\n"
        "--- GAP ANALYSIS ---\n%s\n\n"
        "Instructions for Agent:\n"
        "1. Compare the local logic against the official spec, using the pre-processed signatures and gap analysis above as a starting point.\n"
        "2. Identify any missing parameters, mismatched algorithms, or structural differences not already flagged.\n"
        "3. Output a detailed Gap Analysis with severity ratings."
    ) % (local_logic, official_spec, _format_signature("Local", local_sig), _format_signature("Spec", spec_sig), gap_report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", required=True)
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    local_content = args.local
    spec_content = args.spec
    if os.path.isfile(args.local):
        with open(args.local, "r", encoding="utf-8") as f: local_content = f.read()
    if os.path.isfile(args.spec):
        with open(args.spec, "r", encoding="utf-8") as f: spec_content = f.read()
    print(verify_logic(local_content, spec_content))
