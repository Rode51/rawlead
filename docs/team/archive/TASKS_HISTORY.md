# TASKS — архив

Краткие записи после сдачи Coder (Lead).

---

## 2026-05-23 — Coder: статус номеров в боте (принято Lead)

- Кнопка **ℹ Статус** / `/status`: FL/Kwork + acc1/2/3 (чаты, сообщения, новые, в бот, ошибки)
- `src/radar_status.py`, правки `telegram_control.py`, `tg_monitor.py`, `main.py`, `tg_main.py`

---

## 2026-05-23 — Coder: multi-session TG (принято Lead)

- Один `tg_main`: acc1+acc2+acc3; `telethon_chat_ids_accN.txt`; `TELETHON_MONITOR_ACCOUNTS`
- `tg_sync_chat_ids.py --account all`; join → `join:listen:add` для monitor-аккаунтов
- Владелец: `.env` + sync + тест JS Jobs (acc2)

---

## 2026-05-23 — Coder: join supervisor (принято Lead)

- Один `tg_join_daemon.py` для acc2/acc3/acc4; registry; 3 окна в `start-radar-full.bat`

---

## 2026-05-23 — Coder: авто-join в чаты (принято Lead)

- `src/tg_join_runner.py` — `run_join_tick(account, client=…)`
- acc1 join в `tg_monitor` + `listen+` без рестарта; acc1 в CLI запрещён
- acc2/acc3 — 2 окна `--daemon`; `start-radar-full.bat`
- Следующий шаг: один `tg_join_daemon` (бэклог)

---

## 2026-05-23 — Coder: авто `telethon_chat_ids.txt` (принято Lead)

- append после join acc1; `tg_sync_chat_ids.py`; `.env` → файл id

---

## 2026-05-23 — Coder: TG accounts + join queue (принято Lead)

- `--account acc1|acc2|acc3`, `tg_join_lib.py`, `tg_join_queue.py`, CSV, `data/tg_join.log`
- `acc4` — бэклог

---

_Старые записи MVP/TG-кнопки — в истории чатов / бэкапе docs при необходимости._
