"""O206-t4 / O207-t1: TG funnel breakdown from radar log → data/tg_funnel_audit.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

_TS_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\s+UTC)?)"
)
_TG_MSG_RE = re.compile(
    r"тг:сообщ acc=(\w+) chat=(-?\d+) msg=(\d+) новый=(\d+) увед=(\d+) ош=(.+)$"
)
_L1_RE = re.compile(
    r"pipeline:L1 (tg:[^\s]+) visible=(\d+)"
)
_FILTER_RE = re.compile(r"pipeline:skip filter (tg:[^\s]+)")
_SKIP_AI_RE = re.compile(r"skip:ai:([^\s;]+)")


def _parse_ts(line: str) -> datetime | None:
    m = _TS_RE.match(line)
    if not m:
        return None
    raw = m.group(1).replace(" UTC", "").replace("T", " ")
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _within_days(ts: datetime | None, *, since: datetime) -> bool:
    if ts is None:
        return True
    return ts >= since


def _recommendation(*, received: int, visible: int, skip_ai: int, skip_filter: int, mimo: int) -> str:
    mimo_rate = round(mimo / received, 3) if received else 0.0
    visible_rate = round(visible / received, 3) if received else 0.0

    if received < 50:
        return "insufficient_sample: need more тг:сообщ lines in window"
    if mimo_rate >= 0.35 and visible_rate < 0.08:
        return (
            "tg_l1_strict: МИМО dominates; review mimo_samples for false positives "
            "before any threshold change; consider TG allowlist chat bypass only after "
            "manual review of 20 samples"
        )
    if skip_filter > skip_ai * 2:
        return (
            "word_filter_heavy: pipeline:skip filter > skip:ai; check filters.py / "
            "tg_spam_filter before L1 tune"
        )
    if visible_rate >= 0.08:
        return "funnel_ok: visible rate within expected band for job chats"
    return (
        "mixed_funnel: moderate drop; sample chats may be low-signal spam — "
        "no automatic loosen"
    )


def audit_log(path: Path, *, days: int = 7, now: datetime | None = None) -> dict:
    anchor = now or datetime.now(timezone.utc)
    since = anchor - timedelta(days=days)
    counts: Counter[str] = Counter()
    per_account: dict[str, Counter[str]] = defaultdict(Counter)
    mimo_samples: list[dict] = []
    visible_chats: Counter[str] = Counter()

    if not path.is_file():
        return {
            "error": f"log not found: {path}",
            "days": days,
            "since": since.isoformat(),
        }

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ts = _parse_ts(line)
        if not _within_days(ts, since=since):
            continue

        if "тг:сообщ" in line:
            counts["тг:сообщ"] += 1
            m = _TG_MSG_RE.search(line)
            if m:
                acc = m.group(1)
                per_account[acc]["тг:сообщ"] += 1
                err = m.group(6)
                chat = m.group(2)
                if "skip:ai:" in err:
                    counts["skip:ai"] += 1
                    per_account[acc]["skip:ai"] += 1
                    vm = _SKIP_AI_RE.search(err)
                    if vm:
                        verdict = vm.group(1)
                        key = f"skip:ai:{verdict}"
                        counts[key] += 1
                        per_account[acc][key] += 1
                        if verdict == "МИМО" and len(mimo_samples) < 20:
                            mimo_samples.append(
                                {
                                    "ts": ts.isoformat() if ts else "",
                                    "acc": acc,
                                    "chat": chat,
                                    "msg": m.group(3),
                                    "err": err[:200],
                                }
                            )
                if "pipeline:skip filter" in err or "skip:filter" in err:
                    counts["skip:filter"] += 1
                    per_account[acc]["skip:filter"] += 1
                if m.group(4) == "1" and "visible=1" in err:
                    counts["visible=1"] += 1
                    per_account[acc]["visible=1"] += 1

        if "тг:пропуск" in line and "не_слушаем" in line:
            counts["тг:пропуск:не_слушаем"] += 1

        m1 = _L1_RE.search(line)
        if m1:
            src = m1.group(1)
            vis = int(m1.group(2))
            counts["pipeline:L1"] += 1
            if vis:
                counts["visible=1"] += 1
                visible_chats[src] += 1
            else:
                counts["visible=0"] += 1

        if _FILTER_RE.search(line):
            counts["pipeline:skip filter"] += 1

    received = counts["тг:сообщ"]
    visible = counts["visible=1"]
    skip_ai = counts["skip:ai"]
    skip_filter = counts["skip:filter"] + counts["pipeline:skip filter"]
    mimo = counts.get("skip:ai:МИМО", 0)
    mimo_rate = round(mimo / received, 3) if received else 0.0
    visible_rate = round(visible / received, 3) if received else 0.0

    return {
        "log_path": str(path),
        "days": days,
        "since": since.isoformat(),
        "counts": dict(counts),
        "per_account": {acc: dict(c) for acc, c in sorted(per_account.items())},
        "rates": {
            "visible_per_received": visible_rate,
            "mimo_per_received": mimo_rate,
        },
        "mimo_samples": mimo_samples,
        "recommendation": _recommendation(
            received=received,
            visible=visible,
            skip_ai=skip_ai,
            skip_filter=skip_filter,
            mimo=mimo,
        ),
    }


def build_multi_day_report(
    path: Path, *, windows: tuple[int, ...] = (7, 30), now: datetime | None = None
) -> dict:
    anchor = now or datetime.now(timezone.utc)
    sections = {}
    for days in windows:
        key = f"days_{days}"
        sections[key] = audit_log(path, days=days, now=anchor)
    return {
        "generated_at": anchor.isoformat(),
        "log_path": str(path),
        **sections,
    }


def human_summary(report: dict) -> str:
    lines = [
        "# TG funnel audit (O207)",
        "",
        f"Log: `{report.get('log_path', '?')}`",
        f"Generated: {report.get('generated_at', '?')}",
        "",
    ]
    for key in ("days_7", "days_30"):
        block = report.get(key)
        if not block or block.get("error"):
            lines.append(f"## {key}: {block.get('error') if block else 'missing'}")
            lines.append("")
            continue
        days = block.get("days", "?")
        c = block.get("counts", {})
        r = block.get("rates", {})
        lines.extend(
            [
                f"## Last {days} days",
                "",
                f"| Metric | Count |",
                f"|--------|------:|",
                f"| тг:сообщ (received) | {c.get('тг:сообщ', 0)} |",
                f"| skip:filter | {c.get('skip:filter', 0) + c.get('pipeline:skip filter', 0)} |",
                f"| skip:ai (all) | {c.get('skip:ai', 0)} |",
                f"| skip:ai:МИМО | {c.get('skip:ai:МИМО', 0)} |",
                f"| visible=1 | {c.get('visible=1', 0)} |",
                f"| visible rate | {r.get('visible_per_received', 0)} |",
                f"| МИМО rate | {r.get('mimo_per_received', 0)} |",
                "",
                f"**Recommendation:** {block.get('recommendation', '—')}",
                "",
            ]
        )
        per_acc = block.get("per_account") or {}
        if per_acc:
            lines.append("**Per account:**")
            for acc, ac in sorted(per_acc.items()):
                lines.append(
                    f"- `{acc}`: received={ac.get('тг:сообщ', 0)} "
                    f"visible={ac.get('visible=1', 0)} "
                    f"filter={ac.get('skip:filter', 0)} "
                    f"ai={ac.get('skip:ai', 0)}"
                )
            lines.append("")
        samples = block.get("mimo_samples") or []
        if samples and key == "days_7":
            lines.append(f"**МИМО samples (up to {len(samples)}):**")
            for s in samples[:5]:
                lines.append(
                    f"- acc={s.get('acc')} chat={s.get('chat')} msg={s.get('msg')} "
                    f"err={s.get('err', '')[:80]}"
                )
            if len(samples) > 5:
                lines.append(f"- … +{len(samples) - 5} more in JSON")
            lines.append("")
    lines.append(
        "**VPS:** `cd /opt/rawlead && .venv/bin/python scripts/tg_funnel_audit.py "
        "--log data/radar_site.log`"
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="TG funnel audit (O206/O207)")
    parser.add_argument("--log", default="data/radar_site.log")
    parser.add_argument("--days", type=int, default=0, help="Single window; 0 = 7+30")
    parser.add_argument("--out", default="data/tg_funnel_audit.json")
    parser.add_argument(
        "--human-out",
        default="data/tg_funnel_audit_human.md",
        help="Human summary (default when --days=0)",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = _ROOT / log_path

    if args.days > 0:
        report = audit_log(log_path, days=args.days)
    else:
        report = build_multi_day_report(log_path)

    out = Path(args.out)
    if not out.is_absolute():
        out = _ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    human_path = Path(args.human_out)
    if not human_path.is_absolute():
        human_path = _ROOT / human_path
    if args.days <= 0:
        human_path.parent.mkdir(parents=True, exist_ok=True)
        human_path.write_text(human_summary(report), encoding="utf-8")
        print(f"wrote {out} + {human_path}", file=sys.stderr)
    else:
        print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
