# PROD_FACTS — снимок prod (живой канон)

**Кто обновляет:** Lead Architect **после каждого verify/deploy** (5 мин).  
**Кто читает:** все AI **перед triage**, инцидентами и ответами про «что на prod».  
**Не дублировать** в чат то, что уже здесь — ссылаться на этот файл.

> Детали задач → [`STATUS.md`](STATUS.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md)

**Обновлено:** 2026-06-24 (RETENTION-2D **deploy**)

## RETENTION-2D (2026-06-24 deploy)

| | |
|---|---|
| **Код** | `public_feed.py` `FEED_VISIBILITY_DAYS=2` · `purge_old_leads.py` `_DEFAULT_DAYS=2` · `api_server` / `quiz_adaptive` счётчик за 2d |
| **Web** | `AnnouncementBar` «лидов за 2 дня» · `deploy-web-rawlead-vps.py` |
| **systemd** | `rawlead-purge-leads.service` + timer (описание 2d) |
| **Smoke** | `rawlead-api` **active** · `FEED_VISIBILITY_DAYS = 2` на VPS · `GET /v1/public/site-stats` → `leads_week=734` |
| **Не менялось** | JWT session TTL 7d · `DELIST_PURGE_DAYS` default 1d |

## YOUDO-IMAP-ONLY — model B (2026-06-23 deploy)

| | |
|---|---|
| **Код** | `youdo_imap.py` (last N, no cursor) · `youdo_imap_poller.py` (PG dedup) · `lead_pipeline` (email≥300→detail_ok) · `youdo_parser` (`listing_skip`) |
| **systemd** | `rawlead-youdo-imap.timer` (~90s) → oneshot `rawlead-youdo-imap.service` |
| **Env** | `YOUDO_IMAP_ENABLED=1` · `YOUDO_IMAP_FETCH_LAST=30` · `YOUDO_LISTING_FETCH=0` · `YOUDO_CLICK_DETAIL=0` · `YOUDO_DETAIL_FETCH=0` |
| **Backup** | `/opt/rawlead/data/backups/pre_youdo_imap_b_20260623-065533.tar.gz` |
| **Smoke** | IMAP poll **30 tasks** · `youdo:listing_skip reason=imap_only` в `radar_site.log` · timer **active** (NEXT ~90s) |
| **Watch** | `journalctl -u rawlead-youdo-imap` · `grep youdo:imap /opt/rawlead/data/radar_site.log` · oneshot может долго жить при ingest — см. STATUS |
| **Откат** | `tar -xzf pre_youdo_imap_b_20260623-065533.tar.gz -C /` + env listing `1` + `systemctl restart rawlead-radar` |

## YOUDO-IMAP-DISCOVERY (архив 2026-06-22)

| | |
|---|---|
| **Код** | `youdo_imap.py` · `youdo_imap_poller.py` · mail.ru `INBOX/Newsletters` → ingest + `detail_ok` |
| **systemd** | `rawlead-youdo-imap.timer` (90s) → `rawlead-youdo-imap.service` (oneshot `--once`) |
| **Env (prod сейчас)** | `YOUDO_IMAP_*` · `YOUDO_IMAP_BOOTSTRAP_SKIP_OLD=1` · **устарело:** UID-курсор `youdo_imap_last_uid` |
| **Env (после §)** | `YOUDO_IMAP_FETCH_LAST=30` · listing/browser **0** · **без** bootstrap/cursor |
| **Backup** | `/opt/rawlead/data/backups/pre_youdo_imap_20260622-162048.tar.gz` |
| **Smoke** | timer `active` · catch-up: `FETCH_LAST=50` + `poller --once` · новые → `youdo:imap new_id=` |
| **Лог watch** | `journalctl -u rawlead-youdo-imap` · `grep youdo:imap /opt/rawlead/data/radar_site.log` |

## YOUDO-CLICK-RETRY + SP-STABLE (2026-06-22 deploy)

| | |
|---|---|
| **Код** | `youdo_detail_pending:{id}` · retry click на листинге · `click_summary` trace · SP-STABLE hover/jitter/go_back |
| **Файлы** | `youdo_sticky_worker.py` · `youdo_parser.py` · `exchange_browser_fetch.py` · `lead_pipeline.py` |
| **Backup** | `/opt/rawlead/data/backups/pre_click_retry_20260622-141501.tar.gz` |
| **Откат** | `tar -xzf pre_click_retry_20260622-141501.tar.gz -C / && systemctl restart rawlead-radar` |
| **pytest** | 44 passed (Lead verify 2026-06-22) |
| **Лог watch** | `fetch:youdo … pending=N click_ok=K` · `stage=click_summary` · `click_detail outcome=ok` |
| **24h DoD** | pending id на листинге -> `click_retry` / `click_detail` в течение 1-2 циклов |

