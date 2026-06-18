# Parser stability audit — 2026-06-16

**Owner:** «каждый день падает · нужен аудит · prod-уровень»  
**Lead:** triage + § **O257** in `CODER_PROMPT.md`

---

## TL;DR (facts, not guesses)

| Fact | Evidence |
|------|----------|
| **fl.ru is UP** | VPS `curl https://www.fl.ru/projects/` → HTTP **200**, ~330 KB |
| **FL DC proxy alive** | `fetch:fl proxy=212.102.151.153:8000 alive=4/4` |
| **FL parsed=0** | `fl_listing:empty_html` · `html_snip snip=` (empty) — **our fetch returned nothing** |
| **Not «site down»** | Last OK `listing:fl parsed=30` at **13:03** same day |
| **httpx fallback OFF** | `FL_LISTING_SUBPROCESS=1` → `_fl_allow_httpx_fallback()` default **false** (O210) — docs say browser→httpx, code disables it |
| **restart loop** | `fl_hard_reset` sets `restart_source_fl=1` → every cycle closes contexts **before** fetch (`main.py`) |
| **YouDo separate** | Camoufox subprocess · `html_len=0 status=Error` · RU retry fails when node-proxy dead |

**Wrong diagnosis to avoid:** «freelance.ru лёг» · «only residential traffic ended».

---

## Architecture today (per source)

| Source | Listing fetch | Proxy primary | Recovery layers (count) |
|--------|---------------|---------------|------------------------|
| **FL** | Playwright subprocess (`fl_fetch_worker.py`) | 4 DC | O222 ban stop · O233 ban clear · O256 soft reset · hard_reset · restart_source · ops button |
| **Kwork** | Playwright Chromium | DC | lighter |
| **YouDo** | Camoufox subprocess | DC slot 1 (O191) · RU on retry | O254 teardown · O255 hard reset @1 · traffic_guard · cooldown |
| **TG** | Telethon | acc proxies | join queue |

**Problem:** 5+ recovery hooks on FL/YouDo **overlap** · failures often **silent** in `radar_site.log` (only journal).

---

## § A. Fetch path map (Coder audit 2026-06-16)

### FL (`fl_parser.py`)

| Step | Code path | Logged where |
|------|-----------|-------------|
| Entry | `fetch_listing_projects` → `_fetch_listing_pages` → `_fetch_listing_html` | — |
| Browser check | `listing_browser_enabled()` → `EXCHANGE_LISTING_BROWSER` default `"1"` | — |
| Subprocess check | `fl_listing_subprocess_enabled()` → `FL_LISTING_SUBPROCESS` default `"1"` | — |
| Fetch | `fetch_listing_html_browser_slots_wall_clock("fl", ...)` → `fetch_listing_html_browser_slots` → `_fetch_fl_listing_subprocess` → `subprocess.run(fl_fetch_worker.py)` | journal only on error |
| httpx gate | `_fl_allow_httpx_fallback()`: when subprocess enabled AND browser enabled → returns **False** unless `FL_HTTPX_FALLBACK=1` | — |
| httpx path | `_fetch_listing_html_requests` | journal |
| Fetch start | `log_pipeline_line: "fetch:fl proxy=..."` | `radar_site.log` ✅ |
| Fetch end | `log_pipeline_line: "listing:fl parsed=N fresh=M"` | `radar_site.log` ✅ |
| Browser error | `logger.warning("fl_listing: Playwright failed")` | **journal only** ❌ |
| Subprocess JSON fail | `_log_fl_subprocess_json_fail` → `log_pipeline_line` | `radar_site.log` ✅ |
| parsed=0 path | `_maybe_fl_parsed_zero_recovery` → `fl_listing:empty_html`, `fl_listing:html_snip` | `radar_site.log` ✅ |
| **parsed=0 without fetch_error** | When subprocess returns valid HTML without `b-page__lenta_item` → `_parse_items` returns `[]` → no exception, `parsed=0` | **silent** ❌ |
| **parsed=0 without fetch_error** | When subprocess returns `{"html": ""}` (empty string, no error) → `_validate_listing_browser_html` not called; `_parse_items("")` raises `FlListingError` | raises, not silent |

### Kwork (`kwork_parser.py`)

