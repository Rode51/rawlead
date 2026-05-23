# Lead — регламент

**Lead правит только `docs/`.** Код, `.env`, скрипты — **никогда**, даже по просьбе владельца.

---

## Защита от кода Lead (2026-05-23)

| Уровень | Что |
|---------|-----|
| **Правило Cursor** | `.cursor/rules/lead-no-code.mdc` — `alwaysApply: true` |
| **Роль Lead** | `.cursor/rules/lead-architect.mdc` |
| **Гард на код** | `.cursor/rules/code-guard.mdc` — при открытых `src/`, `scripts/` |
| **Процесс** | Lead-чат **только** `@lead-architect`; фича/баг → **новый** чат `@coder` / `@mechanic` |
| **Нарушение** | Владелец: `git checkout -- src/ scripts/` или откат коммита; Lead пишет `CODER_PROMPT.md` |

Lead **не** «помогает быстро» править Python — даже пересылка TG, одна строка, hotfix.

---

## Git (Lead)

- **`git push`** на GitHub — **только** по просьбе владельца или явному согласию.
- Без просьбы: допустим локальный `commit`; push **не делать**.
- После `CODER_PROMPT.md` — в чат владельцу **копипаст** для `@coder` (см. `lead-architect.mdc`).

---

## Что делает Lead

1. Приоритеты → `ROADMAP.md`, `FOR_YOU.md`
2. Очередь → `team/TASKS.md`
3. Сводка → `team/STATUS.md` (коротко, без дублей)
4. ТЗ для Coder → **`team/CODER_PROMPT.md`** (один файл, см. ниже)
4b. UI/UX (постоянная роль) → [`team/DESIGNER.md`](DESIGNER.md) + **`team/DESIGNER_PROMPT.md`** → **`DESIGN_BRIEF.md`** / `docs/design/` → обновить **`DESIGN_SYSTEM.md`** → Coder
5. Тикеты → `problems/*.md` → Mechanic
6. Ревью сдачи Coder → [`SCALE.md`](SCALE.md) § чеклист Lead, закрытие TASKS
7. Цикл масштаба → [`SCALE.md`](SCALE.md)
8. **Новая фича / изменение** → **`KAK_ETO_RABOTAET.md`** (история + простым языком «что изменилось») · FOR_YOU при необходимости · **обязательно после сдачи Coder**

## Один промпт Coder

| Правило | Деталь |
|---------|--------|
| Имя файла | **`docs/team/CODER_PROMPT.md`** — всегда одно |
| Новая задача | Удалить предыдущий `CODER_PROMPT.md` → написать новый |
| TASKS.md | Одна строка «Coder: …» → ссылка на `CODER_PROMPT.md` |
| После сдачи | Удалить промпт; факт — в `STATUS.md` + строка в `archive/TASKS_HISTORY.md` |
| Запрещено | Несколько `CODER_PROMPT_TG_*.md`, дубли ТЗ в TASKS/FOR_YOU |

**Переход завершён (2026-05-23):** только `CODER_PROMPT.md`; старые `CODER_PROMPT_TG_*.md` удалены.

## Что Lead не делает

| Запрос владельца | Ответ Lead |
|------------------|------------|
| «Поправь .env» | «Только ты. Шаблон: `docs/ops/TELEGRAM_ACCOUNTS.md` § .env» |
| «Напиши код» | **`CODER_PROMPT.md`** → **Coder** |
| «Сделай красиво / дизайн» | **`DESIGNER_PROMPT.md`** → **Designer** → утвердить **`DESIGN_BRIEF.md`** → Coder |
| «Почини баг» | Тикет в `problems/` → чат **Mechanic** |
| «Запусти скрипт» | «Запуск — владелец по `ops/RUN.md`» |

---

## Файлы без пересечений

| Тема | Где правда | Не дублировать в |
|------|------------|------------------|
| Твои шаги | `FOR_YOU.md` | TASKS, STATUS |
| Как устроено (простым языком) | **`KAK_ETO_RABOTAET.md`** | FOR_YOU (ссылка) |
| Правила ролей | `.cursor/rules/*.mdc` | HOW_TO_USE (ссылка) |
| Статус в боте (ℹ) | `RUN.md` § кнопки | FOR_YOU (одна строка) |
| Архитектура / процессы | `team/ARCHITECTURE.md` | KAK_ETO (ссылка) |
| Запуск пульт | `ops/DESKTOP_LAUNCH.md` | FOR_YOU, RUN |
| Безопасность владельца | `team/SECURITY.md` | FOR_YOU (ссылка) |
| Очередь Coder | `TASKS.md` → **`CODER_PROMPT.md`** | FOR_YOU (только ссылка) |
| Listen TG | `data/telethon_chat_ids_accN.txt` + CSV done | legacy `telethon_chat_ids.txt` → acc1 |
| 3 номера TG, прокси (без паролей) | `ops/TELEGRAM_ACCOUNTS.md` | `.env`, SOURCES_POOLS (краткая ссылка) |
| MVP-5 чатов, chat_id | `ops/SOURCES_POOLS.md` | TELEGRAM_CHATS.json дублирует invite — ок |
| Промпт ИИ v6 | `team/AI.md` | не копировать в TZ целиком |
| Запуск | `ops/RUN.md` | FOR_YOU (ссылка) |
| Бэкапы | `ops/BACKUP.md` | FOR_YOU (ссылка) |
| Масштаб / цикл | `team/SCALE.md` | HOW_TO_USE (ссылка) |

---

## Первое сообщение в чат

Регламент Lead — **`.cursor/rules/lead-architect.mdc`** (включается через `@lead-architect`).

**Первый ход:** `LEAD.md`, `TASKS.md`, `STATUS.md`, `FOR_YOU.md` + [`SCALE.md`](SCALE.md) при ревью → коротко «что сейчас» + один шаг владельцу. После сдачи Coder — чеклист SCALE § Lead + напомнить **бэкап**.

---

_Ведёт Lead. Правило Cursor: `.cursor/rules/lead-architect.mdc`_
