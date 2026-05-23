# Бэкапы

**Зачем:** `.env` и локальные данные **не в Git**.

**Куда:** `D:\Backups\<project>\` или свой путь в `scripts/backup.config.json`. **Не OneDrive** для секретов.

---

## Запуск

```powershell
scripts\backup.bat
```

или

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
```

---

## Настройка

1. `Copy-Item scripts\backup.config.example.json scripts\backup.config.json`
2. Пропиши `projectRoot`, `backupRoot`, `sessionDirs` (если есть)
3. Запусти `backup.bat`

---

## Когда

- После принятой фичи (шаг 5b [`SCALE.md`](../team/SCALE.md))
- Раз в неделю
- Перед сменой `.env` / обновлением Windows

---

## Восстановление

1. Остановить приложение
2. Вернуть `.env` и файлы из последней папки бэкапа
3. Запуск по RUN.md
