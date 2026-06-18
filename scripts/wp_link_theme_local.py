#!/usr/bin/env python3
"""O118: junction rawlead-kadence-child repo -> Local WP (live edit in Cursor)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from wp_install_rawlead_theme import LOCAL_SITE, _ensure_db_host, wp_cli

ROOT = Path(__file__).resolve().parent.parent
THEME_SRC = (ROOT / "wordpress" / "rawlead-kadence-child").resolve()
THEME_DEST = LOCAL_SITE / "wp-content" / "themes" / "rawlead-kadence-child"
CHILD_SLUG = "rawlead-kadence-child"
QUIZ_SLUG = "quiz"
QUIZ_TEMPLATE = "page-quiz.php"


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


def ensure_quiz_page() -> int:
    """Idempotent /quiz page with page-quiz.php (Local WP-CLI)."""
    if not LOCAL_SITE.is_dir():
        print(f"FAIL: Local site missing: {LOCAL_SITE}")
        print("Start Local -> radarzakaz -> Start")
        return 1

    _ensure_db_host()
    probe = wp_cli("option", "get", "siteurl")
    if probe.returncode != 0:
        print("FAIL: Local MySQL unavailable. Start radarzakaz in Local app.")
        return 1

    listed = wp_cli(
        "post",
        "list",
        "--post_type=page",
        f"--name={QUIZ_SLUG}",
        "--field=ID",
        "--format=ids",
    )
    page_id = (listed.stdout or "").strip() if listed.returncode == 0 else ""

    if not page_id:
        created = wp_cli(
            "post",
            "create",
            "--post_type=page",
            "--post_title=Quiz",
            f"--post_name={QUIZ_SLUG}",
            "--post_status=publish",
            "--porcelain",
        )
        if created.returncode != 0:
            print("FAIL: wp post create quiz")
            print((created.stderr or created.stdout or "").strip())
            return 1
        page_id = (created.stdout or "").strip()
        print(f"Created page {QUIZ_SLUG} id={page_id}")
    else:
        print(f"Page {QUIZ_SLUG} already exists id={page_id}")

    meta = wp_cli("post", "meta", "get", page_id, "_wp_page_template")
    current = (meta.stdout or "").strip() if meta.returncode == 0 else ""
    if current != QUIZ_TEMPLATE:
        updated = wp_cli(
            "post",
            "meta",
            "update",
            page_id,
            "_wp_page_template",
            QUIZ_TEMPLATE,
        )
        if updated.returncode != 0:
            print("FAIL: wp post meta update _wp_page_template")
            print((updated.stderr or updated.stdout or "").strip())
            return 1
        print(f"Set template {QUIZ_TEMPLATE}")
    else:
        print(f"Template already {QUIZ_TEMPLATE}")

    site = wp_cli("option", "get", "siteurl")
    base = (site.stdout or "").strip() if site.returncode == 0 else "http://radarzakaz.local"
    url = f"{base.rstrip('/')}/{QUIZ_SLUG}/"
    print(f"OK: quiz page id={page_id} url={url}")
    return 0


def _print_help() -> None:
    print(
        """usage: wp_link_theme_local.py [--force] [--ensure-pages]

  Junction repo theme -> Local WP (radarzakaz).

  --force         Replace existing theme dir with junction.
  --ensure-pages  Create /quiz page with page-quiz.php (idempotent, WP-CLI).
"""
    )


def main() -> int:
    if "-h" in sys.argv or "--help" in sys.argv:
        _print_help()
        return 0

    force = "--force" in sys.argv
    ensure_pages = "--ensure-pages" in sys.argv

    rc = link_theme(force=force)
    if ensure_pages:
        page_rc = ensure_quiz_page()
        if page_rc != 0:
            return page_rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
