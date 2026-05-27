"""Категории Digital v0.10 (vision §0i) — ingest + эвристика read."""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

CATEGORIES: tuple[str, ...] = ("dev", "design", "marketing", "text")
OTHER_CATEGORY = "other"

_FL_CATEGORY_SLUG_RE = re.compile(r"/projects/category/([^/]+)/?", re.IGNORECASE)

# FL: slug рубрики в URL ленты → category (INGEST_CATEGORY_STRATEGY §2)
_FL_SLUG_TO_CATEGORY: dict[str, str] = {
    "programmirovanie": "dev",
    "administrirovanie-saytov": "dev",
    "sozdanie-saytov": "dev",
    "verstka": "dev",
    "mobilnye-prilozheniya": "dev",
    "seo": "marketing",
    "reklama-i-marketing": "marketing",
    "kontekstnaya-reklama": "marketing",
    "smm": "marketing",
    "dizayn": "design",
    "grafika": "design",
    "video": "design",
    "foto": "design",
    "animaciya": "design",
    "teksty": "text",
    "perevod": "text",
    "kopirajting": "text",
}

# Kwork: query `c=` на ленте (0 ₽, без LLM)
_KWORK_C_TO_CATEGORY: dict[str, str] = {
    "41": "dev",
    "79": "dev",
    "11": "dev",
    "37": "design",
    "38": "design",
    "20": "design",
    "39": "marketing",
    "40": "marketing",
    "15": "marketing",
    "5": "text",
    "6": "text",
    "7": "text",
}

_KWORK_ID_TO_CATEGORY: dict[int, str] = {
    11: "dev",
    41: "dev",
    79: "dev",
    37: "design",
    38: "design",
    20: "design",
    39: "marketing",
    40: "marketing",
    15: "marketing",
    5: "text",
    6: "text",
    7: "text",
}

CATEGORY_TITLES: dict[str, str] = {
    "dev": "Разработка & Код",
    "design": "Дизайн & Видео",
    "marketing": "Маркетинг & SMM",
    "text": "Тексты & Переводы",
}

_DEFAULT_DIGITAL_MIN = 55
_DEFAULT_DEV_MIN = 70

# Подстроки в tag/title/body → вес категории
_CATEGORY_HINTS: dict[str, tuple[str, ...]] = {
    "dev": (
        "python",
        "fastapi",
        "django",
        "flask",
        "парсер",
        "парсинг",
        "telegram bot",
        "телеграм бот",
        "tg бот",
        "бот",
        "webhook",
        "api",
        "wordpress",
        "автоматизац",
        "скрипт",
        "excel",
        "google sheets",
        "neon",
        "supabase",
        "php",
        "javascript",
        "backend",
        "интеграц",
    ),
    "design": (
        "figma",
        "ui",
        "ux",
        "ui/ux",
        "монтаж",
        "reels",
        "shorts",
        "motion",
        "after effects",
        "premiere",
        "видео",
        "анимац",
        "иллюстрац",
        "photoshop",
        "фотошоп",
        "дизайн",
        "баннер",
        "логотип",
    ),
    "marketing": (
        "таргет",
        "контекст",
        "яндекс директ",
        "google ads",
        "seo",
        "smm",
        "senler",
        "salebot",
        "прогрев",
        "воронк",
        "трафик",
        "email-маркет",
        "маркетинг",
        "реклам",
        "аналитик",
    ),
    "text": (
        "копирайт",
        "рерайт",
        "локализац",
        "редактур",
        "субтитр",
        "transcription",
        "перевод",
        "статья",
        "текст",
        "наполнение",
    ),
}


def _haystack(title: str, body: str, tags: list[str] | tuple[str, ...]) -> str:
    parts = [title or "", body or ""]
    parts.extend(tags or ())
    return "\n".join(parts).casefold()


def _score_category(hay: str, category: str) -> int:
    score = 0
    for hint in _CATEGORY_HINTS.get(category, ()):
        if hint.casefold() in hay:
            score += 1
    return score


def normalize_category(raw: str) -> str | None:
    """dev|design|marketing|text|other|None."""
    c = (raw or "").strip().lower()
    if c in CATEGORIES:
        return c
    if c == OTHER_CATEGORY:
        return OTHER_CATEGORY
    return None


def category_from_fl_listing_url(url: str) -> str | None:
    """Рубрика из URL ленты FL; None — широкая лента (?kind=1)."""
    m = _FL_CATEGORY_SLUG_RE.search(url or "")
    if not m:
        return None
    return _FL_SLUG_TO_CATEGORY.get(m.group(1).strip().lower())


def category_from_kwork_listing_url(url: str) -> str | None:
    """Параметр c= на ленте Kwork; None — c=all или без фильтра."""
    parsed = urlparse(url or "")
    raw = (parse_qs(parsed.query).get("c") or [""])[0].strip().lower()
    if not raw or raw == "all":
        return None
    return _KWORK_C_TO_CATEGORY.get(raw)


def category_from_kwork_want(want: dict) -> str | None:
    """Поля карточки Kwork → category."""
    for key in ("categoryId", "parentCategoryId", "category_id"):
        raw = want.get(key)
        if raw is None:
            continue
        try:
            mapped = _KWORK_ID_TO_CATEGORY.get(int(raw))
        except (TypeError, ValueError):
            continue
        if mapped:
            return mapped
    for key in ("categoryName", "nameCategory", "parentCategoryName", "rubricName"):
        val = want.get(key)
        if not val:
            continue
        hit = category_from_label(str(val))
        if hit:
            return hit
    return None


