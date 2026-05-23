# Coder — TG: единый join в tg_main + уведомления acc2/acc3

**Решение владельца (2026-05-23):** убрать «особый» acc1 и лишние процессы; join и слушание — **одинаково** для acc1/acc2/acc3; в боте видно, **какой номер** нашёл заказ.

---

## Проблема

| Сейчас | Зачем больно |
|--------|----------------|
| `_join_acc1_loop` только для acc1 | Дубли логики, отдельный флаг `TG_JOIN_AUTO_ACC1` |
| `tg_join_daemon.py` для acc2/acc3 | Второй процесс, риск `database is locked`, после join — рестарт TG |
| Уведомления | Pipeline в `tg_monitor` **уже** на всех сессиях с `chat_ids`, но acc2/3 мало слушают до join; в боте неочевидно **какой acc** |

---

## Цель

1. **Один join** внутри `tg_main`: для **каждого** подключённого acc — цикл `run_join_tick(account, client=…)` + `register_monitor_join` (как сейчас acc1).
2. **Убрать** отдельный child **`tg_join_daemon`** из пульта / `radar_control` / `start-radar-full.bat` (или оставить скрипт как deprecated no-op с логом «используйте tg_main» — предпочтительно удалить из автозапуска).
3. **Удалить** или обобщить `TG_JOIN_AUTO_ACC1` → например `TG_JOIN_IN_TG_MAIN=1` для всех `TELETHON_MONITOR_ACCOUNTS`.
4. После join **любого** acc — hot-reload listen (`_reload_listen_chats`), без обязательного рестарта.
5. **Бот:** в пересылке/разборе явная метка номера, напр. `acc2 · ПОМОГАТОР` (не ломать существующий формат бирж).

---

## Файлы (ожидаемо)

| Файл | Действие |
|------|----------|
| `src/tg_monitor.py` | `_join_loop` для всех sessions; убрать acc1-only |
| `src/config.py` | конфиг join для monitor accounts |
| `src/tg_join_registry.py` | все monitor acc регистрируют join |
| `scripts/tg_join_daemon.py` | не в автозапуске; docstring deprecated |
| `scripts/radar_control.py`, `scripts/radar_desktop.py` | убрать ChildSpec join |
| `scripts/start-radar-full.bat`, `start-join-daemons.bat` | убрать окно join |
| `src/lead_pipeline.py` / `telegram_notify.py` / `tg_forward.py` | метка acc в уведомлении |
| `.env.example` | новые имена env |
| `docs/ops/RUN.md`, `docs/team/ARCHITECTURE.md` | одна схема |
| `docs/team/STATUS.md` | сдача |

**Lead обновит** `KAK_ETO_RABOTAET.md` после приёмки.

---

## Не ломать

- `TG_JOIN_QUEUE.csv`, лимиты 4/час · 25/сутки · ночь
- `tg_queue_import.py`
- 73 pending волны 3
- FL/Kwork, пульт Tauri

---

## Как проверить (STATUS)

1. Пульт ▶ — **2** фоновых процесса (биржи + TG), **без** отдельного join.
2. `data/tg_join.log` — `join:ok account=acc2` / acc3 без `database is locked`.
3. Тестовый пост в чате acc2 (после join) → пересылка + разбор в боте с подписью **acc2**.
4. ℹ Статус в боте — счётчики по acc1/2/3.
5. `python scripts/tg_join_queue.py --account acc1` — по-прежнему отказ / предупреждение про lock (если tg_main запущен).

---

## Не делать

- Править `TASKS.md`, `FOR_YOU.md`
- Push на GitHub

---

_Lead · 2026-05-23_
