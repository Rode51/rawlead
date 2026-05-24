# Правила Cursor (`.cursor/rules/`)

## Старт по роли (одинаковая схема)

**Всегда:** `docs/README.md` → `docs/team/PROJECT_MAP.md` (§ «Агентам») → **файл задачи**.

| Роль в чате | Правило `.mdc` | Файл задачи (шаг 3) |
|-------------|----------------|----------------------|
| `@lead-architect` | `lead-architect.mdc` | `TASKS` · `STATUS` · пишешь `CODER_PROMPT` |
| `@lead-product` | `lead-product.mdc` | `PRODUCT_VISION.md` · `LEAD_PRODUCT_PROMPT.md` |
| `@lead-designer` | `lead-designer.mdc` | `LEAD_DESIGN_PROMPT.md` → `DESIGNER_PROMPT.md` |
| `@coder` | `coder.mdc` | **`CODER_PROMPT.md`** |
| `@designer` | `designer.mdc` | **`DESIGNER_PROMPT.md`** |
| `@mechanic` | `mechanic.mdc` | **`docs/problems/<тикет>.md`** |
| `@owner` | `owner.mdc` | **`FOR_YOU.md`** |

**Always (в каждом чате):** `economy.mdc` · `lead-no-code.mdc` (Lead не кодят)

---

## Что значит выпадашка в UI

| Режим в Cursor | Поле в `.mdc` | Когда подключается |
|----------------|---------------|-------------------|
| **Always Apply** | `alwaysApply: true` | В **каждом** чате и cmd-k |
| **Apply Intelligently** | `alwaysApply: false`, без `globs` | Agent сам решает по `description` |
| **Apply Manually** | то же + вызываешь **`@имя-файла`** в чате | Только когда ты @-упомянул правило |
| **Apply to Specific Files** | `globs: src/**,…` | Когда открыт/трогаешь файл под маской |

**Рекомендация:** роли — **`@coder`**, **`@lead-architect`**, … в начале чата, не полагаться на «умное» подключение.

---

## Карта файлов

### Всегда (2)

| Файл | Зачем |
|------|--------|
| `economy.mdc` | Старт 1–2–3 · кратко · git Lead · MCP |
| `lead-no-code.mdc` | Все Lead — запрет кода |

### Lead — `@…`

| Файл | В чате |
|------|--------|
| `lead-architect.mdc` | `@lead-architect` |
| `lead-product.mdc` | `@lead-product` |
| `lead-designer.mdc` | `@lead-designer` |

### Исполнители — `@…`

| Файл | В чате |
|------|--------|
| `coder.mdc` | `@coder` |
| `mechanic.mdc` | `@mechanic` |
| `designer.mdc` | `@designer` |
| `owner.mdc` | `@owner` |

### Гарды (globs)

| Файл | Когда |
|------|--------|
| `code-guard.mdc` | открыт `src/` · `scripts/` · `desktop/` |
| `docs-guard.mdc` | открыт `docs/**` |

---

## Быстрый старт владельца

1. **Settings → Rules** — Project Rules включены.
2. Закладки чатов: Lead PM · Lead Design · Lead Arch · Coder · Designer · Mechanic.
3. [`docs/team/HOW_TO_USE_CURSOR.md`](../../docs/team/HOW_TO_USE_CURSOR.md)
4. MCP: [`docs/team/MCP_POOL.md`](../../docs/team/MCP_POOL.md)
