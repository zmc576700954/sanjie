import os
import shutil
from datetime import datetime
from pathlib import Path

from skills.utils import _get_file_lock

INDEX_HEADER = (
    "# Memory Index\n\n"
    "| Date | Topic | Summary | Path |\n"
    "|------|-------|---------|------|\n"
)


def archive_file(filepath: str, topic: str, summary: str, docs_root: str = "docs") -> bool:
    """Moves a file to the archive directory and updates the memory index.

    The index update is protected by a per-file lock so that concurrent
    calls never produce duplicate or interleaved entries.
    """
    if not os.path.exists(filepath):
        return False

    filename = os.path.basename(filepath)
    archive_dir = os.path.join(docs_root, "archive")
    index_file = os.path.join(docs_root, "MEMORY_INDEX.md")

    os.makedirs(archive_dir, exist_ok=True)

    # Move file
    dest_path = os.path.join(archive_dir, filename)
    shutil.move(filepath, dest_path)

    # Update Index under a lock to prevent race conditions
    date_str = datetime.now().strftime("%Y-%m-%d")
    relative_dest = (Path("docs/archive") / filename).as_posix()
    index_entry = f"| {date_str} | {topic} | {summary} | `{relative_dest}` |\n"

    lock = _get_file_lock(index_file)
    with lock:
        need_header = not os.path.exists(index_file)
        with open(index_file, "a", encoding="utf-8") as f:
            if need_header:
                f.write(INDEX_HEADER)
            f.write(index_entry)
            f.flush()
            os.fsync(f.fileno())
    return True
