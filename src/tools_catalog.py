"""Free-form tool names for audit/display — NOT canonical skills / picker (O72b)."""

from __future__ import annotations

import re
from typing import Any

from skills_catalog import CANONICAL_TAGS, resolve_canonical_tag

# Audit whitelist + display names (does not expand CANONICAL_TAGS picker set).
KNOWN_TOOLS: frozenset[str] = frozenset(
    {
        "photoshop",
        "illustrator",
        "canva",
        "figma",
        "sketch",
        "after_effects",
        "premiere_pro",
        "cinema_4d",
        "blender",
        "powerpoint",
        "word_processor",
        "excel",
        "google_analytics",
        "yandex_metrika",
        "google_sheets_api",
        "google_apps_script",
        "google_docs",
        "google_drive",
        "google_calendar",
        "instagram",
        "crm",
        "consulting",
        "text_editor",
        "psd_editor",
        "seo_tools",
        "joomla",
        "celery",
        "redis",
        "debugging_tools",
        "gltf_pipeline",
        "image_editor",
        "chart_js",
        "make_com",
        "telegram_api",
        "git",
        "adb",
        "postgresql",
        "mysql",
        "telegram",
        "telegram_bot",
        "python",
        "php",
        "javascript",
        "html_css",
        "wordpress",
        "elementor",
        "wp_rocket",
        "woocommerce",
        "tilda",
        "rhino",
        "fontlab",
        "lcp",
        "mailwizz",
        "selenium",
        "netcat",
        "1c",
        "ton",
        "nft",
        "blockchain",
        "hex_editor",
        "vpn",
        "ide",
        "llm_api",
        "style_guide",
        "windows_api",
    }
)

# L2 часто отдаёт синонимы — приводим к KNOWN_TOOLS или canonical_tag.
_TOOL_ALIAS_MAP: dict[str, str] = {
    "adobe_photoshop": "photoshop",
    "adobe_illustrator": "illustrator",
    "google_sheets": "google_sheets_api",
    "google_sheet": "google_sheets_api",
    "google_таблиц": "google_sheets_api",
    "google_tables": "google_sheets_api",
    "apps_script": "google_apps_script",
    "gsuite": "google_apps_script",
    "wp": "wordpress_dev",
    "wordpress": "wordpress_dev",
    "word_press": "wordpress_dev",
    "вордпресс": "wordpress_dev",
    "tg": "telegram_bot_dev",
    "telegram_bot": "telegram_bot_dev",
    "telethon": "telegram",
    "aiogram": "telegram",
    "pyrogram": "telegram",
    "js": "javascript",
    "html": "javascript",
    "css": "javascript",
    "react": "javascript",
    "vue": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "ae": "after_effects",
    "c4d": "cinema_4d",
    "ppt": "powerpoint",
    "ms_powerpoint": "powerpoint",
    "keynote": "powerpoint",
    "ps": "photoshop",
    "ai": "illustrator",
    "фотошоп": "photoshop",
    "фигма": "figma",
    "motion_design_software": "after_effects",
    "video_editing_software": "premiere_pro",
    "3x_ui": "vpn",
    "3x-ui": "vpn",
    "google_metrika": "yandex_metrika",
    "яндекс_метрика": "yandex_metrika",
    "metrika": "yandex_metrika",
    "search_console": "seo_tools",
    "gsc": "seo_tools",
    "wildberries": "consulting",
    "ozon": "consulting",
}

# O72e-2: vendor-specific libs → generic stack names for display + L2 ingest.
_VENDOR_TOOL_MAP: dict[str, str] = {
    "neon": "postgresql",
    "supabase": "postgresql",
    "planetscale": "postgresql",
    "telethon": "telegram",
    "aiogram": "telegram",
    "pyrogram": "telegram",
    "python_telegram_bot": "telegram",
    "telegram_api": "telegram",
    "fastapi": "python",
    "django": "python",
    "flask": "python",
    "uvicorn": "python",
    "starlette": "python",
    "cursor": "ide",
    "cursor_agent": "ide",
    "openrouter": "llm_api",
    "gemini_deep_research": "llm_api",
    "gemini": "llm_api",
}

