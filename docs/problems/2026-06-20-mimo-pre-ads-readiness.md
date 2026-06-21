# PRE-ADS readiness audit — MiMo 2026-06-20

**Scope:** PA-3 load · PA-2 L3 uniquify · PA-4 K-hide · PA-5 security · rawlead-next
**Method:** static analysis (read-only) · no pentest, no load test
**Coder §:** PRE-ADS-GATE → PA-1…PA-5

---

## P0 — blockers before ads spend

| # | PA | File:line | Finding |
|---|----|-----------|---------|
| **1** | PA-4 | (absent) | **K-hide (O208-B) entirely missing.** No `draft_count`, no `reply_count`, no auto-hide after K replies. `feed_visibility_where_sql` has zero count gating. Manual `hide_lead()` exists but no threshold logic. Ads spend → users see leads others already replied to → waste of drafts + bad UX. |
| **2** | PA-3 | `api_server.py:1529,1598,1715,+25` | **28 route handlers bypass connection pool.** Use bare `psycopg.connect(_db_url())` instead of `_db_conn()`. Under concurrent load: each request opens+close TCP+TLS, saturates Postgres `max_connections`. Includes `/v1/auth/telegram`, `/v1/me/avatar`, `/v1/me/tags/*`, `/v1/me/feed-prefs`, subscription endpoints, `/v1/internal/leads` (ingest). |
| **3** | PA-2 | `ai_analyze.py:2572` | **No cross-user dedup on L3 uniquify.** `l3_too_similar(base, draft)` checks against shared base only. 50 users on same lead → seed maps to 12 combos (3 struct × 4 voice) → ~4 users share identical system prompt + temperature. LLM stochasticity is only separator. Risk of near-identical drafts visible to owner in M1 postseeding. |

## P1 — fix before ads or hotfix after

| # | PA | File:line | Finding |
|---|----|-----------|---------|
| **4** | PA-3 | `api_server.py:620-638,855,1010,1083,1155` | **Correlated `COUNT(*)` subquery in every feed SELECT.** Doubles table scans. `SELECT COUNT(*) FROM leads WHERE ...` embedded as scalar subquery — Postgres cannot merge with outer `ORDER BY LIMIT N`. |
| **5** | PA-3 | `api_server.py:748-763` | **`_feed_today_count` with categories = full Python scan.** Fetches ALL today's leads (no LIMIT), iterates every row calling `resolve_lead_category()`. Cached 180s but uncached path is O(N). |
| **6** | PA-3 | `pg_storage.py:222-227` | **`NeonLeadStorage` opens new connection per call.** 30+ methods, each `psycopg.connect()`. No pool reuse. Ops dashboard + ingest path. |
| **7** | PA-5 | `api_server.py:3074` | **YooKassa webhook timing-unsafe comparison.** `got != secret` plain `!=` instead of `hmac.compare_digest()`. Ops gate at line 3390 correctly uses `compare_digest` — webhook endpoint should too. |
| **8** | PA-5 | `api_server.py:2689` | **Draft endpoint missing feed-membership check.** Any subscribed user can POST `/v1/me/leads/{lead_id}/draft` for any `is_visible=TRUE` lead. No verification that lead appears in user's personalized feed. |
| **9** | PA-2 | `ai_analyze.py:2489` | **L3 seed maps to only 12 prompt combos.** `variation_seed % 3` (structure) × 4 voice variants. With 50+ concurrent users on same lead, statistical collision is near-certain. |
| **10** | Next | `lib/api.ts:29,40` | **JWT in `localStorage`.** XSS → full account takeover. No HttpOnly cookie fallback. No `middleware.ts` for server-side auth. Cabinet page is client-side-only gate (`auth.status === 'anon'`). |
| **11** | Next | `lib/api.ts:276` | **Bot auth token in query string** `?auth=...`. Logged in server access logs, proxy logs, browser history. `history.replaceState` removes from URL bar but not from Referer. |
| **12** | Next | `app/cabinet/layout.tsx:14` | **No server-side auth guard on `/cabinet/`.** Static export = full HTML+JS served to all visitors. Auth is client-side only. |

## P2 — harden post-launch

| # | PA | File:line | Finding |
|---|----|-----------|---------|
| **13** | PA-3 | `api_server.py:1061,1081,1190` | **`_personal_feed_page` = 3 sequential DB round-trips** (tags → feed → replies). Could CTE or parallelize. |
| **14** | PA-3 | `api_server.py:166,603-617` | **500-row wide scan** (`_ME_FEED_SCAN_LIMIT`) for match sort, ranked in Python. Acceptable at current scale. |
| **15** | PA-3 | `api_server.py:712` | **In-process cache** not shared across uvicorn workers. 4× DB load on cache-miss windows. |
| **16** | PA-2 | `ai_analyze.py:2564` | **Exact-match dedup is cosmetic** — inserts space after "Здравствуйте!" not structural dedup. |
| **17** | PA-2 | `ai_analyze.py:2528` | **Narrow temperature range** 0.38–0.50 reduces output diversity. |
| **18** | PA-5 | `api_server.py:1370` | **Missing auth header defaults to owner UUID.** No header → silent owner escalation. Intended for dogfood but implicit. |
| **19** | PA-5 | `api_server.py:1434-1450` | **No HTTP rate limiting middleware** on `/v1/me/*`. Only draft endpoints have per-user hourly caps. |
| **20** | PA-5 | `api_server.py:3388` | **Ops gate leaks password length** via early `len()` return before `compare_digest`. |
| **21** | PA-5 | `api_server.py:3065` | **Webhook uses header check, not HMAC-SHA256 body signature** per YooKassa spec. |
| **22** | Next | `lib/user-meta.ts:54` | **`can_ops_admin` cached in `localStorage`** — readable by XSS. |
| **23** | Next | `public/robots.txt:6` | **`Disallow: /ops/` discloses admin path exists.** |

---

## What's OK

| Area | Finding |
|------|---------|
| Feed inbox (IDOR) | `/v1/me/replies` correctly filters by `user_id` — no cross-user leak |
| YooKassa replay | Atomic `UPDATE WHERE status='pending'` — idempotent against duplicate webhooks |
| Metrika PII | Zero PII leakage — only boolean goal events, gated to `rawlead.ru` |
| Sitemap | Only public routes — no `/cabinet/`, no `/ops/` |
| Connection pool exists | `ConnectionPool(min_size=4, max_size=40)` at startup — but 28 handlers bypass it |
| Feed caching | `_feed_today_count_cached` works correctly with 180s TTL |
| OPS gate core | `secrets.compare_digest` used for main comparisons (but length leak + webhook exception) |
| JWT rotation | `X-Rawlead-Access-Token` header rotation works correctly |

---

## Recommended order (Coder §)

```
1. PA-3: bare psycopg.connect → _db_conn() (28 handlers) ← mechanical P0, biggest impact
2. PA-5: YooKassa compare_digest ← one-line P1
3. PA-2: cross-user dedup or wider temperature/variant space ← design decision
4. PA-4: K-hide schema + counter + feed filter ← feature, needs Product K value
5. Next: localStorage → cookie, middleware.ts ← P1 security
6. PA-3: feed COUNT(*) → materialized counter or async ← P1 performance
```

**Deploy:** no code in this report. All findings → `@coder` via `CODER_PROMPT` § PA-*.
