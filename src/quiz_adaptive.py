"""O197: adaptive quiz — deterministic branching from client history (stateless).

O217: card source swapped from Neon `leads` to data/quiz_cards_v1.json (static pack).
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

QUIZ_NICHES: tuple[str, ...] = ("dev", "design", "marketing", "text")
QUIZ_PHASE1_SEED = 9
QUIZ_MAX_CARDS = 20
QUIZ_EARLY_STOP_MIN = 6
QUIZ_NORMAL_STOP_MIN = 13

QUIZ_POOL_EXCLUDE_IDS = frozenset({21483, 22251, 21419})

# ---------------------------------------------------------------------------
# O217/O221: JSON card packs (replaces Neon allowlist + SQL queries for quiz cards)
# ---------------------------------------------------------------------------

_QUIZ_CARD_PACKS: tuple[str, ...] = ("quiz_cards_v1.json", "quiz_cards_v2.json")

_JSON_CARDS: list[dict[str, Any]] | None = None
_JSON_CARDS_LOADED = False

# _JSON_CATEGORIES: {card_id_str: niche} for fast lookup
_JSON_CATEGORIES: dict[str, str] = {}


def _load_json_cards() -> list[dict[str, Any]] | None:
    global _JSON_CARDS, _JSON_CARDS_LOADED, _JSON_CATEGORIES
    if _JSON_CARDS_LOADED:
        return _JSON_CARDS
    _JSON_CARDS_LOADED = True
    data_dir = Path(__file__).resolve().parent.parent / "data"
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for name in _QUIZ_CARD_PACKS:
        path = data_dir / name
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                for card in raw:
                    cid = card.get("id")
                    if not cid or cid in seen_ids:
                        continue
                    seen_ids.add(str(cid))
                    merged.append(card)
        except Exception as exc:
            logger.warning("%s load failed: %s", name, exc)
    if merged:
        _JSON_CARDS = merged
        _JSON_CATEGORIES = {
            c["id"]: c["niche"] for c in merged if "id" in c and "niche" in c
        }
        logger.info("quiz card packs loaded: %d cards", len(merged))
        return _JSON_CARDS
    logger.warning("quiz card packs not found — falling back to Neon")
    return None


def _liked_tags_from_history(history: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for item in history:
        if not item.get("liked"):
            continue
        for tag in item.get("tags") or []:
            t = str(tag).strip()
            if t:
                out.add(t)
    return out


def _unseen_skill_score(card: dict[str, Any], liked_tags: set[str]) -> int:
    skills = card.get("skills_on_like") or []
    return sum(1 for skill in skills if str(skill) not in liked_tags)


def _pick_json_candidate(
    candidates: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    liked_tags = _liked_tags_from_history(history)
    random.shuffle(candidates)
    candidates.sort(key=lambda c: _unseen_skill_score(c, liked_tags), reverse=True)
    return candidates[0]


def _query_card_json(
    niche: str,
    signal: str | None,
    shown_ids: list[str],
    *,
    card_type: str | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Pick a card from JSON pack by niche/signal, skipping already-shown ids."""
    cards = _load_json_cards()
    if cards is None:
        return None
    shown_set = set(shown_ids)
    hist = history or []
    # Priority: exact signal match first, then any card in niche
    candidates = [
        c for c in cards
        if c.get("niche") == niche
        and c.get("id") not in shown_set
        and (card_type is None or c.get("card_type") == card_type)
        and (signal is None or c.get("signal") == signal)
    ]
    if not candidates and signal is not None:
        # fallback: any card for this niche (traps + boundaries included)
        candidates = [
            c for c in cards
            if c.get("niche") == niche
            and c.get("id") not in shown_set
            and (card_type is None or c.get("card_type") == card_type)
        ]
    if not candidates:
        return None
    return _pick_json_candidate(candidates, hist)


def _card_payload_json(card: dict[str, Any]) -> dict[str, Any]:
    """Build API response payload from JSON card dict."""
    return {
        "card_id": card["id"],
        "title": card.get("title", ""),
        "category": card.get("niche", ""),
        "lead_tags": card.get("skills_on_like", []),
        "source": "synthetic",
        "body": card.get("task_summary", ""),
        "budget_text": "",
        "url": "",
        "task_summary": card.get("task_summary", ""),
        "complexity": card.get("complexity"),
    }


# ---------------------------------------------------------------------------
# Legacy Neon allowlist (O216b — kept for backward compat until O217 deploy)
# ---------------------------------------------------------------------------

