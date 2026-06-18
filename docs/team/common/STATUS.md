# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

**Next:** **O280** WP→Next · O200 ⏸ · rode51.ru DNS

**Откат до переноса:** ветка `o280/pre-wp-to-next-migration` · тег `backup/pre-wp-next-2026-06-18` · локальный бэкап `D:\Backups\uisness\2026-06-18_2348`

---

## O280 WP → Next UI — 🔴 P0 до ads (2026-06-18)

**Handoff:** [`WP_TO_NEXT_HANDOFF.md`](../architect/WP_TO_NEXT_HANDOFF.md) · пакет `web/` · API не трогаем.

---

## O272 quiz→feed tags sync — ✅ prod (2026-06-18)

**Fix:** `rawlead-tags-imported` → `reloadTagsFromSync()` в feed + cabinet · `pytest` **4/4** · theme deploy ✅

**Owner smoke:** `/lenta/` → квиз без reload → замочки снимаются · при старом кэше JS — один раз **Ctrl+Shift+R**

---

## O271 VPS Postgres migration — ✅ cutover · login fix (2026-06-18)

**Prod DB:** `DATABASE_URL` → **127.0.0.1** (local Postgres) · Neon только в `NEON_DATABASE_URL` (архив, не используется).

**Post-cutover:** `rawlead-bot-poll` **не перезапускался** → бот ходил в Neon → `bot_auth:fail db error` · **fix:** `systemctl restart rawlead-bot-poll` **07:54 UTC**.

**Owner seed:** uuid `#1` · `tg_user_id=1342741103` · `plan=owner`.

**Smoke:** API `/health` ok · повторить TG login после restart bot-poll.

---

## O270 Neon quota — 🔴 (superseded by O271 migrate)

**Symptom:** `exceeded the compute time quota` — purge dry-run ❌ · O200 regen ❌.

**Autocleanup:** `rawlead-purge-leads.timer` **active** · **03:15** deleted **607** old + **92** delisted.

