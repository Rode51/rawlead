"""O133-TZ-BACKFILL: mock fetch+enrich → dry-run / apply UPDATE."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import backfill_tz_attachments as bf  # noqa: E402
from tz_attachments import ATTACHMENT_EXTRACTED_MARKER  # noqa: E402


def _lead(
    *,
    lead_id: int = 19944,
    source: str = "kwork",
    external_id: str = "3193806",
    body: str = "Нужен лендинг, ТЗ прикреплено к заказу",
) -> bf.BackfillLead:
    return bf.BackfillLead(
        lead_id=lead_id,
        source=source,
        external_id=external_id,
        title="Тест",
        body=body,
        url=f"https://kwork.ru/projects/{external_id}/view",
        budget_text="5000 ₽",
        ai_reasons=["причина 1"],
    )


def test_strip_tz_attachment_blocks_removes_markers():
    old = (
        "Описание заказа\n\n"
        f"{ATTACHMENT_EXTRACTED_MARKER} из brief.pdf]\nстарый текст"
    )
    assert bf.strip_tz_attachment_blocks(old) == "Описание заказа"
    assert bf.strip_tz_attachment_blocks("plain body") == "plain body"


def test_strip_idempotent_on_re_enrich():
    base = "Описание заказа"
    enriched = (
        f"{base}\n\n{ATTACHMENT_EXTRACTED_MARKER} из brief.pdf]\nновый текст"
    )
    stripped = bf.strip_tz_attachment_blocks(enriched)
    assert stripped == base
    re_enriched = f"{stripped}\n\n{ATTACHMENT_EXTRACTED_MARKER} из brief.pdf]\nновый текст"
    assert re_enriched.count(ATTACHMENT_EXTRACTED_MARKER) == 1


@patch("backfill_tz_attachments._resolve_ingest_body")
def test_process_lead_dry_run_no_update(mock_resolve: MagicMock):
    enriched = (
        "Описание\n\n"
        f"{ATTACHMENT_EXTRACTED_MARKER} из tz.pdf]\nТекст из PDF"
    )
    mock_resolve.return_value = (
        enriched,
        {"status": "extracted", "filename": "tz.pdf", "size_mb": 0.1, "reason": "extracted"},
    )
    lead = _lead()
    cfg = MagicMock()
    cur = MagicMock()

    result = bf.process_lead(lead, cfg, apply=False, cur=cur)

    assert result.skipped is False
    assert result.applied is False
    assert result.old_len == len(lead.body)
    assert result.new_len == len(enriched)
    assert result.marker == "extracted"
    cur.execute.assert_not_called()


@patch("backfill_tz_attachments._resolve_ingest_body")
def test_process_lead_apply_updates_neon(mock_resolve: MagicMock):
    enriched = (
        "Описание\n\n"
        f"{ATTACHMENT_EXTRACTED_MARKER} из tz.pdf]\nТекст из PDF"
    )
    tz_meta = {
        "status": "extracted",
        "filename": "tz.pdf",
        "size_mb": 0.1,
        "reason": "extracted",
    }
    mock_resolve.return_value = (enriched, tz_meta)
    lead = _lead()
    cfg = MagicMock()
    cur = MagicMock()

    result = bf.process_lead(lead, cfg, apply=True, cur=cur)

    assert result.applied is True
    assert result.marker == "extracted"
    cur.execute.assert_called_once()
    sql, params = cur.execute.call_args[0]
    assert "UPDATE leads" in sql
    assert "last_fetch_ok_at" in sql
    assert params[0] == enriched
    assert params[2] == lead.lead_id


@patch("backfill_tz_attachments._resolve_ingest_body")
def test_process_lead_unchanged_skips_apply(mock_resolve: MagicMock):
    body = "same body"
    mock_resolve.return_value = (body, None)
    lead = _lead(body=body)
    cur = MagicMock()

    result = bf.process_lead(lead, MagicMock(), apply=True, cur=cur)

    assert result.skipped is True
    assert result.skip_reason == "unchanged"
    cur.execute.assert_not_called()


def test_process_lead_unsupported_source():
    lead = _lead(source="youdo")
    result = bf.process_lead(lead, MagicMock(), apply=False)
    assert result.skipped is True
    assert result.skip_reason == "unsupported_source"


@patch("backfill_tz_attachments._resolve_ingest_body")
def test_idempotent_second_run_same_body(mock_resolve: MagicMock):
    """Повторный run с тем же enriched body → unchanged, без дубля маркера."""
    body_with_marker = (
        "Описание\n\n"
        f"{ATTACHMENT_EXTRACTED_MARKER} из tz.pdf]\nТекст"
    )
    mock_resolve.return_value = (body_with_marker, None)
    lead = _lead(body=body_with_marker)

    result = bf.process_lead(lead, MagicMock(), apply=True, cur=MagicMock())

    assert result.skipped is True
    assert result.skip_reason == "unchanged"


def test_fetch_leads_by_external_id():
    cur = MagicMock()
    cur.fetchone.return_value = (
        19944,
        "kwork",
        "3193806",
        "title",
        "body",
        "https://kwork.ru/projects/3193806/view",
        "5k",
        ["r1"],
    )
    leads = bf.fetch_leads(
        cur,
        lead_id=None,
        external_id="3193806",
        source="kwork",
        limit=20,
    )
    assert len(leads) == 1
    assert leads[0].lead_id == 19944
    cur.execute.assert_called_once()
