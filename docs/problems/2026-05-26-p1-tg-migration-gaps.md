# P1 + TG migration — пробелы приёмки (2026-05-26)

**Статус:** ⏳ открыт (TG) · P1.3c парсеры ✅ smoke 2026-05-26  
**Контекст:** владелец **не имеет доступа** к acc1/2/3 — ручная отписка невозможна. Coder сдал § P1; Lead проверил repo.

---

## Что пробилось ✅

| § | Факт в коде |
|---|-------------|
| P1.1 | `src/public_feed.py` → `GET /v1/feed`, skills catalog, `pg_storage` `is_visible` |
| P1.2 | `filter_listen_chat_ids` — только `TG_PUBLIC_FEED_ALLOWLIST.txt` ∩ `TG_JOIN_QUEUE_v2.csv` (done); TG-A JSON и droplist не в listen |
| P1.3 частично | 4 парсера в `main.py`; **habr_career** работает; VC/FH/Habr Freelance — ошибки в логе (см. STATUS) |

MVP-чаты (`ipomogator`, `workk_on`, …) **не в** новом allowlist → **не слушаются**, если фильтр активен.

---

## Что НЕ пробилось ❌

### 1. Отписка — **не делаем** (владелец 2026-05-26)

- Подписки на старые чаты **можно оставить** — радар их **не читает** (`filter_listen_chat_ids`).
- `TG_DROPLIST` — справочно / опционально для порядка в клиенте TG, **не блокер**.
- ~~`tg_leave_droplist.py`~~ — **отменено**, не в scope.

### 2. Новая пачка PDF не в join

- В `TG_JOIN_QUEUE.csv` **нет** theyseeku, remoteit, digital_jobster, perezvonyu, workoo, webfrl, …
- Listen = только `chat_id` из queue **done** ∩ allowlist → **новые каналы из allowlist молчат**, пока join не сделает Coder.

**Нужно:** `TG_JOIN_QUEUE_v2.csv` только Tier A из [`TG_PUBLIC_FEED_ALLOWLIST.txt`](../ops/TG_PUBLIC_FEED_ALLOWLIST.txt) · волны 2–3/нед.

### 3. Два канона TG-A (рассинхрон)

- `public_feed.py` всё ещё тянет **старый** `INGEST_SOURCES_SNG_25.json` priority=TG-A (`@gogetajob`, `@dh_jobs`, `@textodrom`…).
- Allowlist PDF: `@designhunters`, `@textodromo` — **другие handle**.
- Риск: слушаем не те / не слушаем нужные.

**Нужно:** единый источник — **только** `TG_PUBLIC_FEED_ALLOWLIST.txt` (убрать TG-A из JSON для listen) или синхронизировать JSON с PDF.

### 4. Парсеры сайтов

| source | Статус (Coder STATUS) |
|--------|------------------------|
| habr_career | ✅ ~25 карточек |
| vc_ru | ✅ smoke: **12** постов/API (`api.vc.ru/v2.8/timeline?subsitesIds=jobs`) |
| freelancehunt | ✅ smoke: **10** проектов (API + `FREELANCEHUNT_API_TOKEN`) |
| habr_freelance | ✅ убран из `main.py` / whitelist (410) |

**В логе радара** `vc_ru`/`freelancehunt` появятся после **перезапуска** с полным `PUBLIC_FEED_SOURCES` (до 16:53 в `radar.log` их не было).

### 5. Док vs продукт

- [`TG_MIGRATION_2026-05-26.md`](../ops/TG_MIGRATION_2026-05-26.md) пишет «владелец отписывается» — **неверно** для владельца без доступа.

---

## Приёмка (Coder)

- [x] Отписка — **не требуется** (только фильтр listen)
- [x] Listen **только** allowlist (без старого TG-A) — `public_feed.py` 2026-05-27
- [x] Join queue v2 → Tier A из allowlist — `docs/ops/TG_JOIN_QUEUE_v2.csv`, site: `TG_JOIN_QUEUE_CSV`
- [x] `PUBLIC_FEED_SOURCES` + FH token в `.env.example` / у владельца
- [x] VC + Freelancehunt smoke (12 + 10 карточек)
- [x] habr_freelance убран
- [ ] Владелец: перезапуск радара → в `radar.log` строки `vc_ru:id=…`, `freelancehunt:id=…`

---

_Lead Architect · 2026-05-26_
