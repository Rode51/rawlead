# Ops /ops/ — «Радар 154м» + нет residential badge + DC красные зря

**Date:** 2026-06-14  
**Owner:** «всё красное, не понимаю что работает»  
**Triage:** Lead · код + VPS verify

---

## Root causes (Lead 2026-06-14)

### 1. cycle_age stale (154м при живом радаре)

`_cycle_age_min(summary)` читает `summary.ts` из SQLite (`status_cycle_summary`).  
`record_cycle_summary` пишет в SQLite в конце каждого **полного** цикла `main.py`.

**После деплоя** O213+O212 (`systemctl restart rawlead-radar`) SQLite summary не обновлялся ~2,5 ч — либо:
- радар перезапустился, начал цикл, но SQLite на VPS смонтирован иначе / path не совпадает  
- или первый цикл после рестарта ещё не завершился (в логе видно: `── Цикл 14:06`, `── Цикл 14:11`, `── Цикл 14:23` — они есть, но в SQLite summary не записывается)

**Fallback (быстрый фикс):** `_cycle_age_min` должен иметь запасной источник — `── Цикл` строки в логе, если SQLite summary stale.

### 2. DC прокси 🔴 «Временно отключён (бан)» — ops таблица

`list_ui_groups()` в `exchange_proxy.py:1140` передаёт **только DC пул** (`_fl_dc_pool()`).  
Residential пул (`FL_PROXY_URLS_RESIDENTIAL`, 25 слотов) — **не отображается** в /ops/.

Владелец видит 4 красных DC и думает «всё сломано», хотя FL ходит через residential.

### 3. После «Сбросить баны» — что происходит

`clear_all_bans()` чистит `_banned_until` и `_strike_count` in-memory.  
При **следующем** `exchange_fetch_begin("fl")` → `_fl_pool_triple()` → `_alive_urls(dc, "fl")`:  
- бан снят → DC живые → возвращает DC пул  
- радар **автоматически** вернётся на DC при следующем fetch  

**Но:** resident. пул переключился **без рестарта**. DC тоже вернётся **без рестарта** — просто по TTL (1ч) или после «Сбросить».

---

## Actions → @coder O214

Ticket: `docs/problems/2026-06-14-ops-cycle-age-stale.md`
