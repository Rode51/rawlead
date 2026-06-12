# 2026-06-12 — YouDo antibot permanent block + ops honesty

**Статус:** ✅ **решено Mechanic 2026-06-12** · **Lead deploy ✅** · ingest live smoke ⏳ (cooldown после restart)

---

## Симптом

Owner: «парсеры опять упали». YouDo не работает с **2026-06-09 ~12:49 UTC** (последний `new>0`). Сегодня June 12 — та же картина.

---

## Факты из логов (read-only Lead)

### YouDo — `data/radar_site.log` (2026-06-11 / 2026-06-12)

| Метрика | Значение |
|---------|----------|
| `html_len` при каждой попытке | **626 bytes** — постоянно, все слоты |
| `antibot_hit` | **0** (false negative — код не детектирует этот формат) |
| `goto_ms` | 0–31 ms (быстрый ответ = не timeout, блокировка на уровне proxy/antibot) |
| `slot_retry ephemeral proxy_hint=5.6.7.8:8000 slot=2` | все 3 retry → тот же 626-байт результат |
| traffic_guard cooldown | работает (разрывы ~90 мин) — но не решает корень |
| **Последний реальный успех** | **2026-06-09 12:49 UTC** `parsed=50 fresh=50 new=46` |

### Паттерн (3 дня подряд, каждый цикл)

```
stage=browser antibot_hit=0 goto_ms=0 html_len=626 status=200   ← slot 1 → antibot
stage=slot_retry ephemeral=1 proxy_hint=5.6.7.8:8000 slot=2
stage=slot_retry ephemeral=1 proxy_hint=5.6.7.8:8000 slot=2
stage=slot_retry ephemeral=1 proxy_hint=5.6.7.8:8000 slot=2     ← slot 2/3 → тот же 626 байт
```

### Ops dishonesty (June 10 диагностика `_overnight_youdo_diag.txt`)

```
health:youdo status=ok parsed=0 fresh=0 new=0   ← /ops/ 🟢, хотя 0 лидов
```

### FL — June 10 (же файл)

```
health:fl status=fail kind=unknown
FlListingError: pool_exhausted slot=1/4
```
FL на June 10 тоже падал. Текущий статус FL на VPS — не известен из локальных логов.

---

## Корень (анализ) — уточнение 2026-06-12

**Owner уточнение:** на YouDo уже используются **residential прокси** node-proxy.com — и US-пул (api57e…_c_US_s_1–25), и RU-пул (api475…_c_RU_s_1–25). Были переключения между ними. Тип прокси — НЕ причина.

| # | Причина | Подтверждение |
|---|---------|---------------|
| **1** | **Playwright headless fingerprint** — YouDo детектирует браузер, не IP | residential proxy не помогает если Chrome/Playwright виден как headless (navigator.webdriver, CDP, etc.) |
| **2** | **html_len=626 — начало SPA-shell** (пустой каркас) | при `wait_until=commit` Playwright фиксирует первые байты ответа до рендера JS; real cards = после ~2-5s JS execution |
| **3** | **`antibot_hit=0` — false negative** | код не детектирует этот формат; 626 байт — не 403, не явная antibot-страница, а SPA skeleton |
| **4** | **`health:youdo status=ok` при `parsed=0`** | /ops/ 🟢 хотя YouDo мёртв 3+ дня |

**Гипотеза корня:** сочетание `wait_until=commit` (введён O179 для slot 2+) + headless-детекция YouDo. Нужно проверить:
1. `wait_until=networkidle` вместо `commit` (медленнее, но ждёт JS)
2. stealth mode / `playwright-stealth` / скрытие CDP
3. Сравнить поведение до O179 и после

| 2026-06-12 | **Смена US→RU→US прокси** | residential уже есть в обоих пулах, проблема не в типе прокси | O185 t6 |

---

## Задачи Mechanic (O185 t6 расширенный)

### t6-diag — Диагностика корня (P0, прежде всего)

**Нужно выяснить на VPS:**
```bash
# 1. Какой wait_until сейчас на slot 1?
grep -n 'wait_until\|commit\|networkidle' src/exchange_browser_fetch.py

# 2. Есть ли playwright-stealth / navigator.webdriver скрытие?
grep -n 'stealth\|webdriver\|CDP\|navigator' src/exchange_browser_fetch.py src/youdo_parser.py

# 3. Что именно в 626 байтах (последний debug HTML)?
ls -lt /opt/rawlead/data/debug_listings/youdo_* | head -3
cat /opt/rawlead/data/debug_listings/youdo_antibot_*.html 2>/dev/null | head -30

# 4. Когда последний раз html_len > 1000?
grep 'youdo:trace.*html_len' /opt/rawlead/data/radar_site.log | tail -20
```

