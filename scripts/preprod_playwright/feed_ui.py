"""Shared Playwright selectors/helpers for RawLead feed UI (O127+).

Desktop skills: #rl-feed-skills-modal (not legacy .rl-feed-skills-dd).
Sort: input[name=rl-feed-sort] / input[name=rl-sheet-sort].
Count: #rl-feed-toolbar .rl-feed-toolbar__meta (not hidden #rl-feed-count).
Cards: O149 inline expand — `.rl-feed-card__body-inner` (no flip faces).
"""

from __future__ import annotations

import time
from typing import Any

FEED_APP = '[data-rl-app="feed"]'
FEED_READY = "#rl-feed-list .rl-lead-card, #rl-feed-list .rl-feed-empty"
FEED_META = "#rl-feed-toolbar .rl-feed-toolbar__meta"
FEED_CARD = "#rl-feed-list .rl-lead-card[data-id]"
CARD_FRONT_BODY = ".rl-feed-card__body-inner"
CARD_FRONT_SECTION = ".rl-feed-card__section"
SKILLS_TRIGGER = "#rl-feed-skills-trigger"
SKILLS_MODAL = "#rl-feed-skills-modal"
SKILLS_TREE = "#rl-feed-skill-tree-roots"
SKILLS_CHIP = (
    "#rl-feed-skill-tree-roots .rl-skill-chip.rl-feed-skill:not(.is-disabled), "
    "#rl-feed-skill-tree-roots .rl-feed-skill:not(.is-disabled)[data-tag]"
)
SKILLS_APPLY = "#rl-feed-skills-apply"
SKILLS_OVERLAY = "#rl-feed-skills-modal-overlay"
SORT_DD = "#rl-feed-sort-dd"
SORT_PANEL = "#rl-feed-sort-panel"
SORT_RADIO_DESKTOP = 'input[name="rl-feed-sort"]'
SORT_RADIO_MOBILE = 'input[name="rl-sheet-sort"]'
MOBILE_FILTERS = "#rl-feed-filters-open"
MOBILE_SHEET = "#rl-feed-sheet"
MOBILE_SHEET_PANEL = ".rl-feed-sheet__panel"
MOBILE_SHEET_APPLY = "#rl-feed-sheet-apply"
MOBILE_SKILLS_OPEN = "#rl-sheet-skills-open"


def feed_error_visible(page: Any) -> str | None:
    err = page.locator("#rl-feed-error:not([hidden])")
    if err.count() and err.is_visible():
        return (err.inner_text() or "")[:300]
    return None


def goto_lenta(page: Any, base: str) -> None:
    page.goto(f"{base.rstrip('/')}/lenta/", wait_until="domcontentloaded")
    page.wait_for_selector(FEED_APP, state="visible")
    page.wait_for_selector(FEED_READY, timeout=45_000)
    page.wait_for_timeout(800)


def _skills_modal_open(page: Any) -> bool:
    return bool(
        page.evaluate(
            f"() => {{ const m = document.querySelector('{SKILLS_MODAL}'); return !!(m && !m.hidden); }}"
        )
    )


def _close_skills_modal_if_open(page: Any) -> None:
    if not _skills_modal_open(page):
        return
    apply = page.locator(SKILLS_APPLY)
    if apply.count() and apply.is_enabled():
        apply.click()
        page.wait_for_timeout(800)
    else:
        close_btn = page.locator("#rl-feed-skill-tree-close")
        if close_btn.count():
            close_btn.click(force=True)
            page.wait_for_timeout(400)
        if _skills_modal_open(page):
            close_skills_modal_overlay(page)
            page.wait_for_timeout(400)
        if _skills_modal_open(page):
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
    page.wait_for_function(
        f"() => {{ const m = document.querySelector('{SKILLS_MODAL}'); return !m || m.hidden; }}",
        timeout=10_000,
    )


