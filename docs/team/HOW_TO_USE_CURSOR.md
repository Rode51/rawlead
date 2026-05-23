# Схема работы в Cursor (экономия токенов)

## Главное правило

**Всё важное — в файлах `docs/`, не в чате.**  
Чат = короткая команда. Длинные обсуждения — **Gemini в браузере**, итог 5–10 строк → Lead кладёт в `docs/`.

---

## Кому писать

| Вопрос / задача | Куда | Первое сообщение |
|-----------------|------|------------------|
| Что делать **тебе** | **`docs/FOR_YOU.md`** | без чата |
| План, docs, ревью | **Lead** `@lead-architect` | `.cursor/rules/lead-architect.mdc` · **без кода, ever** |
| **Дизайн UI** (постоянно) | **Designer** (новый чат) | `@designer` + `@docs/team/DESIGNER_PROMPT.md` · роль: [`DESIGNER.md`](DESIGNER.md) |
| **Фича / код** | **Coder** (новый чат) | `@coder` + `@docs/team/CODER_PROMPT.md` |
| **Поломка** | **Mechanic** `@mechanic` | `@docs/problems/…` + `.cursor/rules/mechanic.mdc` |
| Brainstorm | **Gemini** → итог → Lead | — |

Роли: **`.cursor/rules/`** (`@lead-architect` · `@designer` · `@coder` · `@mechanic` · `@owner`) · масштаб: **[`SCALE.md`](SCALE.md)** · бэкап: **[`../ops/BACKUP.md`](../ops/BACKUP.md)**

**Не пиши Coder** «объясни весь проект» — он читает `CODER_PROMPT.md` / `TZ.md` сам.

**Lead никогда не кодит** — отдельный чат `@lead-architect`; любая правка `src/` → новый чат `@coder` + `CODER_PROMPT.md`. Правила: `lead-no-code.mdc`.

---

## Три роли → три чата

Стартовые фразы — в **`.cursor/rules/*.mdc`** (не дублировать здесь).

| Роль | Когда писать | Не писать |
|------|--------------|-----------|
| **Lead** | план, docs, промпты, ревью | код, `.env`, скрипты |
| **Coder** | есть **`CODER_PROMPT.md`** | без промпта от Lead |
| **Mechanic** | есть тикет в **`docs/problems/`** | дебаг MVP в Lead-чате |

**После Mechanic:** Lead — «тикет закрыт, обнови FOR_YOU».

---

## Цикл одной фичи

Полный регламент: **[`SCALE.md`](SCALE.md)**.

```
1. Gemini/ты — идея (5–10 строк)
2. Lead → ROADMAP + TASKS + CODER_PROMPT.md (задача 1–2 дня)
3. Coder → НОВЫЙ чат → код + STATUS.md
4. Ты → RUN.md, ~5 мин приёмка
5. Lead → закрыть, FOR_YOU, TASKS_HISTORY, удалить CODER_PROMPT.md
5b. Ты → бэкап (BACKUP.md)
6. Повтор
```

Не ок на шаге 4 → Lead → `problems/` → Mechanic.

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

| Файл | Кто правит |
|------|------------|
| `docs/team/SCALE.md` | Lead — цикл большого проекта |
| `.cursor/rules/*.mdc` | Lead — правила ролей (Project Rules) |
| `docs/ops/BACKUP.md` | Lead — **ты делаешь** бэкап |
| `docs/team/SECURITY.md` | Lead — для владельца |
| `docs/team/LEAD.md` | Lead — регламент |
| `docs/FOR_YOU.md` | Lead — **ты читаешь** |
| `docs/team/TASKS.md` | Lead |
| `docs/team/CODER_PROMPT.md` | Lead (один; удалить после сдачи) |
| `docs/team/STATUS.md` | Coder (после работы), Lead (сводка) |
| `docs/ops/FILTERS.md`, `PROFILE.md` | **Ты** или Lead |
| `.env` | **Только ты**, на ПК |
| `src/` | **Coder** / **Mechanic** |
| `docs/problems/*.md` | **Lead** → **Mechanic** |

---

## Один раз в Cursor

1. **Open Folder** → `uisness`
2. **Settings → Rules** → Project Rules включены
3. Закладки чатов: **Lead**, **Coder**, **Mechanic** (переименуй в UI)
