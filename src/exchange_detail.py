"""O141: единый dispatch detail-fetch для web-бирж (без tg:)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config

_WEB_DETAIL_SOURCES = frozenset(
    {
        "fl",
        "kwork",
        "youdo",
        "freelance_ru",
        "freelancejob",
        "pchyol",
    }
)


def is_web_detail_source(source: str) -> bool:
    return (source or "").strip() in _WEB_DETAIL_SOURCES


def fetch_project_detail(
    source: str,
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 30.0,
) -> tuple[str, str, bool]:
    """(description, html, detail_ok) — fallback snippet при ошибке."""
    key = (source or "").strip()
    if key == "fl":
        from fl_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    if key == "kwork":
        from kwork_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    if key == "youdo":
        from youdo_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    if key == "freelance_ru":
        from freelance_ru_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    if key == "freelancejob":
        from freelancejob_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    if key == "pchyol":
        from pchyol_parser import fetch_project_detail as _fetch

        return _fetch(
            project_url,
            cfg,
            fallback_snippet=fallback_snippet,
            timeout_sec=timeout_sec,
        )
    return fallback_snippet, "", False
