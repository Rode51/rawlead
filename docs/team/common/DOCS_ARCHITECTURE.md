# Архитектура документации — один источник правды

**Lead Architect ведёт этот файл** (`docs/team/common/`).

---

## Корень `docs/` — только 3 файла

| Файл | Канон |
|------|--------|
| **`README.md`** | Главная карта всего repo docs |
| **`FOR_YOU.md`** | Шаги владельца **сейчас** |
| **`KAK_ETO_RABOTAET.md`** | Как работает (простым языком) |

**Всё остальное — в подпапках.** Новый файл в корень **запрещён** без согласия владельца.

---

## Папки `docs/team/`

| Папка | Кто | Содержание |
|-------|-----|------------|
| **`common/`** | все AI | PROJECT_MAP, STATUS, TASKS, SCALE, DOCS_ARCHITECTURE, HOW_TO_USE_CURSOR, MCP |
| **`architect/`** | Lead Architect, Coder (промпт) | LEAD, ROADMAP, CODER_PROMPT, ARCHITECTURE, CODE_STRUCTURE, NEON_SCHEMA, TZ_* |
| **`product/`** | Lead Product | PRODUCT_VISION, LEAD_PRODUCT*, PORTFOLIO |
| **`design/`** | Lead Designer, Designer | LEAD_DESIGN*, DESIGN_SYSTEM, DESIGNER_PROMPT, DESIGN_BRIEF |
| **`archive/`** | — | история, исследования (не обновлять) |

Другие папки `docs/`: `ops/`, `problems/`, `design/` (макеты PNG), `archive/`.

---

## Канон по темам

| Тема | Файл |
|------|------|
| **Навигация AI** | `team/common/PROJECT_MAP.md` |
| Фазы (из vision) | `team/architect/ROADMAP.md` — **Lead Architect** |
| Vision продукта | `team/product/PRODUCT_VISION.md` — **Lead Product** |
| Шаги владельца | `FOR_YOU.md` |
| Как устроено | `KAK_ETO_RABOTAET.md` |
| Очередь | `team/common/TASKS.md` |
| Снимок | `team/common/STATUS.md` |
| Coder ТЗ | `team/architect/CODER_PROMPT.md` |
| Product план | `team/product/LEAD_PRODUCT_PROMPT.md` |
| Design план | `team/design/LEAD_DESIGN_PROMPT.md` |
| Product регламент | `team/product/LEAD_PRODUCT.md` |
| Design регламент | `team/design/LEAD_DESIGN.md` |
| Git / чистота | `team/architect/LEAD.md` § Git |
| MCP | `team/common/MCP_POOL.md` |
| Запуск | `ops/RUN.md` |
| TG acc | `ops/TELEGRAM_ACCOUNTS.md` |
| Фильтр (код) | `ops/FILTERS.md` |
| FL/Kwork + TG | `ops/SOURCES_POOLS.md` |

---

## Архив (не обновлять)

| Было | Стало |
|------|--------|
| `docs/ROADMAP.md` | `team/architect/ROADMAP.md` |
| `docs/PORTFOLIO.md` | `team/common/PORTFOLIO.md` |
| `team/*.md` в корне team | `common/` · `architect/` · `product/` · `design/` |
| `ops/SOURCES.md` | `archive/SOURCES.md` |
| `ops/SOURCES_SAAS.md` | `archive/SOURCES_SAAS.md` + stub в `ops/` |

---

## Правила

1. Одна тема = один канон (таблица выше).
2. FOR_YOU ≤ 1 экран; детали → README или KAK_ETO.
3. STATUS без копипаста ТЗ.
4. Новый `.md` — только с согласия владельца + строка в § Канон.
5. **Coder/Designer/Mechanic** — не создают файлы вне своей зоны (см. PROJECT_MAP § «Агентам»).

---

## Проверка чистоты

| Проверено | Результат |
|-----------|-----------|
| Корень `docs/` | 3 файла |
| `docs/team/` | 4 рабочие папки + `archive/` |
| `docs/team/design/` vs `docs/design/` | markdown vs макеты — **не путать** |

---

_Lead Architect · 2026-05-24 · реорганизация team/_
