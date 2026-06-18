"""Shared Playwright helpers for RawLead quiz overlay (O218).

Entry: /lenta/#quiz · overlay #rl-feed-quiz-overlay · cards #rl-quiz-like / #rl-quiz-nope.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable

import feed_ui

QUIZ_OVERLAY = "#rl-feed-quiz-overlay"
QUIZ_INTRO = "#rl-quiz-intro"
QUIZ_INTRO_START = "#rl-quiz-intro-start"
QUIZ_RESULT = "#rl-quiz-result"
QUIZ_PLAY = "#rl-quiz-play"
QUIZ_STAGE = "#rl-quiz-stage"
QUIZ_LIKE = "#rl-quiz-like"
QUIZ_NOPE = "#rl-quiz-nope"
QUIZ_EARLY_BTN = "#rl-quiz-early-btn"
QUIZ_CARD = "#rl-quiz-card"
QUIZ_CARD_SOURCE = "#rl-quiz-card-source"
QUIZ_CARD_TITLE = "#rl-quiz-card-title"
QUIZ_RETAKE_COMPLETED = "#rl-quiz-retake-completed"
QUIZ_OVERLAY_CLOSE = "#rl-feed-quiz-overlay-close"
QUIZ_OVERLAY_BACKDROP = "#rl-feed-quiz-overlay-backdrop"
CABINET_QUIZ_RETAKE = "#rl-cabinet-quiz-retake"
CABINET_APP = "#rl-cabinet-app"

SESSION_KEY = "rawlead_quiz_session"
COMPLETED_KEY = "rawlead_quiz_completed_v1"
RETAKE_KEY = "rawlead_quiz_retake"
TOKEN_KEY = "rawlead_access_token"

DESKTOP_VIEWPORT = {"width": 1280, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}

ACC1_USER_ID = "895912a1-ffb6-46fb-be7e-4e051f2ff8c1"
MONICA_USER_ID = "8d5afb3d-e8bd-4970-a33d-21c3ddeafdef"

_ANIM_MS = 350
_SCENARIO_TIMEOUT_MS = 180_000

_CLEAR_QUIZ_STORAGE_JS = """() => {
  try {
    if (typeof window.rawleadClearQuizLocalKeys === "function") {
      window.rawleadClearQuizLocalKeys();
      return;
    }
    localStorage.removeItem("rawlead_quiz_session");
    localStorage.removeItem("rawlead_quiz_completed_v1");
    localStorage.removeItem("rawlead_quiz_restore_import_v1");
    sessionStorage.removeItem("rawlead_quiz_restore_import_v1");
    sessionStorage.removeItem("rawlead_quiz_retake");
  } catch (e) {}
}"""

_INJECT_TOKEN_JS = """(tok) => {
  localStorage.setItem("rawlead_access_token", tok);
  document.cookie =
    "rl_access=" + encodeURIComponent(tok) + "; path=/; max-age=2592000; SameSite=Lax";
}"""


def _page_has_origin(page: Any) -> bool:
    url = (page.url or "").strip()
    return bool(url) and url != "about:blank"


def _goto_lenta_origin(page: Any, base: str) -> None:
    page.goto(f"{base.rstrip('/')}/lenta/", wait_until="domcontentloaded")


def add_quiz_clear_init_script(context: Any) -> None:
    """Clear quiz keys before any page script runs (fresh context isolation)."""
    context.add_init_script(
        """() => {
          try {
            localStorage.removeItem("rawlead_quiz_session");
            localStorage.removeItem("rawlead_quiz_completed_v1");
            localStorage.removeItem("rawlead_quiz_restore_import_v1");
            sessionStorage.removeItem("rawlead_quiz_restore_import_v1");
            sessionStorage.removeItem("rawlead_quiz_retake");
          } catch (e) {}
        }"""
    )


def clear_quiz_storage(page: Any, *, base: str | None = None) -> None:
    if not _page_has_origin(page):
        if not base:
            return
        _goto_lenta_origin(page, base)
    page.evaluate(_CLEAR_QUIZ_STORAGE_JS)


def inject_access_token(page: Any, token: str, *, base: str | None = None) -> None:
    if not _page_has_origin(page):
        if not base:
            raise RuntimeError("inject_access_token on about:blank requires base")
        _goto_lenta_origin(page, base)
    page.evaluate(_INJECT_TOKEN_JS, token)


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


def goto_lenta_quiz(page: Any, base: str) -> None:
    page.goto(f"{base.rstrip('/')}/lenta/#quiz", wait_until="domcontentloaded")
    page.wait_for_selector(feed_ui.FEED_APP, state="visible")
    page.wait_for_selector(feed_ui.FEED_READY, timeout=45_000)
    page.wait_for_timeout(800)
    wait_quiz_overlay_open(page)


def wait_quiz_overlay_open(page: Any, *, timeout_ms: int = 30_000) -> None:
    overlay = page.locator(QUIZ_OVERLAY)
    overlay.wait_for(state="visible", timeout=timeout_ms)
    page.wait_for_function(
        f"() => {{ const o = document.querySelector('{QUIZ_OVERLAY}'); "
        f"return o && !o.hidden && o.getAttribute('aria-hidden') !== 'true'; }}",
        timeout=timeout_ms,
    )


def is_intro_visible(page: Any) -> bool:
    return bool(
        page.evaluate(
            f"""() => {{
              const intro = document.querySelector('{QUIZ_INTRO}');
              const stage = document.querySelector('{QUIZ_STAGE}');
              return !!(intro && !intro.hidden && stage && stage.classList.contains('rl-quiz-stage--intro'));
            }}"""
        )
    )


def is_play_visible(page: Any) -> bool:
    return bool(
        page.evaluate(
            f"""() => {{
              const play = document.querySelector('{QUIZ_PLAY}');
              const stage = document.querySelector('{QUIZ_STAGE}');
              return !!(play && !play.hidden && stage && stage.classList.contains('rl-quiz-stage--cards'));
            }}"""
        )
    )


def is_result_visible(page: Any) -> bool:
    return bool(
        page.evaluate(
            f"""() => {{
              const result = document.querySelector('{QUIZ_RESULT}');
              return !!(result && !result.hidden);
            }}"""
        )
    )


def assert_intro_visible(page: Any) -> None:
    if not is_intro_visible(page):
        raise RuntimeError("expected quiz intro stage")
    if is_play_visible(page):
        raise RuntimeError("quiz stuck on cards stage, expected intro")


def assert_result_visible(page: Any) -> None:
    if not is_result_visible(page):
        raise RuntimeError("quiz result modal not visible")


def start_quiz_from_intro(page: Any) -> None:
    btn = page.locator(QUIZ_INTRO_START)
    btn.wait_for(state="visible", timeout=15_000)
    btn.click()
    page.wait_for_function(
        f"""() => {{
          const play = document.querySelector('{QUIZ_PLAY}');
          const loading = document.getElementById('rl-quiz-loading');
          if (play && !play.hidden) return true;
          if (loading && !loading.hidden) return false;
          return false;
        }}""",
        timeout=45_000,
    )
    wait_quiz_cards_ready(page)


def wait_quiz_cards_ready(page: Any, *, timeout_ms: int = 45_000) -> None:
    page.wait_for_function(
        f"""() => {{
          const play = document.querySelector('{QUIZ_PLAY}');
          const like = document.querySelector('{QUIZ_LIKE}');
          const card = document.querySelector('{QUIZ_CARD}');
          return !!(play && !play.hidden && like && !like.disabled && card && !card.hidden);
        }}""",
        timeout=timeout_ms,
    )


def wait_quiz_action_idle(page: Any, *, timeout_ms: int = 15_000) -> None:
    page.wait_for_function(
        f"""() => {{
          const result = document.querySelector('{QUIZ_RESULT}');
          if (result && !result.hidden) return true;
          const like = document.querySelector('{QUIZ_LIKE}');
          return like && !like.disabled;
        }}""",
        timeout=timeout_ms,
    )


def click_quiz_decision(page: Any, *, like: bool = True) -> None:
    wait_quiz_action_idle(page)
    sel = QUIZ_LIKE if like else QUIZ_NOPE
    btn = page.locator(sel)
    btn.wait_for(state="visible", timeout=10_000)
    btn.click()
    page.wait_for_timeout(_ANIM_MS)
    wait_quiz_action_idle(page, timeout_ms=20_000)


def click_early_finish_if_visible(page: Any) -> bool:
    early = page.locator(QUIZ_EARLY_BTN)
    if early.count() and early.is_visible():
        early.click()
        page.wait_for_timeout(_ANIM_MS)
        return True
    return False


def answer_until_result(
    page: Any,
    *,
    min_answers: int = 5,
    max_answers: int = 16,
    timeout_ms: int = _SCENARIO_TIMEOUT_MS,
) -> int:
    """Click like/nope until result · handle early CTA · return answer count."""
    deadline = time.perf_counter() + timeout_ms / 1000
    answers = 0
    like_turn = True
    while time.perf_counter() < deadline:
        if is_result_visible(page):
            return answers
        if click_early_finish_if_visible(page):
            page.wait_for_function(
                f"() => {{ const r = document.querySelector('{QUIZ_RESULT}'); return r && !r.hidden; }}",
                timeout=30_000,
            )
            return answers
        if not is_play_visible(page):
            if is_intro_visible(page):
                raise RuntimeError("quiz returned to intro before result")
            page.wait_for_timeout(300)
            continue
        if answers >= max_answers:
            if click_early_finish_if_visible(page):
                continue
            raise RuntimeError(f"quiz did not finish after {max_answers} answers")
        click_quiz_decision(page, like=like_turn)
        like_turn = not like_turn
        answers += 1
        if answers >= min_answers:
            click_early_finish_if_visible(page)
    raise RuntimeError("quiz answer loop timeout")


def answer_n_cards(page: Any, n: int) -> None:
    for i in range(n):
        if is_result_visible(page):
            break
        click_quiz_decision(page, like=(i % 2 == 0))


def close_quiz_overlay(page: Any) -> None:
    for sel in (QUIZ_OVERLAY_CLOSE, QUIZ_OVERLAY_BACKDROP):
        btn = page.locator(sel)
        if btn.count() and btn.is_visible():
            btn.first.click(force=True)
            break
    else:
        page.keyboard.press("Escape")
    page.wait_for_function(
        f"() => {{ const o = document.querySelector('{QUIZ_OVERLAY}'); return !o || o.hidden; }}",
        timeout=15_000,
    )


def click_retake_on_result(page: Any, *, start_play: bool = True) -> None:
    assert_result_visible(page)
    btn = page.locator(f"{QUIZ_RETAKE_COMPLETED} button")
    btn.wait_for(state="visible", timeout=10_000)
    btn.click()
    page.wait_for_timeout(400)
    if is_intro_visible(page):
        if start_play:
            start_quiz_from_intro(page)
        return
    wait_quiz_cards_ready(page)


def read_completed_profile(page: Any) -> dict[str, Any] | None:
    raw = page.evaluate(
        f"""() => {{
          try {{
            const raw = localStorage.getItem({json.dumps(COMPLETED_KEY)});
            return raw || null;
          }} catch (e) {{ return null; }}
        }}"""
    )
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def assert_completed_profile_unchanged(page: Any, before: dict[str, Any]) -> None:
    after = read_completed_profile(page)
    if not after:
        raise RuntimeError("completed profile missing after retake abandon")
    before_tags = sorted((before.get("profile") or {}).get("tags_to_import") or [])
    after_tags = sorted((after.get("profile") or {}).get("tags_to_import") or [])
    if before_tags != after_tags:
        raise RuntimeError("retake abandon changed tags_to_import")


def attach_quiz_api_monitor(page: Any, sink: list[dict[str, Any]]) -> Callable[[Any], None]:
    pattern = re.compile(r"/wp-json/rawlead/v1/quiz/(start|next)")

    def on_response(response: Any) -> None:
        try:
            if pattern.search(response.url):
                sink.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "ok": response.ok,
                    }
                )
        except Exception:
            pass

    page.on("response", on_response)
    return on_response


def assert_quiz_api_ok(api_calls: list[dict[str, Any]], *, min_calls: int = 1) -> None:
    if len(api_calls) < min_calls:
        raise RuntimeError(f"expected >= {min_calls} quiz API calls, got {len(api_calls)}")
    bad = [c for c in api_calls if not c.get("ok")]
    if bad:
        raise RuntimeError(f"quiz API non-200: {bad[-1]}")


def count_neon_user_tags(user_id: str) -> int | None:
    db_url = __import__("os").environ.get("DATABASE_URL", "").strip()
    if not db_url:
        return None
    try:
        import psycopg2

        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM user_tags WHERE user_id = %s::uuid",
                    (user_id,),
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0
    except Exception as exc:
        raise RuntimeError(f"Neon tag count failed: {exc}") from exc


def trigger_post_login_import(page: Any) -> None:
    """After anon quiz + JWT inject — import completed profile (TG widget blocked headless)."""
    page.evaluate(
        """async () => {
          if (typeof window.rawleadImportCompletedQuiz === "function") {
            await window.rawleadImportCompletedQuiz();
            return;
          }
          throw new Error("rawleadImportCompletedQuiz missing");
        }"""
    )
    page.wait_for_timeout(1500)


def assert_synthetic_card_in_quiz(page: Any) -> None:
    """Synthetic cards: title visible · source badge hidden (O219)."""
    start_quiz_from_intro(page)
    deadline = time.perf_counter() + 90
    seen_synthetic = False
    answers = 0
    while time.perf_counter() < deadline and answers < 14:
        if is_result_visible(page):
            break
        title = (page.locator(QUIZ_CARD_TITLE).inner_text() or "").strip()
        if not title:
            raise RuntimeError("quiz card title empty")
        source_hidden = page.evaluate(
            f"""() => {{
              const el = document.querySelector('{QUIZ_CARD_SOURCE}');
              return !el || el.hidden || !(el.innerText || '').trim();
            }}"""
        )
        if source_hidden and title:
            seen_synthetic = True
            break
        click_quiz_decision(page, like=(answers % 2 == 0))
        answers += 1
    if not seen_synthetic:
        raise RuntimeError("no synthetic quiz card (hidden source badge + title)")


def expand_first_feed_card(page: Any, *, timeout_ms: int = 60_000) -> Any:
    feed_ui.wait_feed_loading_done(page)
    try:
        feed_ui.reset_feed_filters(page)
    except Exception:
        pass
    page.wait_for_selector(feed_ui.FEED_CARD, timeout=timeout_ms)
    cards = page.locator(feed_ui.FEED_CARD)
    if not cards.count():
        raise RuntimeError("no feed cards for match assert")
    card = cards.first
    feed_ui.expand_card(card, page)
    return card


def goto_cabinet_logged_in(
    page: Any,
    base: str,
    *,
    token: str | None = None,
    timeout_ms: int = 90_000,
) -> None:
    url = f"{base.rstrip('/')}/cabinet/"

    def _wait_app() -> None:
        page.wait_for_selector('[data-rl-app="cabinet"]', state="visible")
        page.wait_for_function(
            f"() => {{ const app = document.querySelector('{CABINET_APP}'); return app && !app.hidden; }}",
            timeout=timeout_ms,
        )

    page.goto(url, wait_until="domcontentloaded")
    try:
        _wait_app()
        return
    except Exception:
        pass

    if token:
        inject_access_token(page, token, base=base)
        page.goto(url, wait_until="domcontentloaded")
        try:
            _wait_app()
            return
        except Exception:
            pass

    try:
        diag = page.evaluate(
            """() => ({
              login: !!(document.getElementById('rl-cabinet-login') && !document.getElementById('rl-cabinet-login').hidden),
              token: !!localStorage.getItem('rawlead_access_token'),
            })"""
        )
    except Exception:
        diag = {"login": None, "token": None}
    raise RuntimeError(f"cabinet app not shown: {diag}")


def click_cabinet_quiz_retake(page: Any, base: str) -> None:
    retake = page.locator(CABINET_QUIZ_RETAKE)
    if retake.count():
        retake.wait_for(state="visible", timeout=20_000)
        if retake.is_visible():
            with page.expect_navigation(url=re.compile(r"/lenta/.*#quiz"), timeout=30_000):
                retake.click()
            wait_quiz_overlay_open(page)
            return
    btn = page.get_by_role("button", name=re.compile(r"заново", re.I))
    if btn.count() and btn.first.is_visible():
        with page.expect_navigation(url=re.compile(r"/lenta/.*#quiz"), timeout=30_000):
            btn.first.click()
        wait_quiz_overlay_open(page)
        return
    page.evaluate(
        """() => {
          sessionStorage.setItem("rawlead_quiz_retake", "1");
        }"""
    )
    page.goto(f"{base.rstrip('/')}/lenta/#quiz", wait_until="domcontentloaded")
    wait_quiz_overlay_open(page)
