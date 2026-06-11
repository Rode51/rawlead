# 2026-06-11 — YouDo: timeout + antibot · 0 лидов · фильтр ленты (отдельно)

**Симптом (owner 11.06):** YouDo «опять не работает» · в ленте выбраны TG+YouDo — показывает Kwork (→ § O175b WP proxy).

**Verify Lead VPS:** `data/_youdo_probe.txt` · radar **active** · 2026-06-11 ~12:42 UTC

---

## YouDo ingest — факты сегодня

| Метрика | Значение |
|---------|----------|
| `browser_fail=youdo` (thread) | последний **2026-06-10 12:50 UTC** — после Mechanic fix thread |
| Сейчас в логе | **`health:youdo status=fail kind=timeout`** (~каждые 10–15 мин при fetch) |
| Между fetch | `parsed=0 fresh=0 new=0` + `youdo:skip fetch_every_n` |
| Antibot | **2026-06-10** `browser_fail=antibot` HTML в `data/debug_listings/youdo_antibot_*.html` |
| Proxy | `fetch:youdo proxy=gate.node-proxy.com:10000 slot=1/8 alive=8/8` — прокси жив |
| Neon youdo | не проверяли в этом прогоне · ожидание 0/24h |

**Вывод:** thread-fix **частично сработал** (нет `cannot switch thread` с 10.06 вечера). Новый паттерн — **Page.goto timeout 45s** и периодический **antibot**. Cooldown маскирует как `status=ok parsed=0`.

---

## Почему «каждый день отваливается»

1. **Разные классы сбоев** — thread (O160) → timeout → antibot; лог без единой trace-линии.
2. **`fetch_every_n=4`** — большую часть циклов skip; owner видит «мёртво» между попытками.
3. **Ops 🟢** при `parsed=0` — см. [`2026-06-10-youdo-playwright-thread.md`](2026-06-10-youdo-playwright-thread.md).

---

## Решение trace (O176 ✅ 2026-06-11)

**VPS 13:15–13:16 UTC — полная воронка:**

```
youdo:trace stage=fetch_start browser_only=1 proxy_hint=gate.node-proxy.com:10000 slot=1/8
youdo:trace stage=browser goto_ms=45040 status=timeout launch_ms=239 html_len=0
youdo:trace stage=fetch_end kind=timeout error_class=timeout
```

**Вывод:** не thread · не proxy ban · **Page.goto timeout 45s** на warm `youdo.com/`.

**→ @mechanic** § O177 · Coder logging done.

---

## Verify

```bash
grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -15
grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -20   # после O176
ls -lt /opt/rawlead/data/debug_listings/youdo_* | head -5
```

Neon: `SELECT count(*) FROM leads WHERE source='youdo' AND created_at > now() - interval '24 hours';`

---

## Решение (Mechanic 2026-06-11)

**Корень:** O176 trace + `data/_youdo_probe.txt` — `Page.goto` **45s timeout на warm `https://youdo.com/`**, не на листинг `/tasks-all-opened-all`. Прокси alive 8/8 · thread-fix O160 **OK**.

**Fix:** `src/exchange_browser_fetch.py` + `src/youdo_parser.py`

| Изменение | Зачем |
|-----------|--------|
| `YOUDO_WARM_HOME=0` (default) | warm home убран — SSR-листинг не требует прогрева главной |
| `YOUDO_GOTO_TIMEOUT_SEC=90` | listing goto 90s внутри wall 120s (было 45s) |
| warm fail non-fatal | если `YOUDO_WARM_HOME=1` и warm упал — идём на листинг |
| slot retry on timeout | при timeout — до 3 alive-слотов (primary + rotate), не break после 1-го |

**Изменённые файлы**

| Файл | Что |
|------|-----|
| `src/exchange_browser_fetch.py` | warm off, goto 90s, slot retry |
| `src/youdo_parser.py` | `_youdo_goto_timeout_sec()` |
| `tests/test_youdo_human.py` | retry on timeout |
| `tests/test_youdo_traffic.py` | warm disabled default |
| `scripts/deploy-o177-vps.py` | deploy + restart radar |

