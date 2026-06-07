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
| 1 | `+66953964608_telethon` | **+66953964608** | 38.154.16.60 (spare) | ✅ | **acc1** — MVP, `tg_main` |
| 2 | `+66967716330_telethon` | **+66967716330** | 38.154.16.60 | ✅ | **acc2** — join волна 2 |
| 3 | `+66985780470_telethon` | — | 168.90.199.99 | ❌ | **снять** — не авторизован |
| 4 | `233333925_telethon` | **+351924778041** | 168.90.199.99 | ✅ | **замена acc3** |
| 5 | `234694761_telethon` | **+15092724173** | 168.90.199.99 | ✅ | **запас acc4** |

Замены **не +66** — это нормально для Session+Json; в `.env` важен **путь к файлу**, не префикс имени.

**Прокси 185.147.131.15** — раньше timeout в probe; **2026-06-01** владелец: все 5 IP оплачены · в пуле FL/Kwork. См. [`DEPLOY_VPS.md`](DEPLOY_VPS.md) § «Карта прокси».

---

## Карта (5 IP) — **2026-06-07**

**Секреты только в `.env` / VPS.** Формат: `http://host:port:user:pass`

| IP:port | Закреплён за | В FL/Kwork pool? | Статус |
|---------|--------------|------------------|--------|
| **45.152.197.25:8000** | ~~acc1~~ · **снят** | **нет** | ❌ TLS до Telegram |
| **38.154.16.60:8000** | **acc2** · **временно acc1 + bot** | **да** | ✅ spare |
| **168.90.199.99:8000** | **acc3** (+ acc4 spare) | **да** | ✅ |
| **212.102.151.153:8000** | — | **да** | ✅ |
| **185.147.131.15:8000** | — | **да** | ✅ |

**Временно (2026-06-07):** `TG_PROXY_URL` · `TELETHON_PROXY_ACC1` = URL **acc2** (38.154). VPS: `fix_tg_proxy_acc2_vps.py` · ПК: `fix_tg_proxy_acc1_local.py`.

**FL/Kwork pool (round-robin + failover O79):**  
`212.102…` → `185.147…` → `38.154…` → `168.90…` (без **45.152**).

Полный блок `.env` для VPS → [`DEPLOY_VPS.md`](DEPLOY_VPS.md) § «Карта прокси».

---

## Что прописать в `.env` (владелец)

```env
TELETHON_SESSION_ACC1=C:/Users/hramo/Desktop/Parser/+66953964608_telethon
TELETHON_PROXY_ACC1=http://38.154.16.60:8000:USER:PASS
# было 45.152.197.25 — мёртв TLS; вернуть когда провайдер починит

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

**acc4** (`234694761`) — бэклог Coder ([`../team/common/TASKS.md`](../team/common/TASKS.md)).

Join: [`TG_JOIN_QUEUE.csv`](TG_JOIN_QUEUE.csv) · [`TG_JOIN_SCHEDULE.md`](TG_JOIN_SCHEDULE.md) · [`RUN.md`](RUN.md).

---

## /start у бота (мониторинговые acc) — только код

**Бот:** [@FLPARSINGBOT](https://t.me/FLPARSINGBOT)

Владелец **не имеет доступа к телефонам** acc — только файлы `.session` на ПК. **`/start` у бота для acc1/2/3 делает Telethon**, не руками.

| Acc | Сессия (`.env`) | Как /start |
|-----|-----------------|------------|
| acc1 | `TELETHON_SESSION_ACC1` | Coder § F: `tg_bot_start.py --account acc1` |
| acc2 | `TELETHON_SESSION_ACC2` | то же |
| acc3 | `TELETHON_SESSION_ACC3` | то же |

После сдачи Coder — одна команда:

```powershell
.venv\Scripts\python.exe scripts/tg_bot_start.py --account all
```

Плюс **auto ensure** при каждом старте `tg_main` (новые acc — тот же скрипт с `--account accN` после добавления сессии в `.env`).

Тикет: [`problems/2026-05-24-tg-acc-bot-start.md`](../problems/2026-05-24-tg-acc-bot-start.md)

---

## Relay acc → бот → владелец (§ H)

Цепочка: **группа → acc (Telethon) → @FLPARSINGBOT → бот пересылает тебе в чат с ботом → карточка ИИ.**

| Файл | Назначение |
|------|------------|
| `data/tg_relay_allowlist.json` | `{ "acc1": user_id, … }` — **не в Git**, обновляется автоматически |
| `data/.tg_bot_started_accN` | acc уже отправил `/start` боту |

**Регистрация allowlist:** при `tg_bot_start.py` (`get_me`) и при старте `tg_main` (refresh всех `TELETHON_MONITOR_ACCOUNTS`).

**Проверка:**

```powershell
.venv\Scripts\python.exe scripts/tg_bot_start.py --account all --force
# пульт ■ → ▶
# тестовый пост не с acc1 — смотреть только чат @FLPARSINGBOT
```

В `data/radar.log`: `тг:relay:accN:msg=…` · нет `PeerUser` на id владельца.

Тикет: [`problems/2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md)