### t6a — Fix `antibot_hit` detection + html_len guard (P0)

- `exchange_browser_fetch.py`: `html_len <= 1500` AND `status=200` → `antibot_hit=True` (SPA shell / antibot page)
- Отдельно: `wait_until=networkidle` или `load` для slot 1 — дать JS отработать
- Рассмотреть `playwright-extra` + `puppeteer-stealth` port для скрытия headless-маркеров
- DoD: `youdo:trace antibot_hit=1` когда 626 bytes · либо `html_len>10000`

### t6b — Ops honesty: YouDo (P0, быстро)

- `health:youdo status=fail kind=antibot` если `antibot_hit=True` во всех попытках последнего цикла
- `/ops/` 🔴 «YouDo: antibot» — не 🟢 при `new=0` несколько часов
- DoD: `/ops/` отражает реальное состояние

### t6c — Stealth / wait_until fix (P1)

- Попробовать `wait_until=load` или `networkidle` для slot 1 (не только commit)
- Если YouDo SPA требует JS: дождаться селектора `.task-list` или аналогичного
- Рассмотреть `playwright-stealth` (скрытие `navigator.webdriver`)
- **Смена провайдера прокси не нужна** — residential US/RU у нас уже есть (node-proxy.com)

### t6d — Alerting (P2, после t6a/b)

- Push `@FLPARSINGBOT`: «🔴 YouDo antibot — лидов нет >6h» если `health:youdo fail` > 6h подряд
- Аналогично FL если `pool_exhausted` > 30 min

### Файлы

- `src/exchange_browser_fetch.py` — antibot detection, proxy config
- `src/youdo_parser.py` — health reporting
- `src/main.py` — health output / alert hook
- `scripts/deploy-o185-t6-vps.py`

---

## Структурная причина «опять и опять»

YouDo обновляет antibot / SPA-рендер периодически → что-то в связке `wait_until` + headless перестаёт работать. После каждого обновления YouDo нужна ручная диагностика. Правильное решение:
1. **Короткосрочно (t6a/b)**: хотя бы /ops/ честный, owner видит 🔴 сразу
2. **Долгосрочно (t6c)**: stealth browser + wait_until=load/networkidle → YouDo рендерит карточки до фиксации ответа

---

## Верификация после фикса

```bash
grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -10
# ожидание: antibot_hit=1 → kind=antibot ИЛИ html_len>10000 при residential

grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -5
# ожидание: status=fail kind=antibot (t6a) ИЛИ status=ok new>0 (t6c)

SELECT count(*) FROM leads WHERE source='youdo' AND created_at > now() - interval '24 hours';
```

---

## Решение (Mechanic 2026-06-12)

### Корень (подтверждён в коде)

1. **626 bytes проходили `_validate_youdo_html`** (порог был 500) → `antibot_hit=0` в trace при status=200.
2. **Lean route на slot 1** резал stylesheet/xhr → SPA не гидратировалась; persistent context тоже всегда включал lean.
3. **`traffic_guard` / cooldown** возвращали `[]` без `fetch_error` → `health:youdo status=ok parsed=0`.

### t6a — antibot detection

- `_validate_youdo_html`: `len <= 1500` или нет карточек при `len < 8000` → `HtmlFetchError` (SPA shell) → trace `antibot_hit=1`.

### t6b — ops honesty

- `traffic_guard` и `cooldown` → `YoudoListingError` (kind=antibot в health).
- `fetch_every_n` skip → не обновляет health (предыдущий статус сохраняется).
- `main._record_source_health`: youdo `parsed=0` после ok-fetch → fail antibot (страховка).

### t6c — ingest

- Default `YOUDO_GOTO_WAIT_UNTIL=load` (slot 1); retry по-прежнему `commit`.
- **Lean off на slot 1**; persistent lean только при `YOUDO_LEAN_PERSISTENT=1` (default 0).
- **Stealth** (default on): `--disable-blink-features=AutomationControlled` + `navigator.webdriver` init_script.

