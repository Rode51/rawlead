# FL: parsed=0 — proxy pool exhausted (recurring)

**Date:** 2026-06-15  
**Symptom (owner):** FL «опять не работает»  
**Triage:** Lead · VPS `radar_site.log` read-only · ~10:08 UTC+3 server time

---

## Facts (VPS now)

| Метрика | Значение |
|---------|----------|
| `rawlead-radar` | **active** |
| `listing:fl` | **`parsed=0 fresh=0`** каждый цикл (с ~08:53 сегодня) |
| `fetch:fl` | **`pool_exhausted alive=0/25`** большую часть времени |
| Краткие окна | `alive=1–2/25` residential (node-proxy) — **всё равно parsed=0** |
| Последний `parsed=30` | **08:25–08:32** при DC `alive=4/4` |
| Последний FL в Neon | **2026-06-14 16:46 UTC** (~46 лидов / 24h до падения) |
| YouDo | **ok** · `parsed=50` в том же логе |

**Вывод:** это **не** «нет новых заказов на FL» (вчерашний fresh=0). Сейчас **листинг не качается вообще** — прокси-пул сожжён, fallback residential не парсит страницу.

---

## Корень (тот же класс, что [`2026-06-14-fl-proxy-pool-exhausted.md`](2026-06-14-fl-proxy-pool-exhausted.md))

1. **25 residential** (`FL_PROXY_URLS_RESIDENTIAL`) + **4 DC** — antibot/403/timeout → бан TTL 1ч → каскад `alive=0/25`.
2. При `pool_exhausted` → **parsed=0** (хуже, чем вчера parsed=30 + fresh=0).
3. Когда 1–2 residential живы — fetch идёт, но **parsed=0** → вероятно пустая/antibot HTML (нужен follow-up в логе `fl_parser` / browser trace).

## Owner request (2026-06-15): hard reboot FL on first ban

**Intent:** при бане **одного** FL-прокси — не крутить остальные слоты в том же цикле (каскад `alive=0/25`). Следующая попытка = **другой пользователь** для antibot.

**Уже есть в коде (не дожали для FL):**
- `invalidate_browser_slot` + wipe profile (`EXCHANGE_BROWSER_WIPE_ON_BAN=1`)
- `restart_source_fl` → `close_all_browser_contexts()` на следующем цикле (`main.py`)
- FL subprocess = **новый** Chromium на каждый fetch (O193), но **тот же** `cfg.http_user_agent` и **до 4 слотов** за цикл (`FL_SLOT_RETRY_MAX=4`)

**Чего нет:** stop-after-first-ban · rotate UA · не жечь пул · code § **O222-FL-HARD-RESET** в `CODER_PROMPT.md`

---

## Immediate ops (owner / отдельный чат @coder)

```powershell
cd C:\Users\hramo\uisness
python scripts\clear-vps-proxy-bans.py
```

Ждать 2–3 цикла (~5 мин) · проверить:

```bash
grep 'listing:fl\|fetch:fl' /opt/rawlead/data/radar_site.log | tail -10
# ожидание: alive=2/4+ DC · parsed=25–30
```

Или `/ops/` → **Clear proxy bans** + restart radar (если кнопка есть).

**Не помогло через 15 мин** → отдельный чат **`@coder`** (не Mechanic на quiz): § FL two-tier из тикета 2026-06-14 — ограничить httpx multi-ban cascade · DC primary · res только slot_retry.

---

## Code (уже в каноне, не сделано / не держит)

| # | Fix | Ref |
|---|-----|-----|
| 1 | FL two-tier proxy · не жечь 25 res за цикл | `2026-06-14-fl-proxy-pool-exhausted.md` |
| 2 | Ops lamp: `parsed=0` + pool_exhausted → 🔴 fail, не ok | `radar_status.py` |
| 3 | Browser retry multi-slot как YouDo | `fl_parser.py` |

---

## Recurrence (Lead VPS 2026-06-15 ~16:10 MSK+8)

| Время | Факт |
|-------|------|
| **14:10** | `parsed=30` · `alive=4/4` DC — последний OK |
| **14:20** | **`parsed=0`** · **`alive=4/4`** — fetch ok, **парсер 0 карточек** (не pool_exhausted) |
| **14:31–14:35** | slot 3→4→1 · `alive` 3→2→1 · всё ещё `parsed=0` |
| **15:23–15:45** | 4× DC ban · reason `browser:fl subprocess bad json` |
| **15:56+** | residential `alive=25/25` · **`parsed=0`** каждый цикл |
| Neon | **0 inserts / 2h** · 32 / 24h |

**Вывод owner «забанили — рефреш»:** O222 **не** = auto clear bans. Он: **1 ban / цикл** + wipe profile + **не** крутит слоты дальше. Но:
1. Сначала **parsed=0 при живом пуле** (antibot/пустая HTML) — баны ещё не при чём.
2. Потом ошибки subprocess → **TTL ban 1ч** на каждый DC · residential не парсит.
3. `fl_hard_reset` **не** чистит ban-table · `restart_source_fl` **не** ставится (storage не передаётся в `_fl_browser_antibot_fail`).
4. **O215** (two-tier, res no-ban) — **code ready, не deploy**.

**Immediate:** `python scripts/clear-vps-proxy-bans.py` → 2–3 цикла. Если снова `parsed=0` при `alive=4/4` → § **O233** (Mechanic).

---

## Verify done

- [x] `listing:fl parsed>=25` — post-clear **2026-06-15 AM**
- [x] **Sustained** parsed>=25 — post O233 deploy **2026-06-15 16:26** `parsed=30 fresh=21`
- [x] O233: hard_reset clears FL bans + storage path
- [x] O215 deploy

---

_Lead triage 2026-06-15 PM · O222 deployed but insufficient · → § O233 CODER_PROMPT_
