# 2026-06-16 — YouDo antibot + Camoufox worker crash, ops funnel vs card mismatch

**Статус:** 🟡 **O254b + mechanic deploy ✅** (~05:20 UTC) · owner smoke · antibot 1701b — watch ingest

---

## Prod stack (важно)

| Источник | Browser на VPS |
|----------|----------------|
| **YouDo** | **Camoufox (Firefox)** · `YOUDO_BROWSER=camoufox` · listing через subprocess `youdo_fetch_worker.py` |
| **FL / Kwork** | Playwright **Chromium** |

YouDo **не** на Playwright Chromium. Ошибки `Browser.close: Connection closed` — про **camoufox/Firefox session**, не про FL headless Chrome.

---

## Симптом (owner)

- Последний заказ YouDo ~**6 ч** (lag **391 мин**).
- Карточка: 🔴 antibot · воронка: зелёные лампы (ложный OK — см. ниже).

---

## Факты VPS (`radar_site.log`, MSK)

| Время | Событие |
|-------|---------|
| **05:35** | Последний ok: `new=19 parsed=50` |
| **06:00+** | `html_len=0` · camoufox worker crash |
| **06:02–06:04** | `html_len=1701 status=200` — SPA-каркас без карточек (soft antibot) |
| **06:13+** | `Browser.close: Connection closed` — zombie camoufox worker |
| **09:40–11:35** | `traffic_guard streak=3→4` |

---

## Корень

1. **Camoufox subprocess** падает / обрывает session → `html_len=0`.
2. **Cooldown + traffic_guard** накапливаются — fetch блокируется часами.
3. **Старый `restart_source`** только `close_all_browser_contexts` — **не** трогал camoufox worker в subprocess.
4. **Ops кнопка** мёртвая (JS hydrate без delegation).

---

## O254 ✅ code (2026-06-16)

- `youdo_hard_reset()` + **`youdo_browser_teardown()`**: contexts + `_abort_playwright_worker` + kill camoufox/youdo_fetch_worker orphans
- Ops кнопка: hard reset + `systemctl restart rawlead-radar`
- Auto: `YOUDO_HARD_RESET_FAILS=3`
- JS event delegation на `#rl-ops-exchanges`
- pytest `test_o254_youdo_restart.py` **5/5**

**Deploy ✅:** `youdo_parser.py` · `exchange_browser_fetch.py` · `owner_admin.py` · `main.py` · `ops-pult.js` · api+radar restart

---

## Post-deploy triage (2026-06-16 ~12:50 MSK)

| Проверка | Факт |
|----------|------|
| O254 на VPS | ✅ `youdo_browser_teardown` в `exchange_browser_fetch.py` |
| `ops-pult.js` на prod | ✅ `bindRestartSourceDelegation` в https://rawlead.ru/ops/static/ops-pult.js |
| POST `/ops/control` в nginx | **0** за сегодня — клики владельца **не доходят** до API |
| `fetch:youdo hard_reset` в journal | **нет** — restart через пульт не срабатывал |
| YouDo после `restart_radar_youdo_cycle.py` | **12:50** снова `Connection closed` · `html_len=0` · `parsed=0` |
| Последний ok | **05:35 MSK** `new=19 parsed=50` |

**Кнопка (гипотеза P0):** вкладка `/ops/` открыта **до** deploy → браузер держит **старый** `ops-pult.js` без delegation (polling `/ops/funnel` JS не перезагружает). **Smoke:** Ctrl+Shift+R → клик → в nginx должен появиться `POST /ops/control`.

**Ingest (корень P0):** Camoufox worker падает независимо от cooldown/guard — O254 infra не лечит driver crash.

---

## Mechanic triage (2026-06-16 ~13:30 MSK)

### Корень ingest (не SQLite, не O254 teardown)

| Факт | Значение |
|------|----------|
| VPS playwright | **1.60.0** |
| VPS camoufox | **0.4.11** (latest PyPI) |
| Симптом | `html_len=0` · `Browser.close: Connection closed` · goto ~2–3s |
| example.com | ✅ camoufox ok (559 bytes) |
| youdo.com | ❌ Playwright FF driver crash |

**Причина:** Playwright **≥1.60** требует `pageError.location.url` в Juggler-событии `Page.uncaughtError`. Camoufox 0.4.11 **не** шлёт `location` → uncaught JS на youdo.com убивает Node driver → `Connection closed`. Не antibot SQLite, не zombie worker (O254 teardown ok).

