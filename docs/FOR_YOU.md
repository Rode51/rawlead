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

## Твои шаги сейчас — Vision v0.10

**Канон:** [`team/product/PRODUCT_VISION.md`](team/product/PRODUCT_VISION.md) §0i

1. ~~§ V10 · W2 · V10.5 · P7~~ ✅ 2026-05-26
2. ~~P1 · D1 · P4 код~~ ✅ принято 2026-05-26 · ворота до прода закрыты по коду
3. **`.env` (обязательно сейчас):**  
   `PUBLIC_FEED_SOURCES=fl,kwork,freelancehunt`  
   (убери `vc_ru` и `habr_career`) → пульт **Стоп → ▶** или `start-radar.bat`
4. **Кабинет P4 (один раз):** Neon [`sql/003_users_telegram.sql`](../sql/003_users_telegram.sql) · `pip install -r requirements.txt` · API на `:18766` · в `wp-config.php`: `RAWLEAD_TG_BOT_USERNAME` · [`scripts/open-cabinet-local.bat`](../scripts/open-cabinet-local.bat) или `/cabinet/`
5. **Прод § P5** — только когда скажешь **«едем на прод»** · [`ops/DEPLOY_BUDGET.md`](ops/DEPLOY_BUDGET.md)
6. **Логи:** [`ops/RADAR_LOG.md`](ops/RADAR_LOG.md) — после правки env в цикле **3** строки бирж + `Итого`

**С тебя сейчас:** пункты 3–4 (10 мин). Dogfood — ▶ на ПК, пока радар не на VPS.

Neon ✅ · dogfood бот — как был.

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