## YOUDO-SOURCE-GATE (2026-06-22 deploy)

| | |
|---|---|
| **Код** | `detail_ok` only · `youdo_no_detail` · dedup `list_project_ids` |
| **FEED-HYGIENE** | `public_feed` МИМО filter · `vacancy_filter` markers |
| **Backup** | `/opt/rawlead/data/backups/pre_source_gate_20260622-114840.tar.gz` |
| **Откат** | [`2026-06-22-youdo-source-gate-rollback.md`](../problems/2026-06-22-youdo-source-gate-rollback.md) |
| **pytest** | 44 passed (Lead verify) |
| **Лог watch** | `new=0` = все id в SQLite · `click_ok=0` = detail не достали |

## YOUDO-CLICK-DETAIL (2026-06-22)

| | |
|---|---|
| **Код** | click-through в sticky session · `youdo_click_through_details` · worker `click_through_details` · кэш → `lead_pipeline` |
| **Env** | `YOUDO_CLICK_DETAIL=1` · `YOUDO_CLICK_DETAIL_MAX=10` |
| **pytest** | `test_o269` + `test_youdo_human` — **45 passed** (Lead verify) |
| **Deploy** | `exchange_browser_fetch.py` · `youdo_parser.py` · `lead_pipeline.py` · `youdo_sticky_worker.py` · radar+api **active** |
| **Лог** | `youdo:trace stage=click_detail …` · `fetch:youdo … click_ok=N` |
| **Watch** | `new=0` на листинге → click-through не запускается · traces появятся на **новых** id · post-restart antibot watch 14:09–14:12 UTC |
| **Откат** | `YOUDO_CLICK_DETAIL=0` · restore `backups/youdo_profile_pre_clickthrough_2026-06-22.tar.gz` |
| **DoD 24h** | ⏳ `grep stage=click_detail.*outcome=ok` ≥10 — ждём новые заказы |

## YOUDO-RESTORE-SNIPPETS (2026-06-22)

| | |
|---|---|
| **Env** | `YOUDO_DETAIL_MIN_CHARS=0` на VPS |
| **Код (prod)** | `_youdo_detail_short_skips_l1` — delist при `detail_ok≠True` + floor 300 · **⏳ меняется** |
| **Target (owner rev2)** | **Только detail_ok** в публичной ленте; сниппет без detail — **не в ленте** · короткое detail-TZ ок · § `YOUDO-SOURCE-GATE` |
| **pytest** | `test_o281` + `test_o223` — **17 passed** |
| **Deploy** | `lead_pipeline.py` + restore script · `rawlead-api` + `rawlead-radar` **active** |
| **DB** | `youdo_visible=4219` · restore `--apply` restored=4219 |
| **API** | `GET /v1/feed?source=youdo&limit=3` — ok |
| **Ограничение** | snippet body · full TZ — click-through deployed, ждём `new>0` для traces |
| **FL/Kwork** | detail HTTP ✅ · полное ТЗ · эталон для YouDo |

## FEED-FILTER-TG-STUCK (2026-06-22)

| | |
|---|---|
| **v2 fix** | `rawlead_feed_prefs_v3` · v2→v3 migrate `sources=[]` · merge без server sources · `filterGenerationRef` |
| **Deploy** | `deploy-web-rawlead-vps.py` **2026-06-22** · `/lenta/` HTTP 200 · chunk `page-853f2c34…js` |
| **pytest** | `test_o280_next_e2e` — **2 passed** (static) · Playwright race test opt-in `RAWLEAD_O280_E2E=1` |
| **DoD** | ✅ owner: Ctrl+F5 `/lenta/` — все биржи после первого захода (v2 TG сброшен) |

## L1-TILDA-TAGS (2026-06-22)

| | |
|---|---|
| **Код** | `sanitize_l1_cms_tags` Tilda · L1 prompt · `enrich_youdo_l1_snippet` + detail parser |
| **Deploy** | `youdo_parser.py` (upload) · `deploy-g6-l3-vps.py` (`ai_analyze`) · `deploy-o230-skills-cap-vps.py` (`skills_catalog`) · `rawlead-api` **active** |
| **pytest** | `test_l1_tags_cms.py` — **4 passed, 6 subtests** (Lead verify) |
| **re-L1 18311** | ✅ Lead verify prod DB: `['tilda_dev','ecommerce_dev','api_integration']` · body 233 chars · `YOUDO_DETAIL_FETCH=1` · TZ-fallback (ServicePipe на detail) |
| **DoD** | ✅ golden · prod 18311 · pytest 4 passed · `YOUDO_DETAIL_FETCH=1` |

