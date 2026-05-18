"""Bulk file operations with destruction logging."""
import os
import re
from datetime import datetime
from typing import List


def bulk_delete(affected_files: List[str]) -> str:
    """Delete files and write destruction log."""
    deleted = []
    for path in affected_files:
        if os.path.exists(path):
            os.remove(path)
            deleted.append(path)

    log_path = _write_log("BULK_DELETE", deleted)
    return f"Deleted {len(deleted)} files. Log: {log_path}"


def global_replace(affected_files: List[str], old_pattern: str, new_str: str) -> str:
    """Regex replace across files and write destruction log."""
    replaced = []
    for path in affected_files:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content, subs = re.subn(old_pattern, new_str, content)
                if subs > 0:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    replaced.append(path)
            except Exception:
                pass

    log_path = _write_log(f"GLOBAL_REPLACE ({old_pattern} -> {new_str})", replaced)
    return f"Replaced in {len(replaced)} files. Log: {log_path}"


def _write_log(action: str, affected_files: List[str]) -> str:
    """Write destruction log."""
    log_dir = os.path.join(os.getcwd(), ".trae", "kaishan_logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"destruction_log_{timestamp}.md")

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"# Destruction Log\n\n")
        f.write(f"- Time: {datetime.now().isoformat()}\n")
        f.write(f"- Action: {action}\n")
        f.write(f"- Files affected: {len(affected_files)}\n\n")
        f.write("## File List\n")
        for file in affected_files:
            f.write(f"- `{file}`\n")

    return log_file
