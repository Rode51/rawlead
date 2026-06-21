# PROD_FACTS — снимок prod (живой канон)

**Кто обновляет:** Lead Architect **после каждого verify/deploy** (5 мин).  
**Кто читает:** все AI **перед triage**, инцидентами и ответами про «что на prod».  
**Не дублировать** в чат то, что уже здесь — ссылаться на этот файл.

> Детали задач → [`STATUS.md`](STATUS.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md)

**Обновлено:** 2026-06-21 (pre-M1 security M1+M2 · G-SEC S-1)

## Pre-M1 security M1+M2 (2026-06-21)

| | |
|---|---|
| **M2** | `_resolve_user_id` — только Bearer JWT · без `X-RawLead-User-Id` / owner fallback |
| **M1** | VPS `.env.site` `RADAR_CORS_ORIGINS=https://rawlead.ru,https://www.rawlead.ru` |
| **Deploy** | `scripts/_deploy_pre_m1_security_vps.py` · `rawlead-api` restart |
| **pytest** | G0 **32 passed**, 1 skipped (Lead verify) |
| **prod** | `GET /v1/me/feed` без Bearer → **401** (curl verify Lead) |

## G-SEC S-1 (2026-06-21)

| | |
|---|---|
| **Авто** | G0 pytest **30 passed** (Lead verify) |
| **S-1 prod** | acc1 replies **200** · monica изоляция overlap=0 · чужой lead draft **404** (@coder curl) |
| **S-2** | owner — `/ops/` auth · webhook без секрета |

## G7b L2 tools + ЛК link (2026-06-21)

| | |
|---|---|
| **Commits** | `3e12011` L2 tools finalize · `2af72a1` stress PASS + InboxCard link |
| **API deploy** | `deploy-l2-stack-vps.py` · `ai_analyze` + `tools_catalog` · `rawlead-api`/`radar` active |
| **Next deploy** | `deploy-web-rawlead-vps.py` · 63 files · cabinet chunk `page-7ea1ba14ae71d0ac.js` · `inbox-exchange-link` |
| **Verify** | `/health` 200 · `https://rawlead.ru/` HTTP 200 |

## Feed UX (O280 · owner accept 2026-06-20)

| | |
|---|---|
| **R1** | Отклик ✓ badge · draft expand/select · login «открыть ссылку» |
| **R2** | Квота справа · «Осталось N откликов» · при лимите «лимит обновится через M мин» |
| **Deploy** | `deploy-web-rawlead-vps.py` · multi-filter **`92060b7`** · owner ✅ 2026-06-21 |

## Support (O116-W4 + TG-reply) ✅

| | |
|---|---|
| **Цикл** | FAB → `TELEGRAM_CHAT_ID` only → reply в боте → thread в FAB |
| **Fallback** | `#N текст` · `тN: текст` в admin chat |
| **Thread** | `user_id` OR `guest_token` · последний активный тикет |
| **Deploy** | `deploy-o116-support-thread-vps.py` + Next · owner smoke OK |

## M1-bot (2026-06-20)

| | |
|---|---|
| **Deploy** | `telegram_control.py` · `rawlead-bot-poll` active |
| **Smoke** | `/start` · `?start=m1_chat` · ▶️ Старт / «привет» → welcome + inline UTM |

## API (PRE-ADS-MIMO W1 · 2026-06-20)

| | |
|---|---|
| **Deploy** | `api_server.py` + `pg_storage.py` · `rawlead-api` active · `/health` ok |
| **Changes** | connection pool on handlers · YooKassa `compare_digest` · draft feed-membership gate · `pg_storage` pool bind |

## Portfolio rode51.ru (2026-06-21)

| | |
|---|---|
| **URL** | https://rode51.ru · P2 static (WhyMe, FAQ, `/en`) |
| **Deploy** | `deploy-portfolio-rode51-vps.py` · owner ✅ **2026-06-21** (Claude Code polish) |
| **Fix** | deploy перезаписал nginx без 443 → восстановлен `deploy/nginx/rode51.ru.conf` SSL block |

---

## Database (O271)

| | |
|---|---|
| **Prod `DATABASE_URL`** | **VPS Postgres** `127.0.0.1:5432/rawlead` (`.env.site`, verify 2026-06-19) |
| **Локальный preprod** | SSH tunnel `:15432` → VPS · см. [`PREPROD_ACCOUNTS.md`](../../ops/PREPROD_ACCOUNTS.md) § 1b |
| **Post-migrate** | после смены URL — **restart** `rawlead-api` + `rawlead-bot-poll` + `rawlead-radar` |

## Billing (O174 / O284)

| | |
|---|---|
| **ЮKassa keys** | `.env.site` (3 vars) · **не** в корневом `.env` |
| **Checkout API** | `POST api.rawlead.ru/v1/me/subscription/checkout` |
| **Webhook** | `POST api.rawlead.ru/v1/webhooks/yookassa` · secret header + `compare_digest` (MiMo M0 ✅) |
| **Return URL** | `https://rawlead.ru/cabinet/` (default) |
| **Next gap** | нет `POST /v1/me/subscription/confirm` на return → § **O284** |

---

<!-- AUTO:VPS_PROBE:START -->
**Probe:** 2026-06-21 06:44 UTC · `python scripts/probe_prod_facts_vps.py --write`

| Unit | State |
|------|-------|
| rawlead-radar | active |
| rawlead-api | active |
| rawlead-bot-poll | active |

- **YOUDO_BROWSER:** `camoufox`
- **RADAR_PROFILE:** `site`
- **Theme prod `ver`:** `?`
- **Last YouDo ok:** 2026-06-21 14:40:23 youdo:trace stage=fetch_end fresh=50 kind=ok new=9 parsed=50
- **O254 code on VPS:** ✅ (`youdo_browser_teardown`)
- **TG join v4 pending:** 101

- **DB site units:** api=`unset` · bot-poll=`unset` · radar=`unset`

- **Deploy `92060b7` on VPS:** ✅ `l3_opener_too_similar` · ✅ `lead_pipeline` (no snippet skip) · ✅ Next `feed-filters` in `/var/www/rawlead.ru` (2026-06-21 06:40 UTC)

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
| **nginx headers** | `X-Frame-Options` · `nosniff` · `Referrer-Policy` · **нет** CSP/HSTS (MiMo M0 → post-M1) |
| **POST-CUTOVER R10** | ⏳ | Next header «Админка» → `/ops/` |
| **POST-CUTOVER R9b** | ✅ **2026-06-19** | avatar dir `/opt/rawlead/data/avatars` · env + guard |
| **POST-CUTOVER R9** | ✅ **2026-06-19** | лента без счётчика · avatar login path |
| **WP rollback** | `/var/www/rawlead.ru-wp` (full copy pre-cutover) |
| **Repo theme (legacy)** | **1.19.20** — не на корне домена |

---

## Deploy snapshot (code vs prod)

| § | Code | Prod |
|---|------|------|
| **G6 L3 v4** + YouDo pipeline + multi-filter | ✅ `92060b7` | ✅ owner deploy 2026-06-21 |
| Push O250→O250d + O253 | ✅ | ✅ owner smoke 2026-06-15 |
| O254 YouDo restart + camoufox teardown | ✅ | ✅ code on VPS |
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