## QUIZ-REDESIGN — texts (2026-06-23 deploy)

| | |
|---|---|
| **Карточки** | `quiz_cards_v1.json` 56 + `v2` 130 = **186** merged |
| **Изменено** | только `title` + `task_summary` (понятный язык) |
| **Без изменений** | `skills_on_like`, signals, niche, логика `quiz_adaptive.py` |
| **Deploy** | `deploy-o217-quiz-vps.py` · `rawlead-api` **active** |
| **Smoke** | `GET /v1/quiz/start` → `source=synthetic` · merged=186 |

---

## FEED-QUIZ-POLISH (2026-06-22)

| | |
|---|---|
| **A — фильтры** | `rawlead_feed_prefs` localStorage + `GET/PUT /v1/me/feed-prefs` · F5 `/lenta/` сохраняет категории/биржи/sort |
| **B — квиз** | `QUIZ_MIN_TOTAL=8` · `QUIZ_EARLY_SIGNAL_MIN=4` (shown signals leader niche) · `QUIZ_NORMAL_STOP_MIN=10` · insufficient → retry UI |
| **Deploy** | `deploy-o217-quiz-vps.py` (API) + `deploy-web-rawlead-vps.py` (Next 63 files) · `rawlead-api` **active** |
| **pytest** | `test_o197_quiz_adaptive` + `test_o280_next_e2e::test_feed_prefs_module_exports` — **24 passed** (Lead verify) |
| **prod** | `GET /v1/quiz/start` → `qc_dev_python_01` synthetic · `/lenta/` HTTP **200** |

## BOT-NOTIFY-START (2026-06-21)

| | |
|---|---|
| **Поведение** | Первый `/start` юзера в `@rawlead_bot` → 1 сообщение владельцу в `TELEGRAM_CHAT_ID` · повторы — молча · свой `/start` (admin) — skip |
| **Флаг** | VPS `.env.site` `BOT_NOTIFY_OWNER_START=1` |
| **Dedup** | `users.bot_start_owner_notified_at` · migration `sql/026` |
| **Deploy** | `telegram_control.py` + `config.py` · `rawlead-bot-poll` **active** |
| **pytest** | `TestBotNotifyOwnerStart` + `TestM1Welcome` — **13 passed** (Lead verify) |

## CABINET-PARITY (2026-06-21)

| | |
|---|---|
| **Push** | `🔔 Match` без процента · VPS ✅ |
| **ЛК** | Уведомления без % на кнопках ✅ |
| **Retake** | `#rl-cabinet-quiz-retake` в шапке «Мои отклики» · навыки **не** показываем |
| **pytest** | `test_match_push_o50` · `test_match_push_o250` |

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

## Portfolio rode51.ru (2026-06-23)

| | |
|---|---|
| **URL** | https://rode51.ru · static export (RU + `/en`) |
| **Deploy** | `deploy-portfolio-rode51-vps.py --skip-build` · owner ✅ **2026-06-23** (Claude Code update) |
| **Smoke** | `curl https://rode51.ru/` → HTTP 200 · title `Rode51 — Боты, парсеры, автоматизация` · `/en/` 200 |
| **Fix** | deploy 2026-06-21 перезаписал nginx без 443 → восстановлен `deploy/nginx/rode51.ru.conf` SSL block |

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
| **Return URL** | `https://rawlead.ru/cabinet/` · `meApi.confirmSubscription()` on mount (`cabinet/page.tsx`, `pricing/page.tsx`) |
| **API** | `POST /v1/me/subscription/confirm` ✅ · webhook `payment.succeeded` |

---

<!-- AUTO:VPS_PROBE:START -->
**Probe:** 2026-06-21 18:46 UTC · `python scripts/probe_prod_facts_vps.py --write`

| Unit | State |
|------|-------|
| rawlead-radar | active |
| rawlead-api | active |
| rawlead-bot-poll | active |

- **YOUDO_BROWSER:** `camoufox`
- **RADAR_PROFILE:** `site`
- **Theme prod `ver`:** `?`
- **Last YouDo ok:** 2026-06-22 02:34:59 youdo:trace stage=fetch_end fresh=0 kind=ok new=0 parsed=50
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
| **nginx headers** | `X-Frame-Options` · `nosniff` · `Referrer-Policy` · **нет** CSP/HSTS (MiMo M0 → post-M1) |
| **POST-CUTOVER R10** | ✅ | `Header.tsx` — ссылка «Админка» → `/ops/` |
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
