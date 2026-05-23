# Для тебя

| Вопрос | Файл |
|--------|------|
| **Как это работает?** | [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Что делать сейчас?** | Ниже «Твои шаги» |
| **Фазы** | [`ROADMAP.md`](ROADMAP.md) |
| **Запуск** | [`ops/RUN.md`](ops/RUN.md) |
| **3 номера + .env** | [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) |
| **Безопасность (без кода)** | [`team/SECURITY.md`](team/SECURITY.md) |
| **Бэкапы** | [`ops/BACKUP.md`](ops/BACKUP.md) · `scripts\backup.bat` |
| **Git / GitHub** | https://github.com/Rode51/uisness · [`ops/GIT.md`](ops/GIT.md) |
| **Роли для нового проекта** | [`../templates/cursor-universal/`](../templates/cursor-universal/) · `C:\Users\hramo\Templates\cursor-universal` |
| **Как вести большой проект** | [`team/SCALE.md`](team/SCALE.md) |

Роли в Cursor: `@lead-architect` · `@designer` · `@coder` · `@mechanic` · `@owner` — `.cursor/rules/` · **Designer** = UI/UX всех проектов (docs, tier-1) · **Coder** = код · **ты** = `.env`, запуск, бэкап.

---

## Что работает

- **FL + Kwork** → фильтр → ИИ → бот
- **TG:** один процесс слушает **acc1 + acc2 + acc3** (свой файл id на аккаунт)
- **Пульт v2 (Tauri):** `scripts\start-radar-desktop.bat` — play/stop, лампы, логи (вместо 3 cmd)
- **Join:** acc1 внутри TG; acc2/acc3 — supervisor (стартуются с пультом)

---

## TG — не путай

| Факт | Деталь |
|------|--------|
| **Один бот** | только уведомления тебе |
| **Чтение чатов** | 3 **user**-аккаунта (Telethon), не Bot API |
| **Radar слушает** | **acc1, acc2, acc3** (одно окно TG) |
| **Статус в боте** | Кнопка **ℹ Статус** — чаты, вакансии, ошибки по каждому номеру |

**Где правда:**

| Файл | Что |
|------|-----|
| [`ops/TG_JOIN_QUEUE.csv`](ops/TG_JOIN_QUEUE.csv) | join: `done` / `pending` |
| `data/telethon_chat_ids_acc1.txt` (или старый `telethon_chat_ids.txt`) | listen acc1 |
| `data/telethon_chat_ids_acc2.txt`, `_acc3.txt` | listen acc2 / acc3 |
| [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) | MVP-5 + описание |

Проверка на аккаунте:

```powershell
.venv\Scripts\python.exe scripts/tg_list_dialogs.py --account acc1
.venv\Scripts\python.exe scripts/tg_list_dialogs.py --account acc2
```

**Сейчас (CSV):** acc1, acc2, acc3 — **все done** ✅.

**Join:** один раз `scripts\start-radar-full.bat` — pending уходят по [`TG_JOIN_SCHEDULE.md`](ops/TG_JOIN_SCHEDULE.md). **Не** запускать `tg_join_queue --account acc1` отдельно (lock сессии).

---

## Твои шаги сейчас

**Пульт v2 готов** — двойной клик [`scripts\start-radar-desktop.bat`](scripts/start-radar-desktop.bat) (Rust ✅). Чеклист: [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md).

**WP локально:** шаг 2 ✅ → **шаг 3** — 5 страниц [`ops/wp-skeleton/`](ops/wp-skeleton/).

Также: перезапуск TG (пересылка постов) · `backup.bat`

---

## Кому писать

| Нужно | Куда |
|-------|------|
| План, docs | **Lead** (`@lead-architect`) — **не проси код** |
| Фича | **Coder** — только если Lead создал `team/CODER_PROMPT.md` |
| Поломка | **Mechanic** + `problems/…` |

Схема: [`team/HOW_TO_USE_CURSOR.md`](team/HOW_TO_USE_CURSOR.md)

---

## Если сломалось

Lead → тикет в `problems/` → Mechanic. Не чини MVP в чате Lead.

Проверка бота: `.venv\Scripts\python.exe src/tg_smoke.py` — [`ops/RUN.md`](ops/RUN.md) §7.
