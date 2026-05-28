"""Keyword router for classifying errors and recommending downstream skills.

Uses weighted scoring to resolve conflicts when multiple keyword categories
match simultaneously.  Action-intent keywords outrank error-type keywords
so that "refactor the NoneType error" routes to the refactor skill.
"""

import re

_ACTION_KEYWORDS = {
    "refactor": 8, "rewrite": 8, "restructure": 8,
    "重构": 8, "重写": 8,
    "bulk": 7, "cleanup": 7, "deprecated": 7,
    "清理": 7, "废弃": 7, "批量": 7, "remove": 6,
    "feature": 6, "implement": 6, "add": 6,
    "新增": 6, "开发": 6, "实现": 6, "new": 5,
}

_ERROR_TYPE_PATTERNS = [
    (re.compile(r"\bAttributeError\b", re.I),             "AttributeError"),
    (re.compile(r"\bKeyError\b", re.I),                   "KeyError"),
    (re.compile(r"\bValueError\b", re.I),                 "ValueError"),
    (re.compile(r"\bTypeError\b", re.I),                  "TypeError"),
    (re.compile(r"\bNoneType\b", re.I),                   "NoneType"),
    (re.compile(r"\bIndexError\b", re.I),                 "IndexError"),
    (re.compile(r"\bImportError\b", re.I),                "ImportError"),
    (re.compile(r"\bModuleNotFoundError\b", re.I),        "ModuleNotFoundError"),
    (re.compile(r"\bNameError\b", re.I),                  "NameError"),
    (re.compile(r"\bRuntimeError\b", re.I),               "RuntimeError"),
    (re.compile(r"\bOSError\b", re.I),                    "OSError"),
    (re.compile(r"\bIOError\b", re.I),                    "IOError"),
    (re.compile(r"\bPermissionError\b", re.I),            "PermissionError"),
    (re.compile(r"\bTimeoutError\b", re.I),               "TimeoutError"),
    (re.compile(r"\bConnectionError\b", re.I),            "ConnectionError"),
    (re.compile(r"\bMemoryError\b", re.I),                "MemoryError"),
    (re.compile(r"\bRecursionError\b", re.I),             "RecursionError"),
    (re.compile(r"\bJSONDecodeError\b", re.I),            "JSONDecodeError"),
    (re.compile(r"\bUnicodeDecodeError\b", re.I),         "UnicodeDecodeError"),
    (re.compile(r"\bFileNotFoundError\b", re.I),          "FileNotFoundError"),
    (re.compile(r"\bIsADirectoryError\b", re.I),          "IsADirectoryError"),
    (re.compile(r"\bnot subscriptable\b", re.I),          "NoneType"),
    (re.compile(r"\bis not callable\b", re.I),            "TypeError"),
    (re.compile(r"\bno attribute\b", re.I),               "AttributeError"),
    (re.compile(r"\bhas no attribute\b", re.I),           "AttributeError"),
    (re.compile(r"\bnot found\b", re.I),                  "LookupError"),
    (re.compile(r"\bconnection refused\b", re.I),         "ConnectionError"),
    (re.compile(r"\baccess denied\b", re.I),              "PermissionError"),
    (re.compile(r"\btimeout\b", re.I),                    "TimeoutError"),
    (re.compile(r"\bno space left\b", re.I),              "OSError"),
    (re.compile(r"\bpermission denied\b", re.I),          "PermissionError"),
    (re.compile(r"\bmodule\b.*\bnot found\b|\bno module\b|\bcannot import\b|\bimport\b", re.I), "ImportError"),
    (re.compile(r"\b数据库\b|\b超时\b|\b连接.*失败\b|\b网络\b", re.I), "ConnectionError"),
]

_ERROR_TYPE_SKILLS = {
    "NoneType":        {"skill": "yindan", "root_cause": "Missing null check - accessing attribute or calling method on None value.", "action": "Add None guard with appropriate default return value."},
    "TypeError":       {"skill": "yindan", "root_cause": "Type mismatch - wrong argument type passed to function or operation.", "action": "Add type validation or cast to expected type before the operation."},
    "ImportError":     {"skill": "yindan", "root_cause": "Import path incorrect or dependency missing.", "action": "Fix import path or add missing dependency declaration."},
    "ModuleNotFoundError": {"skill": "yindan", "root_cause": "Module not installed or import path incorrect.", "action": "Install the missing package or fix the import path."},
    "AttributeError":  {"skill": "yindan", "root_cause": "Accessing attribute that does not exist on the object.", "action": "Verify object type and available attributes; add existence check if needed."},
    "KeyError":        {"skill": "yindan", "root_cause": "Dictionary key not found.", "action": "Use .get() with default or add key-existence check before access."},
    "ValueError":      {"skill": "yindan", "root_cause": "Invalid value passed to function or operation.", "action": "Validate input value format and range before processing."},
    "IndexError":      {"skill": "yindan", "root_cause": "Sequence index out of range.", "action": "Add bounds check before indexing or use safe access pattern."},
    "RuntimeError":    {"skill": "yindan", "root_cause": "Runtime execution error - likely logic or state issue.", "action": "Trace execution flow to identify the invalid state transition."},
    "ConnectionError": {"skill": "yindan", "root_cause": "Network connection failed - server unreachable or connection refused.", "action": "Verify target host availability, port configuration, and network policy."},
    "TimeoutError":    {"skill": "yindan", "root_cause": "Operation exceeded time limit.", "action": "Increase timeout or investigate why the operation is slow."},
    "PermissionError": {"skill": "yindan", "root_cause": "Insufficient permissions to access resource.", "action": "Verify file/resource permissions and process user privileges."},
    "OSError":         {"skill": "yindan", "root_cause": "OS-level error during I/O or system call.", "action": "Check disk space, file existence, and OS-level permissions."},
    "MemoryError":     {"skill": "yindan", "root_cause": "Insufficient memory to complete allocation.", "action": "Optimize memory usage or increase available memory."},
    "LookupError":     {"skill": "yindan", "root_cause": "Lookup failed - key, index, or identifier not found.", "action": "Verify the lookup key/index exists before access."},
    "JSONDecodeError": {"skill": "yindan", "root_cause": "JSON parsing failed - input is not valid JSON.", "action": "Validate input format before JSON parsing."},
    "RecursionError":  {"skill": "yindan", "root_cause": "Maximum recursion depth exceeded - likely infinite loop.", "action": "Add base case or increase recursion limit with caution."},
    "UnicodeDecodeError": {"skill": "yindan", "root_cause": "Character encoding mismatch during decode.", "action": "Specify correct encoding parameter or handle encoding errors."},
    "FileNotFoundError": {"skill": "yindan", "root_cause": "Target file does not exist at specified path.", "action": "Verify file path and existence before access."},
    "IsADirectoryError": {"skill": "yindan", "root_cause": "Attempted file operation on a directory.", "action": "Check path target type before file operations."},
}

