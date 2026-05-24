# Карта проекта — для всех AI

**Одна точка входа.** Детали — по ссылкам, не копировать сюда целиком.

## Навигация — перед любой работой

| Шаг | Кто | Действие |
|-----|-----|----------|
| 0 | **Все AI** | [`docs/README.md`](../README.md) — дерево папок `docs/` |
| 1 | **Все AI** | **Этот файл** (`PROJECT_MAP.md`) — зоны, процессы, «куда идти» |
| 2 | **Все AI** | Файл роли из таблицы «Кому» ниже — **не** обходить repo наугад |
| 3 | **Lead Architect** | После приёмки Coder/Mechanic/Product/Design — **обновить эту карту**, если сменились пути, зоны или lock |

**Lead Architect** ведёт чистоту repo: дедуп docs, `git commit` / `git push` (по просьбе владельца). Coder/Mechanic/Designer **не коммитят** без явной просьбы Lead.

---

## Агентам: куда смотреть и куда **не** писать

| Нужно | Единственный канон | Не дублировать в |
|-------|-------------------|------------------|
| Vision / ставка B | [`PRODUCT_VISION.md`](PRODUCT_VISION.md) v0.9 | ROADMAP, STATUS, чат |
| Фазы «сейчас» | [`ROADMAP.md`](ROADMAP.md) | FOR_YOU, TASKS простынёй |
| Активный план Product | [`LEAD_PRODUCT_PROMPT.md`](LEAD_PRODUCT_PROMPT.md) | новый `TZ_*.md` |
| Задача Coder | [`CODER_PROMPT.md`](CODER_PROMPT.md) | TASKS, чат (только копипаст) |
| Задача Designer | [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) | DESIGN_BRIEF без промпта |
| План Lead Designer | [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) | |
| Снимок / блокеры | [`STATUS.md`](STATUS.md) | не копировать ТЗ |
| Очередь | [`TASKS.md`](TASKS.md) — одна строка на трек | FOR_YOU |
| Шаги владельца | [`../FOR_YOU.md`](../FOR_YOU.md) | TASKS, STATUS |
| Поломка | [`../problems/`](../problems/) один файл | новый md в `team/` |
| Устаревшее | [`archive/`](../archive/), [`team/archive/`](archive/) | не обновлять |

| Роль | Пишет | Не пишет |
|------|-------|----------|
| **Lead Product** | `PRODUCT_VISION`, `LEAD_PRODUCT_PROMPT` | `ROADMAP`, `CODER_PROMPT`, `FOR_YOU` |
| **Lead Designer** | `LEAD_DESIGN*`, `DESIGN_SYSTEM`, `docs/design/` | `wordpress/`, `CODER_PROMPT` |
| **Lead Architect** | `ROADMAP`, `TASKS`, `STATUS`, `CODER_PROMPT`, карты | `src/`, commit чужих без сдачи |
| **Coder** | файлы из § «Файлы» в `CODER_PROMPT` + `STATUS` | любой другой `docs/team/*.md` |
| **Designer** | `docs/design/`, `DESIGN_BRIEF` по промпту | `src/`, `wordpress/` |
| **Mechanic** | `docs/problems/*` + код из тикета | `TASKS`, `FOR_YOU`, vision |

**Отменено v0.9 (не возвращать в код/docs):** `contour` owner/saas · демо `/cabinet` на JSON · [`../archive/SOURCES_SAAS.md`](../archive/SOURCES_SAAS.md)

**Регламент docs (каноны, без дублей):** [`DOCS_ARCHITECTURE.md`](DOCS_ARCHITECTURE.md)

**Визуально (для тебя):** [`PROJECT_MAP_VISUAL.md`](PROJECT_MAP_VISUAL.md) · PNG: [`../design/rawlead/project-map-owner.png`](../design/rawlead/project-map-owner.png)

| Кому | Первый файл |
|------|-------------|
| **Lead Product** | `PRODUCT_VISION.md` v0.9 → `LEAD_PRODUCT_PROMPT.md` |
| **Lead Architect** | этот файл → `ROADMAP.md` → `CODER_PROMPT.md` |
| **Lead Designer** | `LEAD_DESIGN_PROMPT.md` → `DESIGN_SYSTEM.md` |
| **Coder** | **`CODER_PROMPT.md`** → § «Зоны» |
| **Mechanic** | `docs/problems/` → § «Зоны» |
| **Designer** | `DESIGNER_PROMPT.md` → `docs/design/` |
| **Владелец** | `FOR_YOU.md` |

**Lead обновляет** эту карту после каждой сдачи Coder/Mechanic, если менялись процессы, файлы или lock-правила.  
**Coder не правит** этот файл.

---

## MCP (внешние tools)

Канон: **[`MCP_POOL.md`](MCP_POOL.md)** — Perplexity, Playwright, Firecrawl, Glif, Chrome; когда использовать; установка в `~/.cursor/mcp.json`.

| Если в сессии нет MCP, а нужен веб/скрейп/медиа | Сказать владельцу: включить сервер из `MCP_POOL.md` |
| Ключи API | Только у владельца, не в repo |

---

## Процессы на ПК (не плодить)

```mermaid
flowchart TB
  VBS["start-radar-desktop.vbs"]
  RC["radar_control.py :18765"]
  UI["desktop/ Tauri"]
  M["src/main.py"]
  T["scripts/tg_main.py"]

  VBS --> RC
  VBS --> UI
  UI -->|HTTP /start /stop| RC
  RC -->|subprocess .venv only| M
  RC -->|subprocess .venv only| T
```

