# PROJECT MAP — [PROJECT]

**Kit:** [`templates/cursor-team-kit/README.md`](../templates/cursor-team-kit/README.md)

---

## Агентам

| Нужно | Канон | Не дублировать |
|-------|-------|----------------|
| Задача Coder | `architect/CODER_PROMPT.md` hot | чат, TASKS простынёй |
| Снимок | `common/STATUS.md` hot | архив |
| Очередь | `common/TASKS.md` | FOR_YOU |
| Поломка | `docs/problems/` | — |

| Роль | Пишет | Не пишет |
|------|-------|----------|
| Lead Architect | ROADMAP, TASKS, STATUS, CODER_PROMPT | `src/` |
| Coder | § «Файлы» + STATUS | docs кроме STATUS |
| Mechanic | problems + код по тикету | CODER_PROMPT |

---

## Зоны — кто что трогает

| Зона | Пути | Кто |
|------|------|-----|
| Backend | `src/` | Coder / Mechanic |
| Scripts | `scripts/` | Coder |
| Tests | `tests/` | Coder |
| UI | `[UI_ROOT]/` | Coder по промпту |
| Secrets | `.env` | **владелец** |
| Docs | `docs/team/` | Lead |

**Coder:** только файлы из § «Файлы» активного `CODER_PROMPT.md`.

---

_[PROJECT] · PROJECT_MAP_
