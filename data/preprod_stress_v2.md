# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-21T06:08:22.434695+00:00
**Overall:** FAIL

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ❌ |
| load_p95_feed | ✅ |
| l2_auto | ❌ |
| l2_send | ❌ |
| draft_burst | ✅ |
| tz_leads | ❌ |
| ux_journey | ⏭ |
| parsers | ✅ |
| ingest_24h | ✅ |
| skills_mismatch | ⏭ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **1139.2 ms**
- Error rate max: **0.0**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

| Phase | p50 ms | p95 ms |
|-------|--------|--------|
| feed | 937.8 | 971.2 |
| expand | 675.9 | 707.4 |
| tools | 0 | 0 |
| draft_wait | 974.1 | 14834.4 |
| total | 2621.6 | 34002.6 |

_shared_l2/l3 not split at API — see draft_wait_ms_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (530.9ms) | 5 | — |
| free | 200 (535.9ms) | 5 | — |
| trial | 200 (562.9ms) | 5 | — |
| premium | 200 (669.7ms) | 5 | agent |

## TZ attachments

- OK extracted: **0 / 0** (need ≥2/3)

## UX Journey J1–J11

- critical: **—** · pass: **—/—**

## Parser snapshot

_log source: C:\Users\hramo\uisness\data\radar_site.log_
- cascade hits: **0** · runaway cycles: **0**

## L2 quality (O168)

- auto pass: **—%** (draft **—%** · tools **—%** · n=0)
- send gate (—): **—%** (FAIL)

## Ingest 24h

- max cycle gap: **None min** (limit **15**)
