# Coder — Контур 1 «добить» + ЛК на WP (портфолио)

**Дата:** 2026-05-24 · Lead  
**Контекст:** владелец с **пн** массово откликается; завтра — стабильный радар + **личный кабинет** на WP для портфолио (первый проект).

**Vision:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) §0c (Контур 1 = owner) · [`TZ_WP.md`](TZ_WP.md)

---

## Цель завтра (MVP приёмки)

### A. Контур 1 — «работает без сюрпризов»

| # | Готово когда |
|---|----------------|
| A1 | Пульт ▶ — 2 процесса, TG зелёная, `tg_smoke.py` ok |
| A2 | VPN выкл — бот отвечает на **ℹ Статус** |
| A3 | Join волна 3 идёт (`tg_join.log`), acc1/2/3 слушают |
| A4 | Карточка в боте: вердict + (если успеешь) **match % / breakdown** — минимум текущий формат не ломать |
| A5 | `AI_ENABLED=1` в `.env` — ИИ на owner-потоке |

**Не блокирует приёмку:** Neon в проде (можно заглушка / следующий спринт).

### B. ЛК на WordPress — **для портфолио** (не полный SaaS)

Страница **`/cabinet`** (или `/account`) в child theme `rawlead-kadence-child`:

| Блок | MVP |
|------|-----|
| Hero | «Личный кабинет RawLead» + подпись «демо / owner» |
| **Мои теги** | UI: 8–12 chip (Python, FastAPI, парсеры…) — сохранение в **user meta WP** или localStorage (без Neon ok) |
| **Лента** | 3–5 **демо-карточек** в стиле REFERENCE (rank %, источник, вердict) + пометка «live data — этап 2» **ИЛИ** read-only JSON из `wordpress/.../demo-leads.json` в репо |
| CTA | Ссылка на Telegram бота / «как подключить» |

**Стиль:** тот же Manrope/Unbounded, что главная — [`REFERENCE.md`](../design/wp/REFERENCE.md).

**Не делать завтра:** WooCommerce, multi-user, Neon API, Habr ingest, оплата.

### E. TG → бот: бюджет + ссылка — ✅ сдано 2026-05-24

**Тикет:** [`2026-05-24-tg-bot-budget-message-link.md`](../problems/2026-05-24-tg-bot-budget-message-link.md)

### F. TG acc → /start у бота — **частично**

**Тикет:** [`docs/problems/2026-05-24-tg-acc-bot-start.md`](../problems/2026-05-24-tg-acc-bot-start.md)

| # | Готово когда |
|---|----------------|
| F0–F4 | как в тикете · флаги acc1/2/3 |

### G. TG relay PeerUser — **частично** (Mechanic)

**Тикет:** [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md) § G

### H. TG relay acc→бот→ты — **код есть, приёмка нет** (ждёт § I)

**Тикет:** [`2026-05-24-tg-forward-not-via-bot.md`](../problems/2026-05-24-tg-forward-not-via-bot.md)

**Сначала Mechanic § I.** Потом Coder: при `увед=1` в логе — `tg:цепь` + `тг:relay:accN`.

### I. Дубли python — **Mechanic, блокер**

**Тикет:** [`2026-05-24-duplicate-python-processes.md`](../problems/2026-05-24-duplicate-python-processes.md) — сейчас **2× main.py**.

Запуск **только** пульт `start-radar-desktop.vbs` → ▶ / ■.

### K. radar_control.py — убрать PowerShell, подключить process_guard — **Mechanic, СРОЧНО**

**Тикет:** [`2026-05-24-radar-control-psutil.md`](../problems/2026-05-24-radar-control-psutil.md)

`process_guard.py` уже написан на psutil (§ J ✅), но `radar_control.py` его **не использует**.  
В нём живут 2 своих куска PowerShell + `sweep_orphans=False` → дубли продолжают плодиться.

