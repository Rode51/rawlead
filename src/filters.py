"""Уровень 2: правила из docs/ops/FILTERS.md — «берём» / «стоп» по заголовку и краткому описанию листинга.

Публичный API для main: `default_listing_filter()` / `ListingWordFilter.from_path`,
`accepts(title, listing_snippet)` / `rejects(...)`, `accepts_listing(ListingProject)`.
"""

from __future__ import annotations

__all__ = [
    "parse_filters_markdown",
    "ListingWordFilter",
    "default_listing_filter",
    "TG_WIDE_SOFT_STOPS",
    "EXCHANGE_SAFE_STOPS",
    "tg_filter_soft_bypass",
    "exchange_filter_soft_stops",
]

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from lead_category import category_for_listing
from listing import SOURCE_FL, SOURCE_KWORK, ListingProject

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Синхрон с docs/ops/FILTERS.md § Vision v0.10 (v0.10.1)
_GLOBAL_ALWAYS_STOP: tuple[str, ...] = (
    "виртуальный ассистент",
    "va ",
    "диктор",
    "озвучка",
    "голос за",
)
# O207b: FILTERS.md skill stops that block real TG vacancies in FILTER_WIDE mode.
TG_WIDE_SOFT_STOPS: tuple[str, ...] = (
    "figma",
    "фигма",
    "монтаж",
    "монтаж рилс",
    "логотип",
    "баннер",
    "вебинар",
    "иллюстратор",
    "va",
)
_TG_WIDE_SOFT_STOPS_CF: frozenset[str] = frozenset(
    token.casefold() for token in TG_WIDE_SOFT_STOPS
)
# O213: FILTERS.md stops tuned for TG noise — allow on kwork/fl when matched.
EXCHANGE_SAFE_STOPS: tuple[str, ...] = (
    "вебинар",
    "логотип",
    "баннер",
    "дизайн макета",
    "figma",
    "фигма",
    "монтаж",
    "монтаж рилс",
    "иллюстратор",
)
_EXCHANGE_SAFE_STOPS_CF: frozenset[str] = frozenset(
    token.casefold() for token in EXCHANGE_SAFE_STOPS
)
_TG_TEAM_HIRING_MARKERS: tuple[str, ...] = (
    "в команду",
    "в нашу команду",
    "набор в команду",
)

_CATEGORY_STOP: dict[str, tuple[str, ...]] = {
    "dev": (
        "1с",
        "битрикс",
        "bitrix",
        "сисадмин",
        "администрирование сервер",
        "windows server",
        "настройка домена",
    ),
    "design": (
        "рендеринг интерьер",
        "архитектурная визуализация",
        "ландшафтный дизайн",
        "планировка квартир",
    ),
    "marketing": (
        "обзвон",
        "холодные звонки",
        "лайки за",
        "накрутка подписчик",
        "капча-ферм",
        "ручной ввод капчи",
        "реферальн",
        "пирамид",
    ),
    "text": (
        "диплом",
        "реферат",
        "курсовая",
        "контрольная",
        "решебник",
        "ручная транскрибац",
        "расшифровка аудио вручную",
    ),
}

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
        if line.startswith("### TG"):
            mode = "stop"
            continue
        if line.startswith("## Уровень 3") or line.startswith("## Vision v0.10"):
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


def tg_filter_soft_bypass(
    title: str,
    listing_snippet: str = "",
    *,
    wide: bool,
    source: str = "",
) -> bool:
    """True when TG wide filter may ignore TG_WIDE_SOFT_STOPS (O207b)."""
    if not wide or not str(source).startswith("tg:"):
        return False
    from tg_spam_filter import is_tg_order_post

    if not is_tg_order_post(title, listing_snippet):
        return False
    hay = f"{title}\n{listing_snippet}".casefold()
    for marker in _TG_TEAM_HIRING_MARKERS:
        if marker in hay:
            return False
    return True


def exchange_filter_soft_stops(source: str) -> frozenset[str]:
    """O213: kwork/fl may ignore EXCHANGE_SAFE_STOPS (TG path unchanged)."""
    if source in (SOURCE_KWORK, SOURCE_FL):
        return _EXCHANGE_SAFE_STOPS_CF
    return frozenset()


def _log_exchange_filter_safe(project: ListingProject, stop: str) -> None:
    line = (
        f"pipeline:filter:exchange_safe {project.source}:id={project.project_id} "
        f"stop={stop}"
    )
    try:
        from config import load_config, load_radar_env
        from radar_cycle_log import log_pipeline_line

        load_radar_env()
        log_pipeline_line(load_config().radar_log_path, line)
    except Exception:
        logger.info("%s", line)


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

    def accepts(
        self,
        title: str,
        listing_snippet: str = "",
        *,
        wide: bool = False,
        soft_bypass: bool = False,
        soft_stops: frozenset[str] | None = None,
    ) -> bool:
        """Проходит ли текст: wide=только стоп; иначе нужно слово из «берём» и нет стопа."""
        hay = self.haystack(title, listing_snippet)
        if soft_stops is not None:
            skip = soft_stops
        elif soft_bypass:
            skip = _TG_WIDE_SOFT_STOPS_CF
        else:
            skip = frozenset()
        for s in self.stop:
            if s.casefold() in skip:
                continue
            if s.casefold() in hay:
                return False
        if wide:
            return True
        for t in self.take:
            if t.casefold() in hay:
                return True
        return False

    def rejects(
        self,
        title: str,
        listing_snippet: str = "",
        *,
        wide: bool = False,
        soft_bypass: bool = False,
        soft_stops: frozenset[str] | None = None,
    ) -> bool:
        return not self.accepts(
            title,
            listing_snippet,
            wide=wide,
            soft_bypass=soft_bypass,
            soft_stops=soft_stops,
        )

    def rejects_category(
        self,
        title: str,
        listing_snippet: str = "",
        *,
        category: str | None,
    ) -> bool:
        hay = self.haystack(title, listing_snippet)
        for token in _GLOBAL_ALWAYS_STOP:
            if token.casefold() in hay:
                return True
        cat = (category or "").strip().casefold()
        if cat in _CATEGORY_STOP:
            for token in _CATEGORY_STOP[cat]:
                if token.casefold() in hay:
                    return True
        return False

    def accepts_listing(self, project: ListingProject, *, wide: bool = False) -> bool:
        soft_stops: frozenset[str] = frozenset()
        if tg_filter_soft_bypass(
            project.title,
            project.listing_snippet,
            wide=wide,
            source=project.source,
        ):
            soft_stops |= _TG_WIDE_SOFT_STOPS_CF
        exchange_soft = exchange_filter_soft_stops(project.source)
        if exchange_soft:
            hay = self.haystack(project.title, project.listing_snippet)
            matched = next(
                (
                    s
                    for s in self.stop
                    if s.casefold() in exchange_soft and s.casefold() in hay
                ),
                None,
            )
            if matched:
                soft_stops |= exchange_soft
                _log_exchange_filter_safe(project, matched)
        if not self.accepts(
            project.title,
            project.listing_snippet,
            wide=wide,
            soft_stops=soft_stops or None,
        ):
            return False
        cat = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=project.listing_snippet,
        )
        return not self.rejects_category(
            project.title, project.listing_snippet, category=cat
        )


def default_listing_filter() -> ListingWordFilter:
    """Правила по RADAR_PROFILE: FILTERS_LEGACY.md или FILTERS_SITE.md."""
    from config import filters_md_path, load_radar_env

    load_radar_env()
    return ListingWordFilter.from_path(filters_md_path())
