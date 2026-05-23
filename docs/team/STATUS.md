# STATUS

Карта: **[`../ROADMAP.md`](../ROADMAP.md)** · владелец: **[`../FOR_YOU.md`](../FOR_YOU.md)** · **как работает:** [`../KAK_ETO_RABOTAET.md`](../KAK_ETO_RABOTAET.md)

---

## Сейчас

- **Фаза 0** — FL, Kwork, ИИ, бот ✅
- **Фаза 1 TG** — multi-session acc1+acc2+acc3 ✅ · join supervisor ✅
- **Бот «Статус»** — кнопка ℹ / `/status`: биржи + 3 номера (чаты, вакансии, ошибки) ✅

---

## Рантайм (2026-05-23)

- `.env`: `TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3` — включено
- `radar.log`: старт **acc1** (6–8 чатов), **acc2** (4), **acc3** (2)
- acc1: два id в файле с префиксом `-100` (Distantsiya, Фрилансеры) — ошибки PeerUser убраны

---

## Последние сдачи (Coder)

| Задача | Итог |
|--------|------|
| Multi-session TG | `tg_monitor` + `telethon_chat_ids_accN.txt` + `tg_sync --account all` |
| Статус в боте | `radar_status.py`, кнопка ℹ в `telegram_control.py` |

**Как проверить статус:** в боте **ℹ Статус** — FL/Kwork + acc1/2/3. Нужны оба окна (биржи + TG) для свежих счётчиков.

---

## Последняя сессия (Coder)

**Сделано:** пульт `scripts/radar_desktop.py` — Старт/Стоп full-радара (3 процесса без cmd), индикаторы, логи, статус из `radar_status.py`; ярлык `scripts/start-radar-desktop.bat`.

**Файлы:** `scripts/radar_desktop.py`, `scripts/start-radar-desktop.bat`, `docs/ops/DESKTOP_LAUNCH.md`, `docs/ops/RUN.md`

**Как проверить:** закрыть cmd радара → из корня repo: `.venv\Scripts\python.exe scripts\radar_desktop.py` → **▶ Старт** → в диспетчере 3 python, в `data/radar.log` — `радар:старт`, `тг:старт`; **⏹ Стоп** — процессы исчезают; повторный старт без 409.

---

## Следующий шаг

| Кто | Действие |
|-----|----------|
| **Владелец** | Проверить пульт на ПК; ярлык на `start-radar-desktop.bat` |
| **Lead** | FOR_YOU / ROADMAP после ревью |
| **Дальше** | WordPress — [`TZ_WP.md`](TZ_WP.md) |

---

## Блокеры

- нет
