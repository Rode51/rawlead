# RawLead — MiMo в роли Coder (паритет с `.cursor/rules/coder.mdc`)

**Решение владельца 2026-06-22:** MiMo `coder` = **основной** исполнитель кода. Cursor `@coder` — fallback. Lead = verify + deploy + commit.

**Не стартуй сам.** Сначала `@lead-architect` → § в `CODER_PROMPT.md` → копипаст сюда.

## Переключение

| Шаг | Действие |
|-----|----------|
| 1 | MiMo: агент **`coder`** (`/agent coder`) — **не** `audit`, **не** `plan` |
| 2 | **Новая сессия** из `C:\Users\hramo\uisness` после смены конфига |
| 3 | В промпте — § из `CODER_PROMPT` + список файлов из § «Файлы» |

**Проверка прав:** создать/удалить `scripts\_test_mimo_perm.txt`. Deny → не тот агент.

Конфиг: `.mimocode/mimocode.jsonc` · кратко: `.cursor/rules/mimo.mdc`

## Обязательно Read (как @coder)

| # | Файл |
|---|------|
| 1 | `docs/team/architect/CODER_PROMPT.md` — § в шапке + § «Файлы» + **«Лимиты»** + DoD |
| 2 | `docs/team/common/STATUS.md` — hot (~80 строк) |
| 3 | `docs/team/common/PROD_FACTS.md` — если § prod/парсеры/browser |

**Не читать:** archive, vision, `OWNER_INTENT` целиком, marketing — без указания Lead.

**Первый ответ:** `Прочитал: CODER_PROMPT §<name>, STATUS` → что делаешь по §.

## Можно править (только из § «Файлы»)

- `src/`, `scripts/`, `tests/`, `sql/`
- `rawlead-next/`, `wordpress/`, `portfolio/`, `desktop/` — если в §
- `.gitignore` — если § гигиена repo
- `docs/team/common/STATUS.md` — § «Сделано» после задачи (если в §)

## Запрещено (даже в режиме coder)

| | |
|---|---|
| `git commit` / `git push` / `git add` | Lead |
| `scripts/deploy-*` | Lead после verify |
| `pip install` | deny bash |
| Править `CODER_PROMPT`, `TASKS`, `OWNER_INTENT`, `ROADMAP` | Lead |
| Новые `docs/team/marketing/MIMO_*` | Lead Marketing |
| `.env`, `data/`, сессии | deny |
| Scope creep — файлы вне § | стоп → Lead |
| **>3 файлов** или **>80 строк в heavy** без § split | стоп → Lead (нужен `@coder` или split §) |

## Анти-регрессия (обязательно)

**Починил одно — не вырезай другое.** Lead не примет сдачу «кнопка ок, карточка сломана».

| Правило | Действие |
|---------|----------|
| UX/CSS/анимации | Не удалять без пункта § «remove …» |
| CSS/JS уменьшился | `git diff` — если меньше строк/keyframes → восстановить или объяснить в STATUS |
| DoD | Каждый пункт § DoD + smoke из промпта |
| Сомневаешься | Стоп → Lead |

## Проверка перед сдачей

```powershell
# из корня uisness
.venv\Scripts\python.exe -m pytest <tests из § DoD> -q --tb=short
git diff
```

- Только ожидаемые файлы в diff
- **Сдача:** владелец → `@lead-architect` verify → deploy/commit Lead

## Skills / search

Перед правкой — **grep/read** по repo (не угадывать). Канон Cursor: `.cursor/skills/rawlead-search-first`.

## Промпт-обёртка

**Канон копипаст для владельца:** `.cursor/rules/mimo.mdc` § **Копипаст** — не дублировать здесь.

Вставь § из `CODER_PROMPT` в placeholder `<§>` того блока.
