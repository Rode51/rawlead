"""Один getUpdates на весь радар (main + tg_main через lock)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

    msvcrt = None  # type: ignore

from config import Config, bot_poll_lock_path
from storage import ProjectStorage
from telegram_control import poll_commands


def _try_acquire_poll_lock(fh) -> bool:
    if sys.platform == "win32":
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _release_poll_lock(fh) -> None:
    if sys.platform == "win32":
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def try_poll_commands(cfg: Config, storage: ProjectStorage) -> list[str]:
    """
    getUpdates только если удалось взять lock (иначе второй процесс молчит).
    Lock — на bot token, не на RADAR_PROFILE (Site/Legacy — разные боты).
    """
    os.environ.setdefault("RADAR_PROFILE", cfg.radar_profile)
    lock_path = bot_poll_lock_path(cfg.telegram_bot_token)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(lock_path, "a+b")
    except OSError:
        return poll_commands(cfg, storage)

    try:
        if not _try_acquire_poll_lock(fh):
            return []
        return poll_commands(cfg, storage)
    finally:
        _release_poll_lock(fh)
        fh.close()
