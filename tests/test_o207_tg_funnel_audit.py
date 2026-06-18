"""O207-t5: tg_funnel_audit parser counts from fixture log lines."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import tg_funnel_audit as audit  # noqa: E402


FIXTURE_LOG = "\n".join(
    [
        "2026-06-10 10:00:00 тг:сообщ acc=acc1 chat=-100111 msg=1 новый=0 увед=0 ош=pipeline:skip filter tg:-100111:id=1",
        "2026-06-10 10:01:00 тг:сообщ acc=acc1 chat=-100111 msg=2 новый=1 увед=0 ош=pipeline:L1 tg:-100111:id=2 visible=1",
        "2026-06-10 10:02:00 тг:сообщ acc=acc2 chat=-100222 msg=3 новый=0 увед=0 ош=skip:ai:МИМО; pipeline:L1 tg:-100222:id=3 visible=0",
        "2026-06-11 10:00:00 pipeline:L1 tg:-100333:id=4 visible=1",
        "2026-06-11 10:01:00 pipeline:skip filter tg:-100444:id=5",
        "2026-06-05 10:00:00 тг:сообщ acc=acc1 chat=-100999 msg=9 новый=0 увед=0 ош=-",
    ]
)


def test_audit_log_counts_fixture(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(FIXTURE_LOG, encoding="utf-8")
    fixed_now = audit.datetime(2026, 6, 12, 12, 0, 0, tzinfo=audit.timezone.utc)

    report = audit.audit_log(log, days=7, now=fixed_now)
    c = report["counts"]
    assert c["тг:сообщ"] == 3
    assert c["skip:filter"] == 1
    assert c["skip:ai"] == 1
    assert c.get("skip:ai:МИМО") == 1
    assert c["visible=1"] == 3
    assert c["pipeline:skip filter"] == 2
    assert report["per_account"]["acc1"]["тг:сообщ"] == 2
    assert report["per_account"]["acc2"]["тг:сообщ"] == 1
    assert len(report["mimo_samples"]) == 1
    assert report["mimo_samples"][0]["chat"] == "-100222"


def test_build_multi_day_report_keys(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(FIXTURE_LOG, encoding="utf-8")
    fixed_now = audit.datetime(2026, 6, 12, 12, 0, 0, tzinfo=audit.timezone.utc)

    report = audit.build_multi_day_report(log, now=fixed_now)
    assert "days_7" in report
    assert "days_30" in report
    assert report["days_7"]["counts"]["тг:сообщ"] == 3
    assert report["days_30"]["counts"]["тг:сообщ"] == 4


def test_human_summary_renders(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(FIXTURE_LOG, encoding="utf-8")
    fixed_now = audit.datetime(2026, 6, 12, 12, 0, 0, tzinfo=audit.timezone.utc)

    report = audit.build_multi_day_report(log, now=fixed_now)
    md = audit.human_summary(report)
    assert "TG funnel audit" in md
    assert "тг:сообщ" in md
    assert "VPS:" in md
