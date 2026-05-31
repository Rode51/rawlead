# Cursor Team Kit — переносимая команда AI-агентов

**Версия:** 1.0 · **Источник:** проект RawLead (2026-05-30)

Один репозиторий = **роли + гарды + hot-docs**, которые копируешь в любой новый проект за ~30 минут.

---

## Что внутри

| Папка | Назначение |
|-------|------------|
| [`SETUP_NEW_PROJECT.md`](SETUP_NEW_PROJECT.md) | пошаговый bootstrap |
| [`bootstrap.ps1`](bootstrap.ps1) | скрипт копирования (Windows) |
| [`rules/`](rules/) | шаблоны `.mdc` → `.cursor/rules/` |
| [`docs-skeleton/`](docs-skeleton/) | минимальное дерево `docs/team/` |

---

## Роли (минимальный набор)

| Роль | Файл | Код? |
|------|------|------|
| **Lead Architect** | `lead-architect.mdc` | **нет** |
| **Coder** | `coder.mdc` | да, по промпту |
| **Mechanic** | `mechanic.mdc` | hotfix по тикету |
| **Owner** | `owner.mdc` | нет |
| **Always** | `economy.mdc`, `lead-no-code.mdc` | — |
| **Guards** | `code-guard.mdc`, `docs-guard.mdc` | — |

**Расширение (продукт + дизайн):** `lead-product.mdc`, `lead-designer.mdc`, `designer.mdc` — скопировать из RawLead `.cursor/rules/` или добавить позже.

---

## Принципы (не менять)

1. **Чат короткий · ТЗ в файле** — `CODER_PROMPT.md`, не простыня в чате.
2. **Hot vs архив** — агент читает только hot; закрытое → `docs/team/archive/*_ARCHIVE.md`.
3. **Lead = 0 кода** — любая правка `src/` → `@coder`.
4. **Coder = § «Файлы»** — вне списка → стоп.
5. **Один чат = одна задача** — после сдачи новый чат.
6. **Git commit** — только Lead (или владелец в solo-проектах).

---

## Лимиты hot-файлов

| Файл | ≤ строк | Архив |
|------|---------|-------|
| `STATUS.md` | 80 | `STATUS_ARCHIVE.md` |
| `CODER_PROMPT.md` | 120 | `CODER_PROMPT_ARCHIVE.md` |
| `DESIGNER_PROMPT.md` | 80 | `DESIGNER_PROMPT_ARCHIVE.md` |
| `TASKS.md` | 40 | `TASKS_HISTORY.md` |
| `FOR_YOU.md` | 1 экран | `README`, `ops/` |

**Ревизия Lead:** раз в 1–2 недели или когда hot > лимита.

---

## Быстрый старт (новый repo)

```powershell
cd C:\path\to\new-project
# из клона RawLead или копии kit-папки:
.\docs\team\templates\cursor-team-kit\bootstrap.ps1 -TargetRoot .
```

Дальше: [`SETUP_NEW_PROJECT.md`](SETUP_NEW_PROJECT.md) — заполнить `[PROJECT]`, vision, первую задачу.

---

## Кастомизация под проект

| Placeholder | Заменить на |
|-------------|-------------|
| `[PROJECT]` | имя продукта |
| `[CODE_ROOT]` | `src/` или `app/` |
| `[UI_ROOT]` | `frontend/` или `wordpress/` |
| `[VISION_PATH]` | путь к vision-доку |

Шаблоны в `rules/` и `docs-skeleton/` содержат `[PROJECT]` в шапках.

---

## Синхронизация между проектами

1. Правки **универсальных** правил (economy, guards) — правь **здесь в kit**, потом `bootstrap.ps1 -RulesOnly` в других repo.
2. **`.cursor/rules/` в git:** в `.gitignore` добавь исключение `!.cursor/rules/**` — иначе правила не едут на другой ПК.

---

_RawLead · Cursor Team Kit v1.0_