| # | Готово когда |
|---|--------------|
| K1 | `_STOP_PS` + `stop_radar_processes()` удалены из radar_control |
| K2 | `_running_needles()` заменена на psutil через `count_radar_workers()` |
| K3 | `start()`: `sweep_orphans=True` + `kill_duplicate_radar_workers()` + `wait_radar_workers_stopped()` |
| K4 | `main()`: `kill_other_radar_control()` перед захватом порта |
| K5 | Повторный ▶ → не третий процесс |

**Файлы:** `scripts/radar_control.py` (только он)

### J. psutil вместо PowerShell — **Mechanic, ПРИОРИТЕТ #1**

**Тикет:** [`2026-05-24-psutil-migration.md`](../problems/2026-05-24-psutil-migration.md)

**Корень всех регрессий:** `process_guard.py` убивает дубли через `subprocess.run(["powershell", ...])` → regex не матчит системный `pythonw.exe`, таймауты, непредсказуемый stdout.

**Задача:** полная замена PowerShell-слоя на `psutil` в `src/process_guard.py`.

| # | Готово когда |
|---|--------------|
| J1 | `psutil>=5.9.0` в `requirements.txt`, установлен в `.venv` |
| J2 | `process_guard.py` — ноль вызовов `subprocess.run(["powershell"` |
| J3 | Все публичные функции с теми же сигнатурами (совместимость с `radar_control.py`, `main.py`, `tg_main.py`) |
| J4 | Пульт ▶ → ровно 2 worker, повторный ▶ → `already_running` |

---

## Файлы (можно трогать)

| Путь | § |
|------|---|
| `src/process_guard.py` | **J** — psutil замена |
| `requirements.txt` | **J** — добавить psutil |
| `src/telegram_notify.py` | E |
| `src/tg_forward.py` | F, H |
| `src/telegram_control.py` | H |
| `src/tg_relay_allowlist.py` | H (новый) |
| `scripts/tg_bot_start.py` | F, H |
| `scripts/tg_main.py` | F, H |
| `src/tg_bot_start.py` | F, H |
| `docs/ops/RUN.md` | F |
| `docs/ops/TELEGRAM_ACCOUNTS.md` | H |
| `src/tg_monitor.py` | E (бюджет из текста TG) |
| `wordpress/rawlead-kadence-child/...` | B |
| `docs/ops/WP_KADENCE_INSTALL.md` | B |
| `docs/team/STATUS.md` | сдача |
| `tests/` | E — если есть notify |

## Файлы (не трогать)

- `scripts/radar_control.py` — вызывает guard, сигнатуры не меняются
- `src/main.py` — вызывает guard
- `desktop/src/main.ts` (§ D закрыт)
- `src/filters.py`, `docs/ops/FILTERS.md` (§ E — без согласования Lead)
- join-очередь, `TASKS.md`, `FOR_YOU.md`
- `scripts/sync-cursor-proxy.bat`, `scripts/sync_cursor_proxy.py` — proxy Cursor работает, не трогать
- Push без просьбы владельца

Сверка: [`PROJECT_MAP.md`](PROJECT_MAP.md)

---

## Как проверить

1. **§ H:** allowlist + relay в poll → тестовый пост → оригинал + карточка в @FLPARSINGBOT.
2. **§ B:** `http://radarzakaz.local/cabinet` — после H.
3. Пульт ▶ 30 мин — без падений.

---

## D. Пульт: ✕ зависает — ✅ сдано 2026-05-24

**Тикет:** [`docs/problems/2026-05-24-pult-close-hang.md`](../problems/2026-05-24-pult-close-hang.md) — fixed. Приёмка: владелец после `rebuild-pult.bat`.

---

## Не делать

- `TASKS.md`, `FOR_YOU.md`
- Push GitHub без просьбы владельца
- Контур 2 / `SOURCES_SAAS.md`

---

_Lead · 2026-05-24 · порядок: **@mechanic § K (radar_control)** → **§ J ✅** → **@coder § H** → **§ B**_
