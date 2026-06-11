"""O180: central dispatch for source page gone checks (delist)."""

from __future__ import annotations

from typing import Callable

from config import Config
from fl_parser import check_project_page_gone as fl_page_gone
from freelance_ru_parser import check_project_page_gone as freelance_ru_page_gone
from freelancejob_parser import check_project_page_gone as freelancejob_page_gone
from kwork_parser import check_project_page_gone as kwork_page_gone
from listing import (
    SOURCE_FL,
    SOURCE_FREELANCEJOB,
    SOURCE_FREELANCE_RU,
    SOURCE_KWORK,
    SOURCE_PCHYOL,
    SOURCE_YOUDO,
)
from pchyol_parser import check_project_page_gone as pchyol_page_gone
from youdo_parser import check_project_page_gone as youdo_page_gone

CheckerFn = Callable[[str, Config], bool | None]

_REGISTRY: dict[str, CheckerFn] = {
    SOURCE_FL: fl_page_gone,
    SOURCE_KWORK: kwork_page_gone,
    SOURCE_YOUDO: youdo_page_gone,
    SOURCE_FREELANCE_RU: freelance_ru_page_gone,
    SOURCE_FREELANCEJOB: freelancejob_page_gone,
    SOURCE_PCHYOL: pchyol_page_gone,
}


def _normalize_source(source: str) -> str:
    src = (source or "").strip().lower()
    if src.startswith("fl:"):
        return SOURCE_FL
    if src.startswith("kwork:"):
        return SOURCE_KWORK
    return src


def check_source_page_gone(source: str, url: str, cfg: Config) -> bool | None:
    """True=gone, False=alive, None=unknown or unsupported source."""
    src = _normalize_source(source)
    # TG v1: no stable per-lead project URL for recheck.
    if src == "tg" or src.startswith("tg:"):
        return None
    fn = _REGISTRY.get(src)
    if fn is None:
        return None
    return fn(url, cfg)
