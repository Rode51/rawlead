# TG: acc1/2/3 — /start у бота (только через код)

**Дата:** 2026-05-24  
**Статус:** fixed · **блокер снят** 2026-05-24 (Coder § F)  
**Контекст:** пересылка **acc → @FLPARSINGBOT → твой чат**. Владелец **не имеет доступа к телефонам** acc1/2/3 — только `.session` на ПК. **`/start` только через Telethon.**

**Связано:** [`2026-05-24-tg-bot-budget-message-link.md`](2026-05-24-tg-bot-budget-message-link.md) · [`TELEGRAM_ACCOUNTS.md`](../ops/TELEGRAM_ACCOUNTS.md)

---

## Ограничение владельца (2026-05-24)

| Факт | Следствие |
|------|-----------|
| Нет доступа к телефонам acc | **Нельзя** Start вручную в Telegram |
| Есть `.session` + прокси в `.env` | `/start` шлёт **скрипт** или **tg_main при старте** |
| Бот | [@FLPARSINGBOT](https://t.me/FLPARSINGBOT) |

---

## Цепочка

```text
Группа → acc1/2/3 (Telethon, session) → пересыл @FLPARSINGBOT → forwardMessage → TELEGRAM_CHAT_ID (ты)
```

---

## Ожидание Coder (§ F) — обязательно

| # | Готово когда |
|---|----------------|
| F0 | **Без телефона:** весь onboarding acc → бот только кодом |
| F1 | `scripts/tg_bot_start.py --account acc1\|acc2\|acc3\|all` — Telethon: connect session → `send_message('FLPARSINGBOT', '/start')` (или entity по username) |
| F2 | **`tg_main` при старте каждого acc** — вызов ensure `/start` **до** listen (не ждать ручного запуска скрипта) |
| F3 | Флаг `data/.tg_bot_started_<acc>` — idempotent, не спамить каждый рестарт |
| F4 | Новый acc в docs: после `tg_convert_session` / путь в `.env` → **`tg_bot_start.py --account accN`** → потом join |
| F5 | Ошибка forward в `radar.log`: «acc не стартовал бота — запусти tg_bot_start.py» |
| F6 | [`RUN.md`](../ops/RUN.md) § TG: команда для владельца после сдачи |

**Default bot username:** `FLPARSINGBOT` · optional `.env` `TELEGRAM_BOT_USERNAME=FLPARSINGBOT`

---

## Решение (Coder § F, 2026-05-24)

| Файл | Что |
|------|-----|
| `src/tg_bot_start.py` | ensure `/start`, флаг `data/.tg_bot_started_<acc>` |
| `scripts/tg_bot_start.py` | CLI `--account acc1\|acc2\|acc3\|all` |
| `src/tg_monitor.py` | ensure до listen при старте каждого acc |
| `src/tg_forward.py` | подсказка в ошибке, если флага нет |
| `docs/ops/RUN.md` | команда для владельца |

**Не делать:** требовать телефон; ломать § E.

---

## Владелец — после сдачи Coder

```powershell
cd C:\Users\hramo\uisness
.venv\Scripts\python.exe scripts/tg_bot_start.py --account all
```

Затем пульт ▶ (или `tg_main` сам ensure при старте). Проверка: пост в listen-чат → пересыл + карточка у @FLPARSINGBOT.

---

## Приёмка

1. `tg_bot_start.py --account all` — exit 0, в логе ok acc1/2/3.
2. Без предварительного скрипта: **холодный** старт `tg_main` — ensure срабатывает, пересылка работает.
3. Пост в группе → нет `tg:forward:…` в `radar.log`, есть пересыл у владельца.

---

## Файлы

- `scripts/tg_bot_start.py` (новый)
- `src/tg_bot_start.py` или логика в `src/tg_forward.py` / shared helper
- `scripts/tg_main.py`, `src/tg_monitor.py`
- `docs/ops/RUN.md`, `TELEGRAM_ACCOUNTS.md`, `TELEGRAM_LOGIN.md`
- `docs/team/common/STATUS.md`