def reset_feed_filters(page: Any, *, is_mobile: bool = False) -> None:
    """Category all · skills clear · sort/time · min_match default (O129 J3→J4 flake)."""
    page.wait_for_selector(FEED_APP, state="visible")
    if is_mobile:
        _close_skills_modal_if_open(page)
        sheet_reset = page.locator("#rl-feed-sheet-reset")
        if sheet_reset.count():
            sheet_reset.click(force=True)
            page.wait_for_timeout(1500)
        else:
            sheet = open_mobile_feed_sheet(page)
            sheet.locator('input[name="category"][value=""]').check(force=True)
            page.wait_for_timeout(400)
            sheet.locator(MOBILE_SHEET_APPLY).click()
            page.wait_for_timeout(1200)
    else:
        _close_skills_modal_if_open(page)
        page.evaluate(
            """() => {
              const btn = document.querySelector('.rl-feed-reset');
              if (btn) btn.click();
            }"""
        )
        page.wait_for_timeout(1200)
        page.locator("#filter-category-all input").check(force=True)
        page.wait_for_timeout(400)
        _close_skills_modal_if_open(page)
        if not is_filter_locked(page, "sort"):
            sort_dd = page.locator(SORT_DD)
            if sort_dd.count():
                current = page.evaluate(
                    """() => {
                      const checked = document.querySelector('input[name="rl-feed-sort"]:checked');
                      return checked ? checked.value : 'time';
                    }"""
                )
                if current != "time":
                    sort_dd.locator("summary").click()
                    time_radio = page.locator(f'{SORT_RADIO_DESKTOP}[value="time"]')
                    if time_radio.count():
                        time_radio.first.check(force=True)
                        page.locator("#rl-feed-sort-apply").click()
                        page.wait_for_timeout(800)
                    _close_skills_modal_if_open(page)
                    _close_skills_modal_if_open(page)
    wait_feed_loading_done(page)
    page.wait_for_timeout(400)
    err = feed_error_visible(page)
    if err:
        raise RuntimeError(f"feed error after reset: {err}")


def wait_feed_tier(page: Any, *allowed: str, timeout_ms: int = 30_000) -> str:
    """Wait until JS sets data-feed-tier on main."""
    page.wait_for_function(
        f"""
        () => {{
          const m = document.querySelector('{FEED_APP}');
          if (!m) return false;
          const t = m.getAttribute('data-feed-tier') || '';
          return {list(allowed)!r}.includes(t);
        }}
        """,
        timeout=timeout_ms,
    )
    tier = page.locator(FEED_APP).get_attribute("data-feed-tier") or ""
    return tier


def get_feed_tier(page: Any) -> str:
    return page.locator(FEED_APP).get_attribute("data-feed-tier") or "anon"


def feed_meta_text(page: Any) -> str:
    meta = page.locator(FEED_META)
    return meta.inner_text() if meta.count() else ""


def is_filter_locked(page: Any, kind: str) -> bool:
    sel = f'[data-filter-locked="{kind}"]'
    el = page.locator(sel)
    return el.count() > 0 and el.first.is_visible()


def open_skills_modal(page: Any, *, is_mobile: bool = False) -> None:
    if is_filter_locked(page, "skills"):
        raise RuntimeError("skills filter locked (anon tier)")
    if is_mobile:
        sheet = open_mobile_feed_sheet(page)
        btn = sheet.locator(MOBILE_SKILLS_OPEN)
        if not btn.count():
            btn = page.locator(MOBILE_SKILLS_OPEN)
        btn.first.wait_for(state="visible", timeout=15_000)
        btn.first.click()
    else:
        page.locator(SKILLS_TRIGGER).click()
    page.wait_for_function(
        f"() => {{ const m = document.querySelector('{SKILLS_MODAL}'); return m && !m.hidden; }}",
        timeout=15_000,
    )
    page.wait_for_selector(SKILLS_TREE, state="visible", timeout=15_000)


def close_skills_modal_overlay(page: Any) -> None:
    overlay = page.locator(SKILLS_OVERLAY)
    if overlay.count():
        overlay.first.click(force=True)
        page.wait_for_timeout(400)


