# Правила Cursor (`.cursor/rules/`)

## Старт по роли (одинаковая схема)

**Всегда:** `docs/README.md` → `docs/team/common/PROJECT_MAP.md` (§ «Агентам») → **файл задачи**.

| Роль в чате | Правило `.mdc` | Файл задачи (шаг 3) |
|-------------|----------------|----------------------|
| `@lead-architect` | `lead-architect.mdc` | `team/common/TASKS` · `STATUS` · `team/architect/CODER_PROMPT` |
| `@lead-product` | `lead-product.mdc` | `team/product/PRODUCT_VISION` · `LEAD_PRODUCT_PROMPT` |
| `@lead-designer` | `lead-designer.mdc` | `team/design/LEAD_DESIGN_PROMPT` → `DESIGNER_PROMPT` |
| `@coder` | `coder.mdc` | **`CODER_PROMPT.md`** только (без vision) |
| `@designer` | `designer.mdc` | **`team/design/DESIGNER_PROMPT.md`** |
| `@mechanic` | `mechanic.mdc` | **`docs/problems/<тикет>.md`** |
| `@owner` | `owner.mdc` | **`docs/FOR_YOU.md`** |

Папки: `docs/team/common/` · `architect/` · `product/` · `design/`

**Always (в каждом чате):** `economy.mdc` · `lead-no-code.mdc` (Lead не кодят)

---

## Что значит выпадашка в UI

| Режим в Cursor | Поле в `.mdc` | Когда подключается |
|----------------|---------------|-------------------|
| **Always Apply** | `alwaysApply: true` | В **каждом** чате и cmd-k |
| **Apply Intelligently** | `alwaysApply: false`, без `globs` | Agent сам решает по `description` |
| **Apply Manually** | то же + вызываешь **`@имя-файла`** в чате | Только когда ты @-упомянул правило |
| **Apply to Specific Files** | `globs: src/**,…` | Когда открыт/трогаешь файл под маской |

**Рекомендация:** в **новом чате** — один `@coder` / `@lead-product` / … Пути и **обязательное чтение** — в § «Включение» + `economy.mdc` § «Обязательное чтение». Агент **не отвечает по сути**, пока не прочитал канон (первая строка: `Прочитал: …`).

**Важно:** `.mdc` даёт роль и **куда читать**; файлы `CODER_PROMPT.md` и т.д. агент **открывает сам** (Read) — они не подгружаются автоматически, если не `@`-упомянуть.

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
3. **Первое сообщение в чате** — одна строка, например: `@coder` или `@.cursor/rules/coder.mdc`
4. Исключение: **Mechanic** — ещё `@docs/problems/<тикет>.md`
5. [`docs/team/common/HOW_TO_USE_CURSOR.md`](../../docs/team/common/HOW_TO_USE_CURSOR.md)
6. MCP: [`docs/team/common/MCP_POOL.md`](../../docs/team/common/MCP_POOL.md)