**Как проверить**

1. Deploy: `python scripts/deploy-o177-vps.py`
2. Локально: `pytest tests/test_youdo_traffic.py tests/test_youdo_human.py tests/test_exchange_browser_fetch.py -q` → **27/27**
3. VPS после 1–2 fetch-циклов (~40 min с `fetch_every_n=4`):
   ```bash
   grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -10
   grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -5
   ```
   Ожидание: `fetch_start` → `browser status=200 html_len>0` → `parse cards_found>0` → `health:youdo new>0`
4. Neon: `source=youdo` за 1h > 0

**Статус:** код ✅ · pytest **27/27** · deploy VPS ✅ **2026-06-11**

**Lead verify post-deploy (14:31 UTC):**

| До O177 | После O177 |
|---------|------------|
| goto `https://youdo.com/` 45s timeout | goto `tasks-all-opened-all` 90s timeout |
| warm home блокировал | warm skip ✅ |

Ingest **ещё 0** · `health:youdo fail kind=timeout` 14:34 UTC · **→ @mechanic** (listing/network/antibot, не warm home).

---

## Решение (Mechanic O177b · 2026-06-11)

**Корень O177 partial:** slot retry **не работал** — Playwright кидает `TimeoutError`, а цикл ловил только `HtmlFetchError`. Плюс `wall_clock_sec=120` не вмещал 90s×retry.

**Fix O177b** (`exchange_browser_fetch.py` + `youdo_parser.py`):

| Изменение | Зачем |
|-----------|--------|
| `_wrap_youdo_browser_error` | TimeoutError → HtmlFetchError → slot retry |
| wall default `goto×3+60` = **330s** | место для 3 слотов по 90s |
| `_is_youdo_slot_retryable` | retry на timeout **и** 403/antibot/empty |
| slot 2+ → ephemeral + `_abort_playwright_worker` | свежий UA, другой proxy |
| `youdo:trace stage=slot_retry` | видно в логе |
| 403/empty detect + debug HTML save | 403 proxy-ban страница ~2.3KB |

**Post-deploy verify 14:43 UTC:** `wall_clock_sec=330` ✅ · goto **51s** (не 90s timeout) · antibot/empty slot1 → нужен retry (O177b antibot retry deploy следом).

**Изменённые файлы:** `src/exchange_browser_fetch.py` · `src/youdo_parser.py` · `tests/test_youdo_human.py` · `tests/test_youdo_traffic.py` · `scripts/deploy-o177b-vps.py`

**Как проверить**

```bash
python scripts/deploy-o177b-vps.py
pytest tests/test_youdo_traffic.py tests/test_youdo_human.py tests/test_exchange_browser_fetch.py -q  # 30/30
grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -20
# ожидание: slot_retry → browser status=200 html_len>10000 → parse cards_found>0 → health new>0
```

**Статус:** O177+O177b deploy ✅ · ingest DoD ❌ · **новый блокер: radar wall 180s < youdo wall 330s**

---

## Решение (Mechanic O179 · 2026-06-11)

**Корень (подтверждён probe `data/_youdo_probe.txt`):**

1. **Radar wall 180s** убивал fetch на slot 2 mid-retry при internal wall 330s
2. **Все node-proxy слоты** — goto 90s timeout, `html_len=0` (сеть, не antibot)
3. **Traffic waste** — каждый fail жёг 180–330s proxy без guard

**Fix O179:**

| Изменение | Зачем |
|-----------|--------|
| `main.py` `_radar_source_fetch_wall_sec("youdo")` = `max(env, youdo_source_fetch_wall_sec())` | slot_retry 1→2→3 успевает (330s) |
| `youdo_parser` traffic guard `YOUDO_TRAFFIC_GUARD_FAILS=3` | после 3 fail подряд — skip browser 90 min, лог `youdo:skip traffic_guard` |
| `exchange_browser_fetch` slot 2+ → `wait_until=commit`, lean off | domcontentloaded не срабатывает через node-proxy |
| `youdo_source_fetch_wall_sec()` export | единый budget radar ↔ parser |

