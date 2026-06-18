# FL: parsed=0 при alive=4/4, bans_cleared=0 (новый режим)

**Date:** 2026-06-16 13:11 MSK  
**Symptom (owner):** «фл упал»  
**Triage:** Lead Architect · VPS `radar_site.log`

---

## Факты (VPS 2026-06-16 ~13:55 MSK)

| Метрика | Значение |
|---------|----------|
| `rawlead-radar` | **active** |
| `listing:fl` | **`parsed=0 fresh=0`** с 13:11 (до — 13:03 `parsed=30 fresh=1`) |
| `fetch:fl` | **`proxy=212.102.151.153:8000 slot=4/4 alive=4/4`** — прокси живой |
| `fl_listing:auto_ban_clear` | streak=3 и streak=13 · **`bans_cleared=0`** — нет банов в ban-table |
| `fetch:fl restart_source ?` | `browser contexts closed` — без рестарта |
| Restart radar | Не помог — `parsed=0` продолжается |
| Последний `parsed>0` | 13:03 (`fresh=1`) |
| FL inserts | 0 с ~13:03 |

---

## Отличие от предыдущих инцидентов

| Прошлые (14–15.06) | Сейчас (16.06) |
|--------------------|----------------|
| `alive=0/25` proxy ban cascade | `alive=4/4` — нет банов |
| `bans_cleared=N` → O233 hard reset | `bans_cleared=0` → O233 **не триггерит** |
| DC прокси в ban-table | Прокси в ban-table нет |

**Новый режим:** freelance.ru отдаёт antibot HTML (без карточек) без занесения в ban-table. Наш код не различает «нет карточек antibot» от «нет новых заказов».

---

## Корень

1. FL browser (Playwright Chromium) fetch идёт через DC proxy (IP `212.102.151.153`)
2. Freelance.ru блокирует запрос на уровне контента (antibot/CAPTCHA page) — прокси не банится в нашей таблице (нет 403/timeout по условиям `_ban_url`)
3. `fl_listing:auto_ban_clear` (O233) срабатывает на `parsed=0 streak` — но `bans_cleared=0`, поэтому `fl_hard_reset` не вызывается (нет storage-флага `restart_source_fl`)
4. `fetch:fl restart_source ?` — вопрос без ответа: `?` = флаг не выставлен, contexts закрыты но parser не рестартован
5. Результат: radar крутится вхолостую каждые ~90 сек, каждый раз получает antibot HTML

---

## Code fix (→ @coder § O256)

| # | Fix | Файл |
|---|-----|------|
| 1 | При `parsed=0 streak >= 5 AND bans_cleared == 0` → выставить `restart_source_fl` + wipe browser contexts (как hard_reset, но без ban clear) | `fl_parser.py` · `exchange_browser_fetch.py` |
| 2 | При `parsed=0` (browser fetch) log первые 300 байт HTML → видно captcha/antibot | `fl_parser.py` |
| 3 | Ops лампа: `parsed=0 streak > 10 AND bans_cleared=0` → 🔴 `antibot_soft`, не просто `parsed=0` | `radar_status.py` |

---

## Immediate ops

Рестарт radar уже сделан — не помог. Следующие варианты:

1. Подождать — если freelance.ru снимет блок по TTL (~1ч с 13:03) → `parsed=30` само
2. `python scripts/clear-vps-proxy-bans.py` — нет смысла если `bans_cleared=0` уже
3. Долгосрочно: § O256 код-фикс

---

_Lead Architect · triage 2026-06-16 13:56 MSK_
