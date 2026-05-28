# Лог радара — как читать (для владельца)

**Файл:** `data/radar.log` · **Пульт:** вкладки `radar.log` / `tg_join.log` / `Статус`

---

## Воронка одного заказа

```
Парсер скачал N карточек
    → новых в SQLite (ещё не видели id)
    → прошли словесный фильтр (FILTERS.md)
    → прошли бюджет
    → ИИ (не МИМО / или МИМО)
    → уведомление в Telegram (notified_at)
    → видно на сайте /lenta/  (`is_visible=true` + source в `PUBLIC_FEED_SOURCES`, в т.ч. `tg:-100…`)
```

**Если на сайте пусто по VC/Habr** — смотри не «сломался парсер», а **где обрезало** (после § P1.4 в логе будет явно).

---

## Формат цикла (§ P1.4)

```text
── Цикл 2026-05-26 17:30 ──
FL.ru       │ скачано  90 │ новых  3 │ в бот 0 │ filter 2 │ МИМО 1 │ dup 85
Kwork       │ скачано  12 │ новых  1 │ в бот 0 │ …
(источники только из `PUBLIC_FEED_SOURCES` — биржи **fl,kwork** + **tg:-100…** для каждого join `done` из allowlist; пересборка: `python scripts/build_public_feed_sources.py`; vc_ru / Habr Career ⏸)

**TG в ленте:** после join `done` → `python scripts/build_public_feed_sources.py` → строку в **`.env` и `.env.site`** (Site читает `.env.site` первым) → рестарт Site ▶ → one-shot `replay_neon_lite_site.py --profile site --tg-replay --limit 200`.

Итого в бот: 1 │ neon_insert: 3 │ neon_replay: 2 │ neon_dup_skip: 85 │ лента после L1 — см. Neon is_visible │ ИИ L1=5 L2=1
```

| Счётчик | Значение |
|---------|----------|
| `neon_insert` | Новая строка в Neon (wide ingest) |
| `neon_replay` | Dup в Neon, но L1 догнали (зомби после фильтра) |
| `neon_sqlite_resync` | SQLite уже видел id, Neon нет — догнали INSERT |
| `neon_dup_skip` | Dup в Neon, L1 уже был — пропуск |
| `dup` (в строке источника) | Дубль в SQLite / content fingerprint |

---

## Сводка Site за 10 мин (§ SITE-LOG-ROLLUP)

**Файл Site:** `data/radar_site.log` · строка каждые **10 мин** (скользящее окно, не один цикл):

```text
site:сводка │ 10мин │ скачано 102 │ новых_sqlite 4 │ neon_insert 2 │ neon_replay 1 │ l1 5 │ l2 0 │ is_visible 1 │ filter 3 │ мимо 2
```

| Поле | Значение |
|------|----------|
| `скачано` | Карточек с бирж за 10 мин (сумма по источникам) |
| `новых_sqlite` | Новые id в SQLite за окно |
| `neon_insert` | INSERT в Neon (wide ingest) |
| `neon_replay` | Dup в Neon, L1 догнали |
| `l1` / `l2` | Вызовы ИИ L1 / L2 за окно |
| `is_visible` | L1 → `is_visible=true` в Neon (порог score) |
| `filter` | Отсечено словесным фильтром (`skip:filter`) |
| `мимо` | ИИ «МИМО» / прочие `skip:ai:*` (не filter/dup/budget) |

Если `скачано 0` — в той же строке может быть **причина** (ошибка fetch или «биржи без новых карточек»).

**Пульт:** вкладка `radar.log` — ищи `site:сводка`; вкладка **Статус** — блок «Сводка 10 мин».

## Статус пульта (§ PULT-STATUS-LOGS)

**Два пульта:** Legacy `:18765` + `data/radar_legacy.log` · Site `:18775` + `data/radar_site.log`.

| Поле (вкладка «Статус» / `/status`) | Значение |
|--------------------------------------|----------|
| `profile` / `profile_label` | `site` / `legacy` — не путать ботов |
| `bot_label` | `@rawlead_bot` (Site) · `@FLPARSINGBOT` (Legacy) |
| `telegram_chat_id` | Куда шлёт control panel и legacy-карточки |
| `conveyor` | Site: `RADAR_CONVEYOR=1` — опрос 1 мин + L1 batch |
| `poll_min` | `POLL_INTERVAL_MINUTES` |
| `log_file` | `radar_site.log` или `radar_legacy.log` |
| `site_rollup_10m` | Строка `site:сводка │ 10мин │ …` из SQLite |
| `last_visible_at` | `MAX(created_at)` в Neon при `is_visible=true` |
| `last_cycle` | JSON: FL/Kwork скачано/новых/neon_insert/is_visible |
| `neon_consumer_stats` | Legacy: выборка/новых/в бот за цикл и за сессию |
| `bot_start_ok` | Site+TG: все acc отправили /start боту |

**TG-бот:** кнопка «ℹ Статус» — тот же текст, что `/status-text` **своего** профиля (Site ≠ Legacy).

**Ошибка `POLL_INTERVAL_MINUTES: минимум 10`:** в `.env.site` нужны `RADAR_PROFILE=site` и `RADAR_CONVEYOR=1`.

**One-shot replay** (старые строки без L1):  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --dry-run`  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --limit 50`

**TG one-shot** (L1 + `is_visible` для `source LIKE tg:%` уже в Neon):  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --tg-replay --dry-run`  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --tg-replay --limit 200`

**Backfill sqlite→Neon** (id на живой ленте):  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --backfill-missing --dry-run`  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --backfill-missing --limit 30`

---

## Фильтр режет сильно?

**Да, по задумке dogfood:** в бот и на сайт — только прошедшие FILTERS + PROFILE + ИИ.

| Этап | Типично много? |
|------|----------------|
| `dup_content` | Да — повторы с FL/Kwork/TG |
| `skip:ai:МИМО` | Да — пока PROFILE жёсткий |
| `skip:filter` | Средне — стоп-слова §0i |
| `skip:budget` | Реже — `MIN_BUDGET_RUB` |

**Править под концепцию:** [`docs/ops/FILTERS.md`](FILTERS.md), [`docs/ops/PROFILE.md`](PROFILE.md) · отдельная задача Product/Lead после воронки в логах.

**Публичная лента ≠ весь парсинг:** сайт показывает только `notified_at` (как бот). Если нужны все спарсенные вакансии на витрине — отдельное ТЗ Coder (не P1.4).

---

_Lead · 2026-05-26_