**Owner:** [console.neon.tech](https://console.neon.tech) → Billing/upgrade · после green: `purge_old_leads.py --apply` на VPS.

**→ @coder:** § O270 circuit breaker + `probe_neon_storage.py`.

---

## O268 YouDo recovery — ✅ deploy · ⏳ ingest (2026-06-18)

**Coder ✅:** ephemeral-first · profile wipe · reload 15s · 4 DC · RU burst max 2/day · pytest **40/40** · `deploy-o268` VPS **active**.

**Lead verify 2026-06-18 ~14:27:** force restart ✅ · fetch **14:19→14:26** · **`outcome=ok parsed=50` tier=dc** · ephemeral carousel (slots 2–5) · **ingest восстановлен** · RU не нужен.

**Watch 6h:** `ingest done=50` OR `html_len>100000` · `ru_burst=n/2` если дойдёт до RU.

---

## O267 YouDo browser regression — ✅ code · ❌ prod DoD → O268 (2026-06-18)

**Coder ✅:** persistent profile `data/youdo_{hint}/` · sticky worker `launch_persistent_context` · gate ephemeral slot1 · `networkidle` · SP wait 90s · `YOUDO_SOFT_SERVICEPIPE_BAN` · pytest **30/30** · `deploy-o267` VPS **active**.

**Lead verify 2026-06-18:** pytest **30/30** · VPS env ✅ · profile dir `data/youdo_128.237…` **создан** (cookies.sqlite) · fetch **13:16** на `128.237` tier=dc · **`sticky_goto`/ingest=50 пока нет** · 13:03 пачка 1712b (pre-fetch burst).

**Watch 24h:** `sticky_goto html>100k` OR `ingest done=50` OR `sticky_reload goto_ms` < cold.

---

## O218 Playwright quiz E2E — ✅ prod green (2026-06-18)

**Зачем:** автоматические прогоны квиза j1–j7 перед рекламой — разные пользователи, desktop + mobile 390, без смешения localStorage.

**Сделано Coder:**
- `scripts/preprod_playwright/quiz_e2e.py` + `quiz_ui.py` — 7 сценариев (j5 = Monica + anon)
- `tests/test_o218_quiz_e2e.py` — import smoke; prod via `RAWLEAD_O218_E2E=1`
- runbook `PREPROD_STRESS_RUN.md` § O218
- **O218a fix:** `add_init_script` + goto `/lenta/` до localStorage (был SecurityError на about:blank)
- `page-cabinet.php` — кнопка `#rl-cabinet-quiz-retake` (j6)
- `feed_ui` anon assert — locked bar, не «нет match»
- `RAWLEAD_MONICA_TOKEN` + acc1 JWT в `.env.site`

**Lead verify prod `rawlead.ru`:** desktop **8/8** · mobile **5/5** · theme deploy ✅ **`#rl-cabinet-quiz-retake`** · `ver=1.19.20`

**Gate M1 ads:** O218 QA ✅ · дальше O200 L2 · Metrika smoke ⏸ · YouDo отдельно.

---

## O200 L2 category wave — ⏳ judge blocked Neon (2026-06-18)

**Coder:**
- `deploy-o200-l2-vps.py` ✅ VPS **active** · playbooks + `primary_category` on prod
- `_JUDGE_L2_SEND_MIN_PER_CAT` **0.70** (owner gate) · `_l2_judge_targets` stratified 10×4
- `worst_by_category` в judge artifact · pytest `test_l3_human_style -k o200` **7/7** · audit tests **4/4**

**Regen:** `regen_shared_reply_drafts --apply --limit 80` — **11/42 ok** (SSL drop) · retry **❌ Neon compute quota exceeded**

**Judge:** ⏳ `preprod_ai_prod_audit --judge --judge-limit 40` → artifacts `data/preprod_o200_judge.json` + `_human.md` после восстановления Neon

**Owner unblock:** Neon plan/quota → повторить regen + judge · Lead verify gate ≥70%×4

---

## O262k YouDo DC probe — ✅ (2026-06-17)

**DC VPS (O263 owner 2026-06-18):** `YOUDO_O191_DC_SLOTS=3` · 3× RU DC (`194.226.236.204/197`, `185.147.131.15`) · **без** `212.102…` · residential RU fallback **off**.

**Probe** `scripts/probe_youdo_dc_page.py` (Camoufox · slot 1 `185.147.131.15:8000` · no RU):

| Поле | Значение |
|------|----------|
| html_len | **1712** |
| servicepipe | **true** |
| pokazat_spiskom | false |
| data_id_count | 0 |
| view_mode | **servicepipe** (не map/list) |

**Вывод:** DC slot 1 отдаёт **ServicePipe `/exhkqyad` loader**, не YouDo SPA. Артефакт: `data/o262k_dc_probe.json` · HTML на VPS `data/debug_listings/youdo_dc_probe_camoufox_*.html`.

**Deploy:** `scripts/deploy-o262k-youdo-dc-probe-vps.py`

---

## O262j YouDo — ⚠️ verify partial · ingest 1× RU (2026-06-17 ~22:27)

**Coder ✅ code:** `_youdo_dc_pool()` при `DC_SLOTS=0` → `[]` даже с `YOUDO_DC_PROXY_URLS` · pytest **8/8** (o262j+o262i) · deploy ✅ VPS.

**Prod после deploy:**
- `YOUDO_O191_DC_SLOTS=0` · `YOUDO_DC_PROXY_URLS` **удалён** (dc_alive=0/0)
- **22:27** `fetch tier=ru` gate.node-proxy.com:10009 → **`youdo:ingest done=50 new=49`** ✅ (единственный успех вечера)
- **22:47** снова `ServicePipe antibot` · `parsed=0` · ingest 0

**Owner conflict:** RU-only path — **не целевой** (дорого). Код O262j технически верный, но **стратегия отменена** → DC restored для O262k.

**O262k:** ✅ см. секцию выше.

---

**Coder ✅ code:** `max(0, DC_SLOTS)` · cycle wall `≥900` · pytest **16/16** (o262i+h+g) · deploy ✅ VPS.

**Lead verify prod:**

| # | Conflict | Status |
|---|----------|--------|
| 2 | Watchdog 600 vs 750 | ✅ `RADAR_CYCLE_WALL_SEC=900` · после 21:46 **нет** `watchdog:kill>600` на RU-fetch |
| 1 | DC_SLOTS=0 → RU-only | ❌ prod **`YOUDO_DC_PROXY_URLS=4 DC`** — explicit list **обходит** slot count · fetch `21:46:08 tier=dc` |
| 3 | ingest after parse | ⏳ fetch cycle 1 ещё идёт · `youdo:ingest done=0` |

**→ O262j @coder:** `_youdo_dc_pool()` при `DC_SLOTS=0` → `[]` даже если `YOUDO_DC_PROXY_URLS` задан · deploy unset/clear env · test.

---

## O262i YouDo — 🔴 root cause (archive note)

**Симптом:** в ленте YouDo «час назад» · `youdo:ingest done=0 new=0` весь вечер.

**3 конфликта (не ServicePipe alone):**

| # | Конфликт | Факт из лога |
|---|----------|--------------|
| 1 | **Hotfix `YOUDO_O191_DC_SLOTS=0` не работает** | код `max(1, int(raw))` → всё равно 1 DC · cycle 13 `21:15:54 tier=dc` |
| 2 | **Watchdog 600s vs YouDo 750s** | `RADAR_CYCLE_WALL_SEC` не задан (default 600) · `21:24:08 цикл:watchdog:kill` — fetch ещё шёл на RU |
| 3 | **Parse без ingest** | `20:12 outcome=ok parsed=50` + `wall-clock kill 510s` → orphan · ingest 0 |

**Последний реальный ok:** `19:19:49` RU `gate.node-proxy.com:10009` (когда `dc_alive=0/4`).

**→ fixed in code above**

---

## O262f YouDo ✅ deploy (2026-06-17)

**Deploy Lead:** `deploy-o262f-youdo-recovery-vps.py` · early RU + carousel · env `YOUDO_SERVICEPIPE_EARLY_RU=1`.

**Статус:** ✅ listing пробивается RU-нодой · `detail:short` hotfix применён · **→ O262g** для stuck leads.

---

## O265 + O265b ✅ prod deploy (2026-06-17)

**Coder ✅:** 4 кнопки · nope −1 · TG rate limit · pytest **16/16** (O265+O50).

**Prod ✅ Lead verify+deploy:** `deploy-o265-match-push-bot-vps.py` · api+bot-poll active · `o265_ok`.

**Smoke:** дождаться следующего match push → 4 кнопки · tap «Не моё» / «Отклик».

---

## O262d list-view selector gate ✅ prod (2026-06-17)

**Verify:** pytest **25/25** · deploy ✅ Lead ~15:00 MSK · ingest 🔴 antibot 1712b · last ok **14:29** `new=0`.

---

## O262c list-view wait+retry ✅ prod (2026-06-17)

**Сделано:** после `goto` — `networkidle` (cap 15s) или 3s sleep · pass=1 list_view · после shell-wait — pass=2 если `data-id=0` и `html>=50k` · trace `html_len force pass`.

**Файлы:** `exchange_browser_fetch.py` · `tests/test_o262c_youdo_list_view_retry.py` · `deploy-o262c-youdo-list-view-vps.py`

**Verify:** pytest **19/19** · deploy ✅ · prod `14:29:53` `clicked=1 parsed=50` · **→ O262d** (selector gate)

---

## O262b verify ⚠️ prod (2026-06-17 ~14:20 MSK)

**Code+deploy ✅** · trace `stage=list_view` ✅ · **click ❌** — все строки `clicked=0 selector=none` · `parsed=0` · shell **1712b** без «списком».

**Корень:** клик до гидрации SPA · **→ O262c** wait + retry после роста HTML.

**Smoke:** `grep 'stage=list_view' radar_site.log`

---

## O261+O262 deploy ✅ prod (2026-06-17)

**O261:** FL dead-proxy rotate · YouDo max 2 DC-ban/fetch · auto-unban @20min · `/ops/` «Сбросить баны YouDo».

**O262 (owner):** клик **«Показать списком»** перед wait `data-id` · `YOUDO_LIST_VIEW_CLICK=1`.

**Verify:** pytest O261+O262 **12/12** · deploy ok · bans cleared **7** · `dc_alive=4/4` · post-fetch **13:11** still `html_len=1712` antibot · **0×** `list_view_click` (shell без ссылки «списком»).

**Вывод:** O262 поможет когда грузится полная карта; сейчас прокси получает **1712b shell** без UI — нужен Mechanic/antibot или живой DC.

**Smoke:** `grep list_view /opt/rawlead/data/radar_site.log` · `fetch:youdo tier=dc` · `/ops/` кнопка YouDo bans

---

## O261 Parser auto-recovery ✅ prod (2026-06-17)

**Файлы:** `exchange_proxy.py` · `exchange_browser_fetch.py` · `fl_parser.py` · `proxy_ops.py` · `owner_admin.py` · `ops-pult.js` · `tests/test_o261_*` · `deploy-o261-parser-auto-recovery-vps.py`

---

## → Сейчас (prod snapshot 2026-06-16)

| § | Code | Prod |
|---|------|------|
| **O261** Parser auto-recovery | ✅ | ✅ **2026-06-17** |
| **O262** YouDo «Показать списком» click | ✅ | ✅ **2026-06-17** · shell 1712b без ссылки |
| **O259** YouDo DC carousel (4 DC like FL) | ✅ code | ⏳ deploy |
| **O258** Playwright chromium + probe cron alert | ✅ code | ⏳ deploy |
| **O257** Parser stability audit + fixes | ✅ code | ⏳ deploy |
| **O256** FL antibot soft-detect + html_snip | ✅ code | ✅ prod (verify ✅ 35 tests) |
| **O255** YouDo hard reset fail@1 + rate cap | ✅ | ✅ deploy **~06:xx UTC** |
| **O254b** ops cache-bust + re-bind | ✅ | ✅ deploy **~05:20 UTC** |
| **YouDo playwright pin** | ✅ | ✅ deploy **1.58.0** · crash ушёл · antibot ⏳ |
| **YouDo ingest** | — | 🟡 browser ok · last ok **05:35** · ждём цикл |
| **O252** TG content dedup | ✅ | ⏳ deploy |
| **O250d** push km parity | ✅ | ✅ owner smoke |
| **O253** JWT session heal | ✅ | ✅ owner smoke |
| **O250c** push debug/proxy | ✅ | ✅ |
| **O250b** push match parity | ✅ | ✅ |
| **O250** UUID crash | ✅ | ✅ |
| **O237** Yandex Metrika | ✅ **1.19.20** | ⏳ theme deploy |
| **O249** perfect badge removed | ✅ **1.19.19** | ✅ |
| **O248** TG join v4 | ✅ | ✅ ~304 pending |

---

---

## O259 YouDo DC carousel ✅ code (2026-06-16)

**Сделано:** `SPA shell` → retryable · ban+rotate в DC pool (`_youdo_dc_pool`) до RU · log `stage=dc_rotate` · hard_reset skip если `youdo_dc_alive>0`.

**Файлы:** `exchange_proxy.py` · `exchange_browser_fetch.py` · `youdo_parser.py` · `tests/test_o259_youdo_dc_carousel.py` · `scripts/deploy-o259-youdo-dc-carousel-vps.py` · `.env.example`

**Как проверить:** `pytest tests/test_o259_youdo_dc_carousel.py -q` · deploy → log `dc_rotate` before `hard_reset` · `youdo_dc_alive=4/4`

---

## O254 YouDo restart ✅ prod (2026-06-16)

**Prod stack:** YouDo = **Camoufox (Firefox)** · `YOUDO_BROWSER=camoufox` · listing via subprocess `youdo_fetch_worker.py` · FL/Kwork = Playwright Chromium.

**Сделано:**
- **JS:** event delegation `#rl-ops-exchanges` — кнопка «Перезапустить источник» после hydrate
- **`youdo_hard_reset()`** — streak/guard/cooldown/cycle + **`youdo_browser_teardown()`** (contexts + `_abort_playwright_worker` + kill camoufox/youdo worker orphans)
- **Ops:** YouDo restart → hard reset + фоновый `systemctl restart rawlead-radar`
- **Auto:** `YOUDO_HARD_RESET_FAILS=1` → hard reset без 30min cooldown · rate cap 120s / 8/h

**Файлы:** `ops-pult.js` · `youdo_parser.py` · `exchange_browser_fetch.py` · `owner_admin.py` · `main.py` · `tests/test_o254_youdo_restart.py`

**Deploy ✅:** api+radar **04:37 UTC** · **Owner smoke ❌ (2026-06-16):** nginx 0× `POST /ops/control` · YouDo **12:50** still `Connection closed` · last ok **05:35 MSK** → **O254b** + **mechanic**

---

## O258 Playwright + probe cron ✅ code (2026-06-16)

**Сделано:** idempotent `playwright install chromium` on VPS · cron every 15 min · alert → @FLPARSINGBOT · FL `browser_error` + httpx ok same cycle → no alert · cooldown 30 min

**Файлы:** `scripts/parser_probe_alert.py` · `scripts/probe_parsers_health_alert_vps.py` · `scripts/deploy-o258-playwright-probe-vps.py` · `tests/test_o258_probe_alert_logic.py` · `.env.example`

**Как проверить:** `pytest tests/test_o258_probe_alert_logic.py tests/test_o257_* -q` → 26 green · Lead: `python scripts/deploy-o258-playwright-probe-vps.py`

---

## O257 Parser stability audit + fixes ✅ code (2026-06-16)

**Сделано:** audit §A–D+F (ticket) · FL auto httpx fallback (subprocess empty → httpx, `FL_HTTPX_AUTO_FALLBACK=1` default) · fix restart loop (`set_restart_source=False` when subprocess) · pipeline logs all browser failures (`fetch:fl outcome=fail reason=...`) · `fetch:{src} outcome=` for fl/kwork/youdo · YouDo RU dead pool skip · `scripts/probe_parsers_health_vps.py` + `scripts/audit_parser_processes_vps.py`

**Файлы:** `fl_parser.py` · `exchange_browser_fetch.py` · `kwork_parser.py` · `youdo_parser.py` · 2 scripts · deploy script · 3 tests

**Как проверить:** `pytest tests/test_o257_* tests/test_o256_fl_antibot_soft.py tests/test_o255_youdo_hard_reset_rate.py -q` → 30 green

---

## O256 FL antibot soft-detect ✅ code (2026-06-16)

**Intent:** FL `parsed=0` при alive pool без proxy ban — soft antibot reset + ops lamp.

**Сделано:**
- **`fl_parser.py`:** каждый browser `parsed=0` → log `fl_listing:html_snip snip=…` (300 байт)
- **`fl_parser.py`:** streak≥5 + bans=0 → `fl_hard_reset` + `fl_listing:soft_antibot_reset` + `restart_source_fl` (обходит O233 cooldown)
- **`radar_status.py`:** streak>10 + bans=0 + pool ok → `antibot_soft` · hook в **`ops_funnel.py`** → 🔴 lamp /ops/

**Файлы:** `fl_parser.py` · `radar_status.py` · `ops_funnel.py` · `scripts/deploy-o256-fl-antibot-vps.py` · `tests/test_o256_fl_antibot_soft.py`

**Как проверить:** `pytest tests/test_o256_fl_antibot_soft.py -q` · deploy radar · log `fl_listing:html_snip` · streak=5 → `soft_antibot_reset` · /ops/ FL 🔴 при streak>10

---

## O255 YouDo hard reset fail@1 ✅ prod (2026-06-16)

**Intent:** как FL — hard reset с первого browser/antibot fail; подстраховка от hammering.

**Сделано:**
- **`YOUDO_HARD_RESET_FAILS=1`** (default) · no `set_youdo_cooldown(30min)` on auto reset path
- **Rate limit:** `YOUDO_HARD_RESET_MIN_SEC=120` · `youdo_last_hard_reset_at` · too soon → short cooldown 5 min · log `hard_reset_rate_limited`
- **Hourly cap:** `YOUDO_HARD_RESET_MAX_PER_HOUR=8` · rolling window · cap → traffic_guard ~90 min · log `hard_reset_hourly_cap`
- Auto reset: bump hour counter + update `youdo_last_hard_reset_at` · teardown unchanged

**Файлы:** `youdo_parser.py` · `.env.example` · `tests/test_o255_youdo_hard_reset_rate.py`

**Deploy ✅:** `scripts/deploy-o255-vps.py` · radar restart · `.env.site` 4× YOUDO_HARD_RESET_* lines

**Как проверить:** `pytest tests/test_o255_youdo_hard_reset_rate.py tests/test_o254_youdo_restart.py -q` · fail log: `hard_reset reason=auto_fail_streak=1` OR `hard_reset_rate_limited`

---

## O254b ops restart cache-bust ✅ code (2026-06-16)

**Симптом:** кнопка «Перезапустить источник» мёртвая — вкладка держит старый `ops-pult.js` без delegation.

**Сделано:**
- **`owner_admin.py`:** `ops-pult.js?v=<mtime>` — cache bust при deploy
- **`ops-pult.js`:** `bindRestartSourceDelegation()` после hydrate exchanges

**Файлы:** `owner_admin.py` · `ops-pult.js`

**Как проверить:** deploy api → `/ops/` F5 (не Ctrl+Shift+R) → view-source `ops-pult.js?v=` · клик «Перезапустить источник» YouDo → nginx `POST /ops/control` · journal `fetch:youdo hard_reset`

---

## Push ✅ prod (2026-06-15)

**O250→O250d + O253:** push km = feed km · JWT heal Monica · theme JWT rotation · owner **«заработало»**.

Детали → [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md) § O250

---

## Биржи / ingest

| Источник | Browser | Статус |
|----------|---------|--------|
| **FL** | Playwright Chromium | 🔴 `parsed=0` с 13:11 · `alive=4/4` · soft antibot · O233 не триггерит |
| **Kwork** | Playwright Chromium | ok |
| **YouDo** | **Camoufox Firefox** | 🔴 antibot cooldown · O255 code ready · deploy ⏳ |
| **TG** | Telethon | ok · join v4 фон |

Тикет FL: [`docs/problems/2026-06-16-fl-parsed-zero-no-proxy-ban.md`](../../problems/2026-06-16-fl-parsed-zero-no-proxy-ban.md)  
Тикет YouDo: [`docs/problems/2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md)

---

## Недавно закрыто (index)

| § | Fact |
|---|------|
| **O247b** | draft quota toolbar ✅ |
| **O244–O246** | ✅ **1.19.16** |
| **O233** | FL auto-recovery ✅ |
| **O225–O235** | quiz-first **1.19.12** |

Полный лог → [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Tier smoke · ads gate

**PASS:** anon/trial/expired/owner/cross · P3 payment OK  
**Ads ⏸:** **O218** QA · **O200-L2** ≥70%×4 · Metrika smoke ⏸ · O252 ✅ prod
