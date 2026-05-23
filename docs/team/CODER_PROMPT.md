# Coder — волна 3: полная очередь join (Google Doc → CSV)

**Решение владельца (2026-05-23):** все каналы из реестра — в `TG_JOIN_QUEUE.csv` как `pending`, join по лимитам кода (4/час, 25/сутки, ночь 02:00–07:00). Распределение **acc1 / acc2 / acc3** поровну.

---

## Цель

1. Импортировать каналы из [Google Doc](https://docs.google.com/document/d/1KplF0v2eBr_o0ThbON17sRnfDqoMfiIkk_M3HkLtjfE/edit?usp=sharing) в очередь.
2. **Не трогать** строки со `status=done` (14 шт. MVP + волна 2).
3. Новые строки: `wave=3`, `status=pending`, `chat_id` пустой, `account` — round-robin acc1→acc2→acc3.
4. Скрипт импорта + документация для владельца.

**Лимиты в `.env` не повышать** (оставить 4/час, 25/сутки), пока Lead не скажет иначе.

---

## Исключить (обязательно)

| Правило | Деталь |
|---------|--------|
| Секция 7 Google Doc | Спам/серое — не добавлять |
| Блоклист | [`docs/ops/TG_JOIN_BLOCKLIST.txt`](../ops/TG_JOIN_BLOCKLIST.txt) |
| Уже в CSV | Тот же `link` (нормализованный) — пропуск, `done` не менять |
| Дубли в импорте | Одна ссылка = одна строка |

Нормализация ссылки: lowercase host, без trailing `/`, `https://t.me/...`.

---

## Входные данные

**Готово:** [`docs/ops/TG_CHANNELS_EXPORT.txt`](../ops/TG_CHANNELS_EXPORT.txt) — **73** новые ссылки (секции 1–6 Doc, без §7; 14 уже `done` в CSV не дублировать).

Строки «Проверить вручную» без `t.me` / `@` в Doc — **не в EXPORT** (~17 шт.; при необходимости — отдельная задача владельца).

---

## Скрипт (создать)

`scripts/tg_queue_import.py`:

```text
python scripts/tg_queue_import.py --dry-run   # сколько pending, по acc
python scripts/tg_queue_import.py           # записать CSV
```

- Читает `TG_CHANNELS_EXPORT.txt` + blocklist + текущий CSV.
- Round-robin `account` только для **новых** pending.
- Вывод: добавлено N, пропущено (done/duplicate/blocklist).

---

## Распределение acc

| acc | Роль (ориентир) |
|-----|-----------------|
| acc1 | фриланс-агрегаторы, общие чаты |
| acc2 | IT / dev / Python / JS |
| acc3 | WP, 1С, логистика |

При round-robin порядок новых строк: acc1, acc2, acc3, acc1, …

---

## Docs (после импорта)

| Файл | Действие |
|------|----------|
| [`docs/ops/TG_JOIN_SCHEDULE.md`](../ops/TG_JOIN_SCHEDULE.md) | § волна 3: очередь bulk, срок ~3–7 дней при 3 acc |
| [`docs/ops/TG_CHANNELS_BASE.md`](../ops/TG_CHANNELS_BASE.md) | Чеклист волна 3 ✅ |
| [`docs/ops/RUN.md`](../ops/RUN.md) | Одна строка: EXPORT + import |
| [`docs/team/STATUS.md`](STATUS.md) | Сделано / сколько pending / как проверить |

---

## Как проверить (STATUS)

1. `python scripts/tg_queue_import.py --dry-run` — счётчики по acc, 0 в blocklist попаданий ошибочно.
2. `grep pending docs/ops/TG_JOIN_QUEUE.csv | wc -l` (или PowerShell `(Select-String pending ...).Count`).
3. Владелец: пульт ▶ → через сутки `data/tg_join.log` — `join:ok`, не сплошной `fail`/`лимит`.
4. `done` строк MVP/волна 2 — без изменений.

---

## Не делать

- Массовый join вручную одним скриптом без очереди.
- Повышать `TG_JOIN_MAX_*` без задачи Lead.
- Править `TASKS.md`, `FOR_YOU.md`.

---

_Lead · 2026-05-23_
