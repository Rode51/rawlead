# RawLead — правила MiMo Code (обязательно)

**Роль MiMo в этом репо:** только **чтение + аудит**. Код и prod — **Cursor** (`@lead-architect` → `@coder` / `@mechanic`).

## Режимы

| Агент | Когда | Пишет в repo |
|-------|--------|--------------|
| **`audit`** (default) | широкий разбор | только `docs/problems/` |
| **`coder`** | есть § от Lead в чате | `src/`, `scripts/`, `.gitignore`, docs по § — **allow** (не audit) |

Переключи агент на **coder** перед кодингом (`/agent coder`). Правила Coder в чат **недостаточны** без § `CODER_PROMPT` + смены агента. Этот файл — **только для audit**; в coder не подмешивается (v3 конфиг).

## Запрещено без явного «да» владельца в этом чате

| Действие | Почему |
|----------|--------|
| Создавать **любые** новые файлы вне `docs/problems/` | Lead triage → `CODER_PROMPT` |
| Править `src/`, `scripts/`, `tests/`, `rawlead-next/`, `wordpress/`, `portfolio/` | Только `@coder` |
| Править `docs/team/**`, `docs/ops/**`, `.cursor/**` | Только Lead-роли |
| Писать `docs/team/marketing/MIMO_*.md` или дубли планов | Только `@lead-marketing` после сверки |
| `git commit` / `git push` / deploy-скрипты | Только Lead Architect по регламенту |
| `pip install`, `pytest`, restart radar/API | Только Coder/Mechanic |
| Читать `.env`, `data/`, `*.session` | Deny в `mimocode.jsonc` |

## Разрешено (режим по умолчанию)

1. **Read / grep / glob** — код и docs (кроме секретов).
2. **Один deliverable аудита:** новый файл только в `docs/problems/YYYY-MM-DD-mimo-*.md` — **после ask** в UI MiMo.
3. Ответ в чате: findings, таблица P0/P1, **без** правок в repo.

## Порядок работы (владелец + Lead)

```
Владелец → MiMo (аудит, read-only)
        → docs/problems/…-mimo-audit.md
        → @lead-architect (triage)
        → CODER_PROMPT / TASKS / handoff @coder
```

**Не** «MiMo нашёл баг → сразу патч в src».

## Стартовый промпт (копипаст)

```text
RawLead audit mode. Read docs/README.md → PROJECT_MAP.md → PROD_FACTS.md.
Scope: src/ parsers + ai_analyze + rawlead-next risks + docs drift.
Output: ONE markdown report in docs/problems/2026-MM-DD-mimo-<topic>.md
Format: like docs/problems/2026-05-29-gemini-full-audit.md (P0/P1, file:line).
NO code edits. NO new files except docs/problems/. NO marketing plans.
```

## Секреты

- MiMo Auto шлёт чат и tool output на серверы Xiaomi — **не вставляй** ключи в промпт.
- Deny-list: `.mimocode/mimocode.jsonc` · зеркало: `.cursorignore`.

## Если MiMo уже насоздавал лишнее

Владелец: `git checkout -- .` / откат файлов · Lead не принимает diff без triage.

_Обновлено Lead 2026-06-20 · канон: OWNER_INTENT § MIMO-AUDIT_
