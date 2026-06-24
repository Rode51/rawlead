# YouDo Parser Audit — P0 M1 (read-only)

**Scope:** architecture, inconsistencies, human-like gaps, file split, P0/P1/P2 fixes, log gaps
**Files audited:** `youdo_parser.py` (1370 LOC), `exchange_browser_fetch.py` (4249 LOC), `lead_pipeline.py` (1262 LOC), `youdo_sticky_worker.py` (416 LOC), `youdo_fetch_worker.py`, 6 test files (~112 tests)
**Date:** 2026-06-22

---

## 1. Architecture Map

### Pipeline Flow

```
main.py radar cycle
  → fetch_listing_projects() [youdo_parser.py:997]
    → _fetch_listing_html() → browser slots → sticky/ephemeral
    → parse_listing_html() → list[ListingProject]
    → click_through_details() [exchange_browser_fetch.py:2077] (if new>0)
    → cache results → lead_pipeline
  → process_new_listing() [lead_pipeline.py:865]
    → ingest_with_l1()
      → _resolve_ingest_body() [line 72] → click cache → fetch_project_detail → detail_ok
      → _youdo_detail_short_skips_l1() [line 153] → O281 gate
      → if skip: delist from Neon (reason=youdo_detail_short)
      → else: L1/L2/L3 → feed
```

### Module Responsibilities

| Module | Role | LOC |
|--------|------|-----|
| `youdo_parser.py` | Listing parse, detail parse, cooldown/guard, trace logging, click cache | 1,370 |
| `exchange_browser_fetch.py` | Browser infra (shared), YouDo sticky/Camoufox/click-through (~73% YouDo) | 4,249 |
| `lead_pipeline.py` | Ingest orchestration, O281 gate, L1/L2 dispatch | 1,262 |
| `youdo_sticky_worker.py` | Sticky Camoufox subprocess (goto/reload/click_through) | 416 |
| `youdo_fetch_worker.py` | Ephemeral Camoufox subprocess (single fetch) | ~200 |

### Key Functions

| Function | File:line | LOC | Role |
|----------|-----------|-----|------|
| `fetch_listing_projects` | `youdo_parser.py:997` | 156 | Main entry: cooldown → fetch → parse → click-through |
| `_resolve_ingest_body` | `lead_pipeline.py:72` | 55 | Body resolution: cache → fetch → fallback |
| `_youdo_detail_short_skips_l1` | `lead_pipeline.py:153` | 19 | O281 gate: detail_ok + body length |
| `_fetch_youdo_sticky_listing` | `exchange_browser_fetch.py:2407` | 167 | Sticky session: spawn → send → validate |
| `youdo_click_through_details` | `exchange_browser_fetch.py:2077` | 64 | IPC: send click_through_details to worker |
| `_run_click_through_details` | `youdo_sticky_worker.py:147` | ~200 | Worker: click cards → parse detail → fallback |
| `_fetch_youdo_listing_dc_first` | `exchange_browser_fetch.py:3785` | 222 | DC tier → RU fallback → ban cap |

---

## 2. Inconsistencies

### P0: Dead dedup — click-through always runs on all leads

**Location:** `youdo_parser.py:1080`

```python
seen_ids = st.list_seen_ids() if hasattr(st, "list_seen_ids") else set()
```

`ProjectStorage` does NOT have `list_seen_ids()`. The `hasattr` guard silently falls back to `set()`, so `seen_ids` is always empty. **Every lead is treated as "new" for click-through.** The dedup is dead code.

**Impact:** With `YOUDO_CLICK_DETAIL_MAX=10`, all 10 slots are wasted on already-seen leads instead of truly new ones.

### P1: MIN_CHARS=0 semantics — documented vs implemented

**Location:** `lead_pipeline.py:168`

| What docs say | What code does |
|---------------|----------------|
| `YOUDO_DETAIL_MIN_CHARS=0` = "gate disabled" | `length_floor = 300 if min_chars <= 0 else min_chars` — hard floor stays at 300 |
| PROD_FACTS: "gate disabled" | Gate still enforces `detail_ok=True` AND `body >= 300` |

The env var `0` is **functionally identical** to the default `300`. The "gate disabled" documentation is misleading.

### P1: Hot path vs backlog gate inconsistency

**Hot path** (`lead_pipeline.py:168`): Always enforces `length_floor >= 300` regardless of MIN_CHARS.

**Backlog** (`lead_pipeline.py:948-956`):
```python
if row.source == SOURCE_YOUDO and _youdo_detail_min_chars() > 0 and len(snippet) < min_chars:
    continue  # skip
```

When `MIN_CHARS=0`: `_youdo_detail_min_chars() > 0` → `False` → skip check bypassed → short leads processed through L1.

**Result:** Hot path delists short leads; backlog reprocesses them. Two-tier behavior.

### P1: Misleading trace field name

**Location:** `youdo_parser.py:1125`

`new_ids=click_detail_count` — counts click-through successes, not genuinely new lead IDs. The field name suggests dedup count.

