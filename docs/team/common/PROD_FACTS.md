# PROD_FACTS — снимок prod (живой канон)

**Кто обновляет:** Lead Architect **после каждого verify/deploy** (5 мин).  
**Кто читает:** все AI **перед triage**, инцидентами и ответами про «что на prod».  
**Не дублировать** в чат то, что уже здесь — ссылаться на этот файл.

> Детали задач → [`STATUS.md`](STATUS.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md)

**Обновлено:** 2026-06-19 (Lead verify billing + DB on VPS)

## Database (O271)

| | |
|---|---|
| **Prod `DATABASE_URL`** | **local Postgres** `127.0.0.1:5432/rawlead` (`.env.site` L13, verify 2026-06-19) |
| **Neon** | **только** `NEON_DATABASE_URL` в `.env.site` (архив) · **не** в `DATABASE_URL` · guard **§ O272** |
| **Post-migrate** | после смены URL — **restart** `rawlead-api` + `rawlead-bot-poll` + `rawlead-radar` |

## Billing (O174 / O284)

| | |
|---|---|
| **ЮKassa keys** | `.env.site` (3 vars) · **не** в корневом `.env` |
| **Checkout API** | `POST api.rawlead.ru/v1/me/subscription/checkout` |
| **Webhook** | `POST api.rawlead.ru/v1/webhooks/yookassa` (owner: ЮKassa ЛК) |
| **Return URL** | `https://rawlead.ru/cabinet/` (default) |
| **Next gap** | нет `POST /v1/me/subscription/confirm` на return → § **O284** |

---

<!-- AUTO:VPS_PROBE:START -->
**Probe:** 2026-06-19 13:34 UTC · `python scripts/probe_prod_facts_vps.py --write`

| Unit | State |
|------|-------|
| rawlead-radar | active |
| rawlead-api | active |
| rawlead-bot-poll | active |

- **YOUDO_BROWSER:** `camoufox`
- **RADAR_PROFILE:** `site`
- **Theme prod `ver`:** `?`
- **Last YouDo ok:** 2026-06-19 21:18:18 youdo:trace stage=fetch_end fresh=50 kind=ok new=43 parsed=50
- **O254 code on VPS:** ✅ (`youdo_browser_teardown`)
- **TG join v4 pending:** 101

- **DB site units:** api=`unset` · bot-poll=`unset` · radar=`unset`

<!-- AUTO:VPS_PROBE:END -->

---

## Биржи — browser stack (не путать!)

| Источник | Prod browser | Env / код | Listing fetch |
|----------|--------------|-----------|---------------|
| **FL** | Playwright **Chromium** | `EXCHANGE_LISTING_BROWSER=1` | persistent context · O233 auto-recovery |
| **Kwork** | Playwright **Chromium** | same | same |
| **YouDo** | **Camoufox (Firefox)** | `YOUDO_BROWSER=camoufox` | subprocess `scripts/youdo_fetch_worker.py` |
| **TG** | Telethon | acc1/2/3 | не browser |

**YouDo ≠ Playwright Chromium.** Ошибки `Browser.close: Connection closed` на YouDo — **camoufox/Firefox worker**, не FL headless Chrome.

**YouDo recovery (O254):** `youdo_hard_reset()` + `youdo_browser_teardown()` · ops кнопка → restart `rawlead-radar` · auto при `YOUDO_HARD_RESET_FAILS=3`.

**YouDo O269 (2026-06-19):** sticky survival deploy ✅ · DC `194.226.236.204` · profile `youdo_*_g2` **не wipe** · watch `sticky_reload` / `warm=1` в логе.

**YouDo O262h:** ✅ deploy **2026-06-17** · superseded by O268 baseline выше

---

## VPS systemd (site profile)

| Unit | Роль |
|------|------|
| `rawlead-radar` | `main.py` — биржи + L1 |
| `rawlead-api` | FastAPI + `/ops/` |
| `rawlead-bot-poll` | @rawlead_bot |
| `nginx` | WP + proxy API |

Env: `RADAR_PROFILE=site` · SQLite `data/projects.db` · log `data/radar_site.log`

---

## WP theme → Next (O280 cutover 2026-06-19)

| | |
|---|---|
| **rawlead.ru** | **Next.js static** `rawlead-next/out` · deploy `deploy-web-rawlead-vps.py` |
| **POST-CUTOVER R10** | ⏳ | Next header «Админка» → `/ops/` |
| **POST-CUTOVER R9b** | ✅ **2026-06-19** | avatar dir `/opt/rawlead/data/avatars` · env + guard |
| **POST-CUTOVER R9** | ✅ **2026-06-19** | лента без счётчика · avatar login path |
| **WP rollback** | `/var/www/rawlead.ru-wp` (full copy pre-cutover) |
| **Repo theme (legacy)** | **1.19.20** — не на корне домена |

---

## Deploy snapshot (code vs prod)

| § | Code | Prod |
|---|------|------|
| Push O250→O250d + O253 | ✅ | ✅ owner smoke 2026-06-15 |
| O254 YouDo restart + camoufox teardown | ✅ | ⏳ code on VPS · smoke `/ops/` |
| O252 TG content dedup | ✅ | ⏳ |
| O237 Yandex Metrika | ✅ theme **1.19.20** · **ssr:false** deploy 2026-06-16 | owner smoke |

---

## Push (prod)

- Gate: `MATCH_PUSH=1` · per-user `users.push_min_match` (30–100)
- km: `effective_user_tag_weights` — parity feed ↔ push (O250d)
- JWT stale heal: `tg_id` claim (O253)

---

## TG join

- Queue: `docs/ops/TG_JOIN_QUEUE_v4.csv` · ~304 pending (2026-06-15)
- `TG_JOIN_IN_TG_MAIN=1`

---

## Что **не** является каноном

| Тип | Где | Правило |
|-----|-----|---------|
| Исторические тикеты | `docs/problems/` | факты на дату тикета · сверять с **этим файлом** |
| Архив | `team/archive/` | не обновлять |
| Старые § в CODER_PROMPT | archive | только index в hot |

---

## Lead: чеклист после deploy/verify

1. **`python scripts/probe_prod_facts_vps.py --write`** — AUTO-блок VPS (systemd, theme ver, YouDo, O254 marker)
2. Вручную: таблица **Deploy snapshot** ниже (code vs prod §)
3. [`STATUS.md`](STATUS.md) hot · закрытый § CODER → index + archive
4. [`FOR_YOU.md`](../../FOR_YOU.md) «Сейчас» — если меняются шаги владельца
5. Stack биржи изменился → [`ARCHITECTURE.md`](../architect/ARCHITECTURE.md) · [`CODE_STRUCTURE.md`](../architect/CODE_STRUCTURE.md)
