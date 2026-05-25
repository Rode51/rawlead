# Для тебя

**Полная карта docs:** [`README.md`](README.md)

| Вопрос | Файл |
|--------|------|
| **Что делать сейчас?** | Ниже «Твои шаги» |
| **Как это работает?** | [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) |
| **Фазы / приоритет** | [`team/architect/ROADMAP.md`](team/architect/ROADMAP.md) · vision v0.9 |
| **План Product** | [`team/product/LEAD_PRODUCT_PROMPT.md`](team/product/LEAD_PRODUCT_PROMPT.md) |
| **Запуск** | [`ops/RUN.md`](ops/RUN.md) |
| **Пульт** | [`ops/DESKTOP_LAUNCH.md`](ops/DESKTOP_LAUNCH.md) |
| **TG acc + @FLPARSINGBOT** | [`ops/TELEGRAM_ACCOUNTS.md`](ops/TELEGRAM_ACCOUNTS.md) |
| **Схема (картинка)** | [`design/rawlead/project-map-owner.png`](design/rawlead/project-map-owner.png) |

Роли: `@lead-architect` · `@coder` · `@mechanic` · `@designer` — см. [`README.md`](README.md) § по роли.

---

## Что работает

- **FL + Kwork** → фильтр → ИИ → бот **@FLPARSINGBOT**
- **TG:** acc1 + acc2 + acc3 в одном `tg_main`
- **Пульт:** `start-radar-desktop.vbs` — ▶/■/✕, **2** процесса (.venv)

---

## TG — коротко

| Факт | Деталь |
|------|--------|
| Бот | [@FLPARSINGBOT](https://t.me/FLPARSINGBOT) — карточки **тебе** |
| Чтение чатов | 3 session-аккаунта (Telethon), **не** телефоны |
| Пересылка | acc → бот → твой чат · `/start` acc — **только код** (§ F) |
| Listen / join | [`ops/TG_JOIN_QUEUE.csv`](ops/TG_JOIN_QUEUE.csv) · [`ops/SOURCES_POOLS.md`](ops/SOURCES_POOLS.md) |

Подробнее TG: [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) · тикеты: [`problems/2026-05-24-tg-acc-bot-start.md`](problems/2026-05-24-tg-acc-bot-start.md)

---

## Запуск пульта

1. Двойной клик на ярлык **FL Radar** на рабочем столе → подождать **5 с**.
2. Пульт открылся, нет красного баннера → ▶ один раз.
3. Лампы «Биржи» и «TG» зелёные — всё работает.

**Не запускай** `start-radar-full.bat` и `python tg_main` вручную — дубли ломают бота.

## Если пульт не ответил («API не отвечает»)

1. Закрой пульт (✕).
2. Запусти `scripts\stop-radar.bat` (двойной клик).
3. Удали файл `data\.radar_desktop.lock` если есть.
4. Снова двойной клик на ярлык — подождать 5 с.

## Твои шаги сейчас

1. ~~MVP скелет WP (`/lenta/` + `/cabinet/`)~~ ✅ принято 2026-05-25
2. **Приёмка волны 2 (~5 мин):** `scripts/wp_install_rawlead_theme.py` → открыть `http://radarzakaz.local/`
   - nav без «Главная»; hero «Смотреть ленту» + «Смотреть тарифы ↓» → скролл к тарифу
   - «Для кого» — 3 ниши (не только IT); `/how/`, `/faq/` — новые тексты (если старые: WP → Плагины → выкл/вкл **RawLead Landing** или `python scripts/wp_skeleton_setup.py`)
   - ок → напиши Lead **«W2 принято»**
3. **Dogfood:** отклики по боту, 1–2 в день
4. **§ 3j** у `@coder`: 2 карточки в ряд, wheel в раскрытых «Навыки», пульт (вкладка Статус)
5. После 3j → **3f** ИИ-агент

С понедельника: отклики **по боту** (вердикт «Брать»), 1–2 сильных в день.

| Блокер | Кто |
|--------|-----|
| **`/lenta/` не грузится** | **@mechanic** · [`problems/2026-05-25-wp-lenta-feed-not-loading.md`](problems/2026-05-25-wp-lenta-feed-not-loading.md) |
| pythonw.exe = launcher (2 процесса) | **@mechanic** |
| TG relay+card | ✅ acc шлют в бот; при сбое — prompt-test · [`problems/2026-05-24-tg-forward-not-via-bot.md`](problems/2026-05-24-tg-forward-not-via-bot.md) |

---

## Кому писать

| Нужно | Куда |
|-------|------|
| План, docs | **Lead** — не проси код |
| Фича | **Coder** — если есть `team/architect/CODER_PROMPT.md` |
| Поломка | **Mechanic** + `problems/` |

Проверка бота: `.venv\Scripts\python.exe src/tg_smoke.py` — [`ops/RUN.md`](ops/RUN.md) §7.

---

## Cursor — прокси

| В `.env` | Действие |
|----------|----------|
| `CURSOR_PROXY_ENABLED=1` | Прокси **вкл** (по умолчанию `TG_PROXY_URL`) |
| `CURSOR_PROXY_ENABLED=0` | Прокси **выкл** |

После смены: `scripts\sync-cursor-proxy.bat` → **перезапуск Cursor**.
