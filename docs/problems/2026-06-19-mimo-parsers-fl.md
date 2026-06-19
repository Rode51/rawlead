# Parser-only deep dive — MiMo Auto (2026-06-19)

**Статус:** **✅ triaged Lead 2026-06-19** · P0 → `CODER_PROMPT` § **O283-MIMO** **FL-LOOP**  
**Дата:** 2026-06-19  
**Контекст:** prod logs 2026-06-19 — FL OK, restart_source events at 17:56/19:02

---

## 1. Root cause: restart_source fires while FL still succeeds

**Hypothesis confirmed: the restart_source loop is a no-op in subprocess mode, but still fires because two `fl_hard_reset` callers bypass the O257 fix.**

### The loop (prod log evidence)

```
17:56  fetch:fl restart_source → browser contexts closed
17:56  fetch:fl outcome=ok parsed=30
19:02  fetch:fl restart_source → browser contexts closed
19:02  fetch:fl outcome=ok parsed=30
```

### Mechanism

1. `fl_hard_reset()` is called with default `set_restart_source=True`
2. This writes `restart_source_fl=1` to SQLite storage (`exchange_browser_fetch.py:629`)
3. Next cycle, `_fetch_source()` in `main.py:357-370` reads the flag
4. For FL (not YouDo), it calls `_safe_close_browser_contexts()` → `close_all_browser_contexts()`
5. **With `FL_LISTING_SUBPROCESS=1`**, persistent contexts are empty — the close is a **no-op**
6. Flag is cleared to `"0"` (`main.py:365`)
7. FL fetch proceeds normally via subprocess — **succeeds**
8. But the underlying trigger (antibot/proxy ban) fires `fl_hard_reset` again → loop

### Is it harmful?

**Not directly** — FL still parses 30 cards every cycle. But:
- Unnecessary `close_all_browser_contexts()` call every ~3 cycles adds latency
- Operator sees "restart_source → browser contexts closed" in logs — creates noise/confusion
- If the underlying antibot trigger persists, the loop runs indefinitely
- The real fix (teardown inline) already happened — the deferred flag is redundant

### The O257 fix only patched 2 of 4 callers

**Patched (set_restart_source=False when subprocess):**
- `fl_parser.py:199` — `_maybe_fl_soft_antibot_reset()`
- `fl_parser.py:257` — `_maybe_fl_parsed_zero_recovery()`

**NOT patched (still default set_restart_source=True):**
- **`exchange_browser_fetch.py:717`** — `_fl_browser_antibot_fail()` calls `fl_hard_reset(reason=str(exc), storage=storage)` — no `set_restart_source` param
- **`exchange_proxy.py:1287`** — proxy failover calls `fl_hard_reset(reason=reason, storage=_storage())` — no `set_restart_source` param

**These two callers are the root cause of the ongoing restart_source events in prod.**

---

## 2. Why 194.226.236.204 fails but pool shows alive=4/4

### Pool mechanics

`exchange_proxy.py` tracks proxy health via:
- `alive_urls()` — URLs not currently banned
- `banned` list — URLs with active ban (cooldown-based)
- `alive=4/4` means **all 4 DC proxy slots are unbanned**

### The disconnect

194.226.236.204 is a **DC-tier proxy** in the pool. The pool shows `alive=4/4` because:
- The ban on 194.226.236.204 **expired** (cooldown-based, `YOUDO_COOLDOWN_MIN=30`)
- After cooldown, the proxy is marked alive again
- But the **underlying issue** (ServicePipe challenge, IP reputation, or network route) persists

### Evidence from June 17

```
ERR_PROXY_CONNECTION_FAILED on 194.226.236.204
httpx cascade exhausted
soft_antibot_reset streaks
```

The proxy connection failure is at the **network level** — the proxy server itself rejects the connection. This is not a ban that cooldown can fix. The proxy is "alive" in the pool (no active ban) but functionally dead (connection refused).

### Why pool doesn't self-heal

- `exchange_proxy` ban logic is **timeout-based**, not **health-check-based**
- A proxy that returns `ERR_PROXY_CONNECTION_FAILED` gets banned for cooldown minutes
- After cooldown, it's unmarked — but the network issue persists
- The next fetch attempt hits the same failure → re-ban → cooldown → repeat

---

## 3. Gaps vs O257 fix — fl_hard_reset callers analysis

