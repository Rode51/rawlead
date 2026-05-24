# Схема работы в Cursor (экономия токенов)

## Главное правило

**Всё важное — в файлах `docs/`, не в чате.**  
Чат = короткая команда. Длинные обсуждения — **Gemini в браузере**, итог 5–10 строк → Lead кладёт в `docs/`.

---

## Кому писать

| Вопрос / задача | Куда | Первое сообщение |
|-----------------|------|------------------|
| Что делать **тебе** | **`docs/FOR_YOU.md`** | без чата |
| **Продукт:** vision, контуры, метрики | **Lead Product** `@lead-product` | **`PRODUCT_VISION.md`** · инициатива: `LEAD_PRODUCT_PROMPT.md` |
| **Roadmap, TASKS, приоритеты в работу** | **Lead Architect** `@lead-architect` | **`ROADMAP.md`** ← из vision |
| **Дизайн:** стратегия UI, система, план | **Lead Designer** `@lead-designer` | [`LEAD_DESIGN.md`](team/LEAD_DESIGN.md) · план: `LEAD_DESIGN_PROMPT.md` |
| **Инженерия:** docs, Coder, приёмка | **Lead Architect** `@lead-architect` | `lead-architect.mdc` · `CODER_PROMPT.md` |
| **Дизайн UI** (исполнение) | **Designer** (новый чат) | `@designer` + `DESIGNER_PROMPT.md` (от Lead Designer) |
| **Фича / код** | **Coder** (новый чат) | `@coder` + `CODER_PROMPT.md` (от Lead Architect) |
| **Поломка** | **Mechanic** `@mechanic` | `docs/problems/…` |
| Brainstorm | **Gemini** → итог → нужный Lead | — |

### Правила Cursor — не путать

Карта всех AI: **[`docs/team/PROJECT_MAP.md`](team/PROJECT_MAP.md)** · детали: `ARCHITECTURE.md`, `CODE_STRUCTURE.md`.

Карта всех `.mdc`: **`.cursor/rules/README.md`**.

| Тип | Файлы |
|-----|--------|
| **Always** | `economy.mdc`, `lead-no-code.mdc` |
| **Роль (@ в чате)** | `lead-architect`, `lead-product`, `lead-designer`, `coder`, `mechanic`, `designer`, `owner` |
| **Гард по путям** | `code-guard.mdc` — когда открыт код |

**Apply Intelligently** в UI = Agent сам решает по `description`; для ролей надёжнее **`@coder`** / **`@lead-architect`**, а не полагаться на «умное» подключение.

Роли: **`.cursor/rules/`** · масштаб: **[`SCALE.md`](SCALE.md)** · бэкап: **[`../ops/BACKUP.md`](../ops/BACKUP.md)**

**Не пиши Coder** «объясни весь проект» — он читает `CODER_PROMPT.md` / `TZ.md` сам.

**Lead никогда не кодит** — отдельный чат `@lead-architect`; любая правка `src/` → новый чат `@coder` + `CODER_PROMPT.md`. Правила: `lead-no-code.mdc`.

---

## Отдельный чат на роль

Стартовые фразы — в **`.cursor/rules/*.mdc`**.

| Роль | Когда | Чат |
|------|-------|-----|
| **Lead Product** | стратегия, roadmap | `@lead-product` |
| **Lead Designer** | план UI, design system | `@lead-designer` |
| **Lead Architect** | инженерия, Coder-промпт | `@lead-architect` |
| **Designer** | есть `DESIGNER_PROMPT.md` | `@designer` |
| **Coder** | есть `CODER_PROMPT.md` | `@coder` |
| **Mechanic** | тикет `docs/problems/` | `@mechanic` |

**Lead-* не кодят.** Внедрение — ты + Coder/Designer по их PROMPT-файлам.

**После Mechanic:** Lead — «тикет закрыт, обнови FOR_YOU».

---

## Цикл одной фичи

Полный регламент и чеклисты: **[`SCALE.md`](SCALE.md)** (таблица шагов 1–6, Lead, владелец, бэкап).

---

## Как экономить токены (чеклист)

| Делай | Не делай |
|-------|----------|
| `@docs/team/CODER_PROMPT.md` в чат Coder | Копировать весь TZ в чат |
| Одна задача = **новый** Coder-чат | Переиспользовать старый Coder-чат |
| Одна поломка = один чат Mechanic + один файл `docs/problems/` | Дебаг всего MVP в чате Lead |
| «Смотри CODER_PROMPT.md» | «Сделай всё из TZ» |
| Ошибка: последние 15 строк консоли | Скрин + простыня переписки |
| Правки FILTERS/PROFILE — файл на диске | «Запомни 20 слов навсегда» |
| Lead / Coder / Mechanic: **Agent** | Ask для правок кода |
| Модель **Auto** | Max без причины |
| Итог сессии в `STATUS.md` | «Напомни что мы делали вчера» в новом чате |
| Факты только из файлов repo | AI «помнит» то, чего нет в docs |

**Gemini:** черновики, «а что если 5 вариантов», обучение.  
**Cursor Lead:** зафиксировать решение в `docs/`.  
**Cursor Coder:** фичи по `CODER_PROMPT.md`.  
**Cursor Mechanic:** починка по `docs/problems/*.md`.

---

## Файлы — шпаргалка

Иерархия документов: **[`SCALE.md`](SCALE.md)** § «Документы». Правила ролей: **`.cursor/rules/*.mdc`**.

---

## Один раз в Cursor

1. **Open Folder** → `uisness`
2. **Settings → Rules** → Project Rules включены
3. Закладки чатов: **Lead PM**, **Lead Design**, **Lead Arch**, **Coder**, **Designer**, **Mechanic**