## Изменённые файлы

- `src/exchange_browser_fetch.py`
- `src/youdo_parser.py`
- `src/main.py`
- `scripts/deploy-o185-t6-vps.py`
- `tests/test_youdo_traffic.py`, `tests/test_youdo_human.py`, `tests/test_exchange_browser_fetch.py`

## Как проверить

```bash
python -m pytest tests/test_youdo_traffic.py tests/test_youdo_human.py tests/test_exchange_browser_fetch.py -q
python scripts/deploy-o185-t6-vps.py
# после 1–2 циклов radar:
grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -10
grep 'health:youdo' /opt/rawlead/data/radar_site.log | tail -5
```

Ожидание после deploy:
- при SPA shell: `antibot_hit=1` **или** `html_len>10000` с карточками;
- при traffic_guard: `health:youdo status=fail kind=antibot`;
- `/ops/` 🔴 YouDo, не 🟢 при `new=0`.

---

## Lead verify post-t6 (2026-06-12 ~15:08 UTC) — **ingest NOT recovered**

| Check | Result |
|-------|--------|
| `health:youdo` | `status=fail kind=antibot` (since 14:39, latest 15:08) |
| `youdo:trace` | `traffic_guard` streak=13 · `guard_until=07:40` · cycles mostly `skip` |
| Last `fetch_start` | **14:06:37** — no successful parse after t6 deploy |
| Neon `youdo_24h` | **107** — old rows, not proof of live ingest |
| Owner | «Юду так и не появился» — **confirmed** |

**Conclusion:** t6 fixed **ops honesty** (🔴 not 🟢 at 0) but **did not bypass YouDo antibot**. Next wave **t6c** — see below.

---

## Next — t6c (→ @mechanic)

**Owner ideas (2026-06-12) — Lead triage vs current code:**

| Idea | Already in code? | Lead priority | Notes |
|------|------------------|---------------|-------|
| **`networkidle` + drop `commit` on slot 1** | Env `YOUDO_GOTO_WAIT_UNTIL` supports it; **default=`load`**; retry slot 2+ still **`commit`** | **P1 — try first** | Best match for SPA shell `html_len~626`. Set default `networkidle` on slot 1; retry → `load` not `commit`. Add **selector wait** on task cards before `page.content()`. |
| **Random delay before parse** | **`_youdo_jitter_sleep()`** already (default **2–8 s** via `YOUDO_JITTER_MS`) before launch | **P1 — extend** | Add **post-goto** jitter `1.5–3.5 s` (env `YOUDO_POST_GOTO_JITTER_MS`) before HTML read — owner suggestion still valid **after** navigation. |
| **`headless=False` / Xvfb on VPS** | Hardcoded `headless: True` in `exchange_browser_fetch.py` | **P2 — diagnostic** | Headless fingerprint is a known antibot vector. One-shot VPS test: `YOUDO_HEADLESS=0` + `xvfb-run` · compare `html_len`. **Not** permanent on 2 GB RAM without proof. |
| **`playwright-stealth` (@uberguards/…)** | **Partial:** `YOUDO_STEALTH=1` → `--disable-blink-features=AutomationControlled` + `navigator.webdriver` init_script only | **P2 — deepen** | npm lib is **Node**; we use **Python Playwright**. Options: port evasions (plugins, languages, WebGL) into `_apply_youdo_stealth`, or evaluate **rebrowser-playwright** fork. Don't add Node dep to radar. |

**Mechanic task order:** P1 (networkidle + selector + post-goto jitter) → deploy → grep DoD → if still 626 bytes → P2 headless/Xvfb A/B → P2 stealth evasions.

**DoD:** `fetch_end parsed=50` **or** `html_len>10000` + Neon `youdo` row `created_at` within 1h · `/ops/` not stuck 🔴 at `parsed=0` after successful fetch.

**Files:** `src/exchange_browser_fetch.py` · `tests/test_youdo_human.py` · `tests/test_exchange_browser_fetch.py` · deploy `scripts/deploy-o185-t6-vps.py` or successor.

---

## Mechanic t6c (2026-06-12) — P1+P2, DoD **NOT met**

### P1 (deployed)

- `networkidle` slot 1 + selector wait (`a[data-id]`, `.task-list`) + `YOUDO_POST_GOTO_JITTER_MS=1500,3500`
- Retry slot 2+: `domcontentloaded` (not `commit`)

