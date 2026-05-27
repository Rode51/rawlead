"""Один getUpdates на весь радар (main + tg_main через lock)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None  # type: ignore

from config import Config, radar_lock_path
from storage import ProjectStorage
from telegram_control import poll_commands


def try_poll_commands(cfg: Config, storage: ProjectStorage) -> list[str]:
    """
    getUpdates только если удалось взять lock (иначе второй процесс молчит).
    """
    os.environ.setdefault("RADAR_PROFILE", cfg.radar_profile)
    lock_path = radar_lock_path("bot_poll")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(lock_path, "a+b")
    except OSError:
        return poll_commands(cfg, storage)

    try:
        if msvcrt is not None:
            try:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                return []
        return poll_commands(cfg, storage)
    finally:
        if msvcrt is not None:
            try:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        fh.close()