| Step | Code path | Logged where |
|------|-----------|-------------|
| Entry | `fetch_listing_projects` → `_fetch_listing_html` | — |
| Browser | `fetch_listing_html_browser_wall_clock("kwork", ...)` | journal only on error |
| httpx fallback | **Always fallback** when browser fails — no subprocess, no env gate | `radar_site.log` via KworkListingError |
| Fetch start | `log_pipeline_line: "fetch:kwork proxy=..."` | `radar_site.log` ✅ |
| Fetch end | `log_pipeline_line: "listing:kwork parsed=N fresh=M"` | `radar_site.log` ✅ |
| parsed=0 | No recovery — just returns `[]` silently | **silent** ❌ |

### YouDo (`youdo_parser.py`)

| Step | Code path | Logged where |
|------|-----------|-------------|
| Entry | `fetch_listing_projects` → `_fetch_listing_html` → `_fetch_listing_html_browser` | — |
| Browser | `fetch_listing_html_browser_slots_wall_clock("youdo", ...)` → camoufox subprocess | — |
| httpx | **No httpx fallback** — browser-only (`youdo_browser_only()=True`) | — |
| Fetch start | `log_pipeline_line: "fetch:youdo proxy=..."` + `youdo:trace stage=fetch_start` | `radar_site.log` ✅ |
| Browser error | `log_pipeline_line: "youdo_listing: browser_fail=..."` | `radar_site.log` ✅ |
| Fetch end | `youdo:trace stage=fetch_end parsed=N kind=ok|...` | `radar_site.log` ✅ |
| parsed=0 | `youdo:trace stage=fetch_end kind=...` BUT no explicit `reason=` field | partial ⚠️ |
| RU slot retry | `exchange_alive_proxy_urls("youdo")` → may include dead RU slots | no pre-check |

---

## § B. Recovery conflict map (Coder audit 2026-06-16)

### `fl_hard_reset` callers

| Caller | Trigger | Sets restart_source_fl | Problem |
|--------|---------|----------------------|---------|
| `_maybe_fl_soft_antibot_reset` (O256) | streak ≥ 5, bans=0 | **Yes** (via fl_hard_reset) | Causes pre-fetch context close next cycle — redundant when subprocess is stateless |
| `_maybe_fl_parsed_zero_recovery` (O233) | streak ≥ 3, bans cleared | **Yes** | Same — double teardown loop |
| `_fl_browser_antibot_fail` | Browser HtmlFetchError + ban | **Yes** if `FL_HARD_RESET_ON_BAN=1` | OK — ban path needs teardown |
| `fl_hard_reset` itself | Inline close_all + abort_worker | **Yes** | Inline teardown + deferred flag = double |

### The restart loop (O257 root cause)

```
cycle N:   parsed=0 → streak=3 → fl_hard_reset → restart_source_fl=1 → streak=0
cycle N+1: restart_source_fl=1 → close_all_browser_contexts (no-op for subprocess) → reset flag=0
           → subprocess returns empty again → parsed=0 → streak=1
...
cycle N+3: streak=3 → fl_hard_reset → restart_source_fl=1 → streak=0
           LOOP every 3 cycles
```

`close_all_browser_contexts()` is a no-op when `FL_LISTING_SUBPROCESS=1` (subprocess starts fresh regardless). The flag only causes unnecessary context teardown and gives illusion of recovery.

### `youdo_hard_reset` callers

| Caller | Trigger |
|--------|---------|
| `_on_youdo_fetch_fail` (O255) | auto_fail_streak ≥ 1 (rate-limited or hourly-capped) |
| `youdo_hard_reset` explicit | ops button, restart_source_youdo flag in main.py |
| `_fetch_source` (main.py) | `restart_source_youdo=1` flag |

YouDo recovery is better — one path: `_on_youdo_fetch_fail` with rate-limit/hourly-cap guard. No overlapping callers like FL.

### `_abort_playwright_worker` callers (all merge)

Called from: `fl_hard_reset`, `youdo_browser_teardown`, wall-clock timeout in `fetch_listing_html_browser_slots_wall_clock`. These all cancel the shared Playwright thread executor — calling multiple times is safe (idempotent) but wastes cycles on teardown.

---

## § C. Process hygiene script

See: `scripts/audit_parser_processes_vps.py` (Coder adds this per O257)