def pick_first_skill_chip(page: Any) -> None:
    page.wait_for_selector(f"{SKILLS_TREE} .rl-niche-root", timeout=45_000)
    toggles = page.locator(f"{SKILLS_TREE} [data-niche-toggle]")
    for i in range(min(toggles.count(), 6)):
        section = toggles.nth(i)
        try:
            section.click()
            page.wait_for_timeout(400)
            chip = page.locator(
                f"{SKILLS_TREE} .rl-niche-root--expanded .rl-feed-skill:not(.is-disabled)"
            ).first
            if chip.count() and chip.is_visible():
                chip.click()
                return
        except Exception:
            continue
    for sel in (
        f"{SKILLS_TREE} .rl-l1-chip-wrap .rl-feed-skill:not(.is-disabled)",
        f"{SKILLS_TREE} .rl-niche-root__body .rl-feed-skill:not(.is-disabled)",
        SKILLS_CHIP,
    ):
        chips = page.locator(sel)
        for i in range(min(chips.count(), 40)):
            chip = chips.nth(i)
            try:
                if chip.is_visible():
                    chip.click()
                    return
            except Exception:
                continue
    raise RuntimeError("no visible skill chip in modal")


def apply_skills_modal(page: Any) -> None:
    page.locator(SKILLS_APPLY).click()
    page.wait_for_timeout(1500)
    page.wait_for_function(
        f"() => {{ const m = document.querySelector('{SKILLS_MODAL}'); return !m || m.hidden; }}",
        timeout=10_000,
    )


def open_mobile_feed_sheet(page: Any) -> Any:
    open_btn = page.locator(MOBILE_FILTERS)
    open_btn.wait_for(state="visible")
    open_btn.click()
    page.wait_for_function(
        f"() => {{ const s = document.querySelector('{MOBILE_SHEET}'); return s && !s.hidden; }}",
        timeout=10_000,
    )
    panel = page.locator(MOBILE_SHEET_PANEL)
    panel.wait_for(state="visible", timeout=10_000)
    return panel


def close_mobile_sheet_overlay(page: Any) -> None:
    overlay = page.locator("#rl-feed-sheet-overlay")
    if overlay.count():
        box = overlay.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 16)
        else:
            page.mouse.click(195, 16)
    else:
        page.mouse.click(5, 5)
    page.wait_for_timeout(500)


def apply_category_design(page: Any, *, is_mobile: bool = False) -> None:
    if is_mobile:
        sheet = open_mobile_feed_sheet(page)
        design = sheet.locator('input[name="category"][value="design"]')
        design.check(force=True)
        page.wait_for_timeout(800)
        sheet.locator(MOBILE_SHEET_APPLY).click()
        page.wait_for_timeout(1500)
    else:
        page.locator("#filter-category-design input").check(force=True)
        page.wait_for_timeout(1200)


def apply_sort_match(page: Any, *, is_mobile: bool = False) -> None:
    if is_filter_locked(page, "sort"):
        raise RuntimeError("sort filter locked (anon tier)")
    if is_mobile:
        sheet = open_mobile_feed_sheet(page)
        match_radio = sheet.locator(f'{SORT_RADIO_MOBILE}[value="match"]')
        if not match_radio.count():
            raise RuntimeError("mobile sheet: rl-sheet-sort match radio missing")
        time_radio = sheet.locator(f'{SORT_RADIO_MOBILE}[value="time"]')
        if time_radio.count():
            time_radio.first.click(force=True)
            page.wait_for_timeout(400)
        match_radio.first.click(force=True)
        page.wait_for_timeout(800)
        sheet.locator(MOBILE_SHEET_APPLY).click()
        page.wait_for_timeout(1200)
        return

    sort_dd = page.locator(SORT_DD)
    sort_dd.locator("summary").click()
    if not sort_dd.evaluate("el => el.open"):
        raise RuntimeError("sort dropdown did not open")
    match = page.locator(f'{SORT_RADIO_DESKTOP}[value="match"]')
    if not match.count():
        page.wait_for_selector(SORT_PANEL, state="visible", timeout=10_000)
        match = page.locator(f'{SORT_RADIO_DESKTOP}[value="match"]')
    if not match.count():
        raise RuntimeError("desktop: rl-feed-sort match radio missing")
    match.first.check(force=True)
    page.locator("#rl-feed-sort-apply").click()
    page.wait_for_timeout(800)
    if sort_dd.evaluate("el => el.open"):
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)


