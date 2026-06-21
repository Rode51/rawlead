# POST-G1 E2E audit — MiMo 2026-06-20

**Scope:** G1 artifact confirm · harness vs PA-5b parity · remaining draft/feed gaps · delta vs pre-ads-readiness
**G1 artifact:** `data/preprod_next_e2e.json` · 24/24 PASS · 2026-06-20 09:45 UTC
**Baseline:** `2026-06-20-mimo-pre-ads-readiness.md` (23 findings)

---

## 1. G1 artifact confirmation

**24/24 pass** — desktop 23 + mobile 1.

| Scenario | ms | What it does | Note |
|----------|-----|-------------|------|
| **n5** | **132,117** | Draft generation (1 lead) — expand → POST draft → poll → assert text ≥80 chars | **Slow: product, not flake.** OpenRouter API latency + Playwright poll loop. Acceptable for E2E but ~2 min per run. |
| **n16** | **58,557** | Draft twice (2 leads) — 35s hardcoded wait between drafts | **Slow: product + intentional cooldown.** `page.wait_for_timeout(35_000)` at line 365 is deliberate rate-limit spacing. Real user would wait naturally. |
| **n17** | **7,408** | Draft collapse mid — expand → click CTA → click card to collapse | Fast. No API call, just UI state. |
| n1–n4, n6–n25 | 1,473–14,593 | Navigation, quiz, cabinet, pricing, FAQ, filters | Normal range. |

**Flake risk:** Low. n5/n16 timeouts are generous (OpenRouter can take 30–90s for complex leads). If OpenRouter is down, both fail hard with `RuntimeError` — correct behavior. No retry loops masking intermittent failures.

---

## 2. Harness vs PA-5b parity

| Check | Harness (`next_ui.py`) | API (`api_server.py`) | Match? |
|-------|------------------------|----------------------|--------|
| Feed gate | `lead_ids_pass_draft_gate`: `keyword_match` parsed as int, `> 0` required (line 353–368) | `_lead_in_user_feed`: calls `_passes_min_match(km, 0)` which returns `False` if `km is None or km <= 0` (line 658–661) | ✅ Aligned |
| Feed source | `fetch_me_feed` → `GET /v1/me/feed` with preprod token | `/v1/me/feed` applies `feed_visibility_where_sql` + `_personal_feed_page` | ✅ Same endpoint |
| Draft submission | `generate_draft_on_card` → `POST /v1/me/leads/{id}/draft` | `me_lead_draft` endpoint calls `_lead_in_user_feed` before `submit_draft` (line 2743) | ✅ Server-side gate present |
| Draft response | Asserts `len(text) ≥ 80` | Returns `reply_draft` from OpenRouter via `draft_response_body` | ✅ Content check present |

**No gap found** between harness filter logic and API gate. Both require `keyword_match > 0`.

---

## 3. Remaining draft/feed P0/P1 not covered by harness

| # | Severity | File:line | Finding | Delta vs pre-ads |
|---|----------|-----------|---------|-----------------|
| **G1** | **P1** | `FeedCard.tsx:125-126` | **CTA "Написать отклик →" visible on ALL premium cards regardless of km.** `handleReplyClick` only checks `feedTier === 'premium'` — no km check. User clicks → API returns 404 (from `_lead_in_user_feed`) → toast error. UX gap: CTA should be hidden or dimmed when `keyword_match === 0` or `null`. | **NEW** — not in pre-ads (was security-focused, not UX) |
| **G2** | **P2** | `FeedCard.tsx:144` | **No optimistic UI for draft 404.** `meApi.createDraft` catches error and shows toast, but the card stays expanded with empty draft area. Could collapse or show "нет совпадений" hint. | **NEW** |
| **G3** | **P2** | `next_e2e.py:365` | **Hardcoded 35s wait in n16.** If OpenRouter improves to <5s, this wastes 30s per run. Should poll for draft completion instead of fixed sleep. | **NEW** (harness quality) |
| **G4** | **INFO** | `next_e2e.py:224` | **n5 asserts `len(text) ≥ 80` but not content quality.** A draft like "OK" × 40 chars would pass. Acceptable for E2E gate but not for L3 judge. | **NEW** |

---

## 4. Cross-check: pre-ads P0 #8 (draft feed-membership)

**Status: FIXED in product.**

| Component | Evidence |
|-----------|----------|
| API gate | `api_server.py:2743` — `if not _lead_in_user_feed(cur, user_id, lead_id): raise HTTPException(status_code=404)` |
| `_lead_in_user_feed` | `api_server.py:2580-2596` — checks `_fetch_visible_lead` (is_visible + source + 7d window) + `_keyword_match_for_user` > 0 via `_passes_min_match(km, 0)` |
| Harness mirror | `next_ui.py:353-368` — `lead_ids_pass_draft_gate` filters `keyword_match > 0` before attempting draft |
| PRE-ADS-MIMO W1 | `CODER_PROMPT.md` line 47: "PA-5b `_lead_in_user_feed` + draft 404 ✅" |

**Delta:** Pre-ads P0 #8 was "Draft endpoint missing feed-membership check." This is now resolved — server-side gate + harness-side pre-filter both enforced. The new P1 G1 (CTA visible on km=0 cards) is a **UX refinement**, not a security gap.

---

## 5. Summary: new findings delta

| # | Sev | Finding | Action |
|---|-----|---------|--------|
| G1 | **P1** | CTA shows on km=0 cards → user sees 404 toast | FeedCard: hide/dim CTA when `item.keyword_match <= 0` or null |
| G2 | P2 | No optimistic collapse on draft 404 | FeedCard: collapse + hint on error |
| G3 | P2 | n16 hardcoded 35s sleep | Harness: poll instead of sleep |
| G4 | INFO | n5 length-only check | Low priority — L3 judge covers quality |

**Pre-ads items still open (unchanged):**

| Pre-ads # | Status | Note |
|-----------|--------|------|
| P0 #1 (K-hide) | ❌ Still missing | Not in scope of this audit |
| P0 #2 (28 pool bypasses) | ✅ Fixed (PRE-ADS-MIMO W1) | Verified in PROD_FACTS |
| P0 #3 (L3 dedup) | ❌ Still missing | Design decision pending |
| P1 #7 (webhook compare_digest) | ✅ Fixed (PRE-ADS-MIMO W1) | Verified |
| P1 #8 (draft feed-membership) | ✅ Fixed (PRE-ADS-MIMO W1) | Verified above |

---

**Deploy:** no code in this report. G1 → `@coder` FeedCard km=0 CTA gate.
