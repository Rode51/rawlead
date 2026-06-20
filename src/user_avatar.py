"""Local TG avatar cache — download once on login, serve from disk (O185 t3)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import requests

logger = logging.getLogger(__name__)

_DEFAULT_DIR = "/opt/rawlead/data/avatars"
_PUBLIC_BASE = "https://rawlead.ru/wp-content/uploads/rawlead-avatars"
_UA = "RawLead/1.0 (+https://rawlead.ru)"

_resolved_avatar_dir: Path | None = None


def _looks_like_image(data: bytes) -> bool:
    if len(data) < 12:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


def _wp_content_path_unwritable(path: Path) -> bool:
    if "wp-content" not in path.parts:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".rawlead_write_probe"
        probe.write_bytes(b"1")
        probe.unlink(missing_ok=True)
        return False
    except OSError:
        return True


def avatar_dir() -> Path:
    global _resolved_avatar_dir
    if _resolved_avatar_dir is not None:
        return _resolved_avatar_dir

    raw = (os.getenv("RAWLEAD_AVATAR_DIR") or _DEFAULT_DIR).strip()
    chosen = Path(raw)
    if _wp_content_path_unwritable(chosen):
        logger.warning(
            "RAWLEAD_AVATAR_DIR=%s not writable (wp-content post-cutover); using %s",
            raw,
            _DEFAULT_DIR,
        )
        chosen = Path(_DEFAULT_DIR)
    _resolved_avatar_dir = chosen
    return chosen


def reset_avatar_dir_cache() -> None:
    """Test helper — clear memoized avatar_dir()."""
    global _resolved_avatar_dir
    _resolved_avatar_dir = None


def avatar_path(user_id: str) -> Path:
    uid = str(UUID(str(user_id)))
    return avatar_dir() / f"{uid}.jpg"


def avatar_public_url(user_id: str) -> str | None:
    path = avatar_path(user_id)
    if not path.is_file():
        return None
    base = (os.getenv("RAWLEAD_AVATAR_PUBLIC_BASE") or _PUBLIC_BASE).rstrip("/")
    uid = str(UUID(str(user_id)))
    version = int(path.stat().st_mtime)
    return f"{base}/{uid}.jpg?v={version}"


def cache_user_avatar(user_id: str, photo_url: str | None) -> bool:
    url = (photo_url or "").strip()
    if not url:
        return False
    dest = avatar_path(user_id)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=12, headers={"User-Agent": _UA})
        resp.raise_for_status()
        body = resp.content
        if len(body) < 64 or not _looks_like_image(body):
            logger.warning(
                "avatar cache skip bad payload (%s bytes) for %s",
                len(body),
                user_id,
            )
            return False
        dest.write_bytes(body)
        return True
    except Exception:
        logger.warning("avatar cache failed user_id=%s", user_id)
        return False


def read_avatar_bytes(user_id: str) -> tuple[bytes, str] | None:
    path = avatar_path(user_id)
    if not path.is_file():
        return None
    return path.read_bytes(), "image/jpeg"


def clear_neon_photo_url(cur: Any, user_id: str) -> None:
    cur.execute(
        "UPDATE users SET tg_photo_url = NULL WHERE id = %s::uuid",
        (user_id,),
    )


def fetch_photo_url_via_bot(tg_user_id: int, bot_token: str) -> str | None:
    """Fresh file URL via Bot API — works when widget CDN URL is dead."""
    token = (bot_token or "").strip()
    if not token or not tg_user_id:
        return None
    base = f"https://api.telegram.org/bot{token}"
    try:
        resp = requests.get(
            f"{base}/getUserProfilePhotos",
            params={"user_id": int(tg_user_id), "limit": 1},
            timeout=12,
        )
        resp.raise_for_status()
        photos = (resp.json().get("result") or {}).get("photos") or []
        if not photos or not photos[0]:
            return None
        file_id = photos[0][-1].get("file_id")
        if not file_id:
            return None
        file_resp = requests.get(
            f"{base}/getFile",
            params={"file_id": file_id},
            timeout=12,
        )
        file_resp.raise_for_status()
        file_path = (file_resp.json().get("result") or {}).get("file_path")
        if not file_path:
            return None
        return f"https://api.telegram.org/file/bot{token}/{file_path}"
    except Exception as exc:
        logger.warning("bot avatar url tg=%s: %s", tg_user_id, exc)
        return None


def _resolve_photo_source(
    photo_url: str | None,
    tg_user_id: int | None,
) -> str:
    url = (photo_url or "").strip()
    if url:
        return url
    if tg_user_id:
        from telegram_login import login_bot_token

        bot_url = fetch_photo_url_via_bot(int(tg_user_id), login_bot_token())
        if bot_url:
            return bot_url
    return ""


def ensure_avatar_cached(cur: Any, user_id: str) -> bool:
    if avatar_path(user_id).is_file():
        return True
    cur.execute(
        "SELECT tg_photo_url, tg_user_id FROM users WHERE id = %s::uuid",
        (user_id,),
    )
    row = cur.fetchone()
    tg_photo_url = (row[0] if row else None) or ""
    tg_user_id = row[1] if row else None
    url = _resolve_photo_source(str(tg_photo_url).strip() or None, tg_user_id)
    if not url:
        return False
    if not cache_user_avatar(user_id, url):
        return False
    clear_neon_photo_url(cur, user_id)
    return True


def avatar_api_fields(user_id: str) -> dict[str, bool | None]:
    """API profile JSON — cached file → has_avatar, no broken WP uploads URL."""
    if avatar_path(user_id).is_file():
        return {"avatar_url": None, "has_avatar": True}
    url = avatar_public_url(user_id)
    if url and "/wp-content/uploads/" in url:
        return {"avatar_url": None, "has_avatar": False}
    return {"avatar_url": url, "has_avatar": bool(url)}


def sync_avatar_on_login(
    cur: Any,
    user_id: str,
    photo_url: str | None,
    tg_user_id: int | None = None,
) -> str | None:
    """Download at login; drop TG URL from Neon after successful cache."""
    url = _resolve_photo_source(photo_url, tg_user_id)
    if url and cache_user_avatar(user_id, url):
        clear_neon_photo_url(cur, user_id)
        return avatar_public_url(user_id)
    if avatar_path(user_id).is_file():
        return avatar_public_url(user_id)
    return None
