"""Free-form tool names for audit/display — NOT canonical skills / picker (O72b)."""

from __future__ import annotations

import re
from typing import Any

from skills_catalog import CANONICAL_TAGS, resolve_canonical_tag

# Top prod fail names (~30) — audit whitelist only; does not expand CANONICAL_TAGS (51).
KNOWN_TOOLS: frozenset[str] = frozenset(
    {
        "photoshop",
        "canva",
        "illustrator",
        "google_analytics",
        "yandex_metrika",
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
        "google_sheets_api",
        "git",
        "adb",
        "postgresql",
        "mysql",
        "telegram",
        "telegram_bot",
        "python",
        "php",
        "gemini_deep_research",
        "word_processor",
        "style_guide",
        "windows_api",
        "premiere_pro",
        "google_apps_script",
        "rhino",
        "fontlab",
        "elementor",
        "wp_rocket",
        "javascript",
        "html_css",
        "lcp",
    }
)

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
}

# RawLead / executor stack — fail audit if leaked into tools_required (O72e-2, O80).
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
    }
)


def normalize_tool_key(raw: str) -> str:
    """Lowercase slug for KNOWN_TOOLS lookup (spaces/dots/dashes → _)."""
    t = str(raw).strip().lower().lstrip("#")
    t = t.replace(".", "_")
    t = re.sub(r"[\s-]+", "_", t)
    return t


def map_tool_to_generic(key: str) -> str:
    """Map vendor slug to generic tool name; unknown keys pass through."""
    k = normalize_tool_key(key)
    if not k:
        return ""
    return _VENDOR_TOOL_MAP.get(k, k)


def normalize_tools_required(raw: Any, *, limit: int = 8) -> tuple[str, ...]:
    """Lowercase, vendor→generic, dedupe, cap — for L2 ingest and feed display."""
    if isinstance(raw, list):
        items = [str(t) for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        items = [raw.strip()]
    else:
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        mapped = map_tool_to_generic(item)
        if mapped and mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
        if len(out) >= limit:
            break
    return tuple(out)


def vendor_lock_tools(raw_tools: list[str] | tuple[str, ...]) -> list[str]:
    """Tools still flagged as internal/vendor lock before generic map."""
    locked: list[str] = []
    for t in raw_tools:
        key = normalize_tool_key(t)
        if key in VENDOR_LOCK_TOOLS:
            locked.append(key)
    return locked


def is_known_tool(raw: str) -> bool:
    """Audit: canonical skill alias OR KNOWN_TOOLS free-form name."""
    canonical = resolve_canonical_tag(raw)
    if canonical and canonical in CANONICAL_TAGS:
        return True
    key = normalize_tool_key(raw)
    if key in KNOWN_TOOLS:
        return True
    generic = map_tool_to_generic(key)
    return generic in KNOWN_TOOLS
