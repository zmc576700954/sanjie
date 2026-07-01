from __future__ import annotations

from pathlib import Path

from skill_manager.store import FileSystemStore


def load_builtin_skills(store: FileSystemStore, source_root: str | None = None) -> None:
    if source_root is None:
        source_root = str(Path(__file__).parent)

    root = Path(source_root)
    for skill_dir in root.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "skill.json"
        if not skill_path.exists():
            continue

        # Load by copying files into store directory
        target_skill_dir = store._skill_dir(skill_dir.name)
        target_skill_dir.mkdir(parents=True, exist_ok=True)

        for src_file in skill_dir.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(skill_dir)
            dest = target_skill_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src_file.read_bytes())