_ACTION_SKILLS = {
    "refactor": "sanjian", "rewrite": "sanjian", "restructure": "sanjian",
    "重构": "sanjian", "重写": "sanjian",
    "bulk": "kaishan", "cleanup": "kaishan", "deprecated": "kaishan",
    "清理": "kaishan", "废弃": "kaishan", "批量": "kaishan", "remove": "kaishan",
    "feature": "taie", "implement": "taie", "add": "taie",
    "新增": "taie", "开发": "taie", "实现": "taie", "new": "taie",
}


def _extract_error_detail(error_desc, error_type):
    m = re.search(r"No module named '([^']+)'", error_desc)
    if m: return "Missing module: '%s'" % m.group(1)
    m = re.search(r"cannot import name '([^']+)'", error_desc)
    if m: return "Cannot import name: '%s'" % m.group(1)
    m = re.search(r"no attribute '([^']+)'", error_desc)
    if m: return "Missing attribute: '%s'" % m.group(1)
    m = re.search(r"KeyError:\s*'([^']+)'", error_desc)
    if m: return "Missing key: '%s'" % m.group(1)
    m = re.search(r"expected (\w+), got (\w+)", error_desc)
    if m: return "Expected type %s, received %s" % (m.group(1), m.group(2))
    return ""


def _score_context_hints(source_code_context):
    if not source_code_context:
        return 0
    ctx = source_code_context.lower()
    if "none" in ctx or "null" in ctx:
        return 1
    if "import" in ctx:
        return 1
    return 0


def classify_error(error_desc, source_code_context=""):
    desc_lower = error_desc.lower()

    # Phase 1: action-intent scoring
    action_scores = {}
    for keyword, weight in _ACTION_KEYWORDS.items():
        if keyword in desc_lower:
            skill = _ACTION_SKILLS[keyword]
            action_scores[skill] = action_scores.get(skill, 0) + weight

    # Phase 2: error-type scoring
    detected_type = ""
    error_score = 0
    for pattern, etype in _ERROR_TYPE_PATTERNS:
        if pattern.search(error_desc):
            if not detected_type:
                detected_type = etype
            error_score = max(error_score, 5)
    error_score += _score_context_hints(source_code_context)

    # Phase 3: pick winner
    best_action_skill = max(action_scores, key=action_scores.get) if action_scores else ""
    best_action_score = action_scores.get(best_action_skill, 0)

    if best_action_score > error_score:
        for kw, sk in _ACTION_SKILLS.items():
            if sk == best_action_skill and kw in desc_lower:
                return {
                    "logic_chain": "User intent indicates %s action (matched: '%s')." % (best_action_skill, kw),
                    "root_cause": "Task is primarily a %s operation." % best_action_skill,
                    "recommended_skill": best_action_skill,
                    "action": "Route to %s with context from error description." % best_action_skill,
                    "confidence": "HIGH",
                    "error_detail": "",
                    "detected_error_type": detected_type,
                }

    if detected_type and detected_type in _ERROR_TYPE_SKILLS:
        info = _ERROR_TYPE_SKILLS[detected_type]
        detail = _extract_error_detail(error_desc, detected_type)
        return {
            "logic_chain": "Detected %s error in execution." % detected_type,
            "root_cause": info["root_cause"],
            "recommended_skill": info["skill"],
            "action": info["action"],
            "confidence": "HIGH" if error_score >= 5 else "MEDIUM",
            "error_detail": detail,
            "detected_error_type": detected_type,
        }

    return {
        "logic_chain": "Error: %s. Requires further context." % error_desc[:80],
        "root_cause": "Insufficient information for definitive classification.",
        "recommended_skill": "yindan",
        "action": "Gather more context, then apply minimal fix.",
        "confidence": "LOW",
        "error_detail": "",
        "detected_error_type": "",
    }