Upstream: [camoufox#617](https://github.com/daijro/camoufox/issues/617) · fix в Juggler PR #625 — **ещё не в PyPI 0.4.11**.

### Решение (mechanic) — playwright pin

1. **`requirements.txt`:** `playwright>=1.40.0,<1.60.0` (рекоменд. **1.58.0** на VPS)
2. **`_check_camoufox_playwright_compat()`** — явная ошибка вместо cryptic `Connection closed`
3. **Camoufox:** skip `warm_home` (youdo.com/ триггерит тот же crash)
4. **`restart_radar_youdo_cycle.py`:** `youdo_browser_teardown()` перед stop
5. Slot retry: `connection closed` → retryable

**Статус playwright pin:** ✅ VPS **1.58.0** · deploy repo

---

## Mechanic O254c (2026-06-16 ~13:45 MSK) — пул не уходит с мёртвого IP

### Симптом (owner 13:25–13:30)

- `html_len=1701 status=200` · SPA shell без карточек · `new=0 parsed=0`
- Прокси **185.147.131.15:8000** slot=1/26 · 3 slot-retry fail на одном цикле
- Last ok: **05:35 MSK** `new=19`

### Корень (пул)

**YouDo browser antibot** вызывал только `invalidate_browser_slot()` — **без** `_ban_url()` и смены `active_slot`. FL уже банит через `_fl_browser_antibot_fail`. Итог: мёртвый DC-слот оставался primary каждый цикл.

Дополнительно: `_fetch_youdo_camoufox_async` логировал `antibot_hit=0` при `html_len=1701` (валидация только в parent subprocess) → ложный `status=200` в trace.

### Решение O254c ✅

| Изменение | Файл |
|-----------|------|
| `youdo_browser_slot_fail()` — ban + advance active_slot | `exchange_proxy.py` |
| `clear_youdo_source_bans()` | `exchange_proxy.py` |
| `_youdo_browser_slot_fail()` на каждый slot fail | `exchange_browser_fetch.py` |
| `_validate_youdo_html` в camoufox async (честный trace + worker rc≠0) | `exchange_browser_fetch.py` |
| `restart_radar_youdo_cycle.py` — clear youdo bans + teardown | `scripts/` |

### VPS verify (2026-06-16 ~13:42)

```text
youdo_bans 1 · youdo:185.147.131.15:8000 reason=browser:SPA shell without task cards
active_slots {"youdo": 1, ...}   # был 0 → смена слота
playwright 1.58.0 · camoufox 0.4.11
smoke slot 2 (212.102.151.153) → servicepipe SPA (exhkqyad), не ingest ok
fetch_end 13:41 kind=browser · 13:43 kind=antibot (cooldown 28 min)
```

**Ingest `kind=ok`:** ⏳ пул ротирует · но **все** прокси сейчас servicepipe SPA — отдельная волна (residential / wait strategy).

### Как проверить

```bash
cd /opt/rawlead
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python scripts/restart_radar_youdo_cycle.py
# bans + active slot:
sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python -c \
  "from exchange_proxy import exchange_primary_proxy_url; print(exchange_primary_proxy_url('youdo'))"
grep 'youdo:trace.*fetch_end' data/radar_site.log | tail -3
# expect kind=ok · new>0 когда residential обходит servicepipe
```

**Статус:** 🟡 **O254c deploy ✅** · пул ротирует · ingest ok — watch residential slot

**O254c files:** `exchange_proxy.py` · `exchange_browser_fetch.py` · `restart_radar_youdo_cycle.py` · `tests/test_exchange_proxy_cascade.py` · `tests/test_youdo_human.py` · `scripts/deploy-o254c-youdo-proxy-failover-vps.py`

---

## O259 — DC carousel (owner 2026-06-16)

**Гипотеза:** SPA shell на **одном DC** · hard_reset с тем же IP не помогает.

**Решение (Coder):** `YOUDO_DC_PROXY_URLS` = 4 DC как FL · rotate+bann на SPA до hard_reset · RU tier без изменений.

**Spec:** [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § O259

**Mechanic:** только если после O260 deploy все 4 DC → SPA (fingerprint/camoufox, не IP).

---

## O260 — DC-first canon (owner 2026-06-16)

**Проблема:** listing стартует с node-proxy (slot 6/26) — жжёт residential · O259 крутит FL DC только на retry.

**Канон:** slot 1 = DC (4 FL) · node/RU только `dc_alive=0/4` · max 1 node/fetch (общий traffic quota) · баны летят на DC → **hard reset + другой DC**, не node · после TTL → `dc_restored`.

**Spec:** [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § O260

---

## O262e — owner correction (2026-06-17)

**Owner:** YouDo **не появился** в ленте — ранее ошибочно «появился».

| Факт | Значение |
|------|----------|
| Ingest сейчас | 🔴 `html_len=1712` · `antibot_hit=1` · `parsed=0` |
| DC pool | `dc_alive=0/4` · RU node — тот же SPA shell |
| Last ok | **14:29:53** `parsed=50` **`new=0`** |
| Last new | **11:46** `new=11` — в `/lenta/` не видно |
| O262–O262d | ✅ deployed · **не помогают** на antibot shell |

**Действие:** § **O262e** in `CODER_PROMPT.md` · **@mechanic** triage (debug HTML + PG visibility count) → **@coder** fix.

---

## Mechanic triage O262e (2026-06-17 ~16:10 MSK)

### Разделение симптомов

| Вопрос | Ответ |
|--------|--------|
| Ingest=0? | **Да** — с **14:52** каждый цикл `html_len=1712` · `antibot_hit=1` · `parsed=0` |
| Есть youdo в PG? | **Да** — total **3849** · visible **474** · visible в 7d окне **460** |
| Почему owner «нет в ленте»? | **Два фактора:** (1) ingest с утра 🔴 servicepipe; (2) свежие insert **24h** почти все `is_visible=false` (L1 `feed_visible`) — last **visible** created **03:43 GMT** (~06:43 MSK) |
| O262–O262d помогают? | **Нет** на 1712b — в HTML **0×** «Показать списком», **0×** `data-id` |

### Debug HTML (`youdo_antibot_1781682810.html`)

- **1712b** · `servicepipe.ru` loader · meta refresh `/exhkqyad` · **не** YouDo SPA
- Это **ServicePipe challenge**, не map/list UI

### Единственный ok за день (**14:29:53**)

```
DC slot1–2 → 1712b fail (~98s goto)
slot_retry → gate.node-proxy.com:10000 (RU)
goto_ms=17002 · html_len=271507 · clicked=1 · parsed=50 · new=0 (все dup)
```

RU node **может** обойти challenge; DC и другие RU сейчас снова 1712b.

### PG / feed

- `PUBLIC_FEED_SOURCES` includes `youdo` ✅
- visible_24h=**15** · recent rows (06:30 GMT) `is_visible=false` categories design/dev/marketing
- **→ visibility audit** отдельно от ingest (CODER § O262e candidate #4) если после ok ingest owner всё ещё не видит

### Mechanic fix ✅ deploy (2026-06-17 ~16:15 MSK)

1. **`_youdo_html_is_servicepipe`** + wait до 30s (`YOUDO_SERVICEPIPE_WAIT_SEC`) после goto
2. **Fast-fail** `ServicePipe antibot challenge` — не жечь 98s selector wait
3. **`_validate_youdo_html`** / `_looks_like_antibot` — явный marker `servicepipe`
4. pytest `test_o262e_youdo_servicepipe.py` **5/5** · `scripts/deploy-o262e-youdo-servicepipe-vps.py` · **deploy ✅ ~16:08 MSK** (fix v2: short-shell poll, skip 98s selector wait)

**Verify:** next `fetch:youdo` → log `stage=servicepipe_wait` / `servicepipe_cleared` OR fast fail · goto_ms **<45s** per slot.

**→ O262f** owner P0 full recovery (§ CODER_PROMPT).

---

## O262f — ✅ deploy listing recovery (2026-06-17)

**Listing:** RU early fallback + carousel `YOUDO_RU_RETRY_MAX=5` · `YOUDO_SERVICEPIPE_EARLY_RU=1` · deploy ✅
**Результат:** listing проходит через RU (~255KB html) · `parsed=50` · но `detail:short` блокировал L1 → **O262g**

---

## O262g — detail-page ServicePipe → stuck leads (2026-06-17 ~20:00 MSK)

**Симптом:** YouDo нет в ленте больше суток. Последний visible лид: 2026-06-15.

**Причина (Lead диагноз):**
- Listing: ✅ через RU-ноду
- **Detail pages** (`youdo.com/t/ID`): ТОЖЕ ServicePipe ~1700b
- `_youdo_detail_short_skips_l1`: `detail_ok=False AND len(snippet)<300` → skip L1 → `is_visible=false`
- ~73 stuck leads: new=49 (16.06), new=13 (17.06 11:20), new=11 (17.06 11:46) — всё `is_visible=false`

**Hotfix Lead (19:27 MSK):**
- `YOUDO_DETAIL_FETCH=0` → `.env.site` + `systemctl restart rawlead-radar`
- `detail:short` прекратились (последний: 19:27:36) ✅
- Новые YouDo лиды: L1 запустится на listing snippet (detail_ok=None → skip check passes)

**Ещё нужно (@coder O262g):**
- `drain_l1_backlog` находит 0 YouDo лидов — расследовать почему
- Re-trigger L1 для ~73 stuck leads с `is_visible=false`
- DoD: `pipeline:L1 youdo:id=xxx visible=1` в логе · YouDo лиды в `/lenta/`

**Deploy ✅ O262g** — requeue 500/1000 · но owner smoke: «час назад» = старые OK после requeue, не ingest.

---

## O262h — wall-clock race, ingest 0 (2026-06-17 ~20:23 MSK)

**Симптом:** лента YouDo «час назад» — requeue поднял старые лиды; **свежего ingest нет весь день**.

**Факты:** `20:12:06` wall-clock 510s → main `скачано 0` · `20:12:54` `parsed=50` orphan · pipeline не получил projects.

**→ @coder:** § O262h in `CODER_PROMPT.md`

---

## O266 — sticky session (owner 2026-06-18)

**Owner:** после пробоя ServicePipe **не закрывать вкладку** — периодически **reload** listing (см. `fetch_every_n=4` ~15–20 мин).

**Сейчас:** каждый цикл = новый `youdo_fetch_worker` subprocess + cold `goto` → снова 1712b.

**→ @coder:** § **O266-YOUDO-STICKY-SESSION** in `CODER_PROMPT.md` · long-lived worker · `sticky_reload` trace · narrow hard_reset teardown.

**Coder deliverables (2026-06-18):** `scripts/youdo_sticky_worker.py` · sticky manager in `exchange_browser_fetch.py` · `tests/test_o266_youdo_sticky_session.py` · `deploy-o266-youdo-sticky-vps.py` · env `YOUDO_STICKY_SESSION=1`.

**DC pool (O264):** `185.147.128.237` · `185.147.130.67` · RU fallback off.

---

## O267 — browser regression (owner 2026-06-18)

**Owner:** «раньше YouDo нормально работал, падал периодически» → подозрение на **холодный Camoufox** без cookies после O190–O266.

**→ @coder:** § **O267-YOUDO-BROWSER-REGRESSION** — persistent `user_data_dir` per DC · sticky worker reuse · `networkidle` · SP wait 90s · soft fail on 1712b (no instant ban/hard_reset) · **без RU**.

**Coder deliverables (2026-06-18):** `youdo_sticky_worker.py` persistent profile · `exchange_browser_fetch.py` gate ephemeral slot1 · `YOUDO_SOFT_SERVICEPIPE_BAN` · `tests/test_o267_youdo_persistent_profile.py` · `deploy-o267-youdo-regression-vps.py`.

**Prod result:** ❌ reload trap — profile cookies → skip goto → 150s reload on 1712b · last ok **10:04** via **ephemeral** on **`194.226.236.197`**, not O264 IPs.

---

## O268 — recovery package (owner 2026-06-18)

**Owner:** «раньше норм» · RU ~300MB · «может профиль поменять» · «давай всё».

**Lead plan:** § **O268** in `CODER_PROMPT.md` — (A) wipe profile on SP · no reload-on-poisoned-cookies · (B) ephemeral-first like 10:04 · (C) reload fast-fail 15s · (D) restore 4 FL DC incl. `.197` · (E) RU burst max 2/day last slot only · (F) profile generation rotate.

**Coder deliverables (2026-06-18):** `exchange_browser_fetch.py` ephemeral-first + RU burst + profile wipe · `youdo_sticky_worker.py` no cookie→reload · `exchange_proxy.py` FL DC fallback · `tests/test_o268_youdo_recovery.py` · `deploy-o268-youdo-recovery-vps.py`.

**Deploy ✅ Lead verify 2026-06-18:** VPS active · 4 DC `alive=4/4` · ingest **14:26** `parsed=50`.

**Golden baseline 2026-06-19:** стабильный ingest · backup profile+log → [`2026-06-19-youdo-o268-breakthrough.md`](2026-06-19-youdo-o268-breakthrough.md) · **откат сюда** при регрессе.

---

## Backlog

- **O262 follow-up:** O262b–O262d ✅ · ingest блокер = **antibot shell 1712b** → **@mechanic** если unban не помог
- **O260** (@coder): DC-first · node only fallback · dc_restored after TTL · § O260
- **O254b** (@coder): cache-bust `ops-pult.js?ver=` · повторный `bindRestartSourceDelegation()` после `hydrateDashboardFallback`
- **Funnel honesty:** красить fetch/parsed при `lag_min` > 60
- **O255** (@coder): `YOUDO_HARD_RESET_FAILS=1` + rate cap (min 120s между reset, max 8/час → traffic_guard)
