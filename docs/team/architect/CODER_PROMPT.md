# Coder — hot queue (active)

**→ Now:** § **YOUDO-DETAIL-BREAKTHROUGH** (P0 M1) · § **ARTICLE-DEMO-INBOX** · POST-M1 backlog

**Index:** G0–G10 ✅ · YOUDO-RESTORE-SNIPPETS ✅ · FEED-FILTER-TG-STUCK-v2 ✅ · YOUDO-FULL-TZ-GATE ✅ · L1-TILDA-TAGS ✅

---

## § YOUDO-DETAIL-BREAKTHROUGH — owner 2026-06-22 · **P0 M1**

**Контекст:** M1 реклама запущена · первые посетители ~23.06. YouDo в ленте (snippet-режим ✅), но **полное ТЗ не читается** — ServicePipe на VPS блокирует `youdo.com/t{id}`. FL/Kwork detail = обычный HTTP, работает. Код detail-fetch **уже есть** (`fetch_youdo_detail_snapshot`), нужен **стабильный пробой**.

**Prod сейчас:** `detail_ok=False` на ingest · body 60–100 chars · `YOUDO_DETAIL_MIN_CHARS=0` (gate off).

**Probe VPS 2026-06-22:** listing `parsed=50` стабилен · `new=0` после 01:08 UTC (дедуп) · `detail:short` до restore · antibot `html_len=1701` watch 12:59 UTC. Тикет: [`2026-06-22-youdo-m1-day.md`](../../problems/2026-06-22-youdo-m1-day.md)

**Маршрут:** MiMo `coder` (default)

**Бэкап перед deploy (owner 2026-06-22):** VPS `/opt/rawlead/data/backups/youdo_profile_pre_clickthrough_2026-06-22.tar.gz` (64M, sha256 `ae806424c2568199c5201d47bce10d359331efb21680a2d4bea848e111a698f9`, профиль `youdo_194.226.236.197:8000_g2`). Golden: `youdo_profile_g2_2026-06-19.tar.gz` (O268).

**Цель:** `detail_ok_rate` YouDo ≥ **50%** на VPS за 24h radar · body ≥300 на новых лидах · после успеха вернуть `YOUDO_DETAIL_MIN_CHARS=300`.

**Приоритет (owner 2026-06-22):** гипотеза **E** first · B (метрики) вместе с E · A/D fallback.

| # | Гипотеза | Где |
|---|----------|-----|
| **E** | **Click-through detail** — в sticky-сессии после листинга: scroll/hover/click по карточке **нового** заказа → SPA detail → parse body · не cold `goto(/t{id})` | `exchange_browser_fetch.py` · `youdo_parser.py` |
| B | **Метрика + UI-log** `youdo:trace stage=click_detail …` (см. ниже) | `log_youdo_trace` · `radar_site.log` |
| A | sticky + `goto /t{id}` только **fallback** если click miss | `youdo_sticky_worker.py` |
| C | DC / profile — golden O268 · restore из tar при регрессии | `exchange_proxy.py` |
| D | soft ServicePipe на detail — не hard-reset на первый 1712b | env `YOUDO_SOFT_*` |

### § E — Click-through detail (DoD техники)

**Поведение:**
1. Listing OK в **той же** page/context (sticky).
2. Только лиды `new=1` в цикле, cap **`YOUDO_CLICK_DETAIL_MAX`** default **10** (env).
3. Для каждого: найти карточку по `external_id` / `data-id` / href `/t{id}` → `click` → wait description selector → `body` ≥300.
4. Если click/detail fail → **один** fallback `goto(/t{id})` в той же сессии · log `fallback=goto`.
5. Не кликать все 50 — только new.

**Логирование (обязательно — UI может сломаться):**

Каждая попытка — строка grep-friendly в `radar_site.log`:

```text
youdo:trace stage=click_detail ext=14868001 selector=href_t clicked=1 outcome=ok body_len=842 ms=3200
youdo:trace stage=click_detail ext=14868002 selector=data_task_card clicked=0 outcome=selector_miss debug=/opt/rawlead/data/debug_listings/youdo_click_miss_*.html
youdo:trace stage=click_detail ext=14868003 selector=href_t clicked=1 outcome=antibot html_len=1701 fallback=goto detail_ok=0
```