Expected processes on prod:
- **`rawlead-radar`** (main.py) — 1 instance
- **`fl_fetch_worker.py`** — 0 at rest (spawned and dies each cycle) · orphan if radar killed mid-fetch
- **`youdo_fetch_worker.py`** — 0 at rest (same)
- **`camoufox`** / **`firefox`** — 0 at rest · orphan if teardown failed
- **`chromium`** / **`chrome-headless-shell`** — 0 at rest (Playwright headless) · orphan if wall-clock timeout

Post hard_reset / teardown: `youdo_browser_teardown()` calls `cleanup_stale_youdo_browser_processes()` (kills camoufox/youdo_fetch_worker orphans by user). `cleanup_stale_browser_processes()` for FL (kills chromium orphans). These run at cycle end.

Risk: if `cleanup_stale_*` is not called (crash before `finally:`), orphans accumulate and eat RAM.

---

## § D. Log gaps — reason codes (Coder audit 2026-06-16)

### Current gaps

| Source | Scenario | Current log | Missing |
|--------|----------|------------|---------|
| FL | Browser subprocess timeout | journal `logger.warning` only | `fetch:fl outcome=fail reason=browser_timeout` |
| FL | Browser HtmlFetchError | journal only | `fetch:fl outcome=fail reason=browser_error` |
| FL | Subprocess returns None (no exception) | journal `"no alive proxy slots"` | `fetch:fl outcome=fail reason=no_slots` |
| FL | parsed=0 (HTML without listing cards, page 1) | raises `FlListingError` — NOT in pipeline | `fetch:fl outcome=fail reason=no_cards` |
| Kwork | Browser error | journal only | `fetch:kwork outcome=fail reason=browser_error` |
| YouDo | parsed=0 (browser_empty/antibot) | `youdo:trace fetch_end kind=...` — no `reason=` field | `fetch:youdo outcome=fail reason=browser_empty` |
| YouDo | RU tier dead | no log | `fetch:youdo reason=ru_pool_dead` |

### Standard format (O257 implement)

```
fetch:{src} outcome=ok|fail reason={code} tier=dc|res parsed=N
```

Reason codes:
- `ok` — parsed > 0
- `browser_timeout` — HtmlFetchError with "timeout"
- `browser_error` — HtmlFetchError other
- `browser_empty` — html returned but no listing cards
- `httpx_ok` — httpx fallback succeeded
- `httpx_fail` — httpx fallback also failed
- `subprocess_json` — subprocess bad JSON
- `no_slots` — no alive proxy slots
- `antibot_html` — antibot/captcha page
- `pool_exhausted` — all slots tried and failed
- `ru_pool_dead` — YouDo RU tier dead

---

## § E. Probe script

See: `scripts/probe_parsers_health_vps.py` (Coder adds this per O257)

- Reads last 3 cycles from `data/radar_site.log`
- Checks for `fetch:{src} outcome=ok` in recent N lines
- Exits 0 if all sources have recent ok; exits 1 if any source has `outcome=fail` or no recent line
- JSON output for Lead

---

## § F. Weak spots & improvements (Coder 2026-06-16)

Ranked P0 (ship now) / P1 (O258 follow-up) / P2 (strategic).

