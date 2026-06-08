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
| `main.py` | Цикл FL/Kwork + secondary (O63) |
| `fl_parser.py`, `kwork_parser.py` | Биржи primary |
| `youdo_parser.py`, `freelance_ru_parser.py`, `freelancejob_parser.py`, `pchyol_parser.py` | Secondary ingest (O63) |
| `exchange_browser_fetch.py` | Playwright persistent per proxy slot (O99) |
| `exchange_proxy.py` | HTTP proxy pool, per-source bans v2 |
| `tg_client.py` | Telethon connect |
| `proxy_probe.py` | TCP probe прокси (fail-closed) |
| `tg_monitor.py` | Слушание чатов + join-циклы |
| `tg_join_lib.py` | CSV очередь, join_one |
| `tg_join_runner.py` | Тик join, лимиты |
| `tg_join_registry.py` | Один client на acc (без lock) |
| `tg_forward.py` | Пересылка поста владельцу |
| `exchange_detail.py` | O141 dispatch detail-fetch для web-бирж |
| `lead_pipeline.py` | ingest: фильтр → ИИ → notify / L1 pool |
| `telegram_notify.py`, `telegram_control.py` | Bot API |
| `filters.py`, `ai_analyze.py` | Фильтр и ИИ |
| `api_server.py` | FastAPI Site: `/v1/feed`, auth, draft, me — **~2.2k строк** |
| `match_push.py` | Match push + on-demand draft в боте — **~1k** |
| `owner_admin.py` | `/ops/` HTML-пульт — **~1.9k** |
| `pg_storage.py` | Neon CRUD — **~1.8k** |
| `storage.py` | SQLite (локально) |
| `config.py` | `.env` |
| `radar_status.py`, `health_check.py` | Статус, health |

**Не раздувать** `tg_monitor.py` / `config.py` — новое выносить в отдельный файл.

### Тяжёлые файлы (legacy) — риск путаницы

| Файл | Строк | Риск | Как работать |
|------|-------|------|--------------|
| `api_server.py` | ~2260 | 🔴 | Только по § «Файлы» в `CODER_PROMPT`; новые роуты → отдельный router-модуль, не +200 строк внутрь |
| `ai_analyze.py` | ~2140 | 🔴 | L1/L2/L3 в одном месте; новая логика L2 → `l3_human_style.py` / отдельный guard; split — отдельная задача Lead |
| `owner_admin.py` | ~1930 | 🟡 | Ops UI; правки точечно по секции `/ops/` |
| `pg_storage.py` | ~1780 | 🟡 | Одна зона (Neon); новые таблицы — по `NEON_SCHEMA` + Lead |
| `lead_pipeline.py` | ~1010 | 🟡 | Ingest-оркестрация; detail → `exchange_detail.py`, парсинг → `*_parser.py` |

**Coder** не обязан читать эти файлы целиком — только функции из § «Файлы». **Человек без карты** — высокий риск «открыл api_server и потерялся».

**Split god-files** — backlog **после ads** (отдельный § Lead, не «Coder сам переезжает»).

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
- **O142** — `ai_analyze.py` → `src/ai/` (post-ads, § `OWNER_INTENT`)
- **O143** — `api_server.py` → FastAPI routers (post-ads, § `OWNER_INTENT`)

---

_Ведёт Lead. После реорганизации — обновить этот файл и [`ARCHITECTURE.md`](ARCHITECTURE.md)._
