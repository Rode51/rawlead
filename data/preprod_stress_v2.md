# PRE-PROD Stress V2 (O129)

**Generated:** 2026-06-21T09:52:46.338922+00:00
**Overall:** PASS

## Gates

| Gate | PASS |
|------|------|
| tier_matrix | ✅ |
| load_p95_feed | ✅ |
| l2_auto | ✅ |
| l2_send | ⏭ |
| draft_burst | ✅ |
| tz_leads | ✅ |
| ux_journey | ✅ |
| parsers | ✅ |
| ingest_24h | ✅ |
| skills_mismatch | ✅ |

## Load (S3-pre ramp)

- Peak VU: **50** · p95 feed: **1101.0 ms**
- Error rate max: **0.0**
- Neon pooler recommended before 50 VU; see PREPROD_STRESS_RUN § S3-pre

## Timings (draft burst)

| Phase | p50 ms | p95 ms |
|-------|--------|--------|
| feed | 947.5 | 1163.2 |
| expand | 581.1 | 738.5 |
| tools | 0 | 0 |
| draft_wait | 543.1 | 9535.0 |
| total | 2053.5 | 21870.3 |

_shared_l2/l3 not split at API — see draft_wait_ms_

## Tier matrix

| Tier | feed | items | plan |
|------|------|-------|------|
| anon | 200 (543.6ms) | 5 | — |
| free | 200 (729.8ms) | 5 | free |
| trial | 200 (651.9ms) | 5 | trial |
| premium | 200 (643.5ms) | 5 | agent |

## TZ attachments

- OK extracted: **4 / 5** (need ≥2/3)
- lead `16597`: 2971 chars · extracted · 506.8 ms
- lead `16588`: 1385 chars · no extract · 477.5 ms
- lead `16546`: 653 chars · extracted · 481.6 ms
- lead `16141`: 3070 chars · extracted · 530.5 ms
- lead `13963`: 5585 chars · extracted · 535.7 ms

## UX Journey J1–J11

- critical: **0** · pass: **10/10**

## Parser snapshot

_log source: vps:/opt/rawlead/data/radar_site.log_
- cascade hits: **0** · runaway cycles: **0**

## L2 quality (O168)

- auto pass: **100.0%** (draft **100.0%** · tools **100.0%** · n=30)
- send gate (skipped): **—%** (PASS)

## Ingest 24h

- max cycle gap: **None min** (limit **15**)

## S1-b skills_mismatch

- PASS: **True**
