"""Человекочитаемый лог цикла радара (§ P1.4)."""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path

from storage import ProjectStorage

SITE_ROLLUP_WINDOW_SEC = 600
SITE_ROLLUP_EMIT_SEC = 600
_STATUS_SITE_ROLLUP = "status_site_rollup_10m"

_STATUS_CYCLE_SUMMARY = "status_cycle_summary"

SOURCE_LABELS: dict[str, str] = {
    "fl": "FL.ru",
    "kwork": "Kwork",
    "vc_ru": "VC.ru",
    "habr_career": "Habr Career",
}

ALL_CYCLE_SOURCES: tuple[str, ...] = (
    "fl",
    "kwork",
    "vc_ru",
    "habr_career",
)


def cycle_log_source_ids() -> tuple[str, ...]:
    """Источники для строк P1.4 — только из PUBLIC_FEED_SOURCES (порядок канона)."""
    from public_feed import public_feed_sources

    enabled = public_feed_sources()
    return tuple(sid for sid in ALL_CYCLE_SOURCES if sid in enabled)


@dataclass
class SourceCycleStats:
    """Счётчики воронки по одному источнику за цикл."""

    source_id: str
    downloaded: int = 0
    new_ids: int = 0
    to_bot: int = 0
    filter_skip: int = 0
    mimo_skip: int = 0
    ai_unavailable: int = 0
    dup_skip: int = 0
    budget_skip: int = 0
    fetch_error: str = ""

    @property
    def label(self) -> str:
        return SOURCE_LABELS.get(self.source_id, self.source_id)

    def note_skip(self, reason: str) -> None:
        if reason == "skip:filter":
            self.filter_skip += 1
        elif reason == "skip:dup_content":
            self.dup_skip += 1
        elif reason == "skip:neon_dup_skip":
            pass
        elif reason == "skip:budget":
            self.budget_skip += 1
        elif reason == "skip:ai_unavailable":
            self.ai_unavailable += 1
        elif reason.startswith("skip:ai:"):
            self.mimo_skip += 1

    def format_line(self) -> str:
        head = (
            f"{self.label:<14}│ скачано {self.downloaded:3d} │ "
            f"новых {self.new_ids:3d} │ в бот {self.to_bot:3d}"
        )
        if self.fetch_error:
            return f"{head} │ ошибка: {self.fetch_error[:80]}"
        tail: list[str] = []
        if self.filter_skip:
            tail.append(f"filter {self.filter_skip}")
        if self.mimo_skip:
            tail.append(f"МИМО {self.mimo_skip}")
        if self.ai_unavailable:
            tail.append(f"ai_unavailable {self.ai_unavailable}")
        if self.dup_skip:
            tail.append(f"dup {self.dup_skip}")
        if self.budget_skip:
            tail.append(f"budget {self.budget_skip}")
        if tail:
            return f"{head} │ {' │ '.join(tail)}"
        return head


@dataclass
class NeonCycleStats:
    """Счётчики Neon за цикл (§ LOG-NEON-CYCLE) — не смешивать с dup SQLite."""

    insert: int = 0
    replay: int = 0
    skip: int = 0
    sqlite_resync: int = 0
    dup_fast_skip: int = 0


_neon_cycle = NeonCycleStats()


def reset_neon_cycle_counters() -> None:
    global _neon_cycle
    _neon_cycle = NeonCycleStats()


def note_neon_insert() -> None:
    _neon_cycle.insert += 1


def note_neon_replay() -> None:
    _neon_cycle.replay += 1


def note_neon_dup_skip() -> None:
    _neon_cycle.skip += 1


def note_neon_sqlite_resync() -> None:
    _neon_cycle.sqlite_resync += 1


def note_dup_fast_skip() -> None:
    _neon_cycle.dup_fast_skip += 1


def log_pipeline_line(log_path: Path | None, line: str) -> None:
    """Строка pipeline:* в radar log (O34 hot path)."""
    if log_path is None:
        return
    from config import radar_timestamp

    try:
        p = Path(log_path)
        if str(p.parent) not in ("", "."):
            p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{radar_timestamp()} {line.rstrip()}\n")
    except OSError:
        pass


