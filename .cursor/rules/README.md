# Правила Cursor (`.cursor/rules/`)

## Что значит выпадашка в UI

| Режим в Cursor | Поле в `.mdc` | Когда подключается |
|----------------|---------------|-------------------|
| **Always Apply** | `alwaysApply: true` | В **каждом** чате и cmd-k |
| **Apply Intelligently** | `alwaysApply: false`, без `globs` | Agent сам решает по `description` |
| **Apply Manually** | то же + вызываешь **`@имя-файла`** в чате | Только когда ты @-упомянул правило |
| **Apply to Specific Files** | `globs: src/**,…` | Когда открыт/трогаешь файл под маской |

**Рекомендация для ролей:** `alwaysApply: false` → в чате пиши **`@lead-architect`**, **`@lead-product`**, **`@lead-designer`**, **`@coder`**, **`@mechanic`**, **`@designer`**, **`@owner`**.

---

## Карта файлов (11 штук — не дубли)

### Всегда (2)

| Файл | Зачем |
|------|--------|
| `economy.mdc` | Кратко, факты из repo, русский |
| `lead-no-code.mdc` | **Все Lead не кодят** — страховка |

### Lead (стратегия, только docs) — `@…`

| Файл | В чате |
|------|--------|
| `lead-architect.mdc` | `@lead-architect` — инженерия, `CODER_PROMPT` |
| `lead-product.mdc` | `@lead-product` — vision, roadmap, `LEAD_PRODUCT_PROMPT` |
| `lead-designer.mdc` | `@lead-designer` — design system, `LEAD_DESIGN_PROMPT` |

### Исполнители — `@…`

| Файл | В чате |
|------|--------|
| `coder.mdc` | `@coder` — код по `CODER_PROMPT.md` |
| `mechanic.mdc` | `@mechanic` — тикет `docs/problems/` |
| `designer.mdc` | `@designer` — UI/UX по `DESIGNER_PROMPT.md` |
| `owner.mdc` | `@owner` — FOR_YOU, .env, запуск |

### Гард по путям (2)

| Файл | Зачем |
|------|--------|
| `code-guard.mdc` | Открыт `src/` / `scripts/` / `desktop/` → код только `@coder` / `@mechanic` |
| `docs-guard.mdc` | Открыт `docs/**` → не плодить `.md` · [`DOCS_ARCHITECTURE.md`](../../docs/team/DOCS_ARCHITECTURE.md) |

---

## Почему «по 2» у Lead и Coder (+ guards)

| Роль | Файл 1 | Файл 2 |
|------|--------|--------|
| **Lead** | `lead-architect.mdc` — *как* работать (docs, промпты) | `lead-no-code.mdc` — *запрет* кода **всегда** |
| **Coder** | `coder.mdc` — *как* кодить (промпт, STATUS) | `code-guard.mdc` — при правке `src/` |
| **docs/** | — | `docs-guard.mdc` — не плодить `.md` |

Это **не два Lead и не два Coder** — разные триггеры: роль вручную vs страховка always / globs.

---

## Быстрый старт

1. **Settings → Rules** — Project Rules включены.
2. Закладки: Lead PM · Lead Design · Lead Arch · Coder · Designer · Mechanic.
3. Подробнее: [`docs/team/HOW_TO_USE_CURSOR.md`](../../docs/team/HOW_TO_USE_CURSOR.md)