**VPS result (16:05–16:10):** slot 1 `goto_ms≈99s` → antibot; slots 2–3 **timeout 90s** on `load`. No `html_len>10000`.

### P2 (deployed, A/B)

| Config | Result |
|--------|--------|
| `networkidle` + 150s + headless | Timeouts / antibot |
| `YOUDO_HEADLESS=0` + Xvfb `:99` | `ERR_HTTP_RESPONSE_CODE_FAILURE` за ~2.5s (headed) |
| `load` + 150s + headless + stealth evasions | **pending** — env on VPS, radar restart needed |

**Code:** `YOUDO_HEADLESS` env · Xvfb in `deploy/run-radar-site.sh` · `_youdo_wait_listing_ready()` · stealth plugins/languages · default goto timeout 150s when `load`/`networkidle`.

**VPS `.env.site` (post-deploy):** `YOUDO_GOTO_WAIT_UNTIL=load` · `YOUDO_GOTO_TIMEOUT_SEC=150` · `YOUDO_HEADLESS=1` · guard+cooldown reset in deploy script.

**pytest:** 34/34.

**Blocker:** `rawlead-radar` may need manual `systemctl start rawlead-radar` after deploy (pkill left unit `activating`). Re-run:

```bash
python scripts/deploy-o185-t6-vps.py
python scripts/smoke_youdo_t6c_vps.py   # one slot, ~3 min
```

**Next if still fail:** rebrowser-playwright fork · or YouDo ingest pause + owner alert (t6d).

---

## Lead verify (2026-06-12 ~16:30 UTC) — **ingest still broken**

| Check | Result |
|-------|--------|
| VPS env t6c | ✅ `YOUDO_GOTO_WAIT_UNTIL=load` · `TIMEOUT=150` · `POST_GOTO_JITTER=1500,3500` · `STEALTH=1` · `HEADLESS=1` |
| `fetch_start` after t6c | **16:05** (was 14:06) |
| Slot traces **16:05–16:10** | slot1 `goto_ms≈99s` antibot_hit=1 · slots 2–3 **timeout 90s** · `html_len=0` |
| `health:youdo` | 🔴 `fail kind=browser` **16:10** · cooldown **до 08:40** |
| Neon `youdo_2h` | **0** new (stale pool) |
| **DoD parsed=50** | ❌ |

**Lead verdict:** Mechanic t6c **code+deploy ✅** · **ingest DoD ❌** · YouDo остаётся блокером prod · next: rebrowser / pause ingest (t6d) · **не** ускорять fetch

---

## Mechanic анализ (2026-06-12 ~17:00 UTC) — корень CDP-detection

### Ключевые факты из кода + верификации

| Факт | Вывод |
|------|-------|
| Headed (Xvfb) дал `ERR_HTTP_RESPONSE_CODE_FAILURE` за **~2.5s** | Блок **до JS**, на HTTP/TLS уровне — stealth JS-патчи бесполезны |
| networkidle slot 1 → 99s → antibot | YouDo возвращает SPA shell быстро, потом не рендерит cards |
| Текущий stealth = `--disable-blink-features` + `navigator.webdriver` | Только JS layer — не скрывает `Runtime.Enable` CDP call |
| Residential proxy (US+RU) не помогает | Блок — не IP, а browser fingerprint на протокольном уровне |

**Корень:** YouDo проверяет **`Runtime.Enable` CDP call** — это стандартный сигнал автоматизации. Playwright делает его при каждом запуске. Никакие JS-патчи не скрывают этот вызов.

### Варианты (приоритет)

#### P0 — t6d alert (сегодня, ~30 мин, @coder)
Telegram push `🔴 YouDo antibot >6h`. Независим. Уже описан выше.

#### P1 — patchright (завтра, ~2 ч, @coder)
Python drop-in замена `playwright`, патчит `Runtime.Enable` CDP на уровне протокола — именно то, что детектирует YouDo.

```bash
pip install patchright
patchright install chromium
```

Diff в коде — **одна строка** в `exchange_browser_fetch.py`:
```python
# было: from playwright.sync_api import sync_playwright
# стало: from patchright.sync_api import sync_playwright
```
- Тот же API, минимальные правки
- Не Node.js, работает на 2GB VPS
- Активно поддерживается (2025–2026)