def wait_feed_loading_done(page: Any, *, timeout_ms: int = 30_000) -> None:
    page.wait_for_selector(FEED_APP, state="visible")
    page.wait_for_selector(FEED_READY, timeout=timeout_ms)
    page.wait_for_function(
        "() => { const el = document.getElementById('rl-feed-loading'); return !el || el.hidden; }",
        timeout=timeout_ms,
    )


def click_card_title(card: Any) -> None:
    """Toggle expand/collapse — click title span (h3 center misses handler in Playwright)."""
    card.scroll_into_view_if_needed()
    span = card.locator(".rl-lead-card__title span").first
    if span.count():
        span.click()
        return
    card.locator(".rl-lead-card__title").first.click()


def card_is_expanded(card: Any) -> bool:
    return "is-expanded" in (card.get_attribute("class") or "")


def expand_card(card: Any, page: Any) -> None:
    card.scroll_into_view_if_needed()
    last_err: Exception | None = None
    for _ in range(2):
        if not card_is_expanded(card):
            click_card_title(card)
        page.wait_for_timeout(500)
        try:
            card.locator(CARD_FRONT_BODY).first.wait_for(state="visible", timeout=8000)
            return
        except Exception as exc:
            last_err = exc
    if last_err:
        raise last_err


def collapse_card_tap_outside(card: Any, page: Any) -> None:
    expand_card(card, page)
    page.mouse.click(10, 10)
    page.wait_for_timeout(500)
    if "is-expanded" in (card.get_attribute("class") or ""):
        raise RuntimeError("card did not collapse on tap outside")


def card_has_tools_section(card: Any) -> bool:
    titles = card.locator(".rl-feed-card__section-title")
    for ti in range(titles.count()):
        if (titles.nth(ti).inner_text() or "").strip() == "Инструменты":
            return True
    return False


def assert_match_for_tier(card: Any, tier: str) -> None:
    forbidden = ("брать", "сомнительно", "качество заказа", "навыки: 0%")
    if card.locator(".rl-chip--take, .rl-chip--maybe").count():
        raise RuntimeError("verdict chip still visible")
    text = (card.inner_text() or "").casefold()
    for bad in forbidden:
        if bad in text:
            raise RuntimeError(f"forbidden copy «{bad}»")

    if tier == "anon":
        if card.locator(".rl-match").count():
            raise RuntimeError("anon: unexpected .rl-match block")
        if not card.locator("a.rl-card-cta--anon, .rl-card-upsell").count():
            raise RuntimeError("anon: missing login upsell on card")
        return

    if tier == "free":
        if not card.locator(".rl-match--free-locked").count():
            raise RuntimeError("free: missing locked match bar")
        return

    # premium
    if card.locator(".rl-match--free-locked").count():
        raise RuntimeError("premium: free-locked match bar")
    has_match = card.locator(".rl-match").count() > 0
    has_cta = card.locator("[data-open-skills]").count() > 0
    if not has_match and not has_cta:
        raise RuntimeError("premium: no match bar or skills CTA")


def tap_cabinet_skills_backdrop(page: Any) -> None:
    overlay = page.locator("#rl-cabinet-skills-modal-overlay")
    if overlay.count():
        overlay.first.click(force=True)
        page.wait_for_timeout(400)
    else:
        for sel in ("#rl-cabinet-skills-overlay",):
            fallback = page.locator(sel)
            if fallback.count():
                fallback.first.click(force=True)
                page.wait_for_timeout(400)
                break
        else:
            page.mouse.click(8, 8)
            page.wait_for_timeout(400)

    still_open = page.evaluate(
        "() => { const m = document.getElementById('rl-cabinet-skills-modal'); "
        "return m && !m.hidden; }"
    )
    if still_open:
        close_btn = page.locator("#rl-cabinet-skill-tree-close")
        if close_btn.count():
            close_btn.first.click(force=True)
            page.wait_for_timeout(400)
