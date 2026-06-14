# Coder — hot queue (active)

**→ Now:** § **O213-KWORK-COVERAGE** — Kwork pagination + filter scope fix

---

## § O213-KWORK-COVERAGE — Kwork page2-3 + filter scope

**Ticket:** [`2026-06-14-kwork-fl-zero-new.md`](../../problems/2026-06-14-kwork-fl-zero-new.md)

**Owner symptoms:** last Kwork order 6h ago; owner sees orders on kwork.ru but radar misses them.

**Root cause (Lead verify 2026-06-14):**
1. `kwork_parser.py` fetches **page 1 only** (12 items). New orders appear on page 2+ before we pick them up.
2. Some new items on page 1 are blocked by word filter (`pipeline:skip filter kwork:id=…`). Stop words like `вебинар`, `логотип` etc. are too broad when applied to Kwork.

**Facts:** parsed=12 every cycle (page size). Neon last kwork insert 06:09 MSK. Same 12 IDs in page 1 since then. IDs 3196826/3196861/3196862/3196905 appeared fresh but got filter-skipped.

### t1 — Kwork multi-page fetch

**File:** `src/kwork_parser.py`

- Mirror FL approach: iterate pages 2–3 (env `KWORK_MAX_PAGES` default `3`; min 1)
- URL pattern: check how `kwork.ru/projects` paginates — likely `?page=2` query param
- Each page: same `_extract_wants_array` + `_wants_to_projects`. Merge results, dedup by `pid`.
- `trim_listing_at_known` applied after merge (all pages combined)
- Log: `listing:kwork parsed=N fresh=M pages=P` (add pages count)
- If page 2 returns error / empty, stop pagination gracefully (do not raise)

Probe VPS first to confirm pagination param: `curl -s 'https://kwork.ru/projects?page=2'` in a test — check HTML has `"wants":[` array.

### t2 — Filter scope: Kwork-safe stops

**File:** `src/filters.py`

Words that are valid Kwork orders but hit our TG-designed stop list:
- `вебинар` — on Kwork could be "сайт для вебинара" (valid)
- `логотип`, `баннер` — on Kwork could be "добавить логотип на сайт" (valid)
- Keep these in TG stop-list; for **Kwork and FL** add `_KWORK_SAFE_STOPS_SKIP` set: if source is kwork/fl and stop word is in safe set → don't skip

Implement: `accepts_listing(project, wide, source=None)` — pass source through from pipeline. If `source in ('kwork', 'fl')` and stop word is in `_KWORK_SAFE_STOPS_SKIP`, allow through.

Safe set to start: `{'вебинар', 'логотип', 'баннер', 'дизайн макета'}` (conservative)

### t3 — Tests

- Unit `test_kwork_parser.py`: pages=2 fetches 2 html mocks, deduped, returns combined fresh
- Unit `test_filters.py`: kwork source passes `вебинар` (safe for kwork), TG source blocks it
- Existing tests green

### DoD

- VPS kwork shows `listing:kwork parsed=N pages=2-3 fresh>0` within 2 cycles after restart
- Filter: `вебинар` stop no longer blocks kwork source orders
- pytest green (all including test_o207b_filter)
- No regression: TG filter still blocks `вебинар` in TG posts

**Deploy:** `kwork_parser.py` + `filters.py` → restart **`rawlead-radar`**

---

## § O212-OPS-LOG-TRUTH — TG log noise + ops «0 новых» / TG 🔴 [PENDING DEPLOY]

**Ticket:** [`2026-06-14-ops-log-spam-tg-lamp.md`](../../problems/2026-06-14-ops-log-spam-tg-lamp.md)

**Owner symptoms:** log «помойка» (all chat ids) · FL/Kwork/TG show «0 новых» / TG 🔴 while radar alive.

**Facts (VPS 2026-06-14):** all units **active** · FL `parsed=30 fresh=0` · Kwork `parsed=12 fresh=0` · TG `handler_ok` + messages · **not a crash**.

### t1 — Stop chat-id log dump

**File:** `src/tg_monitor.py`

- `тг:монитор:старт` (~895): log `чатов=N file=F filter=K` — **remove** `ids=[sorted(...)]`
- `пропуск чата {id}` (~454): do **not** log every skip on reload; either:
  - increment counter + one summary line per reload (`skip_entity=N`), or
  - log only at DEBUG / first occurrence per account per hour

**Do not break:** O206 t3c watchdog · handler_ok line · join audit counts in storage

### t2 — Ops exchange cards truth

**Files:** `src/owner_admin.py` · optionally `src/static/ops-pult.js`

1. **`today_new_ids`:** use Neon `new_today` from `_lead_counts_by_source` (same MSK day as O211 footer), not `health.last_new_ids`
2. **Secondary line:** show last-cycle `parsed` / `fresh` from health (tooltip or sub-line): «за цикл: parsed=30 fresh=0»
3. **TG status lamp:** for `source_id=tg`, use `tg_pult_lamp_state` / fresh `тг:пульс` — **not** only Neon insert gap for `last_ok_at`
4. **`_last_log_line_for_source('tg')`:** exclude `бот_start:.*skip` · prefer `handler_ok|тг:пульс|listing:tg|health:tg`

### t3 — Tests

- Unit: `_last_log_line_for_source` picks handler_ok over bot_start skip (fixture lines)
- Unit: exchange row maps `today_new_ids` from Neon mock, not health `last_new_ids`
- Existing: `test_o171_ops_funnel.py` green

### DoD

- Restart radar once on VPS → log has **no** multi-line `ids=[…]` block
- `/ops/` FL/Kwork: «сегодня N» matches Neon (may still be 0) + visible parsed/fresh hint
- TG card **not** 🔴 when `handler_ok` + pulse <15m even if Neon TG insert 0
- pytest green

**Deploy:** `tg_monitor.py` → restart **`rawlead-radar`** · API files → restart **`rawlead-api`**

---

## Closed ✅ (hot index)

| § | DoD | deploy |
|---|-----|--------|
| **O212** | log no ids dump · today_new from Neon · TG lamp from pult · pytest 20/20 | ⏳ VPS |
| **O211-DEPLOY** | footer сегодня/24ч | ✅ |
| **O207b** | replay 99/14/7 | ✅ |
| **O209** | WP 1.18.84 | ✅ |

**Archive:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)
