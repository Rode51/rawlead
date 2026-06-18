# Правила Cursor (`.cursor/rules/`)

## Старт по роли (одинаковая схема)

**Всегда:** `docs/README.md` → `docs/team/common/PROJECT_MAP.md` (§ «Агентам») → **файл задачи**.

| Роль в чате | Правило `.mdc` | Файл задачи (шаг 3) |
|-------------|----------------|----------------------|
| `@lead-architect` | `lead-architect.mdc` | **онбординг A+B+C** · **`PROD_FACTS`** · `STATUS` · `TASKS` · `CODER_PROMPT` |
| `@lead-product` | `lead-product.mdc` | `LEAD_PRODUCT_PROMPT` · **онбординг A+B+C** |
| `@lead-marketing` | `lead-marketing.mdc` | `LEAD_MARKETING_PROMPT` · **онбординг A+B+C** |
| `@lead-designer` | `lead-designer.mdc` | **`LEAD_DESIGN_PROMPT`** · регламент **`LEAD_DESIGN.md`** |
| `@lead-portfolio` | `lead-portfolio.mdc` | **`LEAD_PORTFOLIO_PROMPT`** · регламент **`LEAD_PORTFOLIO.md`** |
| `@coder` | `coder.mdc` | **`CODER_PROMPT.md`** только (без vision, без design) |
| `@designer` | `designer.mdc` | **`DESIGNER_PROMPT.md` hot** (~80 строк) |
| `@mechanic` | `mechanic.mdc` | **`PROD_FACTS`** · **`docs/problems/<тикет>.md`** |
| `@owner` | `owner.mdc` | **`docs/FOR_YOU.md`** |

**Always (в каждом чате):** `economy.mdc` · `lead-no-code.mdc` (Lead не кодят)

---

## Design-отдел — один конвейер (не путать)

```text
Владелец ↔ @lead-designer → LEAD_DESIGN_PROMPT (решения)
         → @designer → docs/design/wp/wave-*-brief.md ИЛИ DESIGNER_PROMPT § одна активная
         → @lead-architect → CODER_PROMPT § (ссылки)
         → @coder → wordpress/ (не design docs)
```

| Файл | Кто | Содержание |
|------|-----|------------|
| `LEAD_DESIGN_PROMPT.md` | Lead Designer | Решения владельца · **одна § в шапке** |
| `DESIGNER_PROMPT.md` | Lead Designer | **одна активная §** · архив ниже — **не читать** |
| `docs/design/wp/REFERENCE.md` | Lead Designer | Визуальный канон v5 |
| `docs/design/wp/wave-*-brief.md` | Designer | Техспека для Coder |
| `DESIGN_BRIEF.md` | Designer | **Только пульт Tauri** — не WP |
| `DESIGNER.md` / `LEAD_DESIGN.md` | — | Регламент ролей |

Подробно: [`docs/team/design/LEAD_DESIGN.md`](../../docs/team/design/LEAD_DESIGN.md)

---

## Карта `.mdc`

### Всегда

| Файл | Зачем |
|------|--------|
| `economy.mdc` | Старт · git Lead · MCP · design map |
| `lead-no-code.mdc` | Lead = 0 кода |

### Lead — `@…`

| Файл | В чате |
|------|--------|
| `lead-architect.mdc` | `@lead-architect` |
| `lead-product.mdc` | `@lead-product` |
| `lead-marketing.mdc` | `@lead-marketing` |
| `lead-designer.mdc` | `@lead-designer` |
| `lead-portfolio.mdc` | `@lead-portfolio` |

### Исполнители

| Файл | В чате |
|------|--------|
| `coder.mdc` | `@coder` |
| `mechanic.mdc` | `@mechanic` |
| `designer.mdc` | `@designer` |
| `owner.mdc` | `@owner` |

### Гарды (globs)

| Файл | Когда |
|------|--------|
| `code-guard.mdc` | `src/` · `scripts/` · `wordpress/` · `deploy/` · `sql/` · `desktop/` |
| `docs-guard.mdc` | `docs/**` |

---

## Экономия токенов (2026-05-30)

| Файл | Hot | Архив | Правило |
|------|-----|-------|---------|
| `PROD_FACTS.md` | snapshot + VPS auto-block | — | все AI перед triage |
| `STATUS.md` | ~80 строк | `STATUS_ARCHIVE.md` | Lead: после ✅ → архив |
| `CODER_PROMPT.md` | ~120 строк | `CODER_PROMPT_ARCHIVE.md` | одна § в шапке |
| `TASKS.md` | активное (~50) | `TASKS_HISTORY.md` | одна строка на трек |

**Coder** читает § шапки, не архив. **Lead** не читает архив без grep. Канон: `economy.mdc` § «Бюджет контекста».

**Перенос в другой repo:** [`docs/team/templates/cursor-team-kit/README.md`](../../docs/team/templates/cursor-team-kit/README.md)

---

## Harness O119 (skills, не ECC)

| Что | Где |
|-----|-----|
| Каталог | [`.cursor/skills/README.md`](../../.cursor/skills/README.md) |
| Правила ролей | **без изменений** — `.mdc` как раньше |
| Оркестратор | **только `@lead-architect`** — отдельной роли нет |

Skills подхватываются Agent **по задаче** (дешевле, чем 251 skill ECC). Full ECC в repo **не ставим**.

Владельцу: [`HOW_TO_USE_CURSOR.md`](../../docs/team/common/HOW_TO_USE_CURSOR.md) § Harness.

---

## Быстрый старт владельца

1. **Settings → Rules** — Project Rules включены.
2. **Новый чат = одна роль** — `@coder` / `@lead-designer` / …
3. [`docs/team/common/HOW_TO_USE_CURSOR.md`](../../docs/team/common/HOW_TO_USE_CURSOR.md)
4. MCP: [`docs/team/common/MCP_POOL.md`](../../docs/team/common/MCP_POOL.md)
