# 2026-06-10 — YouDo: 0 лидов · Playwright thread · админка 🟢 ложная

**Симптом (owner):** YouDo «опять не работает», в `/ops/` всё зелёное.

**Verify Lead:** `radar_site.log` + Neon · 2026-06-10 ~13:10 UTC

---

## Факты

| Метрика | Значение |
|---------|----------|
| Сервисы | `rawlead-api` · `rawlead-radar` · `rawlead-bot-poll` — **active** |
| YouDo в Neon за 24h | **0** |
| Последний лид YouDo в Neon | **2026-06-09 04:48 UTC** |
| Последний успешный parse (health log) | **2026-06-09 12:48** · `new=46` (дальше — 0) |
| Proxy bans `youdo:*` | **нет** |

## Что в логе за ночь / утро (10.06)

**YouDo — корень:**

```
fetch:youdo proxy=gate.node-proxy.com:10000 slot=1/8 alive=8/8
youdo_listing: browser_fail=youdo: all browser slots failed (1):
  Playwright launch failed (youdo): cannot switch to a different thread (which happens to have exited)
health:youdo status=fail kind=browser   # ~12:11, ~12:51
health:youdo status=ok parsed=0 fresh=0 new=0   # между fail — cooldown skip
youdo:skip cooldown 29 min …
```

- Ошибка **38×** за сутки в логе (`cannot switch to a different thread`).
- Раньше в том же логе: `Playwright Sync API inside the asyncio loop` (регресс hotfix O63).
- Прокси **жив** (8/8 alive) — **не** IP-ban.

**Другие биржи (параллельно):**

| Биржа | Сейчас | Ошибка |
|-------|--------|--------|
| FL | 🔴 в health | `pool_exhausted slot=1/4` — сетевой сбой ленты |
| Kwork | 🟡 | parsed=12 · fresh=0–1 · работает слабо |
| YouDo | 0 скачано | browser thread |

**L1 pipeline (ночь):**

- `ImportError: cannot import name 'finalize_tools_for_lead' from 'tools_catalog'` — **30×** в `radar_site.log` (циклы «Прочее»).
- На VPS сейчас функция **есть** (`tools_catalog.py:287`) — возможен stale process / старые строки в логе; проверить после restart.

**TZ (фон):** `BadZipFile` / `PdfStreamError` — Kwork PDF, не YouDo.

---

## Почему админка «всё отлично»

`/ops/` для карточки биржи использует `_exchange_status_from_ok_at`: если `last_ok_at` **< 15 мин назад** → 🟢 «Работает».

YouDo между browser-fail пишет `health:youdo status=ok parsed=0` (cooldown skip / пустой цикл) → **last_ok_at обновляется** → лампа зелёная, хотя **скачано 0, в Neon 0**.

`exchange_health.status_level` при `parsed=0` и успешном fetch должен давать 🔴 — **ops SSR упрощает** до «был недавний ok».

→ **UX-баг админки** (отдельный follow-up O152), не «YouDo здоров».

---

## Гипотеза

Playwright для YouDo запускается из **не того потока** после asyncio tg_main / FL browser в том же процессе radar. Thread pool «умирает» → `cannot switch to a different thread`.

Канон: [`2026-06-03-ingest-l1-tg-youdo.md`](2026-06-03-ingest-l1-tg-youdo.md) · hotfix `deploy-youdo-browser-vps.py` (Sync API in asyncio — уже ловили).

---

## Действия

| # | Кто | Что |
|---|-----|-----|
| 1 | **Lead / owner** | `systemctl restart rawlead-radar` — сброс thread state (без правки .env) |
| 2 | **@mechanic** | Playwright YouDo: dedicated thread / async API / isolate browser from tg loop · grep `exchange_browser_fetch.py` `youdo_parser.py` |
| 3 | **@coder** (after) | Ops lamp: не 🟢 при `parsed=0` + neon gap > N · § O152 trace |
| 4 | **Lead verify** | после fix: `health:youdo new>0` · Neon `source=youdo` за 1h |

**Не смешивать** с § O168-PRE-ADS-GATES до зелёного YouDo ingest.

---

## Команды verify (owner/Lead)

```bash
grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -10
grep 'browser_fail=youdo' /opt/rawlead/data/radar_site.log | tail -5
```

Neon: `count(*) FROM leads WHERE source='youdo' AND created_at > now() - interval '1 hour'`

---

## Решение (Mechanic 2026-06-10)

**Корень:** Playwright Sync API привязан к потоку, в котором вызван `sync_playwright().start()`. O160 (`main._fetch_source`) и wall-clock guard создавали **одноразовые** `ThreadPoolExecutor` с `shutdown(wait=False)` — поток умирал, глобальный `_PLAYWRIGHT` оставался «привязанным» к мёртвому потоку → `cannot switch to a different thread (which happens to have exited)`.

**Fix:** `src/exchange_browser_fetch.py`

- Постоянный dedicated thread `rawlead-playwright` (`ThreadPoolExecutor(max_workers=1)`), не shutdown между циклами.
- Все публичные browser API (`fetch_listing_html_browser`, `fetch_youdo_html_browser`, `fetch_listing_html_browser_slots`, `close_all_browser_contexts`, `invalidate_browser_slot`) маршрутизируются через `_playwright_sync`.
- Wall-clock (`*_wall_clock`) — `_playwright_sync_timed` на том же executor; при timeout — `_abort_playwright_worker()` (сброс executor + `_PLAYWRIGHT`, без ожидания зависшего job).

**Изменённые файлы**

| Файл | Что |
|------|-----|
| `src/exchange_browser_fetch.py` | dedicated Playwright thread + abort on timeout |
| `tests/test_exchange_browser_fetch.py` | test foreign-thread routing |
| `tests/test_o160_radar_ingest.py` | tearDown через `reset_playwright_thread_for_tests` |
| `scripts/deploy-youdo-playwright-thread-vps.py` | deploy + restart radar |

**Как проверить**

1. Deploy: `python scripts/deploy-youdo-playwright-thread-vps.py`
2. Локально: `pytest tests/test_exchange_browser_fetch.py tests/test_o160_radar_ingest.py -q`
3. VPS после 1–2 циклов radar:
   ```bash
   grep 'browser_fail=youdo' /opt/rawlead/data/radar_site.log | tail -5   # пусто
   grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -5        # new>0
   ```
4. Neon: `source=youdo` за последний час > 0

**Статус:** код ✅ · pytest 14/14 · **deploy VPS ⏳** (на VPS ещё `CODE_OLD`, последний `browser_fail` 12:50 UTC, Neon youdo 0/2h)

**Owner/Mechanic:** `python scripts/deploy-youdo-playwright-thread-vps.py` → Lead re-verify `health:youdo new>0`
