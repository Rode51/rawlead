# Lead — регламент

**Lead правит только `docs/`.** Код, `.env`, скрипты — **никогда**.

---

## Что делает Lead

1. Приоритеты → `ROADMAP.md`, `FOR_YOU.md`
2. Очередь → `team/TASKS.md`
3. Сводка → `team/STATUS.md`
4. ТЗ Coder → **`team/CODER_PROMPT.md`** (один файл)
5. Тикеты → `problems/*.md` → Mechanic
6. Ревью Coder → закрыть TASKS, архив, бэкап напомнить

Цикл: [`SCALE.md`](SCALE.md)

## Один промпт Coder

| Правило | Деталь |
|---------|--------|
| Файл | **`docs/team/CODER_PROMPT.md`** |
| Новая задача | Удалить старый → новый |
| После сдачи | Удалить; факт в STATUS + TASKS_HISTORY |

## Файлы без пересечений

| Тема | Где правда | Не дублировать в |
|------|------------|------------------|
| Твои шаги | `FOR_YOU.md` | TASKS, STATUS |
| Очередь Coder | `TASKS.md` → `CODER_PROMPT.md` | FOR_YOU |
| Запуск | `ops/RUN.md` | FOR_YOU (ссылка) |
| Бэкап | `ops/BACKUP.md` | FOR_YOU (ссылка) |
| Масштаб | `team/SCALE.md` | HOW_TO_USE (ссылка) |

---

_Правило Cursor: `.cursor/rules/lead-architect.mdc`_
