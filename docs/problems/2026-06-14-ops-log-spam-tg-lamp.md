# Ops log spam + TG 🔴 false alarm + «0 новых» misleading

**Date:** 2026-06-14  
**Owner:** «помойка в логах — не писать все чаты» · FL/Kwork/TG «не показывает фактическое» · «всё упало опять»  
**Triage:** Lead · VPS `radar_site.log` + systemd + code read-only

---

## Facts (VPS ~13:20 MSK, 2026-06-14)

| Check | Result |
|-------|--------|
| `rawlead-radar` / `rawlead-api` / `rawlead-bot-poll` | **active** |
| FL | `listing:fl parsed=30 fresh=0` · fetch ok · residential 21/25 |
| Kwork | `listing:kwork parsed=12 fresh=0` · fetch ok |
| Freelance.ru | `скачано 25 · новых 0` (filter 3) |
| TG monitor | `handler_ok peers=70/64/40` · `тг:сообщ` flowing · **not dead** |
| Neon inserts today | slow / 0 on last cycles → **dedup**, not crash |

**Conclusion:** ingest **works**. Owner sees 🔴 / «0» because **ops UI + log noise**, not because radar stopped.

---

## Root cause 1 — log spam (owner «не писать все чаты»)

On every **tg_main / radar restart**, log dumps **full peer id lists**:

```
тг:монитор:старт account=acc1 чатов=70 ids=[-1003363793339, … 70 ids …]
```

Plus **one line per failed entity** on reload:

```
тг:монитор:acc3: пропуск чата 1697683423
```

**Code:** `src/tg_monitor.py` ~895 (`ids={sorted(sess.chat_ids)}`) · ~454 (`пропуск чата`).

Radar restarted twice in ~19s during deploy window → **3 accounts × (full id list + ~20 skips)** = log «помойка».

**Fix (minimal):** log `чатов=N file=M filter=K` only · skip chat → aggregate counter or DEBUG · never dump `ids=[…]`.

---

## Root cause 2 — TG 🔴 «Не отвечает» (false)

Ops card uses `_exchange_status_from_ok_at(last_ok_at)` (`owner_admin.py` ~317).

For **tg**, `last_ok_at` is bumped only when **Neon has TG insert within 15 min** (`main.py` ~778 `record_ok_ping` if `gap <= GREEN_MAX_MIN*60`).

Monitor can listen + process messages **without Neon insert** → `last_ok_at` stale → 🔴 «1 час назад» even while `handler_ok` / `тг:пульс` fresh.

**Last log line** for TG matches **any** `тг:` — picks noise like `тг:бот_start:acc2:skip (флаг есть)` instead of `handler_ok` / `listing`.

**Fix:** TG lamp from `tg_pult_lamp_state` / pulse age · `last_log_line` exclude `бот_start:.*skip` · prefer `handler_ok|тг:пульс|тг:сообщ`.

---

## Root cause 3 — «Сегодня найдено новых: 0» misleading (FL/Kwork)

Ops row sets:

```python
row["today_new_ids"] = int(health.get("last_new_ids", 0))  # owner_admin.py ~1173
```

`last_new_ids` = **last cycle fresh count** (0 when dedup), **not** Neon calendar-day total.

Label says «Сегодня» → owner thinks parser dead. Log already shows truth: `parsed=30 fresh=0 — догнали`.

**Fix:** footer/card «сегодня N» from Neon SQL (`new_today` in `ops_funnel._lead_counts_by_source`) · tooltip «за цикл: fresh=M · parsed=P».

---

## Root cause 4 — FL «0 новых» is dedup (expected)

Same as [`2026-06-14-fl-proxy-pool-exhausted.md`](2026-06-14-fl-proxy-pool-exhausted.md): parsed>0 fresh=0 = **already in DB**, not outage.

Residential tier working (`fetch:fl … res slot=10/25 alive=21/25`).

---

## Action

| Who | What |
|-----|------|
| **@coder** | § **O212-OPS-LOG-TRUTH** in `CODER_PROMPT` — log trim + ops truth |
| **Owner** | Hard refresh `/ops/` after deploy · no `.env` change needed |

**Not an incident for @mechanic** unless systemd goes inactive.
