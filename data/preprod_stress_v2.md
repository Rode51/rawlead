# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-10T09:35:57.863272+00:00
**Overall:** PASS

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ✅ |
| load_p95_feed | ✅ |
| l2_auto | ⏭ |
| l2_send | ⏭ |
| draft_burst | ⏭ |
| tz_leads | ⏭ |
| ux_journey | ⏭ |
| parsers | ⏭ |
| ingest_24h | ⏭ |
| skills_mismatch | ⏭ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **1462.0 ms**
- Error rate max: **0.0004**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

_draft burst skipped or empty_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (817.1ms) | 5 | — |
| free | 200 (886.3ms) | 5 | free |
| trial | 200 (878.9ms) | 5 | trial |
| premium | 200 (1014.7ms) | 5 | agent |

## TZ attachments

- OK extracted: **0 / 0** (need ≥2/3)

## UX Journey J1–J11

- critical: **—** · pass: **—/—**

## Parser snapshot

_log source: missing_
- cascade hits: **0** · runaway cycles: **0**
