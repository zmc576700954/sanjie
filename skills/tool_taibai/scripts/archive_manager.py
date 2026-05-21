import os
import shutil
from datetime import datetime
from pathlib import Path

def archive_file(filepath: str, topic: str, summary: str, docs_root: str = "docs") -> bool:
    """Moves a file to the archive directory and updates the memory index."""
    if not os.path.exists(filepath):
        return False

    filename = os.path.basename(filepath)
    archive_dir = os.path.join(docs_root, "archive")
    index_file = os.path.join(docs_root, "MEMORY_INDEX.md")

    os.makedirs(archive_dir, exist_ok=True)

    # Move file
    dest_path = os.path.join(archive_dir, filename)
    shutil.move(filepath, dest_path)

    # Update Index
    date_str = datetime.now().strftime("%Y-%m-%d")
    relative_dest = (Path("docs/archive") / filename).as_posix()

    index_entry = f"| {date_str} | {topic} | {summary} | `{relative_dest}` |\n"

    if os.path.exists(index_file):
        with open(index_file, "a", encoding="utf-8") as f:
            f.write(index_entry)
    else:
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("# Memory Index\n\n")
            f.write("| Date | Topic | Summary | Path |\n")
            f.write("|------|-------|---------|------|\n")
            f.write(index_entry)

    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    
    if archive_file(args.file, args.topic, args.summary):
        print(f"Successfully archived {args.file}")
    else:
        print(f"Failed to archive {args.file}")
