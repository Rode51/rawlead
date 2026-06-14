# Coder — hot queue (active)

**→ Now:** § **O213-KWORK-COVERAGE** — Kwork pagination + filter scope fix

---

## § O213-KWORK-COVERAGE — Kwork page2-3 + exchange filter scope

**Ticket:** [`2026-06-14-kwork-fl-zero-new.md`](../../problems/2026-06-14-kwork-fl-zero-new.md)

**Owner symptoms:** sees orders on kwork.ru (screenshot + URLs) but not in RawLead lenta/ops.

**Owner repro URLs (Lead verify 2026-06-14):**
| external_id | title | in Neon? | visible | ingested MSK |
|-------------|-------|----------|---------|--------------|
| **3194789** | Сделать лендинг | ✅ | True | 2026-06-10 15:03 |
| **3196704** | Парсинг сайтов | ✅ | True | 2026-06-13 18:50 |

→ These two **are already in DB**. If owner «не видит» — likely feed scroll/sort (7-day window, newer on top), not parser miss. **Do not re-ingest.**

**Screenshot items (Lead Neon grep):**
| title fragment | in Neon? |
|----------------|----------|
| «Переписать промпт для Gemini» (3196630) | ✅ visible |
| «Поправить выгрузку фида» (3196662) | ✅ visible |
| «Посадка сайта на wordpress» | ✅ (similar titles exist) |
| **«Платформа для учебного центра»** | ❌ **NOT FOUND** — real gap |

**Root causes:**
1. `kwork_parser.py` fetches **page 1 only** (12 items). Orders outside top-12 never fetched → e.g. «Платформа для учебного центра».
2. Some fresh page-1 items blocked by shared L2 filter (`pipeline:skip filter kwork:id=…`).
3. Ops «0 новых» was UX bug (O212) — `fresh=0` = dedup of known ids, not «Kwork empty».

### Filter architecture (do NOT confuse with TG)

| Layer | File | Applies to |
|-------|------|------------|
| **TG spam / CV / seller** | `src/tg_spam_filter.py` (`is_tg_spam`, `is_tg_order_post`) | **TG only** (post-L1 guard) |
| **TG wide soft bypass** | `filters.py` → `tg_filter_soft_bypass()` + `TG_WIDE_SOFT_STOPS` | **TG only** (`source.startswith('tg:')`) — O207b |
| **Shared L2 word filter** | `filters.py` → `ListingWordFilter` from `docs/ops/FILTERS.md` | **kwork, fl, youdo, tg** — stop/take words |

**Kwork does NOT use `tg_spam_filter`.** It uses shared L2 only. Problem: stop words in FILTERS.md were tuned for TG noise; same list blocks valid Kwork orders.

**Fix t2:** add **exchange-safe bypass** for kwork+fl (NOT tg): when `source in ('kwork','fl')`, skip applying selected stop tokens. Do **not** weaken TG path.

### t1 — Kwork multi-page fetch

**File:** `src/kwork_parser.py`

- Mirror FL: pages 1–3 (env `KWORK_MAX_PAGES` default `3`)
- URL: probe pagination (`?page=2` or site pattern) — confirm `"wants":[` in HTML
- Merge pages, dedup by `pid`, then `trim_listing_at_known`
- Log: `listing:kwork parsed=N fresh=M pages=P`

**Acceptance probe after deploy:** «Платформа для учебного центра» appears in log as fresh within 2 cycles OR explain why (filter) with logged id.

### t2 — Exchange-safe L2 stops (kwork + fl only)

**File:** `src/filters.py` · **pipeline:** pass `project.source` into stop logic

Start set `_EXCHANGE_SAFE_STOPS` (conservative): `вебинар`, `логотип`, `баннер`, `дизайн макета`, `figma`, `фигма`, `монтаж`, `монтаж рилс`, `иллюстратор`

- If `source in ('kwork','fl')` and matched stop ∈ `_EXCHANGE_SAFE_STOPS` → **allow** (continue to category check)
- TG path unchanged: `tg_filter_soft_bypass` still only for `tg:*`

Log on allow: `pipeline:filter:exchange_safe kwork:id=… stop=…` (one line, no spam)

### t3 — Tests

- `test_kwork_parser.py`: multi-page mock, dedup, `pages=2`
- `test_filters.py`: kwork passes «логотип» in title; TG post with «логотип» still blocked (no soft bypass unless order markers)
- Regression: `test_o207b_filter.py`, `test_o171_ops_funnel.py` green

### DoD

- VPS: `listing:kwork parsed>12 pages=2-3` within 2 cycles
- «Платформа для учебного центра» ingested OR logged why skipped
- 3194789/3196704 unchanged (already in DB)
- TG filter regression: replay baseline unchanged
- pytest green

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