VENDOR_LOCK_TOOLS: frozenset[str] = frozenset(
    {
        "neon",
        "supabase",
        "telethon",
        "aiogram",
        "pyrogram",
        "cursor",
        "cursor_agent",
        "openrouter",
        "gemini_deep_research",
        "gemini",
        "rawlead",
    }
)

# Regex → slug (canonical_tag предпочтительнее KNOWN_TOOLS для audit pass).
_TZ_TOOL_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bfigma\b|\bфигма\b", re.I), "figma"),
    (re.compile(r"\bphotoshop\b|\bфотошоп\b|\bpsd\b", re.I), "photoshop"),
    (re.compile(r"\billustrator\b|\bиллюстратор\b", re.I), "illustrator"),
    (re.compile(r"\bafter\s*effects\b|\baftereffects\b", re.I), "after_effects"),
    (re.compile(r"\bpremiere\b", re.I), "premiere_pro"),
    (re.compile(r"\bcinema\s*4d\b", re.I), "cinema_4d"),
    (re.compile(r"\bpython\b|\bпитон\b|\bpy\b(?!\w)", re.I), "python"),
    (re.compile(r"\bphp\b|\blaravel\b", re.I), "php"),
    (re.compile(r"\bwordpress\b|\bwp\b|\bвордпресс\b|\belementor\b|\bwoocommerce\b", re.I), "wordpress_dev"),
    (re.compile(r"\bjavascript\b|\breact\b|\bvue\b|\bnode\.?js\b", re.I), "javascript"),
    (re.compile(r"\bgoogle\s+apps\s+script\b|\bapps\s+script\b", re.I), "google_apps_script"),
    (re.compile(r"\brhino\b|\bрино\b", re.I), "rhino"),
    (re.compile(r"\bgoogle\s+sheet", re.I), "google_sheets_api"),
    (re.compile(r"\btelegram\b|\bтелеграм\b|\btg\b|\baiogram\b|\btelethon\b", re.I), "telegram_bot_dev"),
    (re.compile(r"\bпарсинг\b|\bscraping\b|\bscraper\b|\bпарсер\b", re.I), "web_scraping"),
    (re.compile(r"\bseo\b|\bсео\b|\bsearch\s+console\b|\btilda\b|\bтильда\b", re.I), "seo"),
    (re.compile(r"\bsmm\b|\bсмм\b", re.I), "smm"),
    (re.compile(r"\bmailwizz\b|\bspf\b|\bdkim\b|\bdmarc\b", re.I), "email_marketing"),
    (re.compile(r"\bmysql\b|\bpostgresql\b|\bpostgres\b", re.I), "mysql"),
    (re.compile(r"\bpowerpoint\b|\bppt\b|\bпрезентац", re.I), "powerpoint"),
    (re.compile(r"\bexcel\b|\bcsv\b", re.I), "excel"),
    (re.compile(r"\bblender\b", re.I), "blender"),
    (re.compile(r"\bselenium\b", re.I), "selenium"),
    (re.compile(r"\bton\b|\bnft\b|\bblockchain\b", re.I), "blockchain"),
)

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_CONSULTATION_MARKERS = re.compile(
    r"консультац|консалтинг|аудит|сопровожден|нужна\s+консультац|без\s+работ\s+исполнител",
    re.I,
)
_RHINO_3D_MARKERS = re.compile(
    r"\brhino\b|\bрино\b|grasshopper|\b3d\b|cad|черт[её]ж|моделир",
    re.I,
)


def _slug_has_cyrillic(slug: str) -> bool:
    return bool(slug and _CYRILLIC_RE.search(slug))


def _tz_hay(*chunks: str) -> str:
    return "\n".join(c for c in chunks if c)


