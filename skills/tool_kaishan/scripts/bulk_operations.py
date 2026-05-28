"""Bulk file operations with destruction logging."""
from __future__ import annotations

import os
import re
import glob
from datetime import datetime
from typing import List, Optional

# Maximum number of log files to keep. 0 means unlimited.
MAX_LOG_FILES = 200


def bulk_delete(affected_files: List[str], base_dir: str = "") -> str:
    """Delete files and write destruction log.

    Each file is handled independently -- a failure on one file does not
    prevent the remaining files from being processed.

    Args:
        affected_files: List of absolute file paths to delete.
        base_dir: Directory where .trae/kaishan_logs will be created.
                  Defaults to os.getcwd() if empty.
    """
    deleted = []
    failed = []
    skipped = []
    for path in affected_files:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted.append(path)
            except OSError as e:
                failed.append({"path": path, "error": str(e)})
        else:
            skipped.append(path)

    log_path = _write_log("BULK_DELETE", deleted, failed=failed, skipped=skipped, base_dir=base_dir)
    parts = [f"Deleted {len(deleted)} files"]
    if failed:
        parts.append(f"{len(failed)} failed")
    if skipped:
        parts.append(f"{len(skipped)} skipped")
    return f"{', '.join(parts)}. Log: {log_path}"


def global_replace(
    affected_files: List[str],
    old_pattern: str,
    new_str: str,
    base_dir: str = "",
) -> str:
    """Regex replace across files and write destruction log.

    The regex pattern is compiled once before iterating.  If it is invalid
    the function returns immediately with an error message and writes
    nothing.

    Binary files (those that cannot be decoded as UTF-8) are skipped
    and recorded in the log.

    Args:
        affected_files: List of absolute file paths to process.
        old_pattern: Regex pattern to find.
        new_str: Replacement text (may include back-references).
        base_dir: Directory where .trae/kaishan_logs will be created.
    """
    # Pre-compile regex -- fail fast on invalid patterns
    try:
        compiled = re.compile(old_pattern)
    except re.error as e:
        return f"Error: invalid regex pattern '{old_pattern}': {e}. No files processed."

    replaced = []
    skipped = []
    failed = []
    for path in affected_files:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                new_content, subs = compiled.subn(new_str, content)
                if subs > 0:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    replaced.append(path)
            except UnicodeDecodeError:
                skipped.append({"path": path, "reason": "binary/non-UTF8 file"})
            except OSError as e:
                failed.append({"path": path, "error": str(e)})

    log_path = _write_log(
        f"GLOBAL_REPLACE ({old_pattern} -> {new_str})",
        replaced, failed=failed, skipped=skipped, base_dir=base_dir,
    )
    parts = [f"Replaced in {len(replaced)} files"]
    if failed:
        parts.append(f"{len(failed)} failed")
    if skipped:
        parts.append(f"{len(skipped)} skipped (binary)")
    return f"{', '.join(parts)}. Log: {log_path}"


def _write_log(
    action: str,
    affected_files: List[str],
    failed: Optional[list] = None,
    skipped: Optional[list] = None,
    base_dir: str = "",
) -> str:
    """Write destruction log.

    Args:
        action: Description of the action performed.
        affected_files: Files that were successfully processed.
        failed: Files that failed, each {"path": ..., "error": ...}.
        skipped: Files that were skipped, each {"path": ..., "reason": ...}.
        base_dir: Base directory for log output. Falls back to os.getcwd().

    Returns:
        Path to the written log file, or an empty string on write failure.

    Raises:
        Nothing -- disk-full or permission errors are caught and returned
        as part of the error message rather than propagated.
    """
    affected_files = [f for f in affected_files if f is not None]
    failed = failed or []
    skipped = skipped or []

    log_dir = os.path.join(base_dir or os.getcwd(), ".trae", "kaishan_logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        return f"[log-error] could not create {log_dir}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = os.path.join(log_dir, f"destruction_log_{timestamp}.md")

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("# Destruction Log\n\n")
            f.write(f"- Time: {datetime.now().isoformat()}\n")
            f.write(f"- Action: {action}\n")
            f.write(f"- Files affected: {len(affected_files)}\n\n")
            f.write("## File List\n")
            for file in affected_files:
                f.write(f"- `{file}`\n")
            if failed:
                f.write("\n## Failed\n")
                for entry in failed:
                    f.write(f"- `{entry['path']}` -- {entry['error']}\n")
            if skipped:
                f.write("\n## Skipped\n")
                for entry in skipped:
                    if isinstance(entry, dict):
                        reason = entry.get("reason", "unknown")
                        path = entry.get("path", "unknown")
                    else:
                        reason = "unknown"
                        path = str(entry)
                    f.write(f"- `{path}` -- {reason}\n")
    except OSError as e:
        return f"[log-error] could not write {log_file}: {e}"

    _rotate_logs(log_dir)
    return log_file


def _rotate_logs(log_dir: str) -> None:
    """Keep at most MAX_LOG_FILES log files, deleting the oldest ones."""
    if MAX_LOG_FILES <= 0:
        return
    try:
        logs = sorted(glob.glob(os.path.join(log_dir, "destruction_log_*.md")))
        excess = len(logs) - MAX_LOG_FILES
        if excess > 0:
            for old in logs[:excess]:
                try:
                    os.remove(old)
                except OSError:
                    pass
    except OSError:
        pass