| Caller | File:Line | set_restart_source | Subprocess guard | Status |
|--------|-----------|-------------------|-----------------|--------|
| `_maybe_fl_soft_antibot_reset` | `fl_parser.py:199` | `not fl_listing_subprocess_enabled()` | **YES** | ✅ Fixed |
| `_maybe_fl_parsed_zero_recovery` | `fl_parser.py:257` | `not fl_listing_subprocess_enabled()` | **YES** | ✅ Fixed |
| `_fl_browser_antibot_fail` | `exchange_browser_fetch.py:717` | **default=True** | **NO** | ❌ **Gap** |
| Proxy failover | `exchange_proxy.py:1287` | **default=True** | **NO** | ❌ **Gap** |

**Both gaps call `fl_hard_reset()` without checking `fl_listing_subprocess_enabled()`.**

### Fix required

Both callers need:
```python
fl_hard_reset(
    reason=str(exc),
    storage=storage,
    set_restart_source=not fl_listing_subprocess_enabled(),
)
```

---

## 4. Kwork silent parsed=0 — code path and recommended recovery

### Code path

`kwork_parser.py:250-313` — `fetch_listing_projects()`:

1. Loop through `KWORK_MAX_PAGES` (default 3)
2. For each page: `_fetch_listing_html()` → browser or httpx
3. `parse_listing_html()` → `_extract_wants_array()` → manual bracket-depth JSON extraction
4. If `_extract_wants_array()` raises `KworkListingError` on page >1 → `break` (silent)
5. If page 1 raises → propagates (not silent)
6. After loop: `parsed_cards = len(projects)` → log `listing:kwork parsed=0`
7. **No recovery mechanism** — just returns `trimmed` (empty)

### Why it's silent

- `_extract_wants_array()` at `kwork_parser.py:58-82` does manual bracket-depth counting
- If Kwork changes HTML structure (e.g., escapes `]` inside strings), the extraction silently finds no match → raises `KworkListingError`
- On page >1, this is caught and `break`s — no error propagated
- On page 1, it propagates but `_fetch_source` in `main.py` catches `_LISTING_ERRORS` and returns `None`
- `parsed=0` is logged but no recovery action taken

### Recommended recovery

