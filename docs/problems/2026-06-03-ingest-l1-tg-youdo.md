# 2026-06-03 — L1 хвост · TG acc2 join · YouDo баны

**Статус:** mitigated на VPS · канон для ops и Coder.

**Связано:** [`STATUS.md`](../team/common/STATUS.md) · [`KAK_ETO_RABOTAET.md`](../KAK_ETO_RABOTAET.md) · [`FOR_YOU.md`](../FOR_YOU.md)

---

## 1. L1: «Без L1 (48 ч)» и хвост без OpenRouter

### Симптом

- В `/status`: **Без L1 (48 ч)=2** — свежие вакансии в Neon без `ai_verdict`, лента пустая по ним.
- Полная очередь **~80–100** без L1 — drain жрёт OpenRouter на старых строках.

### Корень

| Причина | Деталь |
|---------|--------|
| Drain выкл | `L1_BACKLOG_DRAIN` не был `1` в `.env.site` → пакетный L1 в конце цикла не гонялся |
| Приоритет | `drain_l1_backlog` уже `ORDER BY id DESC` (свежие первые) — ок после включения drain |
| Хвост | Старые id всё равно копились; нужна **пометка без ИИ**, не replay |

### Fix (VPS 2026-06-03)

1. `.env.site`: **`L1_BACKLOG_DRAIN=1`**
2. Снять хвост без API:
   ```powershell
   .venv\Scripts\python.exe scripts\clear_l1_backlog.py --profile site --by-age --days-old 2 --dry-run
   .venv\Scripts\python.exe scripts\clear_l1_backlog.py --profile site --by-age --days-old 2 --apply
   ```
   Факт: `cleared=80`, `missing_after=0` (защита: лиды моложе 48 ч в age-режиме).
3. Свежие при необходимости: `replay_neon_lite_site.py --profile site --lead-ids <id,...>` (sample: `pg.l1_backlog_sample_ids`).

### Лог

`конвейер:L1=N (batch≤40)` в `data/radar_site.log`.

### Не путать

- **48 ч** в `/status` — только счётчик **без L1 за последние 48 часов**.
- **Исторический хвост** — `missing_total − recent_48h` (см. `radar_status.py`).

---

## 2. TG acc2: join есть, listen нет

### Симптом

- acc2: **pending join 6** (v2), в мониторе **0–2 чата**, жёлтая строка в `/status`.
- `tg_join.log` только acc1/acc3 `no_pending`, acc2 не крутился.

### Корень

1. **`tg_monitor.py`:** при пустом `telethon_chat_ids_acc2.txt` аккаунт **пропускался** → `_join_loop` не стартовал (join только у уже слушающих сессий).
2. **CLI join:** `tg_join_queue.py --account acc2` при `TG_JOIN_IN_TG_MAIN=1` → «в отдельном процессе запрещён» + lock сессии, если radar жив.
3. **Ops:** однострочный `TG_JOIN_IN_TG_MAIN=0` в `env` **не помогает** — `load_tg_join_config()` → `load_radar_env(override=True)` перезаписывает из `.env.site`. Нужен **`sed` в файле** или join из `tg_main`.
4. После ops join скрипт мог оставить **`TG_JOIN_IN_TG_MAIN=0`** → `join_auto=нет` в логе.

### Fix

| Что | Где |
|-----|-----|
| **join-bootstrap** | `src/tg_monitor.py`: acc с `pending>0` и без `chat_ids` → сессия только для `_join_loop` |
| **Env** | VPS: `TG_JOIN_IN_TG_MAIN=1` всегда (кроме короткого ручного join со stop radar) |
| **Очередь v2** | `docs/ops/TG_JOIN_QUEUE_v2.csv` — **6** строк на acc2 (tier-a-pdf), не старый CSV |
| **Скорость join** | `TG_JOIN_MIN_DELAY_SEC=900` → ~15 мин между чатами; `TG_JOIN_MAX_PER_HOUR=4` |

### Ops-скрипты (PC → VPS)

| Скрипт | Назначение |
|--------|------------|
| `scripts/ops-vps-tg-l1-fix.py` | deploy `tg_monitor.py`, drain, join acc2 (**max 1/час** в fix), bot_start, replay |
| `scripts/ops-vps-tg-l1-finish.py` | прервать долгий join, L1 sample, restart radar |
| `scripts/tg_bot_start.py --account acc2 --force` | `/start` у **@rawlead_bot** (Site) |

### Два списка чатов

| Файл | acc2 |
|------|------|
| `TG_JOIN_QUEUE.csv` | ~25 **done** (волна 2/3 IT/WP) — id могут **не** быть в `telethon_chat_ids_acc2.txt` на VPS |
| `TG_JOIN_QUEUE_v2.csv` | **6** чатов tier-a-pdf — целевой join сейчас |