_ALLOWLIST: list[int] | None = None
_ALLOWLIST_LOADED = False


def _load_allowlist() -> list[int] | None:
    global _ALLOWLIST, _ALLOWLIST_LOADED
    if _ALLOWLIST_LOADED:
        return _ALLOWLIST
    _ALLOWLIST_LOADED = True
    path = Path(__file__).resolve().parent.parent / "data" / "quiz_pool_allowlist.json"
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            ids = [int(x) for x in raw if isinstance(x, (int, str))]
            _ALLOWLIST = ids if ids else None
            return _ALLOWLIST
    except Exception as exc:
        logger.warning("quiz_pool_allowlist load failed: %s", exc)
    return None
# 21483 — fake review request
# 22251 — freelancer ad, not a client order
# 21419 — junk title

QUIZ_SIGNALS: dict[str, tuple[str, ...]] = {
    "dev": (
        "python",
        "wordpress_dev",
        "api_integration",
        "server_administration",
        "javascript",
        "web_scraping",
        "tilda_dev",
        "data_analysis",
        "ecommerce_dev",
        "html_css",
        "llm_integration",
        "telegram_bot_dev",
    ),
    "design": (
        "ui_ux",
        "video_editing",
        "brand_identity",
        "presentation_design",
        "threed_modeling",
        "infographic_design",
        "illustration",
        "banner_design",
        "figma",
        "logo_design",
        "motion_design",
        "web_design",
    ),
    "marketing": (
        "smm",
        "yandex_direct",
        "seo",
        "marketplace_promotion",
        "target_ads",
        "chatbot_marketing",
        "content_marketing",
        "email_marketing",
        "google_ads",
        "technical_seo",
        "web_analytics",
    ),
    "text": (
        "copywriting",
        "article_writing",
        "editing_proofreading",
        "translation",
        "transcription",
        "product_description",
        "script_writing",
        "seo_copywriting",
        "technical_writing",
        "sales_copywriting",
    ),
}


def phase1_niche_order() -> list[str]:
    niches = list(QUIZ_NICHES)
    random.Random(QUIZ_PHASE1_SEED).shuffle(niches)
    return niches


def compute_niche_confidence(
    history: list[dict[str, Any]],
    categories: dict[str, str],
) -> dict[str, int]:
    conf = {n: 0 for n in QUIZ_NICHES}
    for item in history:
        cat = categories.get(str(item.get("card_id", "")))
        if cat not in conf:
            continue
        if item.get("liked"):
            conf[cat] += 2
        else:
            conf[cat] -= 1
    return conf


def _niches_ge2(conf: dict[str, int]) -> frozenset[str]:
    return frozenset(n for n in QUIZ_NICHES if conf[n] >= 2)


def check_stop(
    history: list[dict[str, Any]],
    categories: dict[str, str],
) -> tuple[bool, bool]:
    """Return (should_stop, null_profile)."""
    n = len(history)
    if n == 0:
        return False, False

    conf = compute_niche_confidence(history, categories)

    if n >= QUIZ_MAX_CARDS:
        return True, all(c <= 0 for c in conf.values())

    if n >= QUIZ_NORMAL_STOP_MIN and all(c <= 0 for c in conf.values()):
        return True, True

    if n >= QUIZ_EARLY_STOP_MIN:
        strong = [niche for niche, c in conf.items() if c >= 4]
        if len(strong) == 1:
            leader = strong[0]
            if all(conf[other] <= 0 for other in QUIZ_NICHES if other != leader):
                return True, False

    if n >= QUIZ_NORMAL_STOP_MIN:
        sets: list[frozenset[str]] = []
        for end in (n - 2, n - 1, n):
            if end < 0:
                continue
            partial = compute_niche_confidence(history[:end], categories)
            sets.append(_niches_ge2(partial))
        if len(sets) == 3 and sets[0] == sets[1] == sets[2]:
            return True, False

    return False, False


def _niche_card_count(history: list[dict[str, Any]], categories: dict[str, str], niche: str) -> int:
    return sum(
        1
        for item in history
        if categories.get(str(item.get("card_id", ""))) == niche
    )


