#!/usr/bin/env python3
"""Dedicated Bot API poller — живёт отдельно от rawlead-radar (B3: ответы после 🛑)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from bot_poll import try_poll_commands  # noqa: E402
from config import (  # noqa: E402
    apply_profile_argv,
    load_config,
    load_radar_env,
    radar_timestamp,
)
from storage import storage_from_config  # noqa: E402
from telegram_control import ensure_bot_polling_mode  # noqa: E402

_POLL_SEC = 2.0


def _append_log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main() -> int:
    apply_profile_argv()
    load_radar_env()
    cfg = load_config()
    storage = storage_from_config(cfg)
    log_path = cfg.radar_log_path

    print(
        f"=== bot-poll {radar_timestamp()} profile={cfg.radar_profile} ===",
        flush=True,
    )

    for line in ensure_bot_polling_mode(cfg):
        ts = radar_timestamp()
        _append_log(log_path, f"{ts} {line}")
        print(f"{ts} {line}", flush=True)

    while True:
        try:
            for line in try_poll_commands(cfg, storage):
                ts = radar_timestamp()
                _append_log(log_path, f"{ts} {line}")
                if (
                    line.startswith("тг:команда:")
                    or "тг:бот:" in line
                    or line.startswith("tg:draft:")
                ):
                    print(f"{ts} {line}", flush=True)
        except KeyboardInterrupt:
            print("bot-poll: стоп", flush=True)
            return 0
        except Exception as exc:
            ts = radar_timestamp()
            print(f"{ts} bot-poll:error:{exc!r}", flush=True)
        time.sleep(_POLL_SEC)


if __name__ == "__main__":
    raise SystemExit(main())
