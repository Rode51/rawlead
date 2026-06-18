# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-08T13:33:49.546034+00:00
**Overall:** FAIL

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ❌ |
| load_p95_feed | ❌ |
| draft_burst | ⏭ |
| tz_leads | ✅ |
| ux_journey | ⏭ |
| parsers | ✅ |
| skills_mismatch | ⏭ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **2601.3 ms**
- Error rate max: **0.0**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

_draft burst skipped or empty_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (1420.6ms) | 5 | — |
| free | 200 (1675.8ms) | 5 | agent |
| trial | 200 (1453.4ms) | 5 | — |
| premium | 200 (1599.7ms) | 5 | agent |

## TZ attachments

- OK extracted: **3 / 3** (need ≥2/3)
- lead `19396`: 11081 chars · extracted · 1498.5 ms
- lead `19332`: 11044 chars · extracted · 1513.2 ms
- lead `19331`: 11282 chars · extracted · 1694.7 ms

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