Синк старых id в listen: `python scripts/tg_sync_chat_ids.py --account acc2` (на VPS под `rawlead`).

---

## 3. YouDo: «всё в банах», категории в UI

### Симптом

- В браузере лента `youdo.com/tasks-all-opened-all` открывается, категории отмечены.
- `/status` secondary / YouDo — все прокси в бане `youdo:host`.

### Корень

| Тема | Факт |
|------|------|
| **Парсер** | `src/youdo_parser.py`, source `youdo` в `PUBLIC_FEED_SOURCES` на VPS |
| **URL** | По умолчанию `YOUDO_LISTING_URL` = `/tasks-all-opened-all` — **вся** открытая лента |
| **Категории в UI** | Чекбоксы на сайте **не попадают** в URL парсера; отсев — word_filter + L1 |
| **403** | YouDo режет datacenter httpx → `exchange_proxy` банит **per-source** `youdo:*` |
| **До 2026-06-03** | YouDo **без** `exchange_browser_fetch` (в отличие от FL/Kwork) |

### Fix (код + VPS)

1. **Browser-first** для YouDo (как FL): `listing_browser_enabled()` → `fetch_listing_html_browser("youdo", ...)`.
2. Deploy: `scripts/deploy-youdo-browser-vps.py` (upload `youdo_parser.py`, clear youdo-банов, restart radar).
3. Сброс всех банов: `scripts/clear-vps-proxy-bans.py`.

### Env (рекомендация)

```env
EXCHANGE_LISTING_BROWSER=1
YOUDO_LISTING_URL=https://youdo.com/tasks-all-opened-all
YOUDO_PROXY_URLS=http://user:pass@DEDICATED_IP:8000
```

Пустой `YOUDO_PROXY_URLS` → secondary pool (`EXCHANGE_PROXY_URLS_SECONDARY` / Telethon acc2/3) — быстрее баны.

### Лог

`fetch:youdo proxy=…` · ошибки `HTTP 403` / `antibot` в `radar_site.log`.

### Опрос

Secondary (YouDo, freelance, Пчёл) — каждый **2-й** цикл: `SECONDARY_FETCH_EVERY_N_CYCLES=2`.

### Диагностика O63 (2026-06-03, VPS `radar_site.log` + Neon)

| source | Симптом в логе | Neon `leads` |
|--------|----------------|--------------|
| **youdo** | `HTTP 403` / `all proxies banned (0/6)` · скачано **0** | **0** всего |
| **freelance_ru** | `нет карточек .project — сменилась вёрстка` | **49**, last 2026-06-01 |
| **freelancejob** | скачано **40**, `filter 6`, новых **0** | **38**, last 2026-06-02 |
| **pchyol** | скачано **0** | **36**, last 2026-06-01 |

**Вывод:** парсеры/прокси/фильтры — не «площадки пустые». **O103** → @coder. См. [`FOR_YOU.md`](../FOR_YOU.md) § YouDo.

### Ops Lead 2026-06-03 (выполнено)

| Шаг | Результат |
|-----|-----------|
| `clear-vps-proxy-bans.py` | `bans_cleared`, radar `active` |
| `deploy-youdo-browser-vps.py` | parsers + `EXCHANGE_LISTING_BROWSER=1` |
| `playwright install chromium` | уже был под `rawlead` |
| `playwright install-deps chromium` | apt-зависимости установлены |
| smoke `_smoke_youdo_vps.py` | browser **стартует** · HTML = **403 Forbidden** через прокси |
| smoke **direct IP VPS** | тоже **антибот** (`exhkqyad`, len≈1762) — datacenter IP режут |
| **После ops (18:25 UTC)** | лог: `browser_fail` → **`антibot после browser`** (не Playwright) · FR.ru **25 новых** ✅ |
| **После ops (2026-06-03 вечер)** | `YOUDO_PROXY_URLS` node-proxy RU ×3 · smoke **OK count=50** · код: antibot fix + ephemeral + Chrome UA |

---

## Проверка после фиксов

| Проверка | Ожидание |
|----------|----------|
| `/status` Без L1 (48 ч) | 0 при живом ingest |
| `/status` acc2 | чатов растёт (v2 до 6), pending ↓ |
| `grep join_auto` radar_site.log | `join_auto=да` |
| `grep fetch:youdo` | без сплошных 403; карточки в Neon `source=youdo` |
| `tg_join.log` acc2 | `join:ok` / `listen:add` |

---

_Lead · 2026-06-03_
