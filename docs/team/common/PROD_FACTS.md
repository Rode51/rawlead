# PROD_FACTS — снимок prod (живой канон)

**Кто обновляет:** Lead Architect **после каждого verify/deploy** (5 мин).  
**Кто читает:** все AI **перед triage**, инцидентами и ответами про «что на prod».  
**Не дублировать** в чат то, что уже здесь — ссылаться на этот файл.

> Детали задач → [`STATUS.md`](STATUS.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md)

**Обновлено:** 2026-06-18 (O271 VPS Postgres cutover)

## Database (O271)

| | |
|---|---|
| **Prod `DATABASE_URL`** | **local Postgres** `127.0.0.1:5432/rawlead` |
| **Neon** | **отключён** · URL в `NEON_DATABASE_URL` (backup only) |
| **Post-migrate** | после смены URL — **restart** `rawlead-api` + `rawlead-bot-poll` + `rawlead-radar` |

---

<!-- AUTO:VPS_PROBE:START -->
**Probe:** 2026-06-17 11:07 UTC · `python scripts/probe_prod_facts_vps.py --write`

| Unit | State |
|------|-------|
| rawlead-radar | active |
| rawlead-api | active |
| rawlead-bot-poll | active |

- **YOUDO_BROWSER:** `camoufox`
- **RADAR_PROFILE:** `site`
- **Theme prod `ver`:** `1.5.0`
- **Last YouDo ok:** 2026-06-17 17:36:47 youdo:trace stage=fetch_end fresh=0 kind=ok new=0 parsed=50
- **O254 code on VPS:** ✅ (`youdo_browser_teardown`)
- **TG join v4 pending:** 101

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

**YouDo O262h:** ✅ deploy **2026-06-17** · outer wall ~750s · ingest watch · `youdo:ingest done=` smoke

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

## WP theme

| | Версия |
|---|--------|
| **Repo (code)** | **1.19.20** (O237 Metrika + O253 JWT JS) |
| **Prod** | проверять: `curl -s https://rawlead.ru/lenta/ \| grep ver=` |

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