**Изменённые файлы:** `src/main.py` · `src/youdo_parser.py` · `src/exchange_browser_fetch.py` · `tests/test_o160_radar_ingest.py` · `tests/test_youdo_traffic.py` · `scripts/deploy-o179-vps.py`

**Как проверить**

```bash
python scripts/deploy-o179-vps.py
pytest tests/test_o160_radar_ingest.py tests/test_youdo_traffic.py tests/test_youdo_human.py tests/test_exchange_browser_fetch.py -q  # 37/37
grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -25
# ожидание: НЕТ `source wall-clock 180s` · slot_retry 1→2→3 · commit on slot 2+
# DoD ingest: browser status=200 html_len>10000 → cards_found>0 → Neon youdo >0/24h
```

**t2 residual:** если все node-proxy slots всё ещё timeout — owner: RU residential в `YOUDO_PROXY_URLS` (`scripts/deploy-youdo-residential-vps.py`).

**Статус:** код ✅ · deploy VPS **✅ 08:04 UTC** · Lead verify: **16:11** listing 50 cards · ingest L1 ⏳

---

## Lead verify 2026-06-11 ~15:25 UTC (O177b deployed)

```
fetch_start wall_clock_sec=330 slot=1/8
browser goto_ms=90085 html_len=0 status=timeout          # slot 1
slot_retry ephemeral=1 slot=2
fetch_end error_snip=source wall-clock 180s              # ← radar убил через 180s
browser goto_ms=90176 html_len=0 status=timeout          # slot 2 (ещё идёт)
slot_retry slot=3
browser goto_ms=90181 html_len=0 status=timeout          # slot 3
parse cards_found=0 skipped_reason=browser
health:youdo status=fail kind=unknown
cooldown_until=07:59
```

**Два блокера:**

| # | Что | Деталь |
|---|-----|--------|
| **1** | **Radar wall 180s** | `main.py` `RADAR_SOURCE_FETCH_WALL_SEC=180` (default) оборачивает **весь** fetch YouDo · O177b внутри считает **330s** (90×3+60) · retry **не успевает** |
| **2** | **Сеть/proxy** | Все 3 слота node-proxy: `Page.goto` **90s timeout**, `html_len=0` — страница **не открывается**, не antibot HTML (debug antibot только 10.06) |

**Логирование:** ✅ O176 `youdo:trace` · O177b `slot_retry` · `health:youdo` · cooldown в trace.

---

## O179 — permanent fix (→ @mechanic)

### t1 — Radar wall sync (P0, быстрый)

- `main.py`: для `source=youdo` wall = `max(RADAR_SOURCE_FETCH_WALL_SEC, youdo_listing_wall_clock_sec())` **или** env `RADAR_SOURCE_FETCH_WALL_SEC=360` на VPS
- DoD: в trace **нет** `source wall-clock 180s` при `fetch_start wall=330` · все 3 slot_retry отрабатывают

### t2 — Достучаться до листинга (P0)

- VPS probe: `curl`/Playwright с каждого node-proxy slot на `tasks-all-opened-all` — latency, HTTP code, body size
- Если все slots timeout → смена стратегии: RU residential (как в O155), другой URL, headless stealth, или fallback parse path
- DoD: `browser status=200 html_len>10000` · `parse cards_found>0` · Neon youdo >0/24h

### t3 — Ops honesty (P1)

- `health:youdo` **fail** если реальный fetch (не skip/cooldown) и `parsed=0`
- `/ops/` не 🟢 при 0/24h YouDo

**pytest:** extend `test_youdo_*` + smoke `scripts/_probe_youdo_vps.py` (read-only diag, no secrets in log)
