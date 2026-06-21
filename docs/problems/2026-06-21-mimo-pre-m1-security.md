# Pre-M1 security audit — MiMo 2026-06-21

**Scope:** JWT/localStorage, /cabinet/ guard, nginx headers, api_server auth edges
**Baseline:** `2026-06-20-mimo-gsec-delta.md` (6 PA-5 items + 4 nginx items)
**Method:** static re-read of `src/api_server.py`, `rawlead-next/`, `deploy/nginx/*.conf`

---

## PA-5 items — delta since gsec-delta

| Baseline # | Finding | Status | Evidence |
|------------|---------|--------|----------|
| **P1 #7** | YooKassa webhook `compare_digest` | ✅ FIXED | `api_server.py:3110` — `secrets.compare_digest` |
| **P1 #8** | Draft feed-membership | ✅ FIXED | `api_server.py:2743` — `_lead_in_user_feed` → 404 |
| **P2 #18** | Owner UUID fallback | ✅ FIXED | `_resolve_user_id` — Bearer required · deploy 2026-06-21 |
| **P2 #19** | No rate limiting middleware | ❌ OPEN | No `slowapi`/throttle on `/v1/me/*` |
| **P2 #20** | Ops gate length leak | ❌ OPEN | `api_server.py:3422` — `len()` pre-check |
| **P2 #21** | Webhook header-only | ❌ OPEN | `api_server.py:3107-3110` — no HMAC body |

## Nginx items — delta since gsec-delta

| Baseline # | Finding | Status | Evidence |
|------------|---------|--------|----------|
| **S1 P1** | No CSP header | ❌ OPEN | `rawlead.ru.conf:13-15` — only X-Frame + nosniff |
| **S2 P1** | No HSTS header | ❌ OPEN | `rawlead.ru.conf` — absent |
| **S3 P2** | API proxy no security headers | ❌ OPEN | `api.rawlead.ru.conf:30-38` |
| **S4 P2** | /ops/ no nginx auth | ❌ OPEN | `rawlead.ru.conf:17-21` |

---

## New findings since gsec-delta

| # | Sev | File:line | Finding |
|---|-----|-----------|---------|
| **M1** | **P1** | `api_server.py:1425-1428` | **✅ FIXED** — VPS `.env.site` `RADAR_CORS_ORIGINS=https://rawlead.ru,https://www.rawlead.ru` · deploy 2026-06-21 |
| **M2** | **P1** | `api_server.py:1353` × 24 | **✅ FIXED** — `_resolve_user_id` Bearer-only, no owner header fallback · prod verify 401 |
| **M3** | **P2** | `rawlead-next/lib/api.ts:29` | **JWT in localStorage** (unchanged from baseline P1 #10). XSS → token theft. Still no `middleware.ts` or HttpOnly cookie. |
| **M4** | **P2** | `rawlead-next/app/cabinet/layout.tsx` | **No server-side auth guard** (unchanged from baseline P1 #12). Static export serves full HTML to all visitors. |

---

## Summary

| Category | gsec-delta | Fixed | Still open | New |
|----------|-----------|-------|------------|-----|
| P0 | 0 | 0 | 0 | 0 |
| P1 (security) | 2 (S1, S2) | 0 | 2 | 2 (M1, M2) |
| P2 (security) | 6 (#18-21 + S3, S4) | 0 | 6 | 2 (M3, M4 — unchanged) |

**Critical chain:** ~~M1 + M2~~ **✅ closed 2026-06-21** — `/v1/me/feed` без Bearer → **401** на prod.

---

## Resolution (2026-06-21 @coder)

- `src/api_server.py` — `_resolve_user_id` требует `Authorization: Bearer`
- VPS `.env.site` — `RADAR_CORS_ORIGINS=https://rawlead.ru,https://www.rawlead.ru`
- G0 pytest: **32 passed**, 1 skipped
- CSP/HSTS — post-M1 (S1+S2)

---

## Recommended order

```
1. M2: Remove owner UUID fallback from _resolve_user_id — require Bearer for all /v1/me/*
2. M1: Set RADAR_CORS_ORIGINS=https://rawlead.ru,https://www.rawlead.ru in .env.site
3. S1+S2: nginx CSP + HSTS headers
4. #21: HMAC-SHA256 body on webhook
5. #20: ops gate length leak
```

**Deploy:** M1+M2 require `.env.site` change + api restart. S1+S2 = nginx reload.
