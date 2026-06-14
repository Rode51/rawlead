# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк · детали → [`archive/STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

## Сейчас prod (2026-06-14 · triage)

| Слой | Факт |
|------|------|
| **Сервисы** | `rawlead-api` · `rawlead-bot-poll` · `rawlead-radar` — **active** |
| **Сайт** | `/lenta/` 200 · feed API 200 |
| **FL** | last Neon insert **00:30 MSK Jun 14** (~13h) · `parsed=30 fresh=0` = возможно мало заказов в вс |
| **Kwork** | O213 fix ✅ src · **deploy pending** — pages 1–3 + exchange-safe filter |
| **TG** | monitor слушает (peers 70/64/40) · O212 fix ✅ deploy pending |
| **Логи** | O212 fix ✅ (`skip_entity=N` вместо dump ids) · deploy pending |

**Корень Kwork/FL:** Kwork → **O213** pagination + filter (src ✅) · FL: воскресенье, мало постинга — мб норма.  
[`2026-06-14-kwork-fl-zero-new.md`](../../problems/2026-06-14-kwork-fl-zero-new.md)

---

## ✅ O213 Kwork coverage (src · 2026-06-14)

**Fix:** `kwork_parser.py` — pages 1–3 (`KWORK_MAX_PAGES`, default 3), dedup, log `pages=N` · `filters.py` — `EXCHANGE_SAFE_STOPS` bypass for kwork/fl only (TG unchanged)  
**pytest:** 38/38 (`test_kwork_parser` + `test_filters` + `test_o207b` + `test_o171` + O117 httpx fallback)  
**Deploy:** `kwork_parser.py` + `filters.py` → restart **`rawlead-radar`**

**Как проверить (VPS):**
```bash
grep 'listing:kwork' data/radar_site.log | tail -5   # parsed>12 pages=2-3
grep 'pipeline:filter:exchange_safe kwork' data/radar_site.log | tail -5
pytest tests/test_kwork_parser.py tests/test_filters.py tests/test_o207b_tg_filter_tune.py tests/test_o171_ops_funnel.py -q
```

---

## Сейчас prod (baseline)

---

## ✅ O200 L2 — закрыто (owner 2026-06-13)

Pilot r5 + batch2: judge **85% / 95%** · cat playbooks deployed.  
**Решение:** regen/judge **пауза** до первых платных · точечно по id · full regen **нет**

---

## ✅ O209 match-first (WP · 2026-06-14)

**Theme:** `1.18.84` · deploy ✅ Lead 2026-06-14 · spec [`wave-o209-match-brief.md`](../../design/wp/wave-o209-match-brief.md)

