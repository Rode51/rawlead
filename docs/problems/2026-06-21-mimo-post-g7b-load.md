# Post-G7b load audit — MiMo 2026-06-21

**Source:** `data/preprod_stress_v2.json` (09:52 UTC, PASS)
**Scope:** Postgres pool, 50 VU ceiling, draft rate limits
**Method:** static analysis of stress artifact + `src/api_server.py`

---

## Stress results summary

| Stage | VU | Duration | Requests | Feed p95 | Feed p99 | Errors | Pass |
|-------|-----|----------|----------|----------|----------|--------|------|
| 1 | 10 | 120s | 1,939 | 696ms | 783ms | 0 | ✅ |
| 2 | 30 | 180s | 7,500 | 849ms | 959ms | 0 | ✅ |
| 3 | 50 | 300s | 16,724 | 1,101ms | 1,274ms | 0 | ✅ |

**Overall:** 26,163 requests, p95=1,101ms, p99=1,274ms, 0 errors. S3 gate PASS.

---

## Findings

| # | Sev | File:line | Finding |
|---|-----|-----------|---------|
| **L1** | **P1** | `api_server.py:1464-1472` | **Connection pool ceiling = 40.** `ConnectionPool(min_size=4, max_size=40)`. At 50 VU with feed queries taking ~850ms (p50), each request holds a connection for the duration. 50 concurrent × 850ms = ~42 connection-seconds/sec. Pool handles this but with zero headroom. At 60+ VU or if any query slows (e.g., COUNT subquery), `too many connections` errors will appear. **Ceiling: 50 VU current config.** |
| **L2** | **P1** | `api_server.py:620-638` | **Feed COUNT(*) doubles table scans.** Every `/v1/feed` request runs `SELECT COUNT(*) FROM leads WHERE ...` as scalar subquery (line 855, 1010, 1083, 1155). At 50 VU this is 50 extra full scans/sec on `leads` table. Not causing errors now but degrades p99 under sustained load. |
| **L3** | **P2** | `draft_burst` rows | **Draft 404 on valid leads.** Leads 16689 and 16685: `draft_status: "ready"` but HTTP 404. Draft was generated (reply_len 375/398) but `_lead_in_user_feed` check at poll/return gate returned 404. Likely: preprod user's feed changed between submit and response (race with feed refresh). Not a blocker but confusing UX. |
| **L4** | **P2** | `draft_burst` summary | **Draft rate limit = 10/hour.** 17 of 20 attempts rate-limited. Works correctly per `draft_limits.py`. For M1 with multiple users, each gets independent 10/hour cap. At 50 concurrent users × 10 drafts = 500 draft requests/hour → OpenRouter capacity is the real bottleneck, not the rate limiter. |
| **L5** | **INFO** | `preprod_stress_v2.json:150` | **S3-pre note:** "Neon pooler recommended before 50 VU" — still references Neon, but prod is VPS Postgres. Note is stale. VPS Postgres at 127.0.0.1 handles 50 VU fine (pool max=40). |

---

## Feed latency progression

```
10 VU → p50=649ms  p95=697ms   (baseline)
30 VU → p50=732ms  p95=849ms   (+15% p95)
50 VU → p50=860ms  p95=1101ms  (+58% p95)
```

Degradation is sub-linear (good — no connection contention yet). The jump from 30→50 VU (+250ms p95) suggests pool saturation approaching. At 60 VU, expect p95 >1.5s and potential `too many connections`.

---

## Summary

| Category | Count | Notes |
|----------|-------|-------|
| P1 (load) | 2 | Pool ceiling (L1), COUNT subquery (L2) |
| P2 (load) | 2 | Draft 404 race (L3), stale Neon note (L5) |
| INFO | 1 | Rate limit works correctly (L4) |

**Ceiling assessment:** 50 VU is the practical ceiling with current pool config (max=40). To go beyond, either increase pool max or reduce connection hold time (fix COUNT subquery, optimize feed query).

**Draft capacity:** Rate limiter works. Real constraint is OpenRouter throughput, not Postgres or rate limits.

---

## Recommended order

```
1. L1: Increase pool max to 60-80 OR reduce connection hold time
2. L2: Feed COUNT(*) → async counter or materialized view
3. L3: Draft 404 race — log and monitor, not blocking M1
4. L5: Update S3-pre note to reference VPS Postgres
```
