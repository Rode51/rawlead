"""O206-t2: join queue done vs telethon file vs filter — per account report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import (  # noqa: E402
    _PROJECT_ROOT,
    parse_telethon_chat_ids,
    telethon_chat_ids_path_for_account,
    telethon_monitor_accounts,
)
from public_feed import (  # noqa: E402
    TG_TEST_GROUP_RAW_ID,
    _chat_id_keys,
    filter_listen_chat_ids,
    tg_test_group_chat_keys,
)
from tg_join_lib import read_queue_csv  # noqa: E402

_STARTUP_RE = re.compile(
    r"тг:монитор:старт account=(\w+) чатов=(\d+) ids=\[(.*?)\]"
)


def _ids_file_has_chat(path: Path, chat_id: int) -> bool:
    if not path.is_file():
        return False
    try:
        listen = set(parse_telethon_chat_ids(str(path)))
    except (OSError, ValueError):
        return False
    keys = _chat_id_keys(chat_id)
    for cid in listen:
        if keys & _chat_id_keys(cid):
            return True
    return False


def _done_rows_for_account(queue_paths: list[Path], account: str) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in queue_paths:
        if not path.is_file():
            continue
        _, rows = read_queue_csv(path)
        for row in rows:
            acc = row.get("account", "").strip().lower()
            if acc != account:
                continue
            if row.get("status", "").strip().lower() != "done":
                continue
            link = row.get("link", "").strip()
            cid = row.get("chat_id", "").strip()
            key = (link, cid)
            if key in seen:
                continue
            seen.add(key)
            rows_out.append(row)
    return rows_out


def _queue_paths() -> list[Path]:
    ops = _PROJECT_ROOT / "docs" / "ops"
    names = ("TG_JOIN_QUEUE.csv", "TG_JOIN_QUEUE_v2.csv", "TG_JOIN_QUEUE_v3.csv")
    return [ops / name for name in names if (ops / name).is_file()]


def _startup_peers_from_log(log_path: Path, account: str) -> int | None:
    if not log_path.is_file():
        return None
    last: int | None = None
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _STARTUP_RE.search(line)
        if not m or m.group(1) != account:
            continue
        last = int(m.group(2))
    return last


def build_report(*, log_path: Path | None = None) -> dict:
    queue_paths = _queue_paths()
    accounts = list(telethon_monitor_accounts()) or ["acc1", "acc2", "acc3"]
    per_account: dict[str, dict] = {}
    gaps: list[str] = []

    for account in accounts:
        done_rows = _done_rows_for_account(queue_paths, account)
        done_with_cid = [r for r in done_rows if r.get("chat_id", "").strip()]
        ids_path = telethon_chat_ids_path_for_account(account)
        try:
            file_ids = parse_telethon_chat_ids(str(ids_path))
        except (OSError, ValueError):
            file_ids = []
        filtered = filter_listen_chat_ids(file_ids)
        missing_in_file: list[str] = []
        for row in done_with_cid:
            try:
                cid = int(row["chat_id"].strip())
            except ValueError:
                continue
            if not _ids_file_has_chat(ids_path, cid):
                missing_in_file.append(str(cid))
        peers = _startup_peers_from_log(log_path, account) if log_path else None
        test_in_file = _ids_file_has_chat(ids_path, TG_TEST_GROUP_RAW_ID)
        row = {
            "queue_done": len(done_rows),
            "queue_done_with_chat_id": len(done_with_cid),
            "ids_file": len(file_ids),
            "after_filter": len(filtered),
            "startup_peers": peers,
            "test_group_in_file": test_in_file,
            "missing_chat_ids_in_file": missing_in_file,
            "ids_path": str(ids_path),
        }
        per_account[account] = row
        if missing_in_file:
            gaps.append(f"{account}: {len(missing_in_file)} done chat_id not in file")
        if peers is not None and peers < len(filtered):
            # File synced but a few ids may fail get_entity at startup (not in session).
            entity_tol = 3
            if missing_in_file or peers < len(filtered) - entity_tol:
                gaps.append(
                    f"{account}: startup peers={peers} < after_filter={len(filtered)}"
                )
        if not test_in_file:
            gaps.append(f"{account}: test group {TG_TEST_GROUP_RAW_ID} missing in file")

    test_keys = tg_test_group_chat_keys()
    return {
        "queue_files": [str(p) for p in queue_paths],
        "test_group_keys": sorted(test_keys),
        "per_account": per_account,
        "gaps": gaps,
        "ok": not gaps,
        "hint": (
            "Run: python scripts/tg_sync_chat_ids.py --account all "
            "then restart tg_main; probe: scripts/probe_tg_test_group_membership.py"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TG join=listen audit (O206-t2)")
    parser.add_argument(
        "--log",
        default="data/radar_site.log",
        help="Radar log for last startup peers per account",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Write JSON report (default: stdout only)",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = _ROOT / log_path
    report = build_report(log_path=log_path if log_path.is_file() else None)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = _ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
