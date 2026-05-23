# STATUS

Карта: **[`../ROADMAP.md`](../ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)**

---

## Сейчас

- **Волна 3** — 73 pending, join по лимитам
- **Coder** — унифицировать join (все acc в `tg_main`) + метка acc2/acc3 в боте → [`CODER_PROMPT.md`](CODER_PROMPT.md)
- **WP** — §3 параллельно

---

## Следующий шаг

| Кто | Что |
|-----|-----|
| **Владелец** | `@coder` + промпт · пульт ▶ |
| **Coder** | см. `CODER_PROMPT.md` |

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
