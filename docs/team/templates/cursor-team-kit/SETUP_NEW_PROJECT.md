# Bootstrap нового проекта (~30 мин)

Чеклист владельца. Kit: [`README.md`](README.md)

---

## 0. Предусловия

- [ ] Cursor · Project Rules включены
- [ ] Git repo инициализирован
- [ ] Папка `docs/` (или скопирован `docs-skeleton/`)

---

## 1. Скопировать rules (5 мин)

```powershell
.\docs\team\templates\cursor-team-kit\bootstrap.ps1 -TargetRoot .
```

Или вручную: `rules/*.mdc` → `.cursor/rules/`

В **`.gitignore`**:

```gitignore
.cursor/
!.cursor/rules/
!.cursor/rules/**
```

---

## 2. Дерево docs (10 мин)

Скопировать из `docs-skeleton/` → `docs/` и заменить `[PROJECT]`:

| Файл | Заполнить |
|------|-----------|
| `docs/README.md` | карта docs |
| `docs/FOR_YOU.md` | «Твои шаги» — 5–10 строк |
| `docs/team/common/PROJECT_MAP.md` | зоны кода · § «Агентам» |
| `docs/team/common/DOCS_ARCHITECTURE.md` | канон (не плодить md) |
| `docs/team/common/STATUS.md` | «Сейчас» пустой шаблон |
| `docs/team/common/TASKS.md` | одна активная строка |
| `docs/team/architect/CODER_PROMPT.md` | шапка «→ Следующее: …» |
| `docs/team/architect/ROADMAP.md` | фазы |
| `docs/team/architect/OWNER_INTENT.md` | журнал решений |
| `docs/team/architect/LEAD.md` | регламент Lead |
| `docs/team/archive/` | пусто · `TASKS_HISTORY.md` |
| `docs/problems/` | `.gitkeep` |

**Product/Design** — добавить позже, если нужны `@lead-product` / `@designer`.

---

## 3. Настроить guards (5 мин)

В `code-guard.mdc` поправить **globs** под стек:

| Стек | globs |
|------|-------|
| Python API | `src/**`, `scripts/**`, `tests/**` |
| Node | `src/**`, `apps/**`, `packages/**` |
| WP theme | `wordpress/**` |
| Monorepo | объединить |

В `PROJECT_MAP.md` § «Зоны» — те же пути.

---

## 4. Первый цикл (10 мин)

1. `@lead-architect` — заполнить `ROADMAP` + одну задачу в `CODER_PROMPT`
2. `@coder` — первая маленькая задача (smoke: health/test)
3. Lead — `STATUS` ✅ · архив пустой · commit

---

## 5. Закладки чатов Cursor

| Чат | Первое сообщение |
|-----|------------------|
| Lead Arch | `@lead-architect` |
| Coder | `@coder` |
| Mechanic | `@mechanic` + тикет |
| Owner | `@owner` |

**Правило:** новая задача Coder = **новый чат**.

---

## 6. Периодическое обслуживание

| Когда | Действие |
|-------|----------|
| После каждой ✅ | hot STATUS + CODER_PROMPT ≤ лимита · § → архив |
| Раз в 2 недели | grep hot-файлов на длину · FOR_YOU урезать |
| Новый проект | `bootstrap.ps1` из kit |

---

## Анти-пatterns

| Не делать | Делать |
|-----------|--------|
| TZ в чате | `CODER_PROMPT.md` |
| Coder читает vision | только § шапки |
| Lead правит `src/` | handoff `@coder` |
| Новый `NOTES.md` | `TASKS` или `OWNER_INTENT` |
| Архив в hot-файле | `archive/*_ARCHIVE.md` |

---

_Setup · Cursor Team Kit v1.0_