def _signal_liked_counts(
    niche: str,
    history: list[dict[str, Any]],
    categories: dict[str, str],
) -> dict[str, int]:
    signals = QUIZ_SIGNALS[niche]
    counts = {signal: 0 for signal in signals}
    cards = _load_json_cards() or []
    card_signal = {
        c["id"]: c.get("signal")
        for c in cards
        if c.get("niche") == niche and c.get("id")
    }
    for item in history:
        if not item.get("liked"):
            continue
        cid = str(item.get("card_id", ""))
        if categories.get(cid) != niche:
            continue
        sig = card_signal.get(cid)
        if sig in counts:
            counts[sig] += 1
        for tag in item.get("tags") or []:
            t = str(tag)
            if t in counts:
                counts[t] += 1
    return counts


def pick_signal_for_niche(
    niche: str,
    history: list[dict[str, Any]],
    categories: dict[str, str],
    *,
    phase3: bool = False,
    conf: dict[str, int] | None = None,
) -> str:
    signals = QUIZ_SIGNALS[niche]
    count = _niche_card_count(history, categories, niche)
    if conf is not None and conf.get(niche, 0) >= 4:
        liked_counts = _signal_liked_counts(niche, history, categories)
        min_count = min(liked_counts[signal] for signal in signals)
        least = [signal for signal in signals if liked_counts[signal] == min_count]
        return least[count % len(least)]
    if phase3 and count >= len(signals):
        return signals[count % len(signals)]
    return signals[min(count, len(signals) - 1)]


def pick_target_niche_and_signal(
    history: list[dict[str, Any]],
    categories: dict[str, str],
) -> tuple[str, str]:
    n = len(history)
    conf = compute_niche_confidence(history, categories)

    if n < 4:
        niche = phase1_niche_order()[n]
        signal = pick_signal_for_niche(niche, history, categories, conf=conf)
        return niche, signal

    max_conf = max(conf.values())
    phase3 = n >= QUIZ_NORMAL_STOP_MIN and max_conf < 2

    if phase3:
        ranked = sorted(QUIZ_NICHES, key=lambda niche: (conf[niche], niche), reverse=True)
        top2 = ranked[:2]
        counts = {niche: _niche_card_count(history, categories, niche) for niche in top2}
        niche = top2[0] if counts[top2[0]] <= counts[top2[1]] else top2[1]
        signal = pick_signal_for_niche(niche, history, categories, phase3=True, conf=conf)
        return niche, signal

    leaders_ge2 = [niche for niche in QUIZ_NICHES if conf[niche] >= 2]
    if len(leaders_ge2) == 1 and all(
        conf[other] <= 0 for other in QUIZ_NICHES if other != leaders_ge2[0]
    ):
        niche = leaders_ge2[0]
        signal = pick_signal_for_niche(niche, history, categories, conf=conf)
        return niche, signal

    ge1 = sorted(
        [niche for niche in QUIZ_NICHES if conf[niche] >= 1],
        key=lambda niche: (conf[niche], niche),
        reverse=True,
    )
    if len(ge1) >= 2:
        leader, second = ge1[0], ge1[1]
        phase2_idx = n - 4
        niche = second if phase2_idx % 3 == 2 else leader
    elif len(ge1) == 1:
        niche = ge1[0]
    else:
        niche = sorted(QUIZ_NICHES, key=lambda niche: (conf[niche], niche), reverse=True)[0]

    signal = pick_signal_for_niche(niche, history, categories, conf=conf)
    return niche, signal