def _has_consultation_markers(*chunks: str) -> bool:
    return bool(_CONSULTATION_MARKERS.search(_tz_hay(*chunks)))


def _has_rhino_3d_markers(*chunks: str) -> bool:
    return bool(_RHINO_3D_MARKERS.search(_tz_hay(*chunks)))


def normalize_tool_key(raw: str) -> str:
    """Lowercase slug for lookup (spaces/dots/dashes → _)."""
    t = str(raw).strip().lower().lstrip("#")
    t = t.replace(".", "_")
    t = re.sub(r"[\s-]+", "_", t)
    return t


def _resolve_tool_slug(key: str) -> str:
    """Alias → vendor map → canonical_tag → passthrough."""
    k = normalize_tool_key(key)
    if not k:
        return ""
    if k in _TOOL_ALIAS_MAP:
        k = _TOOL_ALIAS_MAP[k]
    k = _VENDOR_TOOL_MAP.get(k, k)
    canon = resolve_canonical_tag(k)
    if canon and canon in CANONICAL_TAGS:
        return canon
    if k in KNOWN_TOOLS:
        return k
    return k


def map_tool_to_generic(key: str) -> str:
    return _resolve_tool_slug(key)


def tools_from_tz_text(*chunks: str) -> list[str]:
    """Инструменты/теги из текста ТЗ (fallback если L2 пустой или мусор)."""
    hay = "\n".join(c for c in chunks if c)
    out: list[str] = []
    seen: set[str] = set()
    for pat, slug in _TZ_TOOL_HINTS:
        if pat.search(hay) and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return out


def normalize_tools_required(raw: Any, *, limit: int = 8) -> tuple[str, ...]:
    """Lowercase, alias, vendor→generic, dedupe, cap — for L2 ingest and feed display."""
    if isinstance(raw, (list, tuple)):
        items = [str(t) for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        items = [raw.strip()]
    else:
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        mapped = _resolve_tool_slug(item)
        if (
            mapped
            and not _slug_has_cyrillic(mapped)
            and mapped not in seen
            and is_known_tool(mapped)
        ):
            seen.add(mapped)
            out.append(mapped)
        if len(out) >= limit:
            break
    return tuple(out)


def finalize_tools_for_lead(
    tools: tuple[str, ...] | list[str],
    *,
    title: str = "",
    snippet: str = "",
    task_summary: str = "",
    limit: int = 8,
) -> tuple[str, ...]:
    """O98/L2-tune: нормализация + known + consulting/rhino guards + добор из ТЗ до min 2."""
    tz_chunks = (title, snippet, task_summary)
    out = list(normalize_tools_required(tools, limit=limit))

    if "rhino" in out and not _has_rhino_3d_markers(*tz_chunks):
        out = [t for t in out if t != "rhino"]
    if "consulting" in out and not _has_consultation_markers(*tz_chunks):
        out = [t for t in out if t != "consulting"]

    out = list(normalize_tools_required(out, limit=limit))
    if len(out) < 2:
        for hint in tools_from_tz_text(*tz_chunks):
            if hint not in out:
                extra = normalize_tools_required([hint], limit=1)
                if extra:
                    out.append(extra[0])
            if len(out) >= 2:
                break
    return normalize_tools_required(out, limit=limit)


def vendor_lock_tools(raw_tools: list[str] | tuple[str, ...]) -> list[str]:
    """Tools still flagged as internal/vendor lock (raw keys before resolve)."""
    locked: list[str] = []
    for t in raw_tools:
        key = normalize_tool_key(t)
        if key in VENDOR_LOCK_TOOLS:
            locked.append(key)
    return locked


def is_known_tool(raw: str) -> bool:
    """Audit: canonical skill alias OR KNOWN_TOOLS slug."""
    slug = _resolve_tool_slug(raw)
    if not slug:
        return False
    if slug in CANONICAL_TAGS:
        return True
    return slug in KNOWN_TOOLS
