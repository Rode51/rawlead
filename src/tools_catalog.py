"""Free-form tool names for audit/display — NOT canonical skills / picker (O72b)."""

from __future__ import annotations

import re

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
        "neon",
        "gemini_deep_research",
        "word_processor",
        "style_guide",
        "windows_api",
        "premiere_pro",
    }
)


def normalize_tool_key(raw: str) -> str:
    """Lowercase slug for KNOWN_TOOLS lookup (spaces/dots/dashes → _)."""
    t = str(raw).strip().lower().lstrip("#")
    t = t.replace(".", "_")
    t = re.sub(r"[\s-]+", "_", t)
    return t


def is_known_tool(raw: str) -> bool:
    """Audit: canonical skill alias OR KNOWN_TOOLS free-form name."""
    canonical = resolve_canonical_tag(raw)
    if canonical and canonical in CANONICAL_TAGS:
        return True
    return normalize_tool_key(raw) in KNOWN_TOOLS