#### P2 — camoufox (если patchright ❌, ~4 ч, @coder)
Firefox-based Python антибот браузер. Другой API — больше правок в `exchange_browser_fetch.py`.

#### P3 — YouDo JSON API hunt (параллельно)
Из кода: `_should_abort_youdo_request` пропускает `xhr/fetch` к `youdo.com`. YouDo SPA делает XHR к своему API. Если перехватить network на VPS при успешном fetch — можно забрать карточки через `httpx` без браузера.
Диагностика: `page.on('request', ...)` + лог XHR при каждом listing fetch.

#### НЕ рекомендовать
- **rebrowser-playwright** — Node.js, Python-версии нет
- **Смена прокси** — уже подтверждено, не помогает
- **headless=False постоянно** — Xvfb fail за 2.5s подтвердил, дело не в headless

### Рекомендованный план

| # | Задача | Исполнитель | Когда |
|---|--------|-------------|-------|
| 1 | t6d: Telegram alert YouDo fail >6h | @coder | сегодня |
| 2 | patchright PoC: `pip install patchright` + одна правка + smoke на VPS | @coder | завтра |
| 3 | Если patchright ✅ → полный deploy + тест | @coder | завтра |
| 4 | Если patchright ❌ → camoufox или API-hunt | @coder / @mechanic | +1 день |

**Owner 2026-06-12:** «давай пробовать P1» → **§ O189-YOUDO-PATCHRIGHT** in `CODER_PROMPT.md`

**Файлы для patchright:** `src/exchange_browser_fetch.py` · `requirements.txt` · `scripts/deploy-o189-youdo-patchright-vps.py`

---

## Coder verify O189 (2026-06-12 ~09:24 UTC) — **patchright PoC ❌**

| Check | Result |
|-------|--------|
| Deploy | ✅ `deploy-o189-youdo-patchright-vps.py` · `YOUDO_BROWSER=patchright` · `patchright install chromium` · guard reset |
| pytest | ✅ **21/21** browser/youdo tests |
| Smoke VPS | ❌ `smoke_youdo_t6c_vps.py` — **Terminated** after ~9 min (goto 150s + selector wait on empty page) |
| patchright launch | ✅ driver + chrome-headless-shell on VPS |
| `html_len` | ❌ **39** — `<html><head></head><body></body></html>` (antibot shell, no cards) |
| `parsed=50` | ❌ |
| Neon `youdo` 1h | ❌ (not checked — listing never parsed) |
| radar log 17:22 | `html_len=39` · `antibot_hit=1` · one cycle: `Playwright Sync API inside asyncio loop` |

**Verdict:** P1 patchright **deploy+code ✅** · **ingest DoD ❌** — CDP patch did not restore listing cards. **Next:** P2 camoufox or P3 API-hunt · **do not** loop proxy/headless tweaks (per O189).

---

## Lead verify O190 t0b (2026-06-12) — **camoufox install ✅ · launch ❌**

| Check | Result |
|-------|--------|
| `pip camoufox` + `camoufox fetch` | ✅ v0.4.11 · bin in `~/.cache/camoufox` |
| `YOUDO_BROWSER=camoufox` | ✅ `.env.site` |
| Deploy | ✅ `o190_camoufox_deploy_ok` |
| Playwright during deploy | ⚠️ **missing host dependencies** — `playwright install-deps` not run |
| Smoke | ❌ `XPCOMGlueLoad error` — Firefox/camoufox **не стартует** на VPS |
| Ingest DoD | ❌ (browser never launched) |

**Verdict:** Not YouDo antibot yet — **VPS lacks Firefox/GTK system libs**. **→ O190-t0c** `playwright install-deps` on VPS, then re-smoke.

---

## Coder verify O190 t0c (2026-06-12) — **install-deps ✅ · launch ✅ · html_len ⏳**

| Check | Result |
|-------|--------|
| `deploy-o190-youdo-camoufox-vps.py` | ✅ added `playwright install-deps firefox` + `DEBIAN_FRONTEND=noninteractive` |
| Deploy | ✅ `o190_camoufox_deploy_ok` · apt libs already present (`libgtk-3-0t64`, `libxcursor1`, `xvfb`, …) |
| Browser launch | ✅ **no `XPCOMGlueLoad`** — camoufox reaches `Page.goto` |
| Smoke `html_len` | ❌ `NS_ERROR_PROXY_CONNECTION_REFUSED` on **slot[0]** (8 alive slots) — **proxy**, not antibot/launch |
| Ingest DoD | ⏳ blocked until proxy slot works or smoke tries next slot |