### P2: Duplicate function definitions

`_youdo_detail_fetch_enabled()` defined identically in both `youdo_parser.py:428` and `lead_pipeline.py:64`.

---

## 3. Human-Like Gaps

### Sticky Session Timing

| Gap | Detail | Risk |
|-----|--------|------|
| **No inter-request jitter in click-through** | `_run_click_through_details` clicks cards in rapid succession (only 8s wait_for_selector per card). Real users pause 2-5s between clicks. | MEDIUM — ServicePipe may detect rapid click pattern |
| **No mouse movement before click** | Direct `card.click()` without `hover()` or random mouse path. Camoufox may detect synthetic click patterns. | LOW — Camoufox handles this at browser level |
| **Fixed 2s wait after goto fallback** | `await page.wait_for_timeout(2000)` — hardcoded, not adaptive to page load state. | LOW |

### Headers & Fingerprint

| Gap | Detail | Risk |
|-----|--------|------|
| **No Accept-Language header in sticky worker** | Worker relies on Camoufox defaults. Listing page expects `ru-RU`. | LOW — Camoufox locale set to `ru-RU` at context creation |
| **No viewport randomization** | Fixed `1366×768` across all sessions. Real users have varied viewports. | LOW — Camoufox handles fingerprint diversity |

### Profile & Session

| Gap | Detail | Risk |
|-----|--------|------|
| **Profile wipe on ServicePipe** | `_wipe_youdo_profile_on_poison` deletes persistent profile on SP detection. May lose valid session cookies. | MEDIUM — Golden O268 backup exists as fallback |
| **No cookie refresh mechanism** | Sticky session uses initial cookies. If session expires mid-cycle, next goto gets login page instead of listing. | MEDIUM — Handled by `youdo_hard_reset_on_fail` |

### RU/DC Carousel

| Gap | Detail | Risk |
|-----|--------|------|
| **RU burst cap = 2/day** | `_youdo_ru_burst_max_per_day` defaults to 2. If both consumed early, remaining cycles use only DC (which may be banned). | LOW — Design decision, not a bug |
| **No warm-up after DC→RU switch** | RU tier gets no warm-home. First RU goto may trigger SP challenge. | MEDIUM — `_youdo_servicepipe_early_ru_enabled` partially handles this |

---

## 4. File Size / Split Plan

### Current State

| File | LOC | YouDo % | Risk |
|------|-----|---------|------|
| `exchange_browser_fetch.py` | **4,249** | ~73% | 🔴 GOD-FILE |
| `youdo_parser.py` | 1,370 | 100% | 🟡 Medium |
| `lead_pipeline.py` | 1,262 | ~15% YouDo | 🟡 Shared |
| `youdo_sticky_worker.py` | 416 | 100% | ✅ Clean |

### Proposed Split: `src/youdo/` Package

| New Module | LOC (est.) | Contents from `exchange_browser_fetch.py` |
|------------|------------|------------------------------------------|
| `src/youdo/config.py` | ~350 | All 40+ env-var readers, feature flags, tier config, jitter, timeout |
| `src/youdo/list_view.py` | ~750 | 30 list-view click functions (sync+async), dataclasses, selectors |
| `src/youdo/sticky.py` | ~700 | Sticky session lifecycle: spawn, IPC, teardown, click-through dispatch |
| `src/youdo/browser.py` | ~800 | Camoufox integration, persistent context, ephemeral fetch, detail snapshot |
| `src/youdo/orchestrator.py` | ~400 | DC-first tier, slot retry, ban cap, `_fetch_youdo_listing_dc_first` |
| `src/youdo/trace.py` | ~100 | `_log_youdo_browser_trace`, `_log_youdo_list_view_trace` |
| **Remaining** `exchange_browser_fetch.py` | **~600** | Shared PW infra + FL-only code |

### Split Order (priority)

1. **`exchange_browser_fetch.py`** → `youdo/config.py` + `youdo/list_view.py` + `youdo/sticky.py` (removes ~1,800 LOC)
2. **`youdo_parser.py`** → extract `_parse_youdo_detail_html`, `_youdo_gone_from_html`, `check_project_page_gone` → `youdo/detail_parse.py` (~200 LOC)
3. Move `youdo_sticky_worker.py` → `scripts/youdo/sticky_worker.py` (or keep in `scripts/`)

**Do NOT split during M1 ads.** Split is post-ads backlog (CODE_STRUCTURE.md line 64: "Split god-files — backlog после ads").

---

## 5. P0/P1/P2 Fixes

### P0 (blockers)

| # | Finding | File:line | Fix | Risk | Test |
|---|---------|-----------|-----|------|------|
| **P0-1** | `list_seen_ids()` doesn't exist — click-through dedup dead | `youdo_parser.py:1080` | Use `storage.list_project_ids(["youdo"])` or `storage.has_seen()` in loop | LOW | Unit: mock storage with known IDs, verify only new leads passed to click-through |
| **P0-2** | Click-through IPC untested | `test_o269` | Add test with mocked stdin/stdout pipe: send `click_through_details` command → verify worker processes card click → returns body | LOW | Unit: mock `subprocess.Popen` stdin/stdout, verify JSON round-trip |

