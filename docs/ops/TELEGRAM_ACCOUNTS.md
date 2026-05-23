# Мониторинговые аккаунты Telegram

**Секреты — только в `.env`.** Сессии: `C:\Users\hramo\Desktop\Parser\`

**Последняя проверка:** 2026-05-23 (Telethon + прокси, каждый файл отдельно).

---

## Итог простым языком

| | Количество |
|---|------------|
| **Файлов сессий на ПК** | **5** |
| **Рабочих** | **4** ✅ |
| **Мёртвых** | **1** ❌ (+66985780470) |

**Для радара сейчас:** acc1 (+66953964608) — мониторит 5 чатов (путь в `.env`).
**Для join волны 2:** acc2 + **одна из двух замен** вместо старого acc3.

---

## Таблица (проверено)

| № | Файл сессии | Телефон в TG | Прокси | Статус | Роль |
|---|-------------|--------------|--------|--------|------|
| 1 | `+66953964608_telethon` | **+66953964608** | 45.152.197.25 | ✅ | **acc1** — MVP, `tg_main` |
| 2 | `+66967716330_telethon` | **+66967716330** | 38.154.16.60 | ✅ | **acc2** — join волна 2 |
| 3 | `+66985780470_telethon` | — | 168.90.199.99 | ❌ | **снять** — не авторизован |
| 4 | `233333925_telethon` | **+351924778041** | 168.90.199.99 | ✅ | **замена acc3** |
| 5 | `234694761_telethon` | **+15092724173** | 168.90.199.99 | ✅ | **запас acc4** |

Замены **не +66** — это нормально для Session+Json; в `.env` важен **путь к файлу**, не префикс имени.

**Прокси 185.147.131.15** — не использовать (timeout).

---

## Что прописать в `.env` (владелец)

```env
TELETHON_SESSION_ACC1=C:/Users/hramo/Desktop/Parser/+66953964608_telethon
TELETHON_PROXY_ACC1=http://45.152.197.25:8000:USER:PASS

TELETHON_SESSION_ACC2=C:/Users/hramo/Desktop/Parser/+66967716330_telethon
TELETHON_PROXY_ACC2=http://38.154.16.60:8000:USER:PASS

# вместо +66985780470:
TELETHON_SESSION_ACC3=C:/Users/hramo/Desktop/Parser/233333925_telethon
TELETHON_PROXY_ACC3=http://168.90.199.99:8000:USER:PASS

TELETHON_SESSION_ACC4=C:/Users/hramo/Desktop/Parser/234694761_telethon
TELETHON_PROXY_ACC4=http://168.90.199.99:8000:USER:PASS
```

Дубли для acc1: `TELETHON_SESSION_PATH` / `TELETHON_PROXY_URL` = те же, что ACC1.

---

## Проверка у себя

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts/tg_health.py
.venv\Scripts\python.exe scripts/tg_list_dialogs.py --account acc1
.venv\Scripts\python.exe scripts/tg_list_dialogs.py --account acc2
.venv\Scripts\python.exe scripts/tg_list_dialogs.py --account acc3
```

После смены ACC3 на `233333925` команда `--account acc3` должна показать чаты (не «не авторизована»).

**acc4** (`234694761`) — бэклог Coder ([`../team/TASKS.md`](../team/TASKS.md)).

Join: [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv) · [`TG_JOIN_SCHEDULE.md`](TG_JOIN_SCHEDULE.md) · [`RUN.md`](RUN.md).
