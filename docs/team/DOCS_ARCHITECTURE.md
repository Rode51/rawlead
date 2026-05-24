# Архитектура документации — один источник правды

**Lead ведёт этот файл.**

---

## Корень `docs/` — только 3 файла

| Файл | Канон |
|------|--------|
| **`README.md`** | Главная карта всего репо docs |
| **`FOR_YOU.md`** | Шаги владельца **сейчас** |
| **`KAK_ETO_RABOTAET.md`** | Как работает (простым языком) |

**Всё остальное — в подпапках.** Новый файл в корень **запрещён** — только с **согласия владельца**.

---

## Папки

| Папка | Содержание |
|-------|------------|
| `team/` | ROADMAP, STATUS, TASKS, промпты, PROJECT_MAP, vision |
| `ops/` | RUN, TG, фильтры, WP ops |
| `problems/` | Тикеты Mechanic |
| `design/` | UI, PNG |
| `archive/` | Устаревшее (SOURCES, wp-skeleton, TZ ф0, …) |
| `team/archive/` | История задач, исследования |

---

## Канон по темам

| Тема | Файл |
|------|------|
| Фазы (из vision) | `team/ROADMAP.md` — **Lead Architect** |
| Vision продукта | `team/PRODUCT_VISION.md` — **Lead Product** |
| Шаги владельца | `FOR_YOU.md` |
| Как устроено | `KAK_ETO_RABOTAET.md` |
| Очередь | `team/TASKS.md` |
| Снимок | `team/STATUS.md` |
| Coder ТЗ | `team/CODER_PROMPT.md` |
| Product план (Lead PM) | `team/LEAD_PRODUCT_PROMPT.md` |
| Design план (Lead Design) | `team/LEAD_DESIGN_PROMPT.md` |
| Product регламент | `team/LEAD_PRODUCT.md` |
| Design регламент | `team/LEAD_DESIGN.md` |
| AI карта / навигация | `team/PROJECT_MAP.md` (+ `docs/README.md`) — **первый ход всех AI** |
| Git / чистота repo | `team/LEAD.md` § Git — commit/push **Lead Architect** |
| MCP (веб, браузер, картинки) | `team/MCP_POOL.md` · шаблон `team/mcp.pool.example.json` |
| Запуск | `ops/RUN.md` |
| TG acc | `ops/TELEGRAM_ACCOUNTS.md` |
| Фильтр (код) | `ops/FILTERS.md` |
| FL/Kwork + TG чаты | `ops/SOURCES_POOLS.md` |
| Портфолио | `team/PORTFOLIO.md` |

---

## Архив (не обновлять)

| Было | Стало |
|------|--------|
| `docs/ROADMAP.md` | `team/ROADMAP.md` |
| `docs/PORTFOLIO.md` | `team/PORTFOLIO.md` |
| `ops/SOURCES.md` | `archive/SOURCES.md` |
| `ops/WP_OWNER_STEPS.md` | `archive/WP_OWNER_STEPS.md` |
| `ops/wp-skeleton/` | `archive/wp-skeleton/` |
| `team/TZ.md` | `team/archive/TZ.md` |
| `team/VISION_SAAS_SITE.md` | `team/archive/VISION_SAAS_SITE.md` |
| `team/RESEARCH_TGAIJOBS.md` | `team/archive/RESEARCH_TGAIJOBS.md` |

---

## Правила

1. Одна тема = один канон (таблица выше).
2. FOR_YOU ≤ 1 экран; детали → README или KAK_ETO.
3. STATUS без копипаста ТЗ.
4. **По умолчанию — правка** существующего канона, не новый файл.
5. **Новый `.md`** (кроме тикета `problems/`) — **только с явного согласия владельца** («да» / «согласую»).
6. Lead: нет согласия → секция в каноне или вопрос владельцу одной строкой.
7. **Coder/Designer/Mechanic** — не создают `docs/team/*.md` и не трогают корень `docs/`.

---

## Защита проекта (3 уровня)

### 1. Регламент (этот файл)

Lead: **правка** канона — свободно. **Новый** файл — строка в § Канон **после согласия владельца**.

### 2. Cursor

| Правило | Когда |
|---------|--------|
| [`docs-guard.mdc`](../../.cursor/rules/docs-guard.mdc) | открыт/правится `docs/**` |
| `lead-no-code.mdc` | Lead не плодит код вместо docs |
| `coder.mdc` | Coder — только STATUS + файлы из промпта |

Карта правил: [`.cursor/rules/README.md`](../../.cursor/rules/README.md)

### 3. Git (опционально, задача Coder)

Pre-commit: **reject** если добавлен `.md` в `docs/` корень (кроме 3 файлов) или новый `docs/team/*.md` без Lead. Скрипт — по запросу владельца в `CODER_PROMPT`.

### Что делать, если AI «написал лишний md»

1. Не мержить / `git checkout -- path`
2. Содержимое перенести в **канон** одной секцией
3. Lead обновляет DOCS_ARCHITECTURE, если тема новая и нужна

---

## Чеклист Lead (новый doc)

- [ ] Есть ли уже канон в § Канон? → если да, **только правка**
- [ ] **Владелец согласовал** новый файл (явное «да»)
- [ ] Добавил строку в § Канон
- [ ] Не дублирует FOR_YOU / STATUS / TASKS
- [ ] Корень `docs/` не тронут (кроме 3 файлов)

---

## Проверка чистоты (Lead Architect)

| Проверено | Результат |
|-----------|-----------|
| Корень `docs/` | Только README, FOR_YOU, KAK_ETO |
| Дубли ROADMAP/PORTFOLIO в корне | Нет |
| `team/TZ.md`, `team/RESEARCH_*` вне archive | Нет (только `team/archive/`) |
| `contour` в активных канонах | Только пометки «отменено» + TZ_API исправлен |
| `data/` тесты в git | В `.gitignore` |

---

_Lead · 2026-05-24_