### P1 (fix before ads scale)

| # | Finding | File:line | Fix | Risk | Test |
|---|---------|-----------|-----|------|------|
| **P1-1** | MIN_CHARS=0 docs say "gate disabled" but code enforces 300 | `lead_pipeline.py:168` | Either: (a) fix docs to say "0 = default 300 floor", or (b) fix code to actually bypass floor when 0. **Owner decision needed.** | MEDIUM | Update `test_o281` to match chosen behavior |
| **P1-2** | Hot path vs backlog gate inconsistency | `lead_pipeline.py:948-956` | Align backlog check with hot path: use same `_youdo_detail_short_skips_l1` in drain loop | MEDIUM | Add test: MIN_CHARS=0 + short body → both hot path and backlog should behave identically |
| **P1-3** | No click-through jitter | `youdo_sticky_worker.py:_run_click_through_details` | Add `await page.wait_for_timeout(random.randint(1500, 4000))` between clicks | LOW | Unit: mock page, verify delay between clicks |
| **P1-4** | Trace field `new_ids` misleading | `youdo_parser.py:1125` | Rename to `click_ok` or `detail_enriched` | LOW | Grep: no code reads this field by name |

### P2 (harden post-launch)

| # | Finding | File:line | Fix | Risk | Test |
|---|---------|-----------|-----|------|------|
| **P2-1** | `_click_detail_cache_clear()` never called | `youdo_parser.py:64` | Either expose in ops API or remove dead code | LOW | None |
| **P2-2** | Duplicate `_youdo_detail_fetch_enabled` | `youdo_parser.py:428` + `lead_pipeline.py:64` | Keep in one module, import in other | LOW | None |
| **P2-3** | `_youdo_sticky_teardown_unlocked` has no lock assertion | `exchange_browser_fetch.py:2221` | Add `assert _YOUDO_STICKY_LOCK.locked()` at entry | LOW | None |
| **P2-4** | `_WARMED_YOUDO_KEYS` set has no lock | `exchange_browser_fetch.py:1613` | Use `_YOUDO_STICKY_LOCK` or a dedicated lock | LOW | None |

---

## 6. Log Gaps

| Gap | Where to add | What to log |
|-----|-------------|-------------|
| **DOM change detection** | `youdo_sticky_worker.py:_run_click_through_details` | When all selectors miss: save debug HTML + log `outcome=selector_miss debug_path=...` with current page HTML structure (tag names, classes) |
| **ServicePipe in click-through** | `youdo_sticky_worker.py:_run_click_through_details` | When `antibot` detected during click: log `html_len=`, SP fingerprint, whether fallback goto also hit SP |
| **Cache hit/miss ratio** | `lead_pipeline.py:_resolve_ingest_body` | `youdo:trace stage=click_cache hit=1 ext=... body_len=...` vs `hit=0` |
| **Backlog inconsistency** | `lead_pipeline.py:drain_l1_backlog` | When MIN_CHARS=0 bypasses backlog check: log `drain:youdo min_chars=0 short_body_bypass ext=... body_len=...` |
| **Sticky worker health** | `youdo_sticky_worker.py:_session_loop` | Periodic heartbeat: every N commands, log `stage=sticky_heartbeat pid=... uptime=... cmds_processed=...` |
| **Click-through timing** | `youdo_parser.py:fetch_listing_projects` | After click-through block: `youdo:trace stage=click_summary new_ids=... click_ok=... cache_size=... total_ms=...` |
| **Profile state** | `exchange_browser_fetch.py:_youdo_sticky_teardown_unlocked` | On teardown: `stage=sticky_teardown reason=... profile_dir=... age_sec=... last_valid_age=...` |

### Debug HTML dump thresholds

| Trigger | Action |
|---------|--------|
| All selectors miss in click-through | Dump `page.content()` to `data/debug_listings/youdo_click_miss_{ext_id}.html` |
| Click succeeds but body < 100 chars | Dump detail page HTML to `data/debug_listings/youdo_click_short_{ext_id}.html` |
| Fallback goto also fails | Dump both listing and detail HTML |

---

## Summary

| Category | P0 | P1 | P2 |
|----------|----|----|-----|
| Code bugs | 1 (dead dedup) | 2 (gate inconsistency, trace name) | 2 (dead code, duplicate) |
| Testing gaps | 1 (click-through IPC) | 1 (jitter) | 0 |
| Documentation | 0 | 1 (MIN_CHARS=0 semantics) | 0 |
| Logging | 0 | 0 | 7 gaps |
| Architecture | 0 | 0 | 1 (file split — post-ads) |

**Total:** 2 P0 · 4 P1 · 10 P2

**Deploy:** no code in this report. All findings → `@coder` via `CODER_PROMPT` § YOUDO-*.
