# FL: proxy pool_exhausted — лампа 🔴 при живом parsed=30

**Дата:** 2026-06-14  
**Симптом (owner):** FL «отвалился» снова · YouDo стабилен · FL падает постоянно  
**Triage:** Lead · VPS `radar_site.log` + `probe_all_proxies.py`

---

## Факты (VPS 2026-06-14 ~01:00 MSK+8)

| Метрика | Значение |
|---------|----------|
| `rawlead-radar` | **active** |
| `listing:fl` | **parsed=30** стабильно (парсер **не** в нуле) |
| `fresh` | **0** почти каждый цикл · редко 1–2 |
| `fetch:fl` | **`pool_exhausted slot=1/4 alive=0/4`** — с 00:12 UTC+3 каждый цикл |
| `health:fl` | `status=ok` · `new=0` |
| `listing:fl parsed=0` | последний раз **2026-06-08** (не текущий инцидент) |

**Вывод:** FL **листинг качается**, но **все 4 FL-прокси в ban-table** → ops/TG шум «pool exhausted» · в ленте **нет новых** FL (fresh=0).

---

## Корень

1. **Пул FL_PROXY_URLS = 4 шт** (`.env.site`): `185.147.131.15`, `194.226.236.204`, `194.226.236.197`, `212.102.151.153`
2. **194.226.x** — probe FAIL было из‑за **неоплаты** (owner оплатил 2026-06-14) · **не удалять** из пула
3. **Antibot/403** → бан слота TTL **3600s** (`EXCHANGE_PROXY_BAN_TTL_SEC`)
4. Subprocess при `alive=0` → **parsed=30 держится** (direct/browser без прокси), но ops 🔴 `pool_exhausted`

### «Один улетел — остальные следом» — проверка кода (owner 2026-06-14)

**Нет магии:** бан **per-proxy** ключ `fl:host:port` — один слот **не** банит соседей автоматически.

**Но каскад за минуты — да**, два механизма:

| Механизм | Как |
|----------|-----|
| **httpx fallback за один fetch** | FL: browser subprocess fail → `_fetch_listing_html_requests` → `exchange_get` крутит **все слоты** в цикле · **2×403** (`EXCHANGE_PROXY_HTTP_STRIKES=2`) → `_ban_url` → `advance_failover` → следующий · **все 4 могут улететь в одном цикле** |
| **Мёртвый прокси** | **3** connect timeout (`EXCHANGE_PROXY_STRIKES=3`) → бан · 194.226.x гасят пул быстрее |
| **YouDo иначе** | listing **без httpx fallback** (`youdo_parser` browser-only) · slot retry только на timeout — **меньше шанс сжечь весь пул за раз** |

**FL vs YouDo сейчас:**

| | FL | YouDo |
|--|-----|-------|
| Primary pool | `FL_PROXY_URLS` DC only | `YOUDO_PROXY_URLS` (O191: DC→RU если задеплоен) |
| Fallback tier | **нет** | RU residential на **slot_retry** (не первый слот) |
| httpx multi-ban | **да** (после browser fail) | **нет** (browser-only) |
| TTL выход | **да**, 1ч auto `_is_banned` expiry | то же |

**Owner proposal (принять в канон):**
- FL: **DC primary** · при `alive==0` на DC → **временно residential** (наш node-proxy RU) · через час DC сами оживают
- YouDo: **DC первый слот** · residential **только на ban/retry** — не держать listing постоянно на res (экономия) — **= O191-w**, довести/проверить deploy

---

## Immediate ops (2026-06-14)

- `clear-vps-proxy-bans.py` ✅
- ~~Убрать 194.226~~ **откат** — owner: прокси рабочие, были неоплачены · **восстановлено 4/4** (`patch-vps-exchange-proxies-env.py`) · `alive=4/4`

---

## Code fix (→ @coder)

| # | Fix | Файлы |
|---|-----|-------|
| 1 | **FL two-tier proxy:** `FL_PROXY_URLS` (DC) → если `alive==0` → `FL_PROXY_URLS_RESIDENTIAL` или tail `YOUDO_PROXY_URLS` · **не банить res** при DC antibot (отдельный source или skip ban) | `exchange_proxy.py` · `fl_parser.py` |
| 2 | **FL listing: multi-slot browser retry** (как YouDo) · **убрать/ограничить httpx multi-ban cascade** — не жечь 4 DC за один fallback | `exchange_browser_fetch.py` · `fl_parser.py` |
| 3 | **YouDo O191 verify:** DC slot #1 · RU только `slot_retry` · `YOUDO_ONE_SLOT_PER_CYCLE=1` | env + `youdo_parser.py` |
| 4 | Ops: `parsed>=25` без `fetch_error` → не 🔴 только из-за `pool_exhausted` на DC tier | `radar_status.py` |

**Не делать:** удалять прокси из env без owner · все 4 DC слота рабочие после оплаты.

**Env sketch:**
```env
FL_PROXY_URLS=...          # DC only, 2-4 slots
FL_PROXY_URLS_RESIDENTIAL=...  # node-proxy RU, fallback when DC alive==0
YOUDO_PROXY_URLS=DC_SLOT,...RU_1,...,RU_N   # O191 order
YOUDO_ONE_SLOT_PER_CYCLE=1
```

**Rollback:** `FL_LISTING_SUBPROCESS=0` · RU-only YouDo = старый `patch-vps-youdo-proxy-env.py`

---

## Verify

```bash
grep listing:fl /opt/rawlead/data/radar_site.log | tail -5
# ожидание: alive=2/4+ · fresh>=0 периодически · нет спама pool_exhausted каждый цикл
```

**Resolution (2026-06-14):** код tier-2 задеплоен · smoke `alive=4/4` после ~10:58.  
**Recurring (2026-06-15 ~14:10 UTC+3):** снова **`parsed=0`** · 4 DC banned (`subprocess bad json`) · res fetch ok но **parsed=0** · **0 inserts / 2h** · O222 на VPS **не спасает** (см. ниже).

---

## Recurrence 2026-06-15 (~16:00 MSK triage)

| Метрика | Значение |
|---------|----------|
| `listing:fl` | **`parsed=0`** с ~14:31 (до этого **parsed=30** до 14:10) |
| `fetch:fl` | DC **alive=1/4** · 3/4 в ban-table · res **alive=25/25** |
| Ban reason | `browser:fl subprocess bad json: Expecting value: line 1 column 2` |
| `fetch:fl hard_reset` в log | **0 строк** — wipe/restart flag не виден ops |
| Neon | **0** FL inserts за 2h |

**Почему O222 «не работает» для owner:**

1. O222 **не снимает бан** с прокси — TTL **1ч** или ручной `clear-vps-proxy-bans.py`.
2. За **4 цикла** (~40 мин) сгорают **все DC** (по 1 бану/цикл — каскад в одном цикле остановлен, но пул всё равно кончился).
3. **Residential** качает страницу, но **parsed=0** — antibot/пустой HTML, не «нет новых заказов».
4. `fl_hard_reset()` из `_fl_browser_antibot_fail` **без `storage`** → `restart_source_fl` **не ставится** · systemd **не** рестартует.
5. **O215** (DC→res tier, res no-ban, lamp) — **code ready, не на VPS**.

**Immediate ops:** `python scripts\clear-vps-proxy-bans.py` → 2–3 цикла → ждать `parsed=30`.

**Code → @coder P0 § O233-FL-AUTO-RECOVERY** (см. `CODER_PROMPT`).

---

_ Lead Architect · triage · clear bans applied · code deploy ✅ 2026-06-14 _
