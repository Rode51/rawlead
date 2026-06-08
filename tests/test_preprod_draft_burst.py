"""O129: unit smoke for preprod_draft_burst feed id resolution."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from preprod_draft_burst import fetch_feed_lead_ids  # noqa: E402


def test_fetch_feed_lead_ids_empty_auth_falls_back_anon(monkeypatch) -> None:
    calls: list[tuple[str | None, str]] = []

    def fake_http(method, url, *, token=None, timeout=20.0, data=None):
        calls.append((token, url))
        if token:
            return 0.0, 200, {"items": []}, None
        return 0.0, 200, {"items": [{"id": 42}, {"id": 43}]}, None

    monkeypatch.setattr("preprod_draft_burst._http_json", fake_http)
    ids = fetch_feed_lead_ids("https://api.example", token="prem", limit=2)
    assert ids == [42, 43]
    assert calls[0][0] == "prem"
    assert calls[1][0] is None


def test_fetch_feed_lead_ids_skills_fallback_when_anon_empty(monkeypatch) -> None:
    def fake_http(method, url, *, token=None, timeout=20.0, data=None):
        if token and "skills=design" in url:
            return 0.0, 200, {"items": [{"id": 99}]}, None
        if token:
            return 0.0, 200, {"items": []}, None
        return 0.0, 200, {"items": []}, None

    monkeypatch.setattr("preprod_draft_burst._http_json", fake_http)
    ids = fetch_feed_lead_ids("https://api.example", token="prem", limit=1)
    assert ids == [99]
