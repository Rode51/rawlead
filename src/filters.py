"""Уровень 2: правила из docs/ops/FILTERS.md — «берём» / «стоп» по заголовку и краткому описанию листинга.

Публичный API для main: `default_listing_filter()` / `ListingWordFilter.from_path`,
`accepts(title, listing_snippet)` / `rejects(...)`, `accepts_listing(ListingProject)`.
"""

from __future__ import annotations

__all__ = [
    "parse_filters_markdown",
    "ListingWordFilter",
    "default_listing_filter",
]

import re
from dataclasses import dataclass
from pathlib import Path

from listing import ListingProject

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_FILTERS_PATH = _PROJECT_ROOT / "docs" / "ops" / "FILTERS.md"

# В markdown: **Категория:** слова — двоеточие внутри жирного, конец жирного сразу после «:».
_TAKE_LINE = re.compile(r"^\*\*.+?:\*\*\s*(.+)$")


def _strip_inline_note(token: str) -> str:
    """Убирает хвост «(если не …)» в одном пункте markdown — само слово остаётся."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", token.strip()).strip()


def _split_keywords(blob: str) -> list[str]:
    out: list[str] = []
    for part in blob.split(","):
        cleaned = _strip_inline_note(part)
        if cleaned:
            out.append(cleaned)
    return out


def parse_filters_markdown(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """
    Извлекает списки «берём» и «стоп» из текста FILTERS.md (уровень 2).
    Не меняет сами слова — только читает структуру файла.
    """
    take_raw: list[str] = []
    stop_raw: list[str] = []
    mode: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("### Берём"):
            mode = "take"
            continue
        if line.startswith("### Отсекаем"):
            mode = "stop"
            continue
        if line.startswith("## Уровень 3"):
            break

        if mode == "take":
            m = _TAKE_LINE.match(line.strip())
            if m:
                take_raw.extend(_split_keywords(m.group(1)))
        elif mode == "stop":
            s = line.strip()
            if s.startswith("- "):
                stop_raw.extend(_split_keywords(s[2:]))

    if not take_raw:
        raise ValueError(
            "В docs/ops/FILTERS.md не найдены ключевые слова «берём» "
            "(ожидаются строки вида **Категория:** слово1, слово2 после заголовка ### Берём)."
        )

    def _dedupe(items: list[str]) -> tuple[str, ...]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return tuple(out)

    return _dedupe(take_raw), _dedupe(stop_raw)


@dataclass(frozen=True)
class ListingWordFilter:
    """Правило уровня 2: есть хотя бы одно «берём» (подстрока, без регистра) и ни одного «стоп»."""

    take: tuple[str, ...]
    stop: tuple[str, ...]

    @classmethod
    def from_path(cls, path: Path) -> ListingWordFilter:
        text = path.read_text(encoding="utf-8")
        take, stop = parse_filters_markdown(text)
        return cls(take=take, stop=stop)

    def haystack(self, title: str, listing_snippet: str = "") -> str:
        return f"{title}\n{listing_snippet}".casefold()

    def accepts(self, title: str, listing_snippet: str = "", *, wide: bool = False) -> bool:
        """Проходит ли текст: wide=только стоп; иначе нужно слово из «берём» и нет стопа."""
        hay = self.haystack(title, listing_snippet)
        for s in self.stop:
            if s.casefold() in hay:
                return False
        if wide:
            return True
        for t in self.take:
            if t.casefold() in hay:
                return True
        return False

    def rejects(self, title: str, listing_snippet: str = "", *, wide: bool = False) -> bool:
        return not self.accepts(title, listing_snippet, wide=wide)

    def accepts_listing(self, project: ListingProject, *, wide: bool = False) -> bool:
        return self.accepts(project.title, project.listing_snippet, wide=wide)


def default_listing_filter() -> ListingWordFilter:
    """Правила из docs/ops/FILTERS.md."""
    return ListingWordFilter.from_path(_DEFAULT_FILTERS_PATH)