| Правило | Зачем |
|---------|--------|
| **Один venv** | `.venv\Scripts\python.exe` — не системный Python |
| **2 worker'а max** | `main.py` + `tg_main.py` |
| **Lock** | `data/.tg_main.lock`, `data/.radar_desktop.lock` |
| **Дубли** | `src/process_guard.py` — убить чужие main/tg_main перед стартом |
| **Join** | только **внутри** `tg_main` (`TG_JOIN_IN_TG_MAIN=1`) |

Запуск: [`../ops/DESKTOP_LAUNCH.md`](../ops/DESKTOP_LAUNCH.md) · схема: [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Зоны — кто что трогает

| Зона | Пути | Кто правит | Когда |
|------|------|------------|--------|
| **Пульт UI** | `desktop/src/main.ts`, `desktop/src/styles/` | Coder | только `CODER_PROMPT` § пульт |
| **Пульт API** | `scripts/radar_control.py` | Coder | старт/стоп, логи, process_guard |
| **Биржи** | `src/main.py`, `src/fl_parser.py`, `src/kwork_parser.py` | Coder | по промпту |
| **TG runtime** | `scripts/tg_main.py`, `src/tg_monitor.py` | Coder / Mechanic | промпт / тикет |
| **TG join** | `src/tg_join_*.py`, `docs/ops/TG_JOIN_QUEUE.csv` | Coder | промпт; CSV — Lead + import |
| **Pipeline** | `src/lead_pipeline.py`, `src/filters.py`, `src/ai_analyze.py` | Coder | промпт |
| **Конфиг** | `src/config.py` | Coder | минимальный diff |
| **Guard** | `src/process_guard.py`, `src/health_check.py` | Coder / Mechanic | дубли, lock |
| **Данные ПК** | `data/*` | **никто из AI** | владелец / runtime |
| **Секреты** | `.env` | **владелец** | — |
| **Product docs** | `LEAD_PRODUCT*`, `PRODUCT_VISION`, `ROADMAP` | Lead Product | план с владельцем |
| **Design docs** | `LEAD_DESIGN*`, `DESIGN_SYSTEM`, `docs/design/` | Lead Designer | план с владельцем |
| **Инженерия docs** | `CODER_PROMPT`, `TASKS`, `STATUS` | Lead Architect | после сдачи |
| **Docs ops** | `docs/ops/*`, `FOR_YOU.md` | Lead Architect + владелец | |
| **Тикеты** | `docs/problems/*` | Mechanic | один инцидент |
| **WP** | `wordpress/rawlead-kadence-child/` | Coder | `CODER_PROMPT` § WP |

**Coder:** правит **только** файлы из таблицы «Файлы» в активном `CODER_PROMPT.md`. Вне списка — стоп, спросить Lead.

**Mechanic:** `src/`, `tests/`, `scripts/` — только файлы из тикета «Решение».

---

## Модули `src/` (куда не лезть без причины)

Полная таблица: [`CODE_STRUCTURE.md`](CODE_STRUCTURE.md).

| Симптом / задача | Смотреть сначала |
|------------------|------------------|
| ✕ пульт, ▶/■ | `desktop/src/main.ts`, `radar_control.py` |
| Дубли python | `process_guard.py`, `radar_control.py` `/start` |
| TG не читает чат | `telethon_chat_ids_accN.txt`, `tg_monitor.py`, дубли tg_main |
| Join | `tg_join_runner.py`, `TG_JOIN_QUEUE.csv` |
| Бот молчит | VPN, proxy, `tg_smoke.py`, `telegram_notify.py` |
| Фильтр / ИИ | `filters.py`, `lead_pipeline.py`, `docs/ops/FILTERS.md` |

---

## Промпт Coder — обязательный блок

Каждый `CODER_PROMPT.md` **должен** содержать:

```markdown
## Файлы (можно трогать)
- path/to/file — зачем

## Файлы (не трогать)
- всё остальное
```

Lead проверяет перед выдачей промпта. Coder сверяется **до** первой правки.

---

## Чеклист Lead (после сдачи)

- [ ] `STATUS.md` совпадает с кодом
- [ ] `PROJECT_MAP.md` — если новый процесс/файл/lock
- [ ] [`ROADMAP.md`](ROADMAP.md) — если сменилась фаза, блокер или приоритет «сейчас»
- [ ] `ARCHITECTURE.md` — если изменилась схема процессов
- [ ] `CODE_STRUCTURE.md` — если новый модуль в `src/`
- [ ] `KAK_ETO_RABOTAET.md` — если изменилось поведение для владельца

---

## Связанные документы (не дублировать)

| Документ | Содержание |
|----------|------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | mermaid, SaaS target, поток данных |
| [`CODE_STRUCTURE.md`](CODE_STRUCTURE.md) | файлы `src/` и `scripts/` |
| [`LEAD.md`](LEAD.md) § «Файлы без пересечений» | один источник правды |
| [`SCALE.md`](SCALE.md) | цикл Lead → Coder → приёмка |
| [`PRODUCT_VISION.md`](PRODUCT_VISION.md) | зачем продукт, контуры |

---

_Ведёт Lead · 2026-05-24 · обновлять при смене процессов/зон_
