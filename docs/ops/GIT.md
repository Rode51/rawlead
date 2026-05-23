# Git — версии и откат (как на GitHub)

**Зачем:** точки «вернуться сюда», ветки под задачи (пульт, WP), история **без** секретов в облаке.

**Сейчас:** папка `uisness` **не** была git-репозиторием — откаты через [`BACKUP.md`](BACKUP.md). Git удобнее для кода; бэкап `.env`/сессий — **по-прежнему** нужен.

---

## Что не коммитить

Уже в `.gitignore`: `.env`, `*.session`, `.venv`, `data/*.log`, listen-файлы, `backup.config.json`.

**Никогда:** токены, пароли, сессии Telethon.

---

## Один раз (владелец или Coder)

```powershell
cd C:\Users\hramo\uisness
git init
git add .
git status   # убедись: нет .env и .session
git commit -m "initial: radar MVP + TG multi-session"
```

**GitHub (приватный репо):**

```powershell
git remote add origin https://github.com/ТЫ/uisness.git
git branch -M main
git push -u origin main
```

---

## Обычный цикл (как на GitHub)

| Шаг | Команда / действие |
|-----|-------------------|
| Перед большой задачей | `git checkout -b feature/desktop-pult` |
| Coder сдал | `git add` нужные файлы → `git commit -m "feat: desktop control panel"` |
| Всё ок | `git checkout main` → `git merge feature/desktop-pult` |
| Откат | `git checkout main` → `git log` → `git checkout <хеш>` или `git revert` |

**Правило:** одна задача из [`CODER_PROMPT.md`](../team/CODER_PROMPT.md) ≈ одна ветка ≈ один merge в `main`.

---

## И бэкап

| Git | `backup.bat` |
|-----|----------------|
| Код, docs | `.env`, сессии, SQLite с данными |
| GitHub = копия кода | Диск `D:\Backups\uisness` = полный снимок ПК |

---

## Cursor

Перед «большим» рефакторингом: **commit** или ветка. Подробнее: [`../team/CURSOR_DEEP_RESEARCH_2026.md`](../team/CURSOR_DEEP_RESEARCH_2026.md) § Git.

---

_Lead. После `git init` — строка в [`../KAK_ETO_RABOTAET.md`](../KAK_ETO_RABOTAET.md)._
