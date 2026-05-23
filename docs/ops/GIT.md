# Git — версии и GitHub

**Репозиторий локально:** `git init` ✅ · ветка `main` · remote: `https://github.com/hramo/uisness.git`

**Осталось один раз:** войти в GitHub и **создать пустой репозиторий** + `git push`.

---

## 1. Создай репозиторий на GitHub

1. [github.com/new](https://github.com/new)
2. Имя: **`uisness`**
3. **Private**
4. **Без** README / .gitignore / license (у нас уже есть)
5. Create repository

Если логин **не** `hramo` — после создания:

```powershell
cd C:\Users\hramo\uisness
git remote set-url origin https://github.com/ТВОЙ_ЛОГИН/uisness.git
```

---

## 2. Вход (один раз)

В PowerShell:

```powershell
gh auth login
```

Выбери: GitHub.com → HTTPS → Login with a web browser → скопируй код.

Без `gh` — при `git push` откроется окно входа Git Credential Manager.

---

## 3. Отправить код

```powershell
cd C:\Users\hramo\uisness
git push -u origin main
```

Проверка: в браузере `https://github.com/hramo/uisness` — файлы `src/`, `docs/`.

---

## Что не попадает в Git

`.gitignore`: `.env`, `*.session`, `.venv`, `data/*.db`, `data/*.log`, listen-файлы, `backup.config.json`.

**Бэкап** секретов: [`BACKUP.md`](BACKUP.md) — по-прежнему нужен.

---

## Обычный цикл

```powershell
git checkout -b feature/имя-задачи
# … Coder сдал …
git add .
git commit -m "feat: кратко что сделано"
git checkout main
git merge feature/имя-задачи
git push
```

Одна задача из [`CODER_PROMPT.md`](../team/CODER_PROMPT.md) ≈ одна ветка.

---

## Уже сделано локально

| Коммит | Содержание |
|--------|------------|
| `42770ff` | initial: radar MVP + TG multi-session |
| `2b2ad9f` | gitignore runtime data, GIT docs |

---

_Если `Repository not found` — репозиторий ещё не создан на GitHub или неверный логин в `remote`._