| Зона | Сделано |
|------|---------|
| **P0 /quiz/** | intro → cards (exit anim, early-cta ≥5) → finale (category bars, TG, trial chip) |
| **P1 lenta** | anon strip 30 мин · quiz banner · expired banner · match label · slots только premium |
| **P1 cabinet** | copy · trial badge · expired banner · skills UI hidden |
| **P1 marketing** | hero/pricing/FAQ/how · tier table |

**Хвосты (косметика):** FAQ дубль «% совпадения» в `marketing.php` · `viewsHeadHtml` в refresh (не в initial render)

---

## ✅ FL-PROXY-STABILITY (src · 2026-06-14)

DC tier · residential fallback · FL browser multi-slot · httpx max 1 ban · ops 🟡 при parsed≥25  
**Deploy:** api+radar ✅ · residential **25 slots** ✅ `patch-vps-fl-residential-env.py`

---

## ✅ O211 ops truth metrics (src · 2026-06-14)

Footer: `сегодня N · за 24ч M` (MSK) · parsed в tooltip · YouDo 🟡 при visible_24h>0  
**Verify:** pytest **15/15** · **deploy API** ✅ `deploy-o211-ops-footer-vps.py` 2026-06-14 (Lead verify VPS)

---

## ✅ O206 t2b sync chat_ids (src · 2026-06-14)

**Fix:** `tg_sync_chat_ids.py` + `config.py` — merge **all** `TG_JOIN_QUEUE*.csv` (v1+v2+v3), not single `TG_JOIN_QUEUE_CSV`.  
**VPS:** acc1 file **72** · startup peers **70** (2 `get_entity` skip: `1621850024`, `1031532699`) · audit **`ok: true`**  
**pytest:** 4/4 (`test_o206_tg_sync_chat_ids` + audit)  
**Deploy:** `deploy-o206-t2b-sync-vps.py` ✅

---

## ✅ O207 TG funnel proof (scripts · 2026-06-14)

**t1:** `tg_funnel_audit.py` — `days_7` / `days_30`, per-account, `data/tg_funnel_audit_human.md`  
**t2:** `tg_history_sample.py` — read-only Telethon, no Neon  
**t3:** `tg_filter_replay.py` — offline spam+filter replay, `owner_label` field  
**t4:** owner how-to → `docs/problems/2026-06-13-tg-feed-volume.md` § Owner labeling  
**pytest:** 7/7 (`test_o207_tg_funnel_audit` + `test_o207_tg_filter_replay`)  
**Deploy:** `deploy-o207-tg-funnel-vps.py` ✅ · **owner labels** ✅ 120/120 (canvas 2026-06-14) · replay on VPS

**Replay:** pass **91** · filter **22** · spam **7** · **8 vacancy** wrongly blocked → O207b

**Как проверить (VPS):**
```bash
cd /opt/rawlead && .venv/bin/python scripts/tg_funnel_audit.py --log data/radar_site.log
.venv/bin/python scripts/tg_history_sample.py --account acc1 --max-chats 3 --per-chat 5
.venv/bin/python scripts/tg_filter_replay.py --in data/tg_history_sample.json
```

**Filter rules:** не менялись (replay only).

---

## ✅ O207b TG filter tune (src · 2026-06-14)

**Fix:** `FILTER_WIDE` + FILTERS stop ловил skill-слова в реальных TG-вакансиях. Для `tg:*` + `is_tg_order_post` — soft bypass `TG_WIDE_SOFT_STOPS` (figma, монтаж, логотип, баннер, вебинар, va, иллюстратор); team-hiring «в команду» — bypass off. Расширены order markers (`задача:`, `откликнуться`, `ищем … дизайнера`).

| Метрика | before | after |
|---------|-------:|------:|
| `vacancy_blocked` | 8 | **0** |
| noise filter | 14 | 14 |
| noise pass | 69 | 69 |
| replay pass / filter / spam | 91/22/7 | **99/14/7** |

**pytest:** 49/49 (`test_o207b` + `test_o207` + `test_tg_spam_filter`)  
**Deploy:** ✅ `deploy-o207b-radar-vps.py` 2026-06-14 · VPS replay **99/14/7** · radar **active** (Lead verify VPS)

**Как проверить:**
```bash
python scripts/tg_filter_replay.py --in data/tg_history_sample_labeled.json --out data/tg_filter_replay.json
pytest tests/test_o207b_tg_filter_tune.py tests/test_o207_tg_filter_replay.py tests/test_tg_spam_filter.py -q
```

---

## ✅ O212 ops log truth (src · 2026-06-14)

**Fix:** TG startup log — `чатов/file/filter` без `ids=[…]` · skip → `skip_entity=N` · ops «сегодня N» из Neon · cycle `parsed/fresh` · TG 🔴 из `tg_pult_lamp_state` · log line prefer `handler_ok`  
**pytest:** 20/20 (`test_o212` + `test_o171`)  
**Deploy:** `tg_monitor.py` → restart **`rawlead-radar`** · `owner_admin.py` + `ops-pult.js` → restart **`rawlead-api`**

**Как проверить (VPS):**
```bash
grep 'тг:монитор:старт' data/radar_site.log | tail -3   # no ids=[…]
grep skip_entity data/radar_site.log | tail -5
curl -s -b cookie.txt /ops/dashboard | jq '.exchanges[] | {source_id,today_new_ids,cycle_hint,exchange_level}'
# TG card 🟢 when handler_ok + pulse fresh even if Neon TG insert 0
pytest tests/test_o212_ops_log_truth.py tests/test_o171_ops_funnel.py -q
```

---

## 🔴 Next

| Волна | What | Who |
|-------|------|-----|
| **1** | **O213+O212 deploy** radar + API | @coder · **→ сейчас** |
| **2** | Owner smoke: `/lenta/?source=kwork` + `/ops/` | owner |
| **3** | Perf lenta/home/quiz | Design → @coder |
| **4–6** | L2 70% · stress · ads | ROADMAP |

---

t3c deployed · ops/spam ok · O209+FL deploy 2026-06-14
