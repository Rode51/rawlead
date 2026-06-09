# Coder — горячий контур (активное)

**→ Сейчас:** § **O160-RADAR-INGEST** — per-source lock · wall-clock FL/YouDo · cycle watchdog · systemd notify

**Блокер ads:** ingest стабильность ✅ O160 → perf p95 @50 VU

**Закрыто:** O160 ✅ deploy 2026-06-09 · O159 burst 3/3 ✅ · O158 deploy ✅

**Deploy:** `scripts/deploy-o160-radar-vps.py` ✅ · radar active · `── Цикл ──` каждые ~2–5 мин

**Архив DoD:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O160-RADAR-INGEST — стабильность конвейера навсегда ✅ Lead 2026-06-09

**DoD:** pytest **4/4** · deploy VPS ✅ · `systemctl is-active` = active · `── Цикл ──` пошёл · 24h smoke ⏸ owner

### Что сделал Coder

| Слой | Файл | Что |
|------|------|-----|
| **L1** | `exchange_browser_fetch.py` | `_FETCH_LOCKS: dict[str, Lock]` — per-source вместо глобального `_FETCH_LOCK` |
| **L2** | `fl_parser.py` | `fetch_listing_html_browser_wall_clock` + fallback httpx · env `FL_LISTING_TIMEOUT_SEC=120` |
| **L3** | `youdo_parser.py` | wall-clock · env `YOUDO_LISTING_TIMEOUT_SEC=120` |
| **L4** | `main.py` | `_fetch_source` — thread wrapper с timeout · on kill → `close_all_browser_contexts()` · env `RADAR_SOURCE_FETCH_WALL_SEC=180` |
| **L5** | `main.py` | `_CycleWatchdog` — kill browser + raise если цикл > `RADAR_CYCLE_WALL_SEC=600` |
| **L6a** | `rawlead-radar.service` | `WatchdogSec=660` + `NotifyAccess=all` + `sd_notify(WATCHDOG=1)` каждый цикл |
| **L6b** | `healthchecks.py` | `ping_cycle_overrun()` → `HEALTHCHECKS_SITE_FAIL_URL` при overrun |

**Lead fix при deploy:** `NotifyAccess=main` → `NotifyAccess=all` (sd_notify из Python subprocess, не bash).

### Verify

```powershell
# Tail radar log: ── Цикл ── каждые ~2–5 мин
.venv\Scripts\python.exe scripts\_tmp_ingest_diag_vps.py
```

**Owner 24h smoke:** ни одного gap >15 min в `── Цикл ──` · HC fail URL — нет алертов.

**Не трогать:** draft API · WP theme · Neon schema.

---

## Archived §§ (grep по номеру в CODER_PROMPT_ARCHIVE.md)

| § | Суть | Дата |
|---|------|------|
| O159 | OR semaphore · burst 3/3 · queue_ahead | 2026-06-08 |
| O158 | match push dedup · шкала fill · ?lead= | 2026-06-08 |
| O157 | YouDo traffic ↓ residential | 2026-06-08 |
| O156 | YouDo human browser · cooldown | 2026-06-08 |
| O155 | HC dead man's switch | 2026-06-08 |
| O154 | grid neighbor no jump | 2026-06-08 |
| O153 | card chips collapse +n | 2026-06-08 |
| O152 | exchange trace jsonl · /ops/ | 2026-06-08 |
| O151 | OR acc2 UX | 2026-06-08 |
| O150 | draft UX polish | 2026-06-08 |
| O149 | no-flip inline expand | 2026-06-08 |
| O148 | draft pre-warm · OR proxy · tools regex | 2026-06-08 |
| O147 | match bar · trial hide (flip → O149) | 2026-06-08 |
| O146 | draft card UX flip lock | 2026-06-08 |
