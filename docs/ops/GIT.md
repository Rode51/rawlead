# Git — версии и GitHub

**GitHub:** https://github.com/Rode51/uisness (private) · логин **Rode51** · ветка `main` ✅

---

## Первый push (уже сделано)

Remote: `https://github.com/Rode51/uisness.git`

Дальше после работы Coder:

```powershell
cd C:\Users\hramo\uisness
git add .
git commit -m "feat: описание"
git push
```

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

Одна задача из [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) ≈ одна ветка.

---

## Уже сделано локально

| Коммит | Содержание |
|--------|------------|
| `42770ff` | initial: radar MVP + TG multi-session |
| `2b2ad9f` | gitignore runtime data, GIT docs |

---

_Вход: `gh auth login` (аккаунт Rode51)._
