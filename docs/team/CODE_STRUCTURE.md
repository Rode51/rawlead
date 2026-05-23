# Структура кода — где что лежит

**Для:** Coder, Lead, владелец (карта «куда смотреть»).  
**Схема процессов:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · **запуск:** [`../ops/RUN.md`](../ops/RUN.md)

---

## Папки (сейчас)

| Путь | Что внутри |
|------|------------|
| **`src/`** | Движок радара: парсеры, TG, ИИ, бот, storage, config |
| **`scripts/`** | Точки входа с ПК: `tg_main.py`, `radar_control.py`, join/import, `.bat` |
| **`desktop/`** | Пульт Tauri (UI + `src-tauri/`) |
| **`docs/ops/`** | Настройки владельца: FILTERS, PROFILE, RUN, CSV очереди |
| **`docs/team/`** | Процесс: TASKS, STATUS, TZ, промпты |
| **`data/`** | Только на ПК: БД, логи, сессии, chat_id (gitignore) |

---

## `src/` — модули (одна зона ответственности = один файл)

| Файл | Зона |
|------|------|
| `main.py` | Цикл FL/Kwork |
| `fl_parser.py`, `kwork_parser.py` | Биржи |
| `tg_client.py` | Telethon connect |
| `tg_monitor.py` | Слушание чатов + join-циклы |
| `tg_join_lib.py` | CSV очередь, join_one |
| `tg_join_runner.py` | Тик join, лимиты |
| `tg_join_registry.py` | Один client на acc (без lock) |
| `tg_forward.py` | Пересылка поста владельцу |
| `lead_pipeline.py` | TG: фильтр → ИИ → notify |
| `telegram_notify.py`, `telegram_control.py` | Bot API |
| `filters.py`, `ai_analyze.py` | Фильтр и ИИ |
| `storage.py`, `pg_storage.py` | SQLite / Neon |
| `config.py` | `.env` |
| `radar_status.py`, `health_check.py` | Статус, health |

**Не раздувать** `tg_monitor.py` / `config.py` — новое выносить в отдельный файл.

---

## `scripts/` — запуск

| Файл | Запуск |
|------|--------|
| `tg_main.py` | TG + join (главное окно Telethon) |
| `radar_control.py` | API пульта (:18765) |
| `tg_queue_import.py` | CSV ← EXPORT |
| `tg_join_queue.py` | Ручной join (редко; lock если tg_main жив) |
| `tg_join_daemon.py` | **Deprecated** — no-op |
| `start-radar-full.bat` | 2 cmd: биржи + TG |

---

## Правила Coder (обязательно)

1. **Без «простынь»** — не добавлять в один файл сотни строк без разбиения; новая логика → новый модуль или явный подфайл пакета.
2. **Один файл — одна роль** (см. таблицу выше). Не смешивать join + notify + парсинг FL в одном месте.
3. **Перенос по папкам** — только отдельная задача Lead в `CODER_PROMPT.md`:
   - карта «было → стало»;
   - правка **всех** импортов, `scripts/`, `.bat`, `radar_control`, `.env.example`, `RUN.md`;
   - чеклист запуска пульт + TG + биржи.
4. **Мелкий diff** предпочтительнее «переехать весь src за раз».

---

## Бэклог (не сейчас)

- Пакеты `src/tg/`, `src/parsers/` — если вырастет >40 модулей; до тех пор плоский `src/` ок.

---

_Ведёт Lead. После реорганизации — обновить этот файл и [`ARCHITECTURE.md`](ARCHITECTURE.md)._
