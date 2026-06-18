# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-07T14:17:43.194204+00:00
**Overall:** FAIL

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ✅ |
| load_p95_feed | ❌ |
| draft_burst | ❌ |
| tz_leads | ✅ |
| ux_journey | ⏭ |
| parsers | ✅ |
| skills_mismatch | ✅ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **2396.4 ms**
- Error rate max: **0.0**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

| Phase | p50 ms | p95 ms |
|-------|--------|--------|
| feed | 3600.4 | 4588.7 |
| expand | 1405.1 | 1450.4 |
| tools | 0 | 27136.8 |
| draft_wait | 77533.7 | 84706.1 |
| total | 97136.4 | 104896.0 |

_shared_l2/l3 not split at API — see draft_wait_ms_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (1459.3ms) | 5 | — |
| free | 200 (2733.6ms) | 5 | free |
| trial | 200 (2819.4ms) | 5 | trial |
| premium | 200 (3023.6ms) | 5 | agent |

## TZ attachments

- OK extracted: **3 / 3** (need ≥2/3)
- lead `18205`: 11339 chars · extracted · 1536.0 ms
- lead `18103`: 11171 chars · extracted · 1739.4 ms
- lead `18102`: 11113 chars · extracted · 1580.1 ms

## UX Journey J1–J11

- critical: **—** · pass: **—/—**

## Parser snapshot

- **fl**: kind=— status=ok
- **kwork**: kind=— status=ok
- **youdo**: kind=— status=ok
- **freelance_ru**: kind=— status=ok
- **freelancejob**: kind=— status=ok
- **pchyol**: kind=— status=ok
- cascade hits: **0** · runaway cycles: **0**

## S1-b skills_mismatch

- PASS: **True**
