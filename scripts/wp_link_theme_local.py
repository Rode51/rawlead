#!/usr/bin/env python3
"""O118: junction rawlead-kadence-child repo -> Local WP (live edit in Cursor)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME_SRC = (ROOT / "wordpress" / "rawlead-kadence-child").resolve()
LOCAL_SITE = Path.home() / "Local Sites" / "radarzakaz" / "app" / "public"
THEME_DEST = LOCAL_SITE / "wp-content" / "themes" / "rawlead-kadence-child"
CHILD_SLUG = "rawlead-kadence-child"


def _is_junction(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        # reparse point on Windows
        import stat

        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return path.is_symlink()


def _junction_target(path: Path) -> Path | None:
    if not _is_junction(path):
        return None
    try:
        out = subprocess.run(
            ["cmd", "/c", f"dir /AL {path.parent}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        for line in out.stdout.splitlines():
            if CHILD_SLUG in line and "[" in line:
                # JUNCTION     C:\...\rawlead-kadence-child [C:\...\uisness\...]
                start = line.find("[") + 1
                end = line.find("]")
                if start > 0 and end > start:
                    return Path(line[start:end]).resolve()
    except OSError:
        pass
    return None


def link_theme(*, force: bool = False) -> int:
    if not LOCAL_SITE.is_dir():
        print(f"FAIL: Local site missing: {LOCAL_SITE}")
        print("Start Local -> radarzakaz -> Start")
        return 1
    if not (THEME_SRC / "style.css").is_file():
        print(f"FAIL: theme source missing: {THEME_SRC}")
        return 1

    if THEME_DEST.exists():
        if _is_junction(THEME_DEST):
            target = _junction_target(THEME_DEST)
            if target == THEME_SRC:
                print(f"OK: junction already -> {THEME_SRC}")
                return 0
            if not force:
                print(f"FAIL: junction points elsewhere: {target}")
                print("Re-run with --force")
                return 1
        elif not force:
            print(f"WARN: {THEME_DEST} is a copy (not junction).")
            print("Re-run with --force to replace with junction.")
            return 1
        print(f"Removing {THEME_DEST} ...")
        if _is_junction(THEME_DEST):
            THEME_DEST.rmdir()
        else:
            shutil.rmtree(THEME_DEST)

    THEME_DEST.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["cmd", "/c", "mklink", "/J", str(THEME_DEST), str(THEME_SRC)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("FAIL: mklink /J")
        print(proc.stdout or proc.stderr)
        print("Tip: run terminal as Administrator once, or enable Developer Mode (Windows Settings).")
        return 1

    print(f"OK: junction {THEME_DEST}")
    print(f"    -> {THEME_SRC}")
    print("Edit theme in repo; Local reads same files.")
    return 0


def main() -> int:
    force = "--force" in sys.argv
    return link_theme(force=force)


if __name__ == "__main__":
    raise SystemExit(main())
