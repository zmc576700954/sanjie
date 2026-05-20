---
title: Agent Capability Enhancement — Boundary Checks, Assertion Verification, and Documentation Standards
date: 2025-05-20
status: active
author: Claude
---

# Agent Capability Enhancement Spec

## Summary

This document records the systematic enhancement of three core agents (YangJian, WangLingGuan, Taibai) to address capability deficiencies identified during a real-world code review and documentation audit. The enhancements are based on cross-referencing with authoritative sources including OWASP, CWE, NIST AI RMF, and Anthropic's Building Effective Agents patterns.

## Problem Statement

A real-world review of YangJian (investigation agent) and Taibai (documentation agent) outputs revealed the following deficiencies:

### YangJian Deficiencies
1. **Missing boundary case analysis**: Null return paths not traced
2. **No security audit awareness**: `print_r($err, true)` information exposure missed
3. **Incomplete code tracing**: Abstract registration claims without exact code
4. **No entity differentiation**: UploaderDemo vs UploaderTestResource not distinguished
5. **Surface-level descriptions**: Functional descriptions without concrete code evidence

### Taibai Deficiencies
1. **Architecture diagram errors**: Arrow directions reversed
2. **Speculation presented as fact**: APP_KEY trigger timing unverified
3. **Missing user setup steps**: No "from scratch" instructions
4. **No risk grading**: 8 issues listed flat without severity
5. **No framework version awareness**: Laravel 12 `casts()` not noted
6. **Demo/production confusion**: Test resources presented as production examples

## Solution Architecture

### Design Principles
1. **Self-contained capability**: YangJian must output boundary checks even without other agents
2. **Tool-side execution**: Boundary verification performed by MCP Client, not dependent on WangLingGuan
3. **Layered review**: WangLingGuan retains all original capabilities while adding assertion verification
4. **Explicit triggering**: Clear conditions for when Layer 3 (assertion verification) activates

## Agent Changes

### YangJian — Boundary Check Generation

