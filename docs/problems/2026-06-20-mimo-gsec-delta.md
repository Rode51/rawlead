# G-SEC delta — MiMo 2026-06-20

**Scope:** PA-5 security items re-verify · nginx headers · new P0/P1 since pre-ads-readiness
**Baseline:** `2026-06-20-mimo-pre-ads-readiness.md` (23 findings)
**Method:** static re-read of `src/api_server.py`, `deploy/nginx/*.conf`

---

## PA-5 items — status vs baseline

| Baseline # | Finding | Status | Evidence |
|------------|---------|--------|----------|
| **P1 #7** | YooKassa webhook timing-unsafe `!=` | ✅ **FIXED** | `api_server.py:3110` — `secrets.compare_digest(got, secret)` |
| **P1 #8** | Draft endpoint missing feed-membership | ✅ **FIXED** | `api_server.py:2743` — `_lead_in_user_feed(cur, user_id, lead_id)` → 404 |
| **P2 #18** | Missing auth header → owner UUID | ❌ **STILL OPEN** | `api_server.py:1370` — `uid = (x_rawlead_user_id or "").strip() or _OWNER_USER_ID` |
| **P2 #19** | No HTTP rate limiting middleware | ❌ **STILL OPEN** | No `slowapi`/throttle import. Only draft endpoints have per-user hourly caps (`draft_limits.py`). |
| **P2 #20** | Ops gate leaks password length | ❌ **STILL OPEN** | `api_server.py:3422` — `if len(supplied) != len(plain): return False` before `compare_digest` |
| **P2 #21** | Webhook header-only, not HMAC body | ❌ **STILL OPEN** | `api_server.py:3107-3110` — checks `X-Yookassa-Webhook-Secret` header only. YooKassa spec recommends HMAC-SHA256 of request body. |

---

## New findings since baseline

| # | Sev | File:line | Finding |
|---|-----|-----------|---------|
| **S1** | **P1** | `rawlead.ru.conf:13-15` | **No CSP header.** `X-Frame-Options DENY` + `X-Content-Type-Options nosniff` present, but no `Content-Security-Policy`. XSS via injected `<script>` or inline event handlers unmitigated. For static Next.js export, a strict CSP (`default-src 'self'; script-src 'self'`) is feasible and blocks most XSS vectors. |
| **S2** | **P1** | `rawlead.ru.conf` (absent) | **No HSTS header.** `Strict-Transport-Security` missing. User can be downgraded to HTTP via MitM before 301 redirect takes effect. Add `Strict-Transport-Security: max-age=31536000; includeSubDomains`. |
| **S3** | **P2** | `api.rawlead.ru.conf:30-38` | **API proxy has zero security headers.** No `X-Frame-Options`, no `X-Content-Type-Options`, no `Referrer-Policy` on `/v1/*`. API responses (JSON) are less XSS-prone but still benefit from `nosniff` to prevent MIME sniffing. |
| **S4** | **P2** | `rawlead.ru.conf:17-21` | **`/ops/` proxy has no auth at nginx level.** Relies entirely on FastAPI `_ops_access_granted`. A misconfigured backend would expose admin panel. Consider nginx `auth_basic` or IP whitelist as defense-in-depth. |

---

## Summary: delta since baseline

| Category | Baseline count | Fixed | Still open | New |
|----------|---------------|-------|------------|-----|
| P0 | 3 | 0 | 3 (K-hide, pool bypasses, L3 dedup — all non-security) | 0 |
| P1 (security) | 2 (#7, #8) | 2 ✅ | 0 | 2 (S1, S2 — nginx headers) |
| P2 (security) | 4 (#18-21) | 0 | 4 | 2 (S3, S4 — nginx) |

**Net security delta:** 2 fixed (P1), 0 new P0, 2 new P1 (nginx headers), 6 P2 open.

---

## Recommended order (security-only)

```
1. S1+S2: nginx CSP + HSTS ← 2 headers, immediate XSS/MitM hardening
2. #18: owner UUID fallback — require explicit header or remove default
3. #21: HMAC-SHA256 body signature on webhook
4. #20: ops gate — remove len() pre-check or pad to fixed length
5. S3: API proxy security headers
6. S4: nginx auth_basic on /ops/
7. #19: rate limiting middleware (if ads drive >50 concurrent users)
```

**Deploy:** no code in this report. S1+S2 → nginx reload only.
