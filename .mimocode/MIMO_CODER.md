# RawLead — MiMo в роли Coder (только с handoff Lead)

**Не стартуй сам.** Сначала `@lead-architect` → § в `CODER_PROMPT.md` → копипаст сюда.

## Переключение

В MiMo: агент **`coder`** (не `audit`).  
`default_agent` = audit — код только когда **явно** выбрал coder.

**Права (v3):** только агент **`coder`**. Явный allow: `scripts/**` (удаление `.out`/`.html`/`_tmp_*` по §), `src/**`, `.gitignore`. Deny: секреты, Lead-docs.

**Обязательно перед кодом:**
1. Агент **`coder`** — Tab / `/agent coder`. **Не** `audit`, **не** `plan` (plan отключён в конфиге).
2. **Новая сессия** `mimo` из `C:\Users\hramo\uisness` после смены конфига.
3. В промпте — § из `CODER_PROMPT` (список файлов на удаление).

**Проверка прав (10 сек):** `del scripts\_test_mimo_perm.txt` или edit-tool создать/удалить этот файл. Deny → не тот агент или старая сессия.

Глобальных `instructions` с `MIMO_RULES.md` больше нет — они давали read-only даже в coder.

## Обязательно в первом сообщении (от Lead / владельца)

1. **§ задачи** из `docs/team/architect/CODER_PROMPT.md` (шапка + DoD + «Файлы»).
2. Фраза: «Режим Coder · одна задача · файлы только из §».

Опционально вставить выдержку из `.cursor/rules/coder.mdc` — **дополнительно**, не вместо §.

## Read перед кодом (как @coder)

| # | Файл |
|---|------|
| 1 | `docs/team/architect/CODER_PROMPT.md` — § в шапке |
| 2 | `docs/team/common/STATUS.md` — hot |
| 3 | `docs/team/common/PROD_FACTS.md` — если prod/парсеры |

**Не читать** vision, archive, `OWNER_INTENT` целиком, marketing — без указания Lead.

## Можно править (только файлы из § CODER_PROMPT)

- `src/`, `scripts/`, `tests/`, `rawlead-next/`, `wordpress/` — если в §
- `.gitignore` — если § гигиена repo
- `docs/team/common/STATUS.md` — § «Сделано» после задачи
- `docs/team/marketing/M1_*.md` — **только** если явно в § (не `MIMO_*_PLAN`)

## Запрещено (даже в режиме coder)

| | |
|---|---|
| Новые `docs/team/marketing/MIMO_*` | Lead Marketing |
| Править `CODER_PROMPT`, `TASKS`, `OWNER_INTENT` | Lead |
| `git commit` / `git push` | Lead |
| `scripts/deploy-*` без «задеплой» от владельца | Lead Architect |
| `.env`, `data/`, сессии | deny |
| Scope creep — файлы вне § | стоп → Lead |

## Проверка

- `pytest` по § промпта (релевантные тесты)
- `git diff` — только ожидаемые файлы
- **Сдача:** владелец → `@lead-architect` verify → потом commit Lead

## Промпт-обёртка (копипаст + § от Lead)

```text
Ты Coder RawLead. Одна задача. Английский в промпте, UI-строки RU по цитатам.
Прочитай CODER_PROMPT § ниже + STATUS hot + PROD_FACTS если prod.
Не создавай лишних файлов. Не трогай marketing docs. Не commit.

--- ЗАДАЧА (от Lead) ---
<вставить § CODER_PROMPT>
```

_Канон Cursor: `.cursor/rules/coder.mdc` · lockdown audit: `MIMO_RULES.md`_