**New Core Directive (#6)**: Boundary Check Generation

**Trigger Rules** (based on OWASP Attack Surface Analysis):

| Trigger Type | Condition | Example |
|-------------|-----------|---------|
| NULL_PATH | Function returns potentially null | `getBucket()` returning null |
| INFO_EXPOSURE | Exception contains variables/objects | `print_r($err, true)` |
| REGISTRATION | Plugin/extension registration point | `FilamentUploaderPlugin` registration |
| INPUT_VALIDATION | User input entry point | File upload form fields |

**Output Format**:
```markdown
[boundary_checks]:
  - id: BC-001
    type: NULL_PATH
    location: "ClassName.php:36"
    description: "getBucket() returns null when bucket not found"
    concern: "Filament FileUpload may receive null"
    verification_needed: "Check if caller validates return value"
```

### WangLingGuan — Multi-layer Review Enhancer

**Layer 1: Format Compliance** (retained)
- YAML Frontmatter validation
- A2A_ENVELOPE block verification
- Markdown structure checks

**Layer 2: Quality Assessment** (retained)
- Content depth review (concrete code references required)
- Completeness check (no critical omissions)
- Accuracy review (framework versions, architecture relationships)

**Layer 3: Assertion Verification** (NEW)

| Assertion Type | Verification Method | Pass Criteria |
|---------------|-------------------|--------------|
| NULL_PATH | Read caller code, trace null handling | Caller has explicit null check |
| INFO_EXPOSURE | Inspect exception for sensitive patterns | No credentials/tokens in user-facing errors |
| REGISTRATION | Find exact registration code | Exact `->plugin()` or `->register()` call exists |
| INPUT_VALIDATION | Check input entry points | Type/length/format validation present |

**Risk Severity Grading**:

| Severity | Definition | Example |
|---------|-----------|---------|
| Critical | Data loss, security vulnerability, crash | Unhandled null in write path |
| High | Functional failure but recoverable | Null causes UI error |
| Warning | Best practice violation | Missing input validation |
| Note | Design suggestion | Performance optimization |
| TODO | Reserved/unimplemented | Commented-out code |

**Trigger Conditions**:
- Always: Format compliance + quality assessment for all agent outputs
- Conditional (Layer 3): `[boundary_checks]` non-empty, unverified claims, security-sensitive code, architecture diagrams

### Taibai — Technical Documentation Standards

**New Pillar 4: Technical Documentation Standards**

4.1 **User Perspective — "From Scratch" Completeness**
Every guide must answer: How to register? Publish resources? Compile assets? Prerequisites? Minimum working example?

4.2 **Fact Assertion Marking**
- `[verified: source]`: Direct code evidence
- `[inferred: reasoning]`: Logical deduction
- `[unverified: scope]`: Cannot confirm

4.3 **Risk Severity Grading**
Critical/High/Warning/Note/TODO with distinct visual treatment

4.4 **Architecture Diagram Validation**
- Arrow direction verified against code imports
- No phantom nodes (components must have code)
- Code wins over diagram when conflicting

4.5 **Demonstration vs Production Distinction**
- Demo resources marked `(Demo)`
- Explicit warnings: "For production, create your own Resource"
- Demo setup in appendix, production in main guide

4.6 **Framework Version Awareness**
- Version-specific syntax annotated
- Backward compatibility notes
- Deprecation warnings with alternatives

## New Tools

### code_caller_tracer.py
Finds call sites and checks null handling:
- `find_callers(project_root, target_class, target_method)` — traces all call sites
- `check_null_handling(project_root, file_path, line_number)` — verifies null checks in context

### import_validator.py
Validates architecture diagram arrows:
- `find_imports(project_root, file_path)` — extracts all import/use statements
- `verify_dependency_direction(project_root, from_component, to_component)` — checks if arrow direction matches code imports

## MCP Server Updates

### wanglingguan_server.py
New tools registered:
- `trace_callers` — Layer 3: Find call sites for boundary verification
- `verify_null_handling` — Layer 3: Check null handling in callers
- `verify_architecture_arrow` — Layer 3: Validate diagram arrow direction against imports

## Files Modified

| File | Change |
|------|--------|
| `agents/yangjian.md` | Added boundary check trigger rules, output format, security audit format |
| `agents/wanglingguan.md` | Restructured into 3 layers, added assertion verification, risk grading, trigger conditions |
| `agents/taibai.md` | Added Pillar 4: technical documentation standards (6 sub-sections) |
| `skills/tool_wanglingguan/scripts/code_caller_tracer.py` | NEW: Find call sites and check null handling |
| `skills/tool_wanglingguan/scripts/import_validator.py` | NEW: Extract imports and validate architecture arrows |
| `mcp-servers/wanglingguan_server.py` | Added 3 new MCP tools for Layer 3 verification |
| `config/mcp_settings.json.example` | Fixed paths from `skills/mcp_servers/` to `mcp-servers/` |
| `tests/test_code_caller_tracer.py` | NEW: Unit tests for code_caller_tracer |
| `tests/test_import_validator.py` | NEW: Unit tests for import_validator |

## Test Results

All 127 tests pass (including 9 new tests):
- `test_code_caller_tracer.py`: 4 tests (find_callers, null_handling)
- `test_import_validator.py`: 5 tests (imports, dependency_direction)

## References

- OWASP Error Handling Cheat Sheet — [error information disclosure](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)
- OWASP Attack Surface Analysis — [entry/exit point mapping](https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html)
- CWE-476 — NULL Pointer Dereference
- NIST AI Risk Management Framework — risk severity grading
- Anthropic Building Effective Agents — [Evaluator-Optimizer pattern](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents)

## Future Work

- [ ] Add `mcp_boundary_scanner` — automated AST-based boundary scanning
- [ ] Add `mcp_fact_verifier` — RAG-based fact claim verification
- [ ] Implement routing rules in host configuration for automatic WangLingGuan triggering
