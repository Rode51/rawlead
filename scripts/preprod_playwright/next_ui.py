"""§ O280-E2E-NEXT: Playwright selectors/helpers for rawlead-next (Next.js).

Selector map (grep this header):
  feed-app          [data-testid="feed-app"] · data-feed-tier
  feed-list         #rl-feed-list · [data-testid="feed-list"]
  feed-card         [data-testid="feed-card"] · .rl-lead-card[data-id]
  feed-meta-count   [data-testid="feed-meta-count"]
  feed-cat-*        [data-testid="feed-cat-all|dev|design|marketing|text"]
  feed-filters-open #rl-feed-filters-open
  feed-sheet-*      #rl-feed-sheet · #rl-feed-sheet-apply
  feed-load-more    [data-testid="feed-load-more"]
  feed-draft-*      [data-testid="feed-draft-text|copy|collapse"]
  header-*          logo · nav · login · cabinet
  footer-link-*     footer navigation
  hero-cta-*        home hero CTAs
  quiz-*            #rl-feed-quiz-overlay · #rl-quiz-* (WP parity ids)
  quiz-login-cta    [data-testid="quiz-login-cta"]
  feed-quiz-promo   [data-testid="feed-quiz-promo|feed-quiz-login-promo"]
  login-modal-*     [data-testid="login-modal"]
  anon-strip        [data-testid="anon-strip"]
  cabinet-app       #rl-cabinet-app
  pricing-checkout  [data-testid="pricing-checkout"]
  faq-item-*        accordion buttons
  support-fab       [data-testid="support-fab"]
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_ROOT = Path(__file__).resolve().parent.parent.parent

FEED_APP = '[data-testid="feed-app"]'
FEED_LIST = '#rl-feed-list [data-testid="feed-card"], #rl-feed-list .rl-lead-card'
FEED_META = '[data-testid="feed-meta-count"]'
FEED_CARD = '[data-testid="feed-card"]'
FEED_LOAD_MORE = '[data-testid="feed-load-more"]'
FEED_FILTERS_OPEN = '#rl-feed-filters-open'
FEED_SHEET = '#rl-feed-sheet'
FEED_SHEET_APPLY = '#rl-feed-sheet-apply'
FEED_DRAFT_TEXT = '[data-testid="feed-draft-text"]'
FEED_DRAFT_COPY = '[data-testid="feed-draft-copy"]'
FEED_DRAFT_COLLAPSE = '[data-testid="feed-draft-collapse"]'

QUIZ_OVERLAY = '#rl-feed-quiz-overlay'
QUIZ_INTRO = '#rl-quiz-intro'
QUIZ_INTRO_START = '#rl-quiz-intro-start'
QUIZ_RESULT = '#rl-quiz-result'
QUIZ_PLAY = '#rl-quiz-play'
QUIZ_LIKE = '#rl-quiz-like'
QUIZ_NOPE = '#rl-quiz-nope'
QUIZ_CARD = '#rl-quiz-card'
QUIZ_CLOSE = '#rl-feed-quiz-overlay-close'
QUIZ_BACKDROP = '#rl-feed-quiz-overlay-backdrop'
QUIZ_RETAKE = '#rl-quiz-retake-completed'
QUIZ_LOGIN_CTA = '[data-testid="quiz-login-cta"]'
FEED_QUIZ_PROMO = '[data-testid="feed-quiz-promo"]'
FEED_QUIZ_LOGIN_PROMO = '[data-testid="feed-quiz-login-promo"]'
FEED_QUIZ_LOGIN_CTA = '[data-testid="feed-quiz-login-cta"]'

LOGIN_MODAL = '[data-testid="login-modal"]'
LOGIN_MODAL_CLOSE = '[data-testid="login-modal-close"]'
LOGIN_MODAL_BACKDROP = '[data-testid="login-modal-backdrop"]'

ANON_STRIP = '[data-testid="anon-strip"]'
CABINET_APP = '#rl-cabinet-app'
SUPPORT_FAB = '[data-testid="support-fab"]'

TOKEN_KEY = "rawlead_access_token"
COMPLETED_KEY = "rawlead_quiz_completed_v1"
SESSION_KEY = "rawlead_quiz_session"

DESKTOP_VIEWPORT = {"width": 1280, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}

ACC1_USER_ID = "7a83dbd8-ab41-4350-a183-38370d5b5c1c"
MONICA_USER_ID = "8d5afb3d-e8bd-4970-a33d-21c3ddeafdef"

_ANIM_MS = 350
_DRAFT_TIMEOUT_MS = 180_000

_CONSOLE_IGNORE_SUBSTR = (
    "Failed to fetch RSC payload",
    "Falling back to browser navigation",
    "Download the React DevTools",
    "favicon",
    "Failed to load resource: the server responded with a status of 404",
)

_BENIGN_HTTP_404_PARTS = (
    "/v1/me/avatar",
    "favicon.ico",
    "apple-touch-icon",
    "safari-pinned-tab",
    "manifest.json",
)


def _benign_console_error(text: str) -> bool:
    if any(part in text for part in _CONSOLE_IGNORE_SUBSTR):
        return True
    low = text.lower()
    if "429" in text and "/draft" in low:
        return True
    return False


def attach_console_monitor(page: Any, errors: list[str]) -> None:
    def on_console(msg: Any) -> None:
        if msg.type != "error":
            return
        text = (msg.text or "")[:500]
        if not text:
            return
        if _benign_console_error(text):
            return
        errors.append(text)
    page.on("console", on_console)


def attach_http_monitor(page: Any, errors: list[str]) -> None:
    def on_response(resp: Any) -> None:
        status = resp.status
        if status < 400:
            return
        url = resp.url or ""
        if status == 404 and any(part in url for part in _BENIGN_HTTP_404_PARTS):
            return
        if status == 429 and "/draft" in url:
            return
        errors.append(f"HTTP {status} {url[:300]}")
    page.on("response", on_response)


def api_base_for_site(base_url: str) -> str:
    host = (base_url or "").lower()
    if "rawlead.ru" in host:
        return "https://api.rawlead.ru"
    override = os.environ.get("RAWLEAD_API_URL", "").strip().rstrip("/")
    if override:
        return override
    return "http://127.0.0.1:8000"


def reset_draft_quota_via_api(token: str, *, api_base: str) -> dict[str, Any]:
    """POST /v1/me/draft/quota/reset — preprod E2E only."""
    url = f"{api_base.rstrip('/')}/v1/me/draft/quota/reset"
    req = Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "RawLeadNextE2E/1.0",
        },
        data=b"{}",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"draft quota reset HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"draft quota reset failed: {exc}") from exc


def ensure_draft_quota_for_e2e(token: str, *, base_url: str) -> None:
    api = api_base_for_site(base_url)
    quota = reset_draft_quota_via_api(token, api_base=api)
    remaining = int(quota.get("draft_remaining") or 0)
    limit = int(quota.get("draft_hourly_limit") or 0)
    if limit > 0 and remaining < 3:
        raise RuntimeError(
            f"draft quota too low after reset: remaining={remaining} limit={limit}"
        )


def load_env_token(key: str) -> str | None:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    for name in (".env.site", ".env", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        prefix = f"{key}="
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(prefix):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def goto_path(page: Any, base: str, path: str) -> None:
    url = f"{base.rstrip('/')}{path}"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(400)


def dismiss_quiz_overlay_if_open(page: Any) -> None:
    overlay = page.locator(QUIZ_OVERLAY)
    if overlay.count() and overlay.is_visible():
        close_quiz_overlay(page)


def goto_lenta(page: Any, base: str) -> None:
    goto_path(page, base, "/lenta/")
    page.wait_for_selector(FEED_APP, state="visible", timeout=45_000)
    dismiss_quiz_overlay_if_open(page)
    page.wait_for_function(
        """() => {
          const cards = document.querySelectorAll('[data-testid="feed-card"]');
          if (cards.length > 0) return true;
          const loading = document.querySelector('.animate-pulse');
          if (loading) return false;
          const txt = document.body.innerText || '';
          return txt.includes('Пока нет заказов') || txt.includes('лидов за 7 дней');
        }""",
        timeout=60_000,
    )
    page.wait_for_timeout(600)


def wait_auth_status(page: Any, status: str, *, timeout_ms: int = 60_000) -> None:
    try:
        page.wait_for_function(
            f"""() => {{
              const app = document.querySelector('{FEED_APP}');
              if (!app) return false;
              const tier = app.getAttribute('data-feed-tier') || 'anon';
              if ({json.dumps(status)} === 'auth') return tier !== 'anon' && tier !== 'pending';
              return tier === {json.dumps(status)};
            }}""",
            timeout=timeout_ms,
        )
    except Exception as exc:
        raise RuntimeError(
            "PREPROD auth bootstrap failed — refresh RAWLEAD_PREPROD_ACCESS_TOKEN in .env.site"
        ) from exc


def wait_feed_tier(page: Any, *allowed: str, timeout_ms: int = 30_000) -> str:
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
    return page.locator(FEED_APP).get_attribute("data-feed-tier") or ""


def feed_card_count(page: Any) -> int:
    return page.locator(FEED_CARD).count()


def wait_feed_card_count(
    page: Any,
    min_count: int = 1,
    *,
    timeout_ms: int = 45_000,
) -> int:
    """Wait for feed list to render at least min_count cards (load-more retries)."""
    deadline = time.perf_counter() + timeout_ms / 1000
    while time.perf_counter() < deadline:
        n = feed_card_count(page)
        if n >= min_count:
            return n
        _maybe_load_more_feed(page)
        page.evaluate(
            "document.getElementById('rl-feed-list')?.lastElementChild?.scrollIntoView()"
        )
        page.wait_for_timeout(800)
    n = feed_card_count(page)
    if n < min_count:
        raise RuntimeError(f"need >={min_count} feed cards, got {n}")
    return n


def click_category(page: Any, slug: str) -> None:
    page.locator(f'[data-testid="feed-cat-{slug or "all"}"]').click()
    page.wait_for_timeout(800)


FEED_PREFS_KEY_V1 = "rawlead_feed_prefs"
FEED_PREFS_KEY_V2 = "rawlead_feed_prefs_v2"
FEED_PREFS_KEY_V3 = "rawlead_feed_prefs_v3"


def clear_feed_prefs_storage(page: Any) -> None:
    page.evaluate(
        f"""() => {{
          localStorage.removeItem({FEED_PREFS_KEY_V1!r});
          localStorage.removeItem({FEED_PREFS_KEY_V2!r});
          localStorage.removeItem({FEED_PREFS_KEY_V3!r});
        }}"""
    )


def seed_stuck_feed_prefs_v2(page: Any, source: str = "tg") -> None:
    """v2 localStorage with stuck exchange filter (FEED-FILTER-TG-STUCK repro)."""
    page.evaluate(
        """(source) => {
          localStorage.setItem('rawlead_feed_prefs_v2', JSON.stringify({
            sort: 'time', min_match: 80, category: '', source, sources: [source],
            updated_at: '2020-01-01T00:00:00.000Z'
          }));
          localStorage.removeItem('rawlead_feed_prefs_v3');
        }""",
        source,
    )


def seed_stuck_feed_prefs_v3(page: Any, source: str = "tg") -> None:
    page.evaluate(
        """(source) => {
          localStorage.setItem('rawlead_feed_prefs_v3', JSON.stringify({
            sort: 'time', min_match: 80, category: '', source, sources: [source],
            updated_at: new Date().toISOString()
          }));
        }""",
        source,
    )


def wait_feed_prefs_ready(page: Any, timeout_ms: int = 60_000) -> None:
    page.wait_for_selector('[data-feed-prefs-ready="1"]', timeout=timeout_ms)


def assert_no_tg_source_filter(page: Any) -> None:
    main = page.locator(FEED_APP)
    sources = main.get_attribute("data-feed-sources") or ""
    if "tg" in [s for s in sources.split(",") if s]:
        raise AssertionError(f"TG filter active in data-feed-sources: {sources!r}")
    pill = page.locator('[data-testid="feed-source-pill"]')
    if pill.count() and "Telegram" in (pill.inner_text() or ""):
        raise AssertionError("Telegram pill visible in filter bar")
    dropdown = page.locator('[data-testid="feed-filter-dropdown"]')
    if dropdown.count() and dropdown.get_attribute("data-active") == "1":
        raise AssertionError("feed-filter-dropdown inverted (source filter active)")


def open_feed_filter_dropdown(page: Any) -> None:
    page.locator('[data-testid="feed-filter-dropdown"]').click()
    page.wait_for_selector('[data-testid="feed-sort-panel"]', state="visible", timeout=10_000)


def reset_feed_filter_dropdown(page: Any) -> None:
    open_feed_filter_dropdown(page)
    reset_btn = page.locator('[data-testid="feed-sort-panel"] button:has-text("Сбросить")')
    if reset_btn.count():
        reset_btn.first.click()
        page.wait_for_timeout(400)
    else:
        page.keyboard.press("Escape")


def toggle_dropdown_source(page: Any, slug: str) -> None:
    open_feed_filter_dropdown(page)
    page.locator(f'[data-testid="dropdown-src-{slug}"]').click()
    page.locator('[data-testid="feed-sort-panel"] button:has-text("Применить")').click()
    page.wait_for_timeout(400)


def assert_source_pill_contains(page: Any, label: str) -> None:
    pill = page.locator('[data-testid="feed-source-pill"]')
    if not pill.count():
        raise AssertionError(f"feed-source-pill missing, expected {label!r}")
    text = pill.inner_text() or ""
    if label not in text:
        raise AssertionError(f"feed-source-pill {text!r} does not contain {label!r}")


def open_mobile_filter_sheet(page: Any) -> None:
    page.locator(FEED_FILTERS_OPEN).click()
    page.wait_for_selector(FEED_SHEET, state="visible", timeout=10_000)


def apply_mobile_sheet(page: Any) -> None:
    page.locator(FEED_SHEET_APPLY).click()
    page.wait_for_timeout(900)


def expand_card_element(page: Any, card: Any) -> Any:
    card.scroll_into_view_if_needed()
    title = card.locator("h3").first
    if title.count():
        title.click()
    else:
        card.click(force=True)
    deadline = time.perf_counter() + 8
    while time.perf_counter() < deadline:
        if card_body_visible(card):
            return card
        card.click(force=True)
        page.wait_for_timeout(250)
    lid = card.get_attribute("data-id") or "?"
    raise RuntimeError(f"feed card {lid} did not expand")


def expand_card_at(page: Any, index: int = 0) -> Any:
    card = page.locator(FEED_CARD).nth(index)
    return expand_card_element(page, card)


def _maybe_load_more_feed(page: Any) -> None:
    more = page.locator(FEED_LOAD_MORE)
    if more.count() and more.is_visible():
        more.click()
        page.wait_for_timeout(2500)


def expand_card_by_lead_id(page: Any, lead_id: str) -> Any:
    sel = f'{FEED_CARD}[data-id="{lead_id}"]'
    for _ in range(8):
        card = page.locator(sel)
        if card.count():
            return expand_card_element(page, card.first)
        _maybe_load_more_feed(page)
        page.evaluate(
            "document.getElementById('rl-feed-list')?.lastElementChild?.scrollIntoView()"
        )
        page.wait_for_timeout(800)
    raise RuntimeError(f"feed card lead {lead_id} not found in DOM")


def fetch_me_feed(
    token: str,
    *,
    base_url: str,
    limit: int = 80,
    sort: str = "time",
) -> dict[str, Any]:
    api = api_base_for_site(base_url)
    url = f"{api.rstrip('/')}/v1/me/feed?limit={limit}&sort={sort}"
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "RawLeadNextE2E/1.0",
        },
    )
    try:
        with urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body if isinstance(body, dict) else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"me/feed HTTP {exc.code}: {raw}") from exc
    except URLError as exc:
        raise RuntimeError(f"me/feed failed: {exc}") from exc


def lead_ids_pass_draft_gate(items: list[dict[str, Any]]) -> list[str]:
    """PA-5b / _lead_in_user_feed(min_match=0): keyword_match must be > 0."""
    out: list[str] = []
    for item in items:
        km = item.get("keyword_match")
        if km is None:
            continue
        try:
            if int(km) <= 0:
                continue
        except (TypeError, ValueError):
            continue
        lid = item.get("id")
        if lid is not None:
            out.append(str(lid))
    return out


def draftable_lead_ids_for_e2e(
    token: str,
    *,
    base_url: str,
    need: int = 2,
    min_need: int | None = None,
    prefer_high_match: bool = False,
) -> list[str]:
    feed = fetch_me_feed(token, base_url=base_url, limit=80)
    items = feed.get("items") or []
    gated: list[tuple[int, str]] = []
    for item in items:
        km = item.get("keyword_match")
        if km is None:
            continue
        try:
            km_i = int(km)
        except (TypeError, ValueError):
            continue
        if km_i <= 0:
            continue
        lid = item.get("id")
        if lid is not None:
            gated.append((km_i, str(lid)))
    if prefer_high_match:
        gated.sort(key=lambda pair: pair[0], reverse=True)
    ids = [lid for _, lid in gated]
    floor = need if min_need is None else min_need
    if len(ids) < floor:
        raise RuntimeError(
            f"need {floor} leads with keyword_match>0 for draft (PA-5b); "
            f"API returned {len(ids)}"
        )
    return ids[:need]


def card_body_visible(card: Any) -> bool:
    return card.evaluate(
        """el => {
          if (el.classList.contains('is-expanded')) return true;
          const body = el.querySelector('[data-testid="feed-card-body"]');
          if (!body) return false;
          const h = parseFloat(body.style.maxHeight || '0');
          return h > 20;
        }"""
    )


def assert_match_visible(card: Any) -> None:
    bar = card.locator('[data-testid="feed-match-bar"]')
    if not bar.count():
        raise RuntimeError("match bar missing")
    text = (bar.inner_text() or "").strip()
    if not text:
        raise RuntimeError("match bar empty")


def inject_token(page: Any, token: str, *, base: str | None = None) -> None:
    if not page.url or page.url == "about:blank":
        if base:
            goto_lenta(page, base)
    page.evaluate(
        """(tok) => {
          localStorage.setItem('rawlead_access_token', tok);
          document.cookie =
            'rl_access=' + encodeURIComponent(tok) + '; path=/; max-age=2592000; SameSite=Lax';
        }""",
        token,
    )


def reload_with_token(page: Any, base: str, token: str) -> None:
    """Reload without losing JWT — inject before reload (quiz_e2e j3/j5 parity)."""
    inject_token(page, token, base=base)
    page.reload(wait_until="domcontentloaded")
    inject_token(page, token, base=base)
    page.wait_for_timeout(400)


def bootstrap_preprod_feed(
    page: Any,
    base: str,
    token: str,
    *,
    timeout_ms: int = 60_000,
) -> str:
    """Lenta + token reload + premium tier (retry once on flaky /me)."""
    goto_lenta(page, base)
    reload_with_token(page, base, token)
    try:
        return wait_feed_tier(page, "premium", "free", timeout_ms=timeout_ms)
    except Exception:
        reload_with_token(page, base, token)
        return wait_feed_tier(page, "premium", "free", timeout_ms=timeout_ms)


def add_token_init_script(context: Any, token: str) -> None:
    context.add_init_script(
        f"""() => {{
          const tok = {json.dumps(token)};
          try {{
            localStorage.setItem("{TOKEN_KEY}", tok);
            document.cookie =
              "rl_access=" + encodeURIComponent(tok) + "; path=/; max-age=2592000; SameSite=Lax";
          }} catch (e) {{}}
        }}"""
    )


def clear_quiz_storage(page: Any, *, base: str | None = None) -> None:
    if not page.url or page.url == "about:blank":
        if base:
            goto_lenta(page, base)
    page.evaluate(
        """() => {
          try {
            localStorage.removeItem('rawlead_quiz_session');
            localStorage.removeItem('rawlead_quiz_completed_v1');
            localStorage.removeItem('rawlead_quiz_restore_import_v1');
            sessionStorage.removeItem('rawlead_quiz_restore_import_v1');
            sessionStorage.removeItem('rawlead_quiz_retake');
          } catch (e) {}
        }"""
    )


def add_quiz_clear_init_script(context: Any) -> None:
    context.add_init_script(
        """() => {
          try {
            localStorage.removeItem('rawlead_quiz_session');
            localStorage.removeItem('rawlead_quiz_completed_v1');
            localStorage.removeItem('rawlead_quiz_restore_import_v1');
            sessionStorage.removeItem('rawlead_quiz_restore_import_v1');
            sessionStorage.removeItem('rawlead_quiz_retake');
          } catch (e) {}
        }"""
    )


def goto_lenta_quiz(page: Any, base: str) -> None:
    page.goto(f"{base.rstrip('/')}/lenta/#quiz", wait_until="domcontentloaded")
    page.wait_for_selector(FEED_APP, state="visible", timeout=45_000)
    wait_quiz_overlay_open(page)


def wait_quiz_overlay_open(page: Any, *, timeout_ms: int = 30_000) -> None:
    page.wait_for_selector(QUIZ_OVERLAY, state="visible", timeout=timeout_ms)


def is_intro_visible(page: Any) -> bool:
    intro = page.locator(QUIZ_INTRO)
    return intro.count() > 0 and intro.is_visible()


def is_play_visible(page: Any) -> bool:
    play = page.locator(QUIZ_PLAY)
    return play.count() > 0 and play.is_visible()


def is_result_visible(page: Any) -> bool:
    result = page.locator(QUIZ_RESULT)
    return result.count() > 0 and result.is_visible()


def assert_intro_visible(page: Any) -> None:
    if not is_intro_visible(page):
        raise RuntimeError("expected quiz intro")
    if is_play_visible(page):
        raise RuntimeError("quiz stuck on cards, expected intro")


def start_quiz_from_intro(page: Any) -> None:
    page.locator(QUIZ_INTRO_START).click()
    page.wait_for_selector(QUIZ_PLAY, state="visible", timeout=60_000)
    page.wait_for_selector(QUIZ_LIKE, state="visible", timeout=60_000)
    page.wait_for_function(
        """() => {
          const like = document.querySelector('#rl-quiz-like');
          const nope = document.querySelector('#rl-quiz-nope');
          return like && nope && !like.disabled && !nope.disabled;
        }""",
        timeout=60_000,
    )


def click_quiz_decision(page: Any, *, like: bool = True) -> None:
    sel = QUIZ_LIKE if like else QUIZ_NOPE
    btn = page.locator(sel)
    btn.wait_for(state="visible", timeout=60_000)
    page.wait_for_function(
        f"""() => {{
          const el = document.querySelector({json.dumps(sel)});
          return el && !el.disabled;
        }}""",
        timeout=60_000,
    )
    btn.click()
    page.wait_for_timeout(_ANIM_MS)


def answer_n_cards(page: Any, n: int) -> None:
    for i in range(n):
        if is_result_visible(page):
            break
        click_quiz_decision(page, like=(i % 2 == 0))


def answer_until_result(page: Any, *, max_answers: int = 16) -> int:
    answers = 0
    like_turn = True
    while answers < max_answers:
        if is_result_visible(page):
            return answers
        if not is_play_visible(page):
            page.wait_for_timeout(300)
            if is_result_visible(page):
                return answers
            continue
        click_quiz_decision(page, like=like_turn)
        like_turn = not like_turn
        answers += 1
    if not is_result_visible(page):
        raise RuntimeError(f"quiz did not finish after {max_answers} answers")
    return answers


def close_quiz_overlay(page: Any) -> None:
    for sel in (QUIZ_CLOSE, QUIZ_BACKDROP):
        btn = page.locator(sel)
        if btn.count() and btn.is_visible():
            btn.first.click(force=True)
            break
    else:
        page.keyboard.press("Escape")
    page.wait_for_selector(QUIZ_OVERLAY, state="hidden", timeout=10_000)


def click_retake_on_result(page: Any, *, start_play: bool = False) -> None:
    page.locator(QUIZ_RETAKE).click()
    page.wait_for_timeout(400)
    if start_play and is_intro_visible(page):
        start_quiz_from_intro(page)


def assert_anon_result_login_cta(page: Any) -> None:
    if not is_result_visible(page):
        raise RuntimeError("quiz result missing")
    cta = page.locator(QUIZ_LOGIN_CTA)
    if not cta.count() or not cta.is_visible():
        raise RuntimeError("anon quiz result: login CTA missing")
    retake = page.locator(QUIZ_RETAKE)
    if not retake.count() or not retake.is_visible():
        raise RuntimeError("anon quiz result: retake missing")


def assert_quiz_completed_storage(page: Any) -> dict[str, Any]:
    profile = read_completed_profile(page)
    if not profile:
        raise RuntimeError(f"{COMPLETED_KEY} missing in localStorage")
    inner = profile.get("profile") if isinstance(profile.get("profile"), dict) else {}
    tags = inner.get("tags") if isinstance(inner.get("tags"), dict) else {}
    tags_import = inner.get("tags_to_import") if isinstance(inner.get("tags_to_import"), list) else []
    niches = inner.get("niches") if isinstance(inner.get("niches"), list) else []
    has_signal = (
        (isinstance(tags, dict) and len(tags) > 0)
        or len(tags_import) > 0
        or len(niches) > 0
    )
    if not has_signal:
        raise RuntimeError(f"{COMPLETED_KEY} profile has no tags/niches")
    return profile


def close_quiz_watch_feed_anon(page: Any) -> None:
    btn = page.get_by_role("button", name="Смотреть без входа")
    if btn.count():
        btn.click()
    else:
        close_quiz_overlay(page)
        return
    page.wait_for_selector(QUIZ_OVERLAY, state="hidden", timeout=10_000)
    page.wait_for_timeout(600)


def assert_feed_quiz_login_promo(page: Any) -> None:
    promo = page.locator(FEED_QUIZ_LOGIN_PROMO)
    if not promo.count() or not promo.is_visible():
        raise RuntimeError("feed-quiz-login-promo missing after quiz close")
    cta = page.locator(FEED_QUIZ_LOGIN_CTA)
    if not cta.count() or not cta.is_visible():
        raise RuntimeError("feed-quiz-login-cta missing on promo card")


def open_login_modal_from_strip(page: Any) -> None:
    page.locator(f'{ANON_STRIP} [data-testid="anon-strip-login"]').click()
    page.wait_for_selector(LOGIN_MODAL, state="visible", timeout=10_000)


def close_login_modal(page: Any) -> None:
    page.locator(LOGIN_MODAL_CLOSE).click()
    page.wait_for_selector(LOGIN_MODAL, state="hidden", timeout=10_000)


def generate_draft_on_card(page: Any, card: Any, *, _retry_429: bool = True) -> str:
    draft_errors: list[str] = []

    def on_response(resp: Any) -> None:
        url = resp.url or ""
        if "/draft" not in url:
            return
        if resp.status >= 400:
            draft_errors.append(f"HTTP {resp.status} {url[:120]}")

    page.on("response", on_response)
    btn = card.locator('[data-testid="feed-card-cta"]')
    btn.click()
    deadline = time.perf_counter() + _DRAFT_TIMEOUT_MS / 1000
    while time.perf_counter() < deadline:
        if draft_errors:
            err = draft_errors[0]
            if _retry_429 and "HTTP 429" in err:
                page.wait_for_timeout(90_000)
                return generate_draft_on_card(page, card, _retry_429=False)
            raise RuntimeError(f"draft API failed: {err}")
        draft = card.locator(FEED_DRAFT_TEXT)
        if draft.count() and draft.is_visible():
            text = (draft.inner_text() or "").strip()
            if len(text) >= 40:
                return text
        page.wait_for_timeout(500)
    raise RuntimeError("draft timeout: text < 40 chars")


def collapse_draft_panel(card: Any) -> None:
    """Collapse draft panel by clicking the card (toggle)."""
    card.click()


def copy_draft(card: Any) -> None:
    card.locator(FEED_DRAFT_COPY).click()


def assert_no_horizontal_overflow(page: Any) -> None:
    overflow = page.evaluate(
        """() => {
          const doc = document.documentElement;
          return doc.scrollWidth > doc.clientWidth + 2;
        }"""
    )
    if overflow:
        raise RuntimeError("horizontal overflow on page")


def count_neon_user_tags(user_id: str) -> int | None:
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        return None
    try:
        import psycopg2  # type: ignore

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM user_tags WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return int(row[0]) if row else 0
    except Exception:
        return None


def attach_quiz_api_monitor(page: Any, bucket: list[dict[str, Any]]) -> None:
    def on_response(resp: Any) -> None:
        url = resp.url or ""
        if "/quiz/" in url or "/tags/import" in url:
            bucket.append({"url": url, "status": resp.status})
    page.on("response", on_response)


def trigger_post_login_import(page: Any) -> None:
    page.evaluate(
        """() => {
          window.dispatchEvent(new CustomEvent('rawlead-tags-imported'));
        }"""
    )
    page.wait_for_timeout(1500)


def assert_result_visible(page: Any) -> None:
    if not is_result_visible(page):
        raise RuntimeError("quiz result modal not visible")


def read_completed_profile(page: Any) -> dict[str, Any] | None:
    raw = page.evaluate(
        f"""() => {{
          try {{
            const s = localStorage.getItem('{COMPLETED_KEY}');
            return s ? JSON.parse(s) : null;
          }} catch (e) {{ return null; }}
        }}"""
    )
    return raw if isinstance(raw, dict) else None


def assert_completed_profile_unchanged(page: Any, first: dict[str, Any]) -> None:
    current = read_completed_profile(page)
    if not current:
        raise RuntimeError("completed profile missing after retake abandon")
    if json.dumps(current.get("profile"), sort_keys=True) != json.dumps(first.get("profile"), sort_keys=True):
        raise RuntimeError("completed profile changed after retake abandon")


def assert_quiz_api_ok(calls: list[dict[str, Any]]) -> None:
    quiz_calls = [c for c in calls if "/quiz/" in (c.get("url") or "")]
    if not quiz_calls:
        return
    bad = [c for c in quiz_calls if int(c.get("status") or 0) >= 400]
    if bad:
        raise RuntimeError(f"quiz API errors: {bad[:3]}")


def goto_cabinet_logged_in(page: Any, base: str, *, token: str) -> None:
    inject_token(page, token, base=base)
    goto_path(page, base, "/cabinet/")
    page.wait_for_function(
        """() => {
          const app = document.querySelector('#rl-cabinet-app');
          const login = document.querySelector('[data-testid="cabinet-login"]');
          const spin = document.querySelector('.animate-spin');
          return !!(app || login) && !spin;
        }""",
        timeout=60_000,
    )


def click_cabinet_quiz_retake(page: Any, base: str) -> None:
    goto_path(page, base, "/lenta/#quiz")
    wait_quiz_overlay_open(page)


def expand_first_feed_card(page: Any) -> Any:
    return expand_card_at(page, 0)


def assert_match_for_tier(card: Any, tier: str) -> None:
    text = (card.locator('[data-testid="feed-match-bar"]').inner_text() or "").lower()
    if tier == "anon":
        if "%" in text and "войди" not in text:
            raise RuntimeError("anon should not show real match %")
    elif tier == "premium":
        if "%" not in text:
            raise RuntimeError("premium match % missing")


def assert_synthetic_card_in_quiz(page: Any) -> None:
    start_quiz_from_intro(page)
    title = page.locator("#rl-quiz-card-title")
    if not title.count():
        raise RuntimeError("quiz card title missing")
    if not (title.inner_text() or "").strip():
        raise RuntimeError("quiz card title empty")