def build_tags_to_import(history: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in history:
        if not item.get("liked"):
            continue
        for tag in item.get("tags") or []:
            t = str(tag)
            if t and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def build_profile(
    history: list[dict[str, Any]],
    categories: dict[str, str],
    leads_per_week: int,
) -> dict[str, Any] | None:
    conf = compute_niche_confidence(history, categories)
    if all(c <= 0 for c in conf.values()):
        return None
    niches = sorted(
        [{"niche": niche, "confidence": conf[niche]} for niche in QUIZ_NICHES if conf[niche] >= 2],
        key=lambda row: (-row["confidence"], row["niche"]),
    )
    liked_cx = [
        int(item["complexity"])
        for item in history
        if item.get("liked") and item.get("complexity") is not None
    ]
    if liked_cx:
        cx_pref = round(sum(liked_cx) / len(liked_cx), 1)
        cx_pref = max(1.0, min(2.0, cx_pref))
    else:
        cx_pref = 2.0
    return {
        "niches": niches,
        "tags_to_import": build_tags_to_import(history),
        "leads_per_week": leads_per_week,
        "cx_pref": cx_pref,
    }


def card_payload(row: tuple[Any, ...]) -> dict[str, Any]:
    from src.ai_reasons import difficulty_from_ai_reasons
    from src.skills_catalog import lead_tags_for_feed

    lead_id, title, stored_category, lead_tags = row[:4]
    ai_reasons = row[4] if len(row) > 4 else None
    source = row[5] if len(row) > 5 else ""
    body = row[6] if len(row) > 6 else ""
    budget_text = row[7] if len(row) > 7 else ""
    url = row[8] if len(row) > 8 else ""
    created_at = row[9] if len(row) > 9 else None
    task_summary = row[10] if len(row) > 10 else ""
    tags, _ = lead_tags_for_feed(lead_tags)
    out: dict[str, Any] = {
        "card_id": str(lead_id),
        "title": title or "",
        "category": stored_category or "",
        "lead_tags": tags,
        "source": source or "",
        "body": body or "",
        "budget_text": budget_text or "",
        "url": url or "",
        "task_summary": (task_summary or "").strip(),
    }
    if created_at is not None:
        if hasattr(created_at, "isoformat"):
            out["created_at"] = created_at.isoformat()
        else:
            out["created_at"] = str(created_at)
    complexity = difficulty_from_ai_reasons(ai_reasons)
    if complexity is not None:
        out["complexity"] = complexity
    return out


def _shown_ids_as_int(shown_ids: list[str]) -> list[int]:
    """Neon SQL exclude list — numeric ids only; JSON string ids are skipped."""
    out: list[int] = []
    for raw in shown_ids:
        try:
            out.append(int(raw))
        except (TypeError, ValueError):
            continue
    return out


def fetch_quiz_card(
    cur: Any,
    niche: str,
    signal: str,
    shown_ids: list[str],
    *,
    history: list[dict[str, Any]] | None = None,
    fetcher: Callable[..., tuple[Any, ...] | None] | None = None,
) -> dict[str, Any] | None:
    if fetcher is not None:
        row = fetcher(cur, niche, signal, shown_ids)
        return card_payload(row) if row else None

    hist = history or []
    # O217: try JSON pack first
    shown_str = list(shown_ids)
    json_card = _query_card_json(niche, signal, shown_str, history=hist)
    if json_card is not None:
        return _card_payload_json(json_card)

    # fallback: try other signals from JSON pack
    for alt in QUIZ_SIGNALS.get(niche, ()):
        if alt == signal:
            continue
        json_card = _query_card_json(niche, alt, shown_str, history=hist)
        if json_card is not None:
            return _card_payload_json(json_card)

    # fallback: any JSON card for niche (incl. traps)
    json_card = _query_card_json(niche, None, shown_str, history=hist)
    if json_card is not None:
        return _card_payload_json(json_card)

    # last resort: Neon SQL (only if JSON pack unavailable)
    if _load_json_cards() is None:
        logger.warning("quiz_cards_v1.json unavailable, querying Neon for niche=%s", niche)
        shown_int = _shown_ids_as_int(shown_ids)
        row = _query_card(cur, niche, signal, shown_int)
        if row:
            return card_payload(row)
        for alt in QUIZ_SIGNALS.get(niche, ()):
            if alt == signal:
                continue
            row = _query_card(cur, niche, alt, shown_int)
            if row:
                return card_payload(row)
        row = _query_card(cur, niche, None, shown_int)
        return card_payload(row) if row else None

    return None


def _query_card(
    cur: Any,
    niche: str,
    signal: str | None,
    shown_ids: list[int],
    *,
    min_score: int = 60,
) -> tuple[Any, ...] | None:
    shown = list(shown_ids) if shown_ids else []
    exclude = list(QUIZ_POOL_EXCLUDE_IDS | set(shown))
    if not exclude:
        exclude = [0]

    allowlist = _load_allowlist()

    row = _query_card_inner(cur, niche, signal, exclude, cx_only=True, min_score=min_score, allowlist=allowlist)
    if not row:
        row = _query_card_inner(cur, niche, signal, exclude, cx_only=False, min_score=min_score, allowlist=allowlist)
    if row or min_score <= 45:
        if not row and allowlist:
            logger.warning("quiz_pool_allowlist: pool exhausted for niche=%s signal=%s, using fallback", niche, signal)
            row = _query_card_inner(cur, niche, signal, exclude, cx_only=True, min_score=min_score, allowlist=None)
            if not row:
                row = _query_card_inner(cur, niche, signal, exclude, cx_only=False, min_score=min_score, allowlist=None)
        return row
    row = _query_card_inner(cur, niche, signal, exclude, cx_only=True, min_score=45, allowlist=allowlist)
    if not row:
        row = _query_card_inner(cur, niche, signal, exclude, cx_only=False, min_score=45, allowlist=allowlist)
    if not row and allowlist:
        logger.warning("quiz_pool_allowlist: pool exhausted (min_score=45) for niche=%s signal=%s, using fallback", niche, signal)
        row = _query_card_inner(cur, niche, signal, exclude, cx_only=True, min_score=45, allowlist=None)
        if not row:
            row = _query_card_inner(cur, niche, signal, exclude, cx_only=False, min_score=45, allowlist=None)
    return row


def _query_card_inner(
    cur: Any,
    niche: str,
    signal: str | None,
    exclude_ids: list[int],
    *,
    cx_only: bool,
    min_score: int,
    allowlist: list[int] | None = None,
) -> tuple[Any, ...] | None:
    cx_sql = "AND (ai_reasons->>'complexity')::int IN (1, 2)" if cx_only else ""
    allow_sql = "AND id = ANY(%s)" if allowlist else ""
    if signal:
        params: tuple[Any, ...] = (min_score, niche, json.dumps([signal]), exclude_ids)
        if allowlist:
            params = params + (allowlist,)
        cur.execute(
            f"""
            SELECT id, title, category, lead_tags, ai_reasons,
                   source, body, budget_text, url, created_at, task_summary
            FROM leads
            WHERE is_visible = TRUE
              AND ai_score >= %s
              AND category = %s
              AND lead_tags @> %s::jsonb
              AND id != ALL(%s)
              {allow_sql}
              {cx_sql}
            ORDER BY ai_score DESC, created_at DESC
            LIMIT 1
            """,
            params,
        )
    else:
        params = (min_score, niche, exclude_ids)
        if allowlist:
            params = params + (allowlist,)
        cur.execute(
            f"""
            SELECT id, title, category, lead_tags, ai_reasons,
                   source, body, budget_text, url, created_at, task_summary
            FROM leads
            WHERE is_visible = TRUE
              AND ai_score >= %s
              AND category = %s
              AND id != ALL(%s)
              {allow_sql}
              {cx_sql}
            ORDER BY ai_score DESC, created_at DESC
            LIMIT 1
            """,
            params,
        )
    return cur.fetchone()


def fetch_card_categories(cur: Any, card_ids: list[str]) -> dict[str, str]:
    if not card_ids:
        return {}

    # O217: use JSON categories map when available
    _load_json_cards()  # ensure _JSON_CATEGORIES populated
    json_result: dict[str, str] = {}
    neon_ids: list[int] = []

    for raw in card_ids:
        if raw in _JSON_CATEGORIES:
            json_result[raw] = _JSON_CATEGORIES[raw]
        else:
            try:
                neon_ids.append(int(raw))
            except (TypeError, ValueError):
                continue

    if not neon_ids:
        return json_result

    # fallback for any ids not found in JSON (legacy Neon cards)
    cur.execute(
        """
        SELECT id, category
        FROM leads
        WHERE id = ANY(%s)
        """,
        (neon_ids,),
    )
    neon_result = {str(row[0]): row[1] or "" for row in cur.fetchall()}
    return {**json_result, **neon_result}


def count_leads_per_week(cur: Any, niches: list[str]) -> int:
    if not niches:
        return 0
    cur.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE is_visible = TRUE
          AND category = ANY(%s)
          AND created_at > NOW() - INTERVAL '7 days'
        """,
        (niches,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def quiz_next_response(
    history: list[dict[str, Any]],
    cur: Any,
    *,
    fetcher: Callable[..., tuple[Any, ...] | None] | None = None,
) -> dict[str, Any]:
    card_ids = [str(item.get("card_id", "")) for item in history]
    categories = fetch_card_categories(cur, card_ids)

    should_stop, null_profile = check_stop(history, categories)
    if should_stop:
        if null_profile:
            return {"done": True, "profile": None}
        conf = compute_niche_confidence(history, categories)
        profile_niches = [n for n in QUIZ_NICHES if conf[n] >= 2]
        leads_per_week = count_leads_per_week(cur, profile_niches)
        profile = build_profile(history, categories, leads_per_week)
        return {"done": True, "profile": profile}

    shown_ids = [s for s in card_ids if s]

    niche, signal = pick_target_niche_and_signal(history, categories)
    card = fetch_quiz_card(cur, niche, signal, shown_ids, history=history, fetcher=fetcher)
    if not card:
        return {"done": True, "profile": None}
    return {"done": False, "card": card}
