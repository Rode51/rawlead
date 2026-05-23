"""Проверка мониторингового аккаунта + уведомление в бота при сбое."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from health_check import run_cli  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run_cli())
