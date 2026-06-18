# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-09T15:14:53.398707+00:00
**Overall:** FAIL

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ✅ |
| load_p95_feed | ❌ |
| l2_auto | ❌ |
| l2_send | ❌ |
| draft_burst | ⏭ |
| tz_leads | ✅ |
| ux_journey | ❌ |
| parsers | ✅ |
| ingest_24h | ✅ |
| skills_mismatch | ❌ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **2676.1 ms**
- Error rate max: **0.001**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

_draft burst skipped or empty_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (1353.8ms) | 5 | — |
| free | 200 (1597.5ms) | 5 | free |
| trial | 200 (1805.7ms) | 5 | trial |
| premium | 200 (1692.3ms) | 5 | agent |

## TZ attachments

- OK extracted: **4 / 5** (need ≥2/3)
- lead `20229`: 1607 chars · no extract · 1443.5 ms
- lead `20219`: 9626 chars · extracted · 1505.3 ms
- lead `20217`: 8086 chars · extracted · 1477.1 ms
- lead `20175`: 7559 chars · extracted · 1503.9 ms
- lead `20174`: 3694 chars · extracted · 1519.8 ms

## UX Journey J1–J11

- critical: **0** · pass: **10/10**

## Parser snapshot

- **fl**: kind=ok status=fail
- **kwork**: kind=— status=ok
- **youdo**: kind=— status=ok
- **freelance_ru**: kind=— status=ok
- **freelancejob**: kind=— status=ok
- **pchyol**: kind=— status=ok
- cascade hits: **0** · runaway cycles: **0**

## L2 quality (O168)

- auto pass: **73.3%** (draft **96.7%** · tools **73.3%** · n=30)
- send gate (cached_audit): **64.1%** (FAIL)

## Ingest 24h

- max cycle gap: **None min** (limit **15**)

## S1-b skills_mismatch

- PASS: **False**
