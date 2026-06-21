# PRE-PROD Stress V2 verify (O168)

**Generated:** 2026-06-21T09:52:46.338922+00:00
**Overall:** PASS

## Gates

- **tier_matrix**: ✅
- **load_p95_feed**: ✅
- **l2_auto**: ✅
- **l2_send**: ⏭
- **draft_burst**: ✅
- **tz_leads**: ✅
- **ux_journey**: ✅
- **parsers**: ✅
- **ingest_24h**: ✅
- **skills_mismatch**: ✅

## Metrics

- feed p95 @50 VU: **1101.0 ms** (target <2000)
- L2 auto: **100.0%** · send: **—%** (skipped)
- ingest max gap: **None min**

## Next

- tier_matrix: `DATABASE_URL` + mint acc2 free / acc3 trial if env tokens stale
- p95: Neon pooler on VPS API (`DATABASE_URL` :6543) — см. O131
- L2 send: `preprod_stress_v2.py --l2-judge` or `preprod_ai_prod_audit.py --judge`
