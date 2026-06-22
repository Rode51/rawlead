# RawLead — правила MiMo Code (обязательно)

**Роль MiMo в этом репо (2026-06-22):**
- **`audit`** — read-only · отчёты `docs/problems/`
- **`coder`** — **основной** исполнитель кода (паритет `@coder` Cursor)
- **Lead Architect (Cursor)** — verify · deploy · commit · docs

Кто куда — таблица: `.cursor/rules/lead-architect.mdc` § «Маршрут исполнителя» · кратко: `.cursor/rules/mimo.mdc`

## Режимы

| Агент | Когда | Пишет в repo |
|-------|--------|--------------|
| **`audit`** (default) | широкий разбор | только `docs/problems/` |
| **`coder`** | § `CODER_PROMPT` от Lead | `src/`, `scripts/`, `tests/`, `rawlead-next/` … по § |

Переключи агент на **coder** перед кодингом (`/agent coder`). Правила: `.mimocode/MIMO_CODER.md` (= `coder.mdc`).

## Запрещено audit-агенту

| Действие | Почему |
|----------|--------|
| Создавать **любые** новые файлы вне `docs/problems/` | Lead triage → `CODER_PROMPT` |
| Править `src/`, `scripts/`, `tests/`, `rawlead-next/`, `wordpress/`, `portfolio/` | Только агент **`coder`** + § `CODER_PROMPT` |
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
Владелец → @lead-architect → § CODER_PROMPT + Маршрут: MiMo coder
        → MiMo (агент coder) + копипаст §
        → pytest · git diff
        → @lead-architect verify → deploy → commit Lead
```

**Аудит (параллельно):** MiMo `audit` → `docs/problems/…-mimo-*.md` → Lead triage.

**Не** «MiMo нашёл баг → сразу патч» без § и без агента coder.

## Скиллы (бесплатный MiMo + skills.sh)

**Зачем:** широкий read-only разбор **без** токенов Cursor на PRE-ADS · параллельно G0–G7.

**Установка (один раз, в корне `uisness`):**

```powershell
npx skills find security
npx skills find code-review
npx skills add vercel-labs/agent-skills@security-review   # если есть в find
npx skills add vercel-labs/agent-skills@code-review
```

Подключи скиллы в MiMo UI (Skills / project skills). Приоритет для гейта:

| Скилл / тема | Когда в PRE-ADS |
|--------------|----------------|
| **security-review** | M1 · G-SEC до посевов |
| **code-review** | после каждого FAIL G0–G7 |
| **react-best-practices** | M2 · `rawlead-next` auth/perf |

Каталог: https://skills.sh/ · поиск: `npx skills find <query>`.

**Читать отчёты прогонов:** audit-агент может `data/preprod_*.json` / `*.md` (не `.env`, не сессии).

---

## PRE-ADS — параллельные прогоны MiMo (M0–M4)

Пока **@coder** (Cursor) гоняет G0–G7b, владелец запускает **MiMo audit** (default agent). Выход → `docs/problems/YYYY-MM-DD-mimo-*.md` → `@lead-architect` triage.

| MiMo | После шага Coder | Промпт (копипаст) |
|------|------------------|-------------------|
| **M0** | до G0 | «PRE-ADS G-SEC re-audit: `api_server.py` auth/IDOR/webhook/ops · сверка с `2026-06-20-mimo-pre-ads-readiness.md` · только новые P0/P1» |
| **M1** | после G1 | «Прочитай `data/preprod_next_e2e.json` если есть · static review FAIL сценариев в `next_e2e.py` + `rawlead-next`» |
| **M2** | после G7b | «Прочитай `data/preprod_stress_v2.json` · bottlenecks pool/load · file:line» |
| **M3** | после G6 | «L3 uniquify: `ai_analyze.py` cross-user dedup · риск одинаковых откликов на M1» |
| **M4** | перед sign-off | «`rawlead-next`: localStorage JWT, `/cabinet/` guard, nginx headers — P0/P1 для посевов» |

**Не дублировать:** Cursor `@coder` = pytest/playwright/load · MiMo = **статика + разбор артефактов**.

---

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

_Обновлено Lead 2026-06-22 · канон: OWNER_INTENT § MIMO · `mimo.mdc`_
