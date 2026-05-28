"""Запуск main/tg (или neon consumer) без HTTP API — для /start и аварийного CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    _FLAGS = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
else:
    _FLAGS = 0

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

def _venv_python(root: Path) -> Path:
    if sys.platform == "win32":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


_PYTHON = _venv_python(_ROOT)


def _spawn_one(script: Path, profile: str) -> str | None:
    if not script.is_file():
        return f"Нет файла: {script}"
    if not _PYTHON.is_file():
        return f"Нет Python: {_PYTHON}"
    try:
        subprocess.Popen(
            [str(_PYTHON), "-u", str(script), "--profile", profile],
            cwd=str(_ROOT),
            creationflags=_FLAGS,
        )
    except OSError as exc:
        return f"{script.name}: {exc}"
    return None


def main() -> int:
    from config import apply_profile_argv, load_radar_env, radar_exchanges_enabled
    from process_guard import count_radar_workers, kill_duplicate_radar_workers
    from config import legacy_neon_consumer_enabled, radar_tg_enabled

    apply_profile_argv()
    profile = load_radar_env()

    kill_duplicate_radar_workers(
        role="main",
        log_source="radar_spawn_workers:pre",
        profile=profile,
    )
    kill_duplicate_radar_workers(
        role="tg_main",
        log_source="radar_spawn_workers:pre",
        profile=profile,
    )

    errors: list[str] = []
    if radar_exchanges_enabled():
        err = _spawn_one(_ROOT / "src" / "main.py", profile)
        if err:
            errors.append(err)
    elif legacy_neon_consumer_enabled():
        err = _spawn_one(_ROOT / "src" / "neon_legacy_consumer.py", profile)
        if err:
            errors.append(err)
    if radar_tg_enabled():
        err = _spawn_one(_ROOT / "scripts" / "tg_main.py", profile)
        if err:
            errors.append(err)

    exp_main = 1 if (radar_exchanges_enabled() or legacy_neon_consumer_enabled()) else 0
    exp_tg = 1 if radar_tg_enabled() else 0
    deadline = time.monotonic() + 15.0
    mc = tc = 0
    while time.monotonic() < deadline:
        mc, tc = count_radar_workers(profile)
        if mc >= exp_main and tc >= exp_tg:
            break
        time.sleep(0.35)
    else:
        errors.append(f"воркеры main={mc} tg={tc} (ожидалось {exp_main}/{exp_tg})")

    ok = len(errors) == 0 and mc >= exp_main and tc >= exp_tg
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