def category_from_label(label: str) -> str | None:
    """Название рубрики биржи → category."""
    hay = (label or "").casefold()
    if not hay:
        return None
    if any(
        x in hay
        for x in (
            "программ",
            "разработ",
            "код",
            "сайт",
            "бот",
            "парс",
            "api",
            "backend",
            "1с",
            "wordpress",
        )
    ):
        return "dev"
    if any(
        x in hay
        for x in ("дизайн", "figma", "ui", "ux", "видео", "монтаж", "график", "logo")
    ):
        return "design"
    if any(
        x in hay
        for x in ("маркет", "smm", "seo", "таргет", "реклам", "контекст", "трафик")
    ):
        return "marketing"
    if any(
        x in hay
        for x in ("текст", "копирайт", "перевод", "редактур", "стать")
    ):
        return "text"
    return None


def category_for_listing(
    project_source: str,
    *,
    listing_url: str = "",
    listing_category: str = "",
    title: str = "",
    snippet: str = "",
) -> str:
    """Категория при ingest: биржа → infer (без LLM)."""
    stored = normalize_category(listing_category)
    if stored and stored != OTHER_CATEGORY:
        return stored
    if project_source == "fl":
        from_url = category_from_fl_listing_url(listing_url)
        if from_url:
            return from_url
    if project_source == "kwork":
        from_url = category_from_kwork_listing_url(listing_url)
        if from_url:
            return from_url
    return infer_lead_category(title, snippet, ())


def resolve_lead_category(
    stored: str | None,
    title: str = "",
    body: str = "",
    tags: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Read API: колонка Neon или эвристика."""
    cat = normalize_category(stored or "")
    if cat and cat != OTHER_CATEGORY:
        return cat
    return infer_lead_category(title, body, tags)


def parse_category_param(category: str) -> list[str]:
    """`category=design,text` → ['design','text']."""
    if not (category or "").strip():
        return []
    out: list[str] = []
    for part in category.split(","):
        c = normalize_category(part.strip())
        if c and c != OTHER_CATEGORY and c not in out:
            out.append(c)
    return out


def infer_lead_category(
    title: str = "",
    body: str = "",
    tags: list[str] | tuple[str, ...] | None = None,
) -> str:
    """dev | design | marketing | text — по тегам и тексту."""
    hay = _haystack(title, body, tags or ())
    scores = {cat: _score_category(hay, cat) for cat in CATEGORIES}
    best = max(scores.values())
    if best == 0:
        return "dev"
    winners = [c for c in CATEGORIES if scores[c] == best]
    if len(winners) == 1:
        return winners[0]
    priority = ("dev", "design", "marketing", "text")
    for cat in priority:
        if cat in winners:
            return cat
    return "dev"


def categorize_tag(tag: str) -> str:
    """Один тег → категория для skills catalog."""
    t = (tag or "").strip()
    if not t:
        return "dev"
    hay = t.casefold()
    scores = {cat: _score_category(hay, cat) for cat in CATEGORIES}
    best = max(scores.values())
    if best == 0:
        return "dev"
    winners = [c for c in CATEGORIES if scores[c] == best]
    if len(winners) == 1:
        return winners[0]
    for cat in ("text", "marketing", "design", "dev"):
        if cat in winners:
            return cat
    return "dev"


def digital_min_score() -> int:
    raw = os.getenv("AI_SCORE_MIN_DIGITAL", str(_DEFAULT_DIGITAL_MIN)).strip()
    try:
        return max(0, min(100, int(raw)))
    except ValueError:
        return _DEFAULT_DIGITAL_MIN


def dev_min_score() -> int:
    raw = os.getenv("AI_SCORE_MIN_DEV", str(_DEFAULT_DEV_MIN)).strip()
    try:
        return max(0, min(100, int(raw)))
    except ValueError:
        return _DEFAULT_DEV_MIN


def effective_feed_min_score(requested: int, category: str) -> int:
    """UI «Брать ≥70» → для design/marketing/text порог 50–55."""
    if requested <= 0:
        return 0
    if requested >= dev_min_score() and category in ("design", "marketing", "text"):
        return digital_min_score()
    return requested


def passes_score_filter(score: int | None, requested_min: int, category: str) -> bool:
    if requested_min <= 0:
        return True
    threshold = effective_feed_min_score(requested_min, category)
    return (score or 0) >= threshold


def passes_ai_score(ai_score: int | None, requested_min: int, category: str) -> bool:
    return passes_score_filter(ai_score, requested_min, category)


def take_threshold_for_category(category: str) -> int:
    """Порог чипа «Брать» на карточке."""
    if category in ("design", "marketing", "text"):
        return digital_min_score()
    return dev_min_score()


def build_skills_groups(
    rows: list[tuple[str, int]],
    *,
    categories: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Группы для /v1/skills/catalog + плоский skills для совместимости."""
    active = categories or []
    cat_filter = set(active) if active else None
    buckets: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    flat: list[dict[str, Any]] = []
    for tag, cnt in rows:
        cat = categorize_tag(tag)
        if cat_filter is not None and cat not in cat_filter:
            continue
        item = {"tag": tag, "count": cnt, "category": cat}
        flat.append(item)
        buckets[cat].append({"tag": tag, "count": cnt})
    group_cats = [c for c in CATEGORIES if cat_filter is None or c in cat_filter]
    groups = [
        {
            "category": cat,
            "title": CATEGORY_TITLES[cat],
            "skills": buckets[cat],
        }
        for cat in group_cats
        if buckets[cat]
    ]
    return groups, flat
