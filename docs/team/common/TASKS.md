# TASKS (активное)

**Снимок:** [`STATUS.md`](STATUS.md) · **Prod:** [`PROD_FACTS.md`](PROD_FACTS.md) · **Coder:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md)

---

## → Now (2026-06-20)

**→ Now:** **M1 wave 1** (owner) · UX-audit rerun на Next (опц.)

---

## Очередь

| # | Что | Кто | Статус |
|---|-----|-----|--------|
| **1** | **M1** волна 1 — посевы, baseline Метрики, картинка | owner | ⏳ |
| **2** | Owner smoke: anon квиз → TG → % в ленте | owner | ⏳ |
| **3** | UX-audit rerun `ux_audit.py` на `rawlead.ru` (Next) | @coder | ⏳ · старый отчёт 2026-06-07 |
| **4** | **O39-docs** TZ_API + NEON_SCHEMA | Lead | ⏳ |
| — | **O280-E2E** 24/24 · O286 · O284 · O283 · O280 cutover | — | ✅ |
| — | **O200** LLM judge (owner bar 70%×4 cat) | — | ✅ 2026-06-18 |

---

## Закрыто / архив

O217–O225 · O250/O253 · O261–O262 · O281 · O282 → [`CODER_PROMPT_ARCHIVE`](../architect/CODER_PROMPT_ARCHIVE.md) · [`TASKS_HISTORY`](archive/TASKS_HISTORY.md)

**Гейт GTM:** O218 ✅ · O200 judge ✅ · O280 E2E 24/24 ✅ · M1 ⏳

---

## Аудит repo (2026-06-20)

Источник: [`AUDIT_REPORT_2026-06-20.md`](../../AUDIT_REPORT_2026-06-20.md) · **не блокер M1** · параллельно с посевами.

### P0 — owner (без кода)

| # | Задача | DoD | Статус |
|---|--------|-----|--------|
| A0 | **`.env` гигиена** — не в чат/Git; бэкап локально | [`FOR_YOU.md`](../../FOR_YOU.md) § `.env` | ✅ |
| A1 | Проверить: `.env` не в облачном бэкапе / OneDrive | `D:\Backups\uisness` · не OneDrive · last `2026-06-18` | ✅ Lead 2026-06-20 |

### P1 — Lead (docs only)

| # | Задача | Файлы | Статус |
|---|--------|-------|--------|
| A2 | **FILTERS** индекс (Site/Legacy отдельно — код) | `docs/ops/FILTERS.md` | ✅ |
| A3 | Удалить заглушку | `ops/SOURCES_SAAS.md` | ✅ |
| A4 | Слить карту проекта | `PROJECT_MAP` ← visual redirect | ✅ |
| A5 | Сжать **OWNER_INTENT** hot ≤500 | `archive/OWNER_INTENT_*_ARCHIVE.md` ×3 · hot **311** строк | ✅ Lead 2026-06-20 |
| A6 | Пометить мёртвые docs | `archive/AUDIO_*`, `CURSOR_DEEP_*`, `RESEARCH_PROMPT_TG_*` | ✅ deprecated banner |

### P2 — @coder (малый diff)

| # | Задача | Файлы / DoD | Статус |
|---|--------|-------------|--------|
| A7 | Удалить **только** `src/habr_freelance_parser.py` | + `listing.py` константа · **KEEP** guard/relay | ✅ Coder + Lead verify 2026-06-20 |
| A8 | SQL: дубль префикса `023` | `025_prepaid_subscription.sql` · refs обновлены | ✅ Coder + Lead verify 2026-06-20 |
| A9 | O200 auto-tools (опц.) | judge `tools:empty_but_desc_hints` · regen hints · **не блокер M1** | ⏳ backlog |

### P3 — @coder (архив scripts/)

| # | Задача | Объём | DoD | Статус |
|---|--------|-------|-----|--------|
| A10 | `scripts/_archive/` deploy-o* одноразовые | ~181 файл | не импортируются · README в `_archive/` | ⏳ |
| A11 | `_probe_*` / `_smoke_*` / `_check_*` | ~98 файл | оставить канон probe в `scripts/` (см. `MCP_POOL` / `probe_prod_facts_vps.py`) | ⏳ |
| A12 | `_tmp_*` артефакты в scripts | 11 файлов delete · **KEEP** `_tmp_o170_*` | ✅ 2026-06-20 |

### P4 — backlog (отдельный спринт · не перед M1)

| # | Задача | Файлы | Почему не сейчас |
|---|--------|-------|------------------|
| A13 | Сплит `api_server.py` | ~3900 строк → routers | большой рефактор · OWNER § O142 |
| A14 | 4× `_feed_today_count` | `api_server.py` | внутри A13 |
| A15 | FastAPI `lifespan` | `api_server.py` `on_event` | низкий приоритет |
| A16 | Публичные API vs `_private` | cross-import tests | рефактор |
| A17 | Проекты-призраки | `desktop/`, `wordpress/fl-radar-landing/` | README deprecated · не удалять без owner |
| A18 | `wordpress/node_modules` | `.gitignore` | проверить tracked · ~15 MB |

**Порядок Coder (рекомендация Lead):** A7 → A8 (отдельный PR) → A12 → A10–A11 (один PR, только move) · A13+ после M1 wave 1.

**Уже ок (аудит устарел):** `STATUS.md` ~50 строк · `CODER_PROMPT.md` ~50 строк · `.env` в gitignore · **A0–A6** Lead ✅.

---

## Probe

```powershell
python scripts/probe_prod_facts_vps.py --write
python scripts/probe_parsers_health_vps.py  # on VPS log path
```
