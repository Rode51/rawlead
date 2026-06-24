"""O280 next E2E — prod runner skipped unless RAWLEAD_O280_E2E=1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts" / "preprod_playwright"))


def test_next_e2e_module_imports() -> None:
    import next_e2e  # noqa: F401
    import next_ui

    assert hasattr(next_e2e, "run_next_e2e")
    assert "n1" in next_e2e.SCENARIOS
    assert "n25" in next_e2e.SCENARIOS
    assert "n25" in next_e2e.DESKTOP_IDS
    assert next_ui.lead_ids_pass_draft_gate(
        [
            {"id": 1, "keyword_match": 42},
            {"id": 2, "keyword_match": 0},
            {"id": 3, "keyword_match": None},
            {"id": 4, "keyword_match": 10},
        ]
    ) == ["1", "4"]


def test_feed_prefs_module_exports() -> None:
    """J3 persist smoke — feed-prefs v3 key + one-shot URL API."""
    prefs_path = _ROOT / "rawlead-next" / "lib" / "feed-prefs.ts"
    text = prefs_path.read_text(encoding="utf-8")
    assert "rawlead_feed_prefs_v3" in text
    assert "FEED_PREFS_KEY_V2" in text
    assert "FEED_PREFS_KEY_V1" in text
    assert "hydrateFilterState" in text
    assert "applyUrlFilterOverridesOnce" in text
    assert "stripFeedFilterParamsFromUrl" in text
    assert "persistFeedPrefs" in text
    assert "mergeFeedPrefsOnLogin" in text


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O280_E2E") != "1",
    reason="J3 feed no TG pill — set RAWLEAD_O280_E2E=1",
)
def test_j3_feed_no_tg_pill_cold_f5() -> None:
    """Cold /lenta/ and F5 — no Telegram source filter (v1 migrate + default empty)."""
    from playwright.sync_api import sync_playwright

    import next_ui as ui

    base_url = os.environ.get("RAWLEAD_O280_BASE_URL", "http://localhost:3001")
    timeout_ms = int(os.environ.get("RAWLEAD_O280_TIMEOUT_MS", "60000"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.environ.get("RAWLEAD_O280_HEADED") != "1")
        ctx = browser.new_context(viewport=ui.DESKTOP_VIEWPORT, locale="ru-RU")
        ctx.add_init_script(
            """() => {
              localStorage.setItem('rawlead_feed_prefs', JSON.stringify({
                sort: 'time', min_match: 80, category: '', source: 'tg', sources: ['tg'],
                updated_at: '2020-01-01T00:00:00.000Z'
              }));
              localStorage.setItem('rawlead_feed_prefs_v2', JSON.stringify({
                sort: 'time', min_match: 80, category: '', source: 'tg', sources: ['tg'],
                updated_at: '2020-01-01T00:00:00.000Z'
              }));
              localStorage.removeItem('rawlead_feed_prefs_v3');
            }"""
        )
        page = ctx.new_page()
        page.set_default_timeout(timeout_ms)
        try:
            ui.goto_lenta(page, base_url)
            ui.wait_feed_prefs_ready(page, timeout_ms=timeout_ms)
            ui.assert_no_tg_source_filter(page)
            assert page.evaluate(
                f"() => localStorage.getItem({ui.FEED_PREFS_KEY_V1!r})"
            ) is None
            assert page.evaluate(
                f"() => localStorage.getItem({ui.FEED_PREFS_KEY_V2!r})"
            ) is None
            v3_sources = page.evaluate(
                f"""() => {{
                  const raw = localStorage.getItem({ui.FEED_PREFS_KEY_V3!r});
                  return raw ? JSON.parse(raw).sources : null;
                }}"""
            )
            assert v3_sources == []
            page.reload()
            ui.wait_feed_prefs_ready(page, timeout_ms=timeout_ms)
            ui.assert_no_tg_source_filter(page)
        finally:
            ctx.close()
            browser.close()


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O280_E2E") != "1",
    reason="J3 feed prefs F5 — set RAWLEAD_O280_E2E=1",
)
def test_j3_feed_filter_persist_f5() -> None:
    """J3: category filter survives page reload via rawlead_feed_prefs_v3."""
    from playwright.sync_api import sync_playwright

    import next_ui as ui

    base_url = os.environ.get("RAWLEAD_O280_BASE_URL", "http://localhost:3001")
    timeout_ms = int(os.environ.get("RAWLEAD_O280_TIMEOUT_MS", "60000"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.environ.get("RAWLEAD_O280_HEADED") != "1")
        ctx = browser.new_context(viewport=ui.DESKTOP_VIEWPORT, locale="ru-RU")
        page = ctx.new_page()
        page.set_default_timeout(timeout_ms)
        try:
            ui.clear_feed_prefs_storage(page)
            ui.goto_lenta(page, base_url)
            ui.wait_feed_prefs_ready(page, timeout_ms=timeout_ms)
            ui.click_category(page, "design")
            page.wait_for_timeout(400)
            active = page.locator('[data-testid="feed-cat-design"][data-active="1"]')
            if not active.count():
                raise AssertionError("design category not active before reload")
            page.reload()
            ui.wait_feed_prefs_ready(page, timeout_ms=timeout_ms)
            active_after = page.locator('[data-testid="feed-cat-design"][data-active="1"]')
            if not active_after.count():
                raise AssertionError("design category not active after F5")
        finally:
            ctx.close()
            browser.close()


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O280_E2E") != "1",
    reason="J3 feed TG reset race — set RAWLEAD_O280_E2E=1",
)
def test_j3_feed_tg_reset_logged_in_race() -> None:
    """Logged-in: stuck v3 TG → reset → 2s → no TG · FL toggle shows FL not TG."""
    from playwright.sync_api import sync_playwright

    import next_ui as ui

    token = ui.load_env_token("RAWLEAD_PREPROD_ACCESS_TOKEN")
    if not token:
        pytest.skip("RAWLEAD_PREPROD_ACCESS_TOKEN missing")

    base_url = os.environ.get("RAWLEAD_O280_BASE_URL", "http://localhost:3001")
    timeout_ms = int(os.environ.get("RAWLEAD_O280_TIMEOUT_MS", "60000"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.environ.get("RAWLEAD_O280_HEADED") != "1")
        ctx = browser.new_context(viewport=ui.DESKTOP_VIEWPORT, locale="ru-RU")
        ui.add_token_init_script(ctx, token)
        ctx.add_init_script(
            """() => {
              localStorage.setItem('rawlead_feed_prefs_v3', JSON.stringify({
                sort: 'time', min_match: 80, category: '', source: 'tg', sources: ['tg'],
                updated_at: new Date().toISOString()
              }));
            }"""
        )
        page = ctx.new_page()
        page.set_default_timeout(timeout_ms)
        try:
            ui.goto_lenta(page, base_url)
            ui.wait_feed_prefs_ready(page, timeout_ms=timeout_ms)
            ui.bootstrap_preprod_feed(page, base_url, token, timeout_ms=timeout_ms)
            ui.reset_feed_filter_dropdown(page)
            page.wait_for_timeout(2000)
            ui.assert_no_tg_source_filter(page)
            ui.toggle_dropdown_source(page, "fl")
            ui.assert_source_pill_contains(page, "FL")
            ui.assert_no_tg_source_filter(page)
        finally:
            ctx.close()
            browser.close()


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O280_E2E") != "1",
    reason="prod next E2E — set RAWLEAD_O280_E2E=1",
)
def test_next_e2e_prod_runner() -> None:
    import next_e2e

    viewport = os.environ.get("RAWLEAD_O280_VIEWPORT", "desktop")
    ids = None
    if os.environ.get("RAWLEAD_O280_IDS"):
        ids = [x.strip() for x in os.environ["RAWLEAD_O280_IDS"].split(",") if x.strip()]

    report = next_e2e.run_next_e2e(
        base_url=os.environ.get("RAWLEAD_O280_BASE_URL", "https://rawlead.ru"),
        viewport_name=viewport,
        headless=os.environ.get("RAWLEAD_O280_HEADED") != "1",
        timeout_ms=int(os.environ.get("RAWLEAD_O280_TIMEOUT_MS", "60000")),
        ids=ids,
    )
    assert report["pass"], report.get("results")
