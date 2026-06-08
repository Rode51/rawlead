# 2026-06-08 — Radar OOM · сайт недоступен ночью

**Статус:** mitigated RAM **2 GB** ✅ · **Coder O132 код ✅** · **deploy ⏳** · Wave 2 ⏸

## Симптом (владелец)

- Ночью сайт **пару раз полностью падал** — не открывался
- Рadar **постоянно перезагружается**
- TG «ничего не читает» — **0 заказов за 4 недели** (ожидание владельца)

## Диагностика VPS (Lead probe 2026-06-08 ~04:40 UTC)

### 1. Radar — OOM killer каждый ~1 ч

| Метрика | Значение |
|---------|----------|
| `rawlead-radar` NRestarts | **14** |
| journal 24h | **8× `oom-kill`** (Jun 07 21:36 → Jun 08 04:14 UTC) |
| dmesg | `Out of memory: Killed process … chrome-headless` в cgroup `rawlead-radar.service` |
| RAM | **961 MiB** total · **704 MiB used** · **70 MiB free** · swap **782/1024 MiB** |

**Корень:** Playwright **Chromium headless** (FL/Kwork) + `main.py` + `tg_main` на **1 GB VPS** → global OOM → systemd restart radar → **orphan chrome** копится → цикл.

**Почему «сайт лёг»:** WP (`/var/www/rawlead.ru`) и nginx на **том же VPS** — при swap thrash / OOM вся машина не отвечает, не только API.

`rawlead-api`: **NRestarts=0** с O131 deploy (Jun 07 15:28) — API стабилен, проблема radar/RAM.

### 2. TG — читает, но почти не попадает в ленту

**Radar log (сегодня):**

- `тг:монитор:acc1` **10 чатов** · `acc2` **6 чатов** · `ready`
- `site:сводка │ 10мин │ neon_insert 6–7` · `скачано 320–422`

**Neon (28 дней, `source LIKE 'tg:%'`):**

| Метрика | Значение |
|---------|----------|
| Ingested | **92** (вся TG-история с ~Jun 01) |
| **is_visible** | **6** (~6.5%) |
| Last 7d ingested | **90** |
| Last 7d visible | **6** |

**Не «мёртвый TG»:** сообщения приходят, в Neon пишутся. **Фильтры съедают:** `dup_fast_skip`, `cross_source_dup`, `skip:ai:МИМО`, vacancy — см. `radar_site.log`.

**4 недели:** Neon project с **2026-05-22** — TG в prod БД только **~1 неделя** активного ingest; раньше другой контур/не site profile.

### 3. Сейчас (probe)

- `https://rawlead.ru` → **200**
- `https://api.rawlead.ru/health` → **ok**

## Fix (план Lead)

| Приоритет | Действие | Кто |
|-----------|----------|-----|
| **P0 ops** | Upgrade VPS **→ 2 GB RAM** (дешевле, чем борьба с OOM) | **владелец** |
| **P0 code** | `MemoryMax` systemd · 1 Playwright slot · kill orphan chrome on cycle · O110 profile wipe | **@coder** § O132 |
| **P1** | TG visibility audit: why 6/92 visible — dup vs L1 МИМО vs cross_source | **@mechanic** |
| **Pause** | Wave 2 stress rerun до стабильного radar 24h | owner |

## Файлы

- `deploy/systemd/rawlead-radar.service`
- `src/exchange_browser_fetch.py` · `src/kwork_parser.py`
- `src/main.py` · `src/tg_main.py`