| # | Priority | What breaks | Why fragile | Fix |
|---|----------|------------|-------------|-----|
| 1 | **P0** | FL subprocess empty — no httpx fallback | `_fl_allow_httpx_fallback()` returns False when `FL_LISTING_SUBPROCESS=1` unless explicit `FL_HTTPX_FALLBACK=1`. VPS curl returns 200 ~330KB — httpx would work. | **Implement now**: auto httpx fallback when browser/subprocess returns None/empty OR raises HtmlFetchError. `FL_HTTPX_AUTO_FALLBACK=1` default. |
| 2 | **P0** | restart_source loop after O256 soft reset | `fl_hard_reset` always sets `restart_source_fl=1`, causing pre-fetch context close every ~3 cycles. With subprocess, `close_all_browser_contexts()` is a no-op — loop gives illusion of recovery. | **Implement now**: pass `set_restart_source=False` from `_maybe_fl_soft_antibot_reset` and `_maybe_fl_parsed_zero_recovery` when subprocess enabled. Inline teardown already happened in fl_hard_reset. |
| 3 | **P0** | Silent browser/subprocess failures | Browser errors go to journal only — owner sees nothing in `radar_site.log` at night. | **Implement now**: log `fetch:fl outcome=fail reason=... stderr_tail=...` to pipeline on every browser/subprocess failure. |
| 4 | **P0** | YouDo hammering dead RU tier | When `youdo_ru_alive_urls()` empty (node-proxy down), slot retry still tries RU proxies — they fail immediately, wasting time and burning proxy quota. | **Implement now**: before slot retry, check `youdo_ru_alive_urls()`; if empty → log `fetch:youdo reason=ru_pool_dead` · skip retry. |
| 5 | **P1** | YouDo fetch_end has no `reason=` when parsed=0 | `log_youdo_fetch_end` logs `kind=` but not `reason=`. Owner can't distinguish browser_empty vs antibot vs cooldown in log scan. | **Implement now**: add `reason=` to `youdo:trace fetch_end`. |
| 6 | **P1** | FL listing may not need browser at all (SSR) | VPS curl `https://www.fl.ru/projects/?kind=1` → 200 ~330KB HTML with listing cards. Browser adds 30-120s overhead + antibot risk. | **O258**: validate `httpx_ok` in N=3 consecutive cycles on VPS. If stable, promote httpx to primary with browser as fallback (reverse current order). Saves proxy quota + latency. |
| 7 | **P1** | Overlapping recovery layers, no state machine | O222 ban + O233 ban clear + O256 soft reset + O257 httpx auto fallback — 4 recovery paths with no coordination. Can fire simultaneously. | **O258**: consolidate into `fl_recovery_state_machine` with states: `ok → soft_antibot → hard_reset → cooldown`. Single source of truth. |
| 8 | **P1** | Cycle watchdog vs hung subprocess | `_CycleWatchdog` fires after `RADAR_CYCLE_WALL_SEC` (600s). But subprocess timeout is 120+30=150s. Watchdog fires → `close_all_browser_contexts` (no-op for subprocess). Subprocess continues running as orphan. | **O258**: watchdog should also kill fl_fetch_worker / youdo_fetch_worker subprocess PIDs via `cleanup_stale_*`. |
| 9 | **P2** | ARCHITECTURE.md / RUN.md docs drift | Docs say browser→httpx fallback for FL. Code disables it when subprocess enabled (O210). No docs on subprocess mode or camoufox vs Playwright split. | **O258**: update ARCHITECTURE.md §fetch-path with actual subprocess/camoufox/httpx truth table. |
| 10 | **P2** | Orphan processes after teardown | `cleanup_stale_*` runs at cycle end in `finally:`. If radar killed mid-cycle (SIGKILL from systemd restart), orphans accumulate. | **O258**: add startup cleanup + probe script cron to kill orphans daily. |

---

## Audit checklist (Coder § O257)

### A. Fetch path map
- [x] FL: subprocess path, httpx gate OFF, browser error journal-only, parsed=0 silent paths documented above

### B. Recovery conflict map
- [x] fl_hard_reset callers + restart loop root cause documented above

### C. Process hygiene (VPS)
- [x] script: `scripts/audit_parser_processes_vps.py`

### D. Log gaps
- [x] reason codes + format documented above; implemented in fl_parser.py / kwork_parser.py / youdo_parser.py

### F. Weak spots
- [x] 10 items ranked P0/P1/P2, P0 implemented in O257

---

## § O258 follow-up (owner 2026-06-16)

| # | What | Owner intent |
|---|------|--------------|
| 1 | `playwright install chromium` on VPS (rawlead) | Browser-path FL/Kwork works · not only httpx |
| 2 | Cron `probe_parsers_health` every 15 min | Catch failures before morning |
| 3 | Alert → **@FLPARSINGBOT** | Same channel as proxy alerts |
| 4 | Residential unchanged | DC wait TTL · res = extreme only |

**O257 prod fact:** FL recovered via httpx; root browser error = missing chromium binary.

---

## Verify done (Lead)

- [ ] Audit section A–D filled in this file (Coder) ✅
- [ ] FL `listing:fl parsed>=25` sustained 3 cycles on VPS
- [ ] Every `parsed=0` has `fetch:fl outcome=fail reason=...` in log
- [ ] `probe_parsers_health_vps.py` exits 0 on prod
- [ ] pytest O257 green · deploy script exists

---

_Lead Architect · 2026-06-16_
