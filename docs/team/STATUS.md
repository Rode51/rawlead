# STATUS

Карта: **[`../ROADMAP.md`](../ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)**

---

## Сейчас

- **Фаза 0–1 + пульт v2** ✅
- **Волна 3 TG** — **73 pending** в CSV (join по лимитам, ~3–7 дней)
- **WP локально** — §3 страницы (параллельно)

---

## Следующий шаг

| Кто | Что |
|-----|-----|
| **Владелец** | Пульт ▶ или `start-radar-full.bat` · через сутки `data/tg_join.log` (`join:ok`) |
| **Lead** | После стабильного join — `done` → `SOURCES_POOLS` / `TELEGRAM_CHATS.json` |

---

## Блокеры

- нет

---

## Последняя сессия (Coder)

**Сделано:** `scripts/tg_queue_import.py`; импорт 73 ссылок (wave=3, round-robin acc1/2/3); 14 `done` без изменений.

**Файлы:** `scripts/tg_queue_import.py`, `docs/ops/TG_JOIN_QUEUE.csv`, `docs/ops/RUN.md`, `TG_JOIN_SCHEDULE.md`, `TG_CHANNELS_BASE.md`

**Как проверить:**

1. `python scripts/tg_queue_import.py --dry-run` — добавлено 0, пропуски только done/duplicate
2. `(Select-String ",pending," docs/ops/TG_JOIN_QUEUE.csv).Count` → **73**
3. Пульт ▶ → `data/tg_join.log` — `join:ok`, не сплошной fail/лимит
4. Строки MVP/волна 2 (`status=done`) — без изменений
