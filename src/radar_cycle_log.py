"""Человекочитаемый лог цикла радара (§ P1.4)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from storage import ProjectStorage

_STATUS_CYCLE_SUMMARY = "status_cycle_summary"

SOURCE_LABELS: dict[str, str] = {
    "fl": "FL.ru",
    "kwork": "Kwork",
    "vc_ru": "VC.ru",
    "freelancehunt": "Freelancehunt",
    "habr_career": "Habr Career",
}

ALL_CYCLE_SOURCES: tuple[str, ...] = (
    "fl",
    "kwork",
    "vc_ru",
    "freelancehunt",
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


def neon_cycle_counts() -> tuple[int, int, int, int]:
    return (
        _neon_cycle.insert,
        _neon_cycle.replay,
        _neon_cycle.skip,
        _neon_cycle.sqlite_resync,
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
        ins, rep, sk, resync = neon_cycle_counts()
        self.neon_insert = ins
        self.neon_replay = rep
        self.neon_dup_skip = sk
        self.neon_sqlite_resync = resync

    def format_footer(self) -> str:
        from ai_analyze import cycle_ai_counts

        self.sync_neon_from_globals()
        l1, l2 = cycle_ai_counts()
        parts = [f"Итого в бот: {self.total_to_bot}"]
        if (
            self.neon_insert
            or self.neon_replay
            or self.neon_dup_skip
            or self.neon_sqlite_resync
        ):
            parts.append(f"neon_insert: {self.neon_insert}")
            if self.neon_replay:
                parts.append(f"neon_replay: {self.neon_replay}")
            if self.neon_sqlite_resync:
                parts.append(f"neon_sqlite_resync: {self.neon_sqlite_resync}")
            if self.neon_dup_skip:
                parts.append(f"neon_dup_skip: {self.neon_dup_skip}")
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
    lines.append(" │ ".join(footer_bits))
    if summary.misc_errors:
        lines.append("Прочие ошибки:")
        for err in summary.misc_errors[:3]:
            lines.append(f"  · {err[:120]}")
    return lines