Поля: `ext` · `selector=` (какой селектор сработал или последний tried) · `clicked=0|1` · `outcome=ok|selector_miss|timeout|antibot` · `body_len` · `ms` · `debug_path` при miss · `fallback=goto` если был.

**Селекторы:** минимум 2 fallback (href `/t{id}`, `data-id`, class из текущего listing HTML) — как `list_view` O262. При добавлении селектора — unit test.

**Файлы:** `src/exchange_browser_fetch.py` · `src/youdo_parser.py` · `tests/test_o269_youdo_click_detail.py` (новый) · опционально `tests/test_youdo_human.py`

**DoD:**
- pytest `test_o269` + `test_youdo_human` зелёные
- VPS 24h: `grep 'stage=click_detail.*outcome=ok' radar_site.log` ≥10 **или** отчёт в `docs/problems/` почему блокер
- Lead: probe `detail_ok_rate` · owner smoke: YouDo карточка — описание >2 абзацев

**Откат:** restore `backups/youdo_profile_pre_clickthrough_2026-06-22.tar.gz` · env `YOUDO_CLICK_DETAIL=0` (добавить kill-switch)

**Не делать:** отключать YouDo из ленты · ручной SQL · новый парсер с нуля · удалять `data/youdo_*` без бэкапа.

---

## § ARTICLE-DEMO-INBOX — owner 2026-06-21

**Цель:** 2 карточки в **ЛК** (`/cabinet/` inbox) для скрина статьи — **как prod**, не ручной SQL.

**Prod DB:** VPS Postgres `127.0.0.1:5432` (`.env.site` на VPS). **Не Neon MCP.**

| # | Заказ | source | budget |
|---|--------|--------|--------|
| 1 | ТГ-бот: Excel выход ТС на линию → сводка за день (логистика) | `kwork` | по договоренности |
| 2 | Форма поддержки на сайте + ИИ по документу + эскалация оператору | `kwork` | по договоренности |

**Пайплайн (обязательно):** `record_new_lead` → **`analyze_lite` (L1)** → `update_after_lite` → **`generate_and_store_lead_draft` (L2+L3)** → `user_lead_replies` для owner (`TELEGRAM_CHAT_ID` → `users.id`).

**Не в публичной ленте:** `is_visible=FALSE` · `external_id` prefix `article-demo-v2-*`.

**DoD:** owner заходит в `/cabinet/` → 2 карточки Kwork · даты 19–20 июн · «▼ Черновик» → отклик в стиле L3 · цена «по договоренности» · pytest не обязателен · one-shot script `scripts/seed_article_inbox_vps.py` (idempotent cleanup старых `article-demo%`) · запуск **на VPS** `sudo -u rawlead .venv/bin/python scripts/seed_article_inbox_vps.py`.

**Lead verify:** `SELECT` 2 rows inbox · curl JWT owner `/v1/me/replies` · owner глазами ЛК.

---

## § POST-M1-BACKLOG (после wave 1)

| ID | Что |
|----|-----|
| P1 | CSP/HSTS nginx |
| P2 | JWT httpOnly |
| P3 | DB pool + feed COUNT |
| P4 | `/ops/` nginx auth |
| P5 | Webhook HMAC body |

---

## § CABINET-PARITY — Lead ✅ 2026-06-21

| # | DoD |
|---|-----|
| Push `🔔 Match` без % | VPS `match_push.py` ✅ |
| ЛК уведомления без % | кнопки порога ✅ |
| Retake квиза | `#rl-cabinet-quiz-retake` напротив «Мои отклики» · **без** показа навыков (quiz-first) |

pytest: `test_match_push_o50` · `test_match_push_o250` · deploy API+Next.

---

## § PRE-M1-SECURITY — Lead ✅ 2026-06-21

Commit `786aede` · Bearer-only `/v1/me/*`.

Архив § → [`CODER_PROMPT_ARCHIVE`](../archive/CODER_PROMPT_ARCHIVE.md).
