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
    → видно на сайте /lenta/  (только с notified_at!)
```

**Если на сайте пусто по VC/Habr** — смотри не «сломался парсер», а **где обрезало** (после § P1.4 в логе будет явно).

---

## Формат цикла (§ P1.4)

```text
── Цикл 2026-05-26 17:30 ──
FL.ru       │ скачано  90 │ новых  3 │ в бот 0 │ filter 2 │ МИМО 1 │ dup 85
Kwork       │ скачано  12 │ новых  1 │ в бот 0 │ …
VC.ru       │ скачано  12 │ новых  8 │ в бот 1 │ …
Freelancehunt │ скачано 10 │ новых  4 │ в бот 0 │ …
(источники только из `PUBLIC_FEED_SOURCES` — с 2026-05-26 обычно **3 биржи**: FL, Kwork, Freelancehunt; vc_ru / Habr Career ⏸)
Итого в бот: 1 │ neon_insert: 3 │ neon_replay: 2 │ neon_dup_skip: 85 │ лента после L1 — см. Neon is_visible │ ИИ L1=5 L2=1
```

| Счётчик | Значение |
|---------|----------|
| `neon_insert` | Новая строка в Neon (wide ingest) |
| `neon_replay` | Dup в Neon, но L1 догнали (зомби после фильтра) |
| `neon_sqlite_resync` | SQLite уже видел id, Neon нет — догнали INSERT |
| `neon_dup_skip` | Dup в Neon, L1 уже был — пропуск |
| `dup` (в строке источника) | Дубль в SQLite / content fingerprint |

**One-shot replay** (старые строки без L1):  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --dry-run`  
`.venv\Scripts\python.exe scripts\replay_neon_lite_site.py --profile site --limit 50`

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