1. Add parsed-zero streak tracking (like FL's `_fl_parsed_zero_streak`)
2. After N consecutive zeros: log warning to `radar_site.log` with html_snip
3. After 2N zeros: attempt httpx fallback even if browser was used
4. After 3N zeros: alert operator (ops lamp → bad)

---

## 5. YouDo single-point-of-failure — monitoring checklist

YouDo is **browser-only** (`YOUDO_BROWSER_ONLY=1`). If Camoufox fails, the source is completely dead.

### Current mitigations

| Mechanism | Code | Effect |
|-----------|------|--------|
| Slot retries | `YOUDO_SLOT_RETRY_ON_TIMEOUT=3` | Try multiple DC proxy slots |
| DC carousel | `exchange_browser_fetch.py` | Rotate through DC proxy pool |
| RU fallback | `YOUDO_SERVICEPIPE_EARLY_RU=1` | Switch to RU tier on ServicePipe |
| Traffic guard | `YOUDO_TRAFFIC_GUARD_FAILS=3` | Skip fetch for 90min after 3 fails |
| Hard reset | `YOUDO_HARD_RESET_ON_FAIL=1` | Teardown + new browser on fail |
| Sticky sessions | `YOUDO_STICKY_SESSION=1` | Reuse Camoufox across cycles |
| Persistent profiles | `YOUDO_PERSISTENT_PROFILE=0` | Cookie/session persistence |

### Monitoring checklist for owner

| What to grep | Pattern | What it means |
|--------------|---------|---------------|
| YouDo OK | `fetch:youdo outcome=ok` | Normal operation |
| YouDo fail | `fetch:youdo outcome=fail` | Fetch failed — check reason |
| ServicePipe | `stage=servicepipe` | Anti-bot challenge — waiting 90s |
| DC ban limit | `stage=dc_ban_limit_reached` | All DC slots banned — RU fallback |
| Traffic guard | `youdo:trace stage=traffic_guard` | Cooldown active — skip 90min |
| Hard reset | `youdo:trace stage=hard_reset` | Browser teardown triggered |
| Sticky | `sticky_reload\|warm=1` | Sticky session active |
| Orphan kill | `browser:cleanup killed=` | Zombie processes cleaned |
| Wall timeout | `stage=wall_clock_timeout` | Fetch exceeded time budget |

### Red flags

- `fetch:youdo outcome=fail` repeated 3+ times → traffic guard active
- `stage=dc_ban_limit_reached` → all DC proxies banned
- No `youdo:trace stage=fetch_end` for >2 hours → source likely dead
- `killed=N` with N>0 on every cycle → orphan leak

---

## 6. Top 5 actionable fixes ranked P0/P1

| # | Pri | Fix | File:Line | Impact |
|---|-----|-----|-----------|--------|
| 1 | **P0** | Add `set_restart_source=not fl_listing_subprocess_enabled()` to `_fl_browser_antibot_fail` | `exchange_browser_fetch.py:717` | Eliminates restart_source loop — FL logs clean |
| 2 | **P0** | Add `set_restart_source=not fl_listing_subprocess_enabled()` to proxy failover caller | `exchange_proxy.py:1287` | Same — second source of restart loop |
| 3 | **P1** | Add parsed-zero streak recovery to Kwork (like FL) | `kwork_parser.py:294-310` | Kwork silent death becomes visible + self-healing |
| 4 | **P1** | Add `FL_HTTPX_AUTO_FALLBACK=1` documentation to `FL_LISTING_SUBPROCESS` section | `docs/ops/` or `config.py` docstring | Operator clarity on fallback behavior |
| 5 | **P1** | Add YouDo health-check ping (not just ban-based) to `exchange_proxy.py` | `exchange_proxy.py` | Detect dead proxies that are "alive" in pool |

---

## 7. Ops playbook: what owner should grep when FL "looks dead"

### Quick triage (3 greps)

```bash
# 1. Is FL fetching at all?
grep "fetch:fl outcome=" /opt/rawlead/data/radar_site.log | tail -20

# 2. Is restart_source firing?
grep "restart_source" /opt/rawlead/data/radar_site.log | tail -10

# 3. What's the proxy status?
grep "fetch:fl proxy=" /opt/rawlead/data/radar_site.log | tail -5
```

### Detailed triage

| Symptom | Grep | Interpretation |
|---------|------|----------------|
| FL silent (no logs) | `grep "fetch:fl" … \| tail` | Radar cycle may be stuck — check `rawlead-radar` systemd |
| parsed=0 streak | `grep "fl_listing:empty_html streak=" …` | Antibot blocking — streak N means N consecutive zeros |
| Browser timeout | `grep "fl_listing: timeout after" …` | Browser slots exhausted — check proxy pool |
| httpx fallback OK | `grep "fetch:fl stage=fallback httpx outcome=ok" …` | Browser failed, httpx recovered — working as designed |
| httpx fallback FAIL | `grep "fetch:fl stage=fallback httpx outcome=fail" …` | Both browser and httpx dead — proxy/network issue |
| Proxy ban | `grep "fetch:fl.*ban" …` | Proxy banned — check cooldown |
| hard_reset | `grep "fetch:fl hard_reset" …` | Full browser teardown triggered |
| soft_antibot_reset | `grep "soft_antibot_reset" …` | Parsed=0 + no bans → browser teardown |
| restart_source noise | `grep "restart_source" …` | O257 gap — see §3 (noise, not harmful until fixed) |

### If FL is "dead" (parsed=0 for >30min)

1. Check proxy pool: `grep "fetch:fl proxy=" … | tail`
2. Check if browser or httpx: `grep "fetch:fl outcome=" … | tail`
3. Check antibot: `grep "fl_listing:empty_html" … | tail`
4. Check systemd: `sudo systemctl status rawlead-radar`
5. Manual probe: `curl -s -o /dev/null -w "%{http_code}" "https://fl.ru/projects"` (from VPS)
6. If proxy dead: check log for `proxy_hint` — may need manual ban clear

---

## Lead triage (2026-06-19)

| MiMo claim | Lead verify |
|------------|-------------|
| 2 missing O257 call sites | **✅ подтверждено** — `exchange_browser_fetch.py:717` · `exchange_proxy.py:1287` |
| restart_source = noise, FL ok | **✅ совпадает** с prod grep 19:27 UTC |
| 194 alive but ERR_PROXY | **✅ логика бана** верна · P1 health-check — backlog |
| Kwork silent parsed=0 | **✅** по коду · P1 backlog |
| YouDo checklist | **✅** owner reference |

**→ Coder:** § **O283-MIMO** **FL-LOOP** (2-line fix + tests) · Kwork recovery → P1 backlog.

---

## Cross-references

- Previous audit: [`2026-06-19-mimo-audit.md`](2026-06-19-mimo-audit.md) § Parser stability
- O257 fix test: `tests/test_o257_restart_source_no_loop.py`
- O256 antibot test: `tests/test_o256_fl_antibot_soft.py`
- PROD_FACTS: `docs/team/common/PROD_FACTS.md`
