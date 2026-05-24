# Бэкапы (владелец)

**Зачем:** `.env`, сессии Telethon и SQLite **не в Git** (даже если включишь Git — см. [`GIT.md`](GIT.md)).

**Git** = история кода и ветки. **Бэкап** = секреты и данные на диск.

**Куда:** `D:\Backups\uisness\<дата>\` (настраивается в `scripts/backup.config.json`). **Не OneDrive** для секретов.

---

## Запуск (один клик)

```powershell
scripts\backup.bat
```

или без паузы:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\backup.ps1
```

---

## Что бэкапится

| Что | Откуда |
|-----|--------|
| `.env` | корень проекта |
| `projects.db`, `telethon_chat_ids.txt`, `tg_join_state.json` | `data\` |
| Сессии Telethon | `Desktop\Parser\` (в config) |
| manifest.txt | список в папке бэкапа |

Настройка путей: `scripts\backup.config.json` (локальный, не в Git). Шаблон: `backup.config.example.json`.

---

## Когда

| Событие | Действие |
|---------|----------|
| **Перед большой правкой** (новый Coder, смена `.env`, join волна чатов) | **бэкап сначала** |
| После принятой фичи | бэкап (шаг 5b [`SCALE.md`](../team/common/SCALE.md)) |
| **Раз в неделю** | бэкап |
| Перед обновлением Windows / сменой диска | бэкап |

**Правило:** сомневаешься — `scripts\backup.bat` **до** действия. 10 секунд, спокойнее.

---

## Восстановление

1. `scripts\stop-radar.bat`
2. Из последней папки `D:\Backups\uisness\…` вернуть `.env`, `data\*`, `sessions_Parser\*` → `Desktop\Parser\`
3. `start-radar.bat` → [`RUN.md`](RUN.md) §7

---

## Универсальный шаблон

Скрипт для новых проектов: `C:\Users\hramo\Templates\cursor-universal`.