def neon_cycle_counts() -> tuple[int, int, int, int, int]:
    return (
        _neon_cycle.insert,
        _neon_cycle.replay,
        _neon_cycle.skip,
        _neon_cycle.sqlite_resync,
        _neon_cycle.dup_fast_skip,
    )


@dataclass
class CycleSummary:
    ts: str
    sources: dict[str, SourceCycleStats] = field(default_factory=dict)
    total_to_bot: int = 0
    neon_insert: int = 0
    neon_replay: int = 0
    neon_dup_skip: int = 0
    neon_sqlite_resync: int = 0
    dup_fast_skip: int = 0
    is_visible: int = 0
    cycle_sec: float = 0.0
    misc_errors: list[str] = field(default_factory=list)

    def ensure(self, source_id: str) -> SourceCycleStats:
        if source_id not in self.sources:
            self.sources[source_id] = SourceCycleStats(source_id=source_id)
        return self.sources[source_id]

    def iter_sources(self) -> list[SourceCycleStats]:
        return [self.ensure(sid) for sid in cycle_log_source_ids()]

    def format_header(self) -> str:
        return f"── Цикл {self.ts} ──"

    def sync_neon_from_globals(self) -> None:
        ins, rep, sk, resync, fast = neon_cycle_counts()
        self.neon_insert = ins
        self.neon_replay = rep
        self.neon_dup_skip = sk
        self.neon_sqlite_resync = resync
        self.dup_fast_skip = fast

    def format_footer(self, *, elapsed_sec: float | None = None) -> str:
        from ai_analyze import cycle_ai_counts

        self.sync_neon_from_globals()
        l1, l2 = cycle_ai_counts()
        parts = [f"Итого в бот: {self.total_to_bot}"]
        if elapsed_sec is not None and elapsed_sec >= 0:
            parts.append(f"цикл: {elapsed_sec:.1f}с")
        if (
            self.neon_insert
            or self.neon_replay
            or self.neon_dup_skip
            or self.neon_sqlite_resync
            or self.dup_fast_skip
        ):
            parts.append(f"neon_insert: {self.neon_insert}")
            if self.neon_replay:
                parts.append(f"neon_replay: {self.neon_replay}")
            if self.neon_sqlite_resync:
                parts.append(f"neon_sqlite_resync: {self.neon_sqlite_resync}")
            if self.neon_dup_skip:
                parts.append(f"neon_dup_skip: {self.neon_dup_skip}")
            if self.dup_fast_skip:
                parts.append(f"dup_fast_skip: {self.dup_fast_skip}")
        parts.append("лента после L1 — см. Neon is_visible")
        base = " │ ".join(parts)
        if l1 or l2:
            return f"{base} │ ИИ L1={l1} L2={l2}"
        return base

    def format_lines(self) -> list[str]:
        lines = [self.format_header(), *[s.format_line() for s in self.iter_sources()]]
        lines.append(self.format_footer())
        if self.misc_errors:
            short = "; ".join(self.misc_errors[:5])
            if len(self.misc_errors) > 5:
                short += " …"
            lines.append(f"Прочее: {short[:400]}")
        return lines

    def to_storage_dict(self) -> dict:
        return {
            "ts": self.ts,
            "sources": {
                sid: asdict(st)
                for sid, st in self.sources.items()
            },
            "total_to_bot": self.total_to_bot,
            "neon_insert": self.neon_insert,
            "neon_replay": self.neon_replay,
            "neon_dup_skip": self.neon_dup_skip,
            "neon_sqlite_resync": self.neon_sqlite_resync,
            "dup_fast_skip": self.dup_fast_skip,
            "is_visible": self.is_visible,
            "cycle_sec": round(self.cycle_sec, 1) if self.cycle_sec else 0.0,
            "misc_errors": self.misc_errors[:10],
        }