**Verdict:** t0c **blocker cleared** (OS deps + Firefox launch). **Next:** proxy slot health or smoke slot-failover → then judge `html_len`/antibot (O190 t0d).

---

## Lead verify O190 t0c (2026-06-12 ~18:09 UTC) — **✅ launch · ❌ ingest**

| Check | Result |
|-------|--------|
| `install-deps` in deploy | ✅ `libgtk-3-0t64`, `libxcursor1` on VPS |
| Camoufox launch (VPS python) | ✅ `launch_ok 135.0.1-beta.24` |
| Smoke (Lead re-run) | ❌ **`NS_ERROR_PROXY_CONNECTION_REFUSED`** · slot[0] of 8 · browser **starts**, goto fails |
| Radar trace ~18:08 | `html_len=0` `status=Error` · earlier `Sync API inside asyncio loop` |
| Ingest DoD | ❌ — **not antibot yet** · proxy/path before `html_len` verdict |

---

## Coder O190 t0d (2026-06-12) — **slot failover + Playwright thread routing**

| Change | Detail |
|--------|--------|
| `smoke_youdo_t6c_vps.py` | Uses `fetch_listing_html_browser_slots` (not `slots[0]` only); removed `YOUDO_SLOT_RETRY_ON_TIMEOUT=1` cap |
| `_is_youdo_slot_retryable` | `NS_ERROR_PROXY_CONNECTION_REFUSED` / proxy tunnel errors → next alive slot |
| `_fetch_youdo_ephemeral` | Routes through `_playwright_sync` when not on dedicated Playwright thread |
| `fetch_youdo_detail_snapshot` | Same — fixes radar `Sync API inside asyncio loop` on delist/detail paths |
| pytest | **25/25** `test_exchange_browser_fetch` + `test_youdo_human` |

**Next:** ~~deploy~~ **Lead verify 2026-06-12:** code in repo ✅ · pytest **25/25** local ✅ · **VPS deploy ❌** (`connection_refused` marker absent on VPS; last `fetch_end` 18:20 asyncio) · **→ deploy `exchange_browser_fetch.py` + restart radar**

---

## Lead verify O190 t0d (2026-06-12) — **code ✅ · deploy ✅ · ingest ⏳**

| Check | Result |
|-------|--------|
| Local pytest | ✅ **25/25** |
| Repo changes | ✅ smoke slot failover · `_playwright_sync` on ephemeral/detail |
| VPS deploy | ✅ `deploy-o190-t0d-vps.py` · `connection_refused`=1 · `_playwright_sync`=12 · radar **active** |
| Smoke | ✅ `html_len=267684` data-id **50** (camoufox · 25 slots) |
| Radar asyncio | ✅ last error **18:20** (pre-deploy) · **no asyncio after 18:40 deploy** |
| Radar listing ingest | ⏳ no `fetch_start` after deploy — `fetch_every_n` skip · `health:youdo fail kind=browser` @18:49 |
| Post-deploy browser | ✅ **18:41** `html_len=267684` (delist/detail path) |
| Ingest DoD | ⏳ **wait 1–2 cycles** for `fetch_end parsed>=50` · smoke proves fetch works |

---

## Coder O190 t0e (2026-06-12) — **listing asyncio thread guards**

| Change | Detail |
|--------|--------|
| `_get_playwright` / `_get_youdo_playwright` | Route `sync_playwright().start()` only on dedicated `rawlead-playwright` thread |
| `_launch_youdo_persistent_context` | Thread guard via `_playwright_sync` |
| `fetch_listing_html_browser_*_wall_clock` | Top-level `_playwright_sync` entry (radar `_fetch_source` worker → PW thread) |
| Camoufox listing slot 1 | Ephemeral launch (same path as delist detail — proven on radar) |
| pytest | **26/26** `test_exchange_browser_fetch` + `test_youdo_human` |
| Deploy | `scripts/deploy-o190-t0e-vps.py` → traffic_guard reset · radar restart |

**DoD verify (Lead):** `grep 'fetch_end.*parsed=' /opt/rawlead/data/radar_site.log | tail -5` · `parsed>=50` · Neon `youdo` 1h > 0