def load_cycle_summary(storage: ProjectStorage) -> CycleSummary | None:
    raw = storage.get_setting(_STATUS_CYCLE_SUMMARY, "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    summary = CycleSummary(ts=str(data.get("ts", "")))
    summary.total_to_bot = int(data.get("total_to_bot", 0) or 0)
    summary.neon_insert = int(data.get("neon_insert", 0) or 0)
    summary.neon_replay = int(data.get("neon_replay", 0) or 0)
    summary.neon_dup_skip = int(data.get("neon_dup_skip", 0) or 0)
    summary.neon_sqlite_resync = int(data.get("neon_sqlite_resync", 0) or 0)
    summary.dup_fast_skip = int(data.get("dup_fast_skip", 0) or 0)
    summary.is_visible = int(data.get("is_visible", 0) or 0)
    try:
        summary.cycle_sec = float(data.get("cycle_sec", 0) or 0)
    except (TypeError, ValueError):
        summary.cycle_sec = 0.0
    misc = data.get("misc_errors")
    if isinstance(misc, list):
        summary.misc_errors = [str(x) for x in misc[:10]]
    src_map = data.get("sources")
    if isinstance(src_map, dict):
        for sid, row in src_map.items():
            if not isinstance(row, dict):
                continue
            st = summary.ensure(str(sid))
            st.downloaded = int(row.get("downloaded", 0) or 0)
            st.new_ids = int(row.get("new_ids", 0) or 0)
            st.to_bot = int(row.get("to_bot", 0) or 0)
            st.filter_skip = int(row.get("filter_skip", 0) or 0)
            st.mimo_skip = int(row.get("mimo_skip", 0) or 0)
            st.ai_unavailable = int(row.get("ai_unavailable", 0) or 0)
            st.dup_skip = int(row.get("dup_skip", 0) or 0)
            st.budget_skip = int(row.get("budget_skip", 0) or 0)
            st.fetch_error = str(row.get("fetch_error", "") or "")
    return summary


def record_cycle_summary(storage: ProjectStorage, summary: CycleSummary) -> None:
    """SQLite settings для пульта / TG «Статус»."""
    payload = json.dumps(summary.to_storage_dict(), ensure_ascii=False)
    storage.set_setting(_STATUS_CYCLE_SUMMARY, payload)
    storage.set_setting("status_fl_cycle_at", summary.ts)
    fl = summary.ensure("fl")
    kwork = summary.ensure("kwork")
    total_new = sum(s.new_ids for s in summary.sources.values())
    storage.set_setting("status_fl_cards_fl", str(fl.downloaded))
    storage.set_setting("status_fl_cards_kwork", str(kwork.downloaded))
    storage.set_setting("status_fl_new", str(total_new))
    storage.set_setting("status_fl_notified", str(summary.total_to_bot))
    storage.set_setting(
        "status_fl_errors",
        json.dumps(summary.misc_errors[:5], ensure_ascii=False)
        if summary.misc_errors
        else "[]",
    )


def format_cycle_status_block(storage: ProjectStorage) -> list[str]:
    """Строки «Последний цикл» для format_status_message."""
    summary = load_cycle_summary(storage)
    if summary is None or not summary.ts:
        return ["Последний цикл: ещё не было"]
    lines = [f"Последний цикл: {summary.ts}"]
    lines.extend(s.format_line() for s in summary.iter_sources())
    footer_bits = [f"Итого в бот: {summary.total_to_bot}"]
    if (
        summary.neon_insert
        or summary.neon_replay
        or summary.neon_dup_skip
        or summary.neon_sqlite_resync
    ):
        footer_bits.append(f"neon_insert: {summary.neon_insert}")
        if summary.neon_replay:
            footer_bits.append(f"neon_replay: {summary.neon_replay}")
        if summary.neon_sqlite_resync:
            footer_bits.append(f"neon_sqlite_resync: {summary.neon_sqlite_resync}")
        if summary.neon_dup_skip:
            footer_bits.append(f"neon_dup_skip: {summary.neon_dup_skip}")
        if summary.dup_fast_skip:
            footer_bits.append(f"dup_fast_skip: {summary.dup_fast_skip}")
        if summary.is_visible:
            footer_bits.append(f"is_visible: {summary.is_visible}")
    lines.append(" │ ".join(footer_bits))
    rollup_line = load_site_rollup_line(storage)
    if rollup_line:
        lines.append(f"Сводка 10 мин: {rollup_line}")
    if summary.misc_errors:
        lines.append("Прочие ошибки:")
        for err in summary.misc_errors[:3]:
            lines.append(f"  · {err[:120]}")
    return lines


@dataclass
class SiteRollupTotals:
    downloaded: int = 0
    new_sqlite: int = 0
    neon_insert: int = 0
    neon_replay: int = 0
    l1: int = 0
    l2: int = 0
    is_visible: int = 0
    filter_skip: int = 0
    mimo_skip: int = 0


@dataclass
class _SiteRollupSlice:
    ts: float
    downloaded: int = 0
    new_sqlite: int = 0
    neon_insert: int = 0
    neon_replay: int = 0
    l1: int = 0
    l2: int = 0
    is_visible: int = 0
    filter_skip: int = 0
    mimo_skip: int = 0


_site_rollup_slices: deque[_SiteRollupSlice] = deque()
_site_rollup_current: _SiteRollupSlice | None = None
_site_rollup_last_emit: float = 0.0
_site_rollup_zero_hint: str = ""


def reset_site_rollup_emit_clock() -> None:
    """Старт процесса: первый emit через SITE_ROLLUP_EMIT_SEC."""
    global _site_rollup_last_emit
    _site_rollup_last_emit = time.monotonic()


def begin_site_rollup_cycle() -> None:
    global _site_rollup_current
    _site_rollup_current = _SiteRollupSlice(ts=time.monotonic())


def note_site_rollup_is_visible() -> None:
    if _site_rollup_current is not None:
        _site_rollup_current.is_visible += 1


def note_site_rollup_after_lite(
    lite: object | None,
    *,
    category: str,
    source_public: bool,
) -> None:
    """Счётчик is_visible — та же логика порога, что Neon update_after_lite."""
    if not source_public or _site_rollup_current is None:
        return
    from ai_analyze import AiLiteAnalysis

    if lite is None or not isinstance(lite, AiLiteAnalysis):
        note_site_rollup_is_visible()
        return
    if lite.is_skip_verdict():
        return
    score = {
        "брать": 85,
        "брат": 85,
        "сомнительно": 55,
        "пропустить": 25,
        "мимо": 15,
    }.get(lite.verdict.strip().casefold(), 50)
    cat = category.strip().casefold()
    threshold = 50 if cat in ("design", "marketing", "text") else 40
    if score >= threshold:
        note_site_rollup_is_visible()


def _rollup_zero_hint(summary: CycleSummary) -> str:
    fetch_errors = [
        s.fetch_error.strip()
        for s in summary.sources.values()
        if s.fetch_error.strip()
    ]
    if fetch_errors:
        return f"fetch: {fetch_errors[0][:80]}"
    if summary.misc_errors:
        return summary.misc_errors[0][:80]
    if not any(s.downloaded for s in summary.sources.values()):
        return "скачано 0 — биржи без новых карточек или fetch пуст"
    return ""


def commit_site_rollup_cycle(summary: CycleSummary) -> None:
    """Зафиксировать срез цикла в скользящем окне 10 мин."""
    global _site_rollup_current, _site_rollup_zero_hint
    from ai_analyze import cycle_ai_counts

    summary.sync_neon_from_globals()
    l1, l2 = cycle_ai_counts()
    downloaded = sum(s.downloaded for s in summary.sources.values())
    new_sqlite = sum(s.new_ids for s in summary.sources.values())
    filter_skip = sum(s.filter_skip for s in summary.sources.values())
    mimo_skip = sum(s.mimo_skip for s in summary.sources.values())

    if _site_rollup_current is None:
        begin_site_rollup_cycle()
    assert _site_rollup_current is not None
    cur = _site_rollup_current
    cur.downloaded = downloaded
    cur.new_sqlite = new_sqlite
    cur.neon_insert = summary.neon_insert
    cur.neon_replay = summary.neon_replay
    cur.l1 = l1
    cur.l2 = l2
    cur.filter_skip = filter_skip
    cur.mimo_skip = mimo_skip
    summary.is_visible = cur.is_visible

    _site_rollup_slices.append(cur)
    _site_rollup_current = None
    _prune_site_rollup_slices()

    if downloaded == 0:
        hint = _rollup_zero_hint(summary)
        if hint:
            _site_rollup_zero_hint = hint


def _prune_site_rollup_slices(*, now: float | None = None) -> None:
    cutoff = (now or time.monotonic()) - SITE_ROLLUP_WINDOW_SEC
    while _site_rollup_slices and _site_rollup_slices[0].ts < cutoff:
        _site_rollup_slices.popleft()


def site_rollup_window_totals() -> SiteRollupTotals:
    now = time.monotonic()
    _prune_site_rollup_slices(now=now)
    totals = SiteRollupTotals()
    for sl in _site_rollup_slices:
        totals.downloaded += sl.downloaded
        totals.new_sqlite += sl.new_sqlite
        totals.neon_insert += sl.neon_insert
        totals.neon_replay += sl.neon_replay
        totals.l1 += sl.l1
        totals.l2 += sl.l2
        totals.is_visible += sl.is_visible
        totals.filter_skip += sl.filter_skip
        totals.mimo_skip += sl.mimo_skip
    return totals


def format_site_rollup_line(
    totals: SiteRollupTotals,
    *,
    zero_hint: str = "",
) -> str:
    line = (
        f"site:сводка │ 10мин │ скачано {totals.downloaded} │ "
        f"новых_sqlite {totals.new_sqlite} │ "
        f"neon_insert {totals.neon_insert} │ neon_replay {totals.neon_replay} │ "
        f"l1 {totals.l1} │ l2 {totals.l2} │ "
        f"is_visible {totals.is_visible} │ filter {totals.filter_skip} │ "
        f"мимо {totals.mimo_skip}"
    )
    if totals.downloaded == 0 and zero_hint:
        line += f" │ {zero_hint}"
    return line


def site_rollup_emit_due() -> bool:
    return time.monotonic() - _site_rollup_last_emit >= SITE_ROLLUP_EMIT_SEC


def emit_site_rollup_line(
    storage: ProjectStorage | None = None,
    *,
    zero_hint: str = "",
) -> str:
    """Сформировать строку сводки и обновить часы emit (§ SITE-LOG-ROLLUP)."""
    global _site_rollup_last_emit, _site_rollup_zero_hint
    totals = site_rollup_window_totals()
    hint = zero_hint or (
        _site_rollup_zero_hint if totals.downloaded == 0 else ""
    )
    line = format_site_rollup_line(totals, zero_hint=hint)
    _site_rollup_last_emit = time.monotonic()
    if storage is not None:
        record_site_rollup_line(storage, line)
    if totals.downloaded > 0:
        _site_rollup_zero_hint = ""
    return line


def record_site_rollup_line(storage: ProjectStorage, line: str) -> None:
    storage.set_setting(_STATUS_SITE_ROLLUP, line)


def load_site_rollup_line(storage: ProjectStorage) -> str:
    return storage.get_setting(_STATUS_SITE_ROLLUP, "").strip()


def parse_site_rollup_metrics(line: str) -> tuple[int, int, int]:
    """Из строки site:сводка извлечь (l1, l2, is_visible)."""
    l1 = l2 = visible = 0
    if not line.strip():
        return l1, l2, visible
    for part in line.split("│"):
        token = part.strip()
        for key, slot in (("l1", "l1"), ("l2", "l2"), ("is_visible", "visible")):
            if token.startswith(f"{key} "):
                try:
                    val = int(token.split()[1])
                except (IndexError, ValueError):
                    val = 0
                if slot == "l1":
                    l1 = val
                elif slot == "l2":
                    l2 = val
                else:
                    visible = val
    return l1, l2, visible
