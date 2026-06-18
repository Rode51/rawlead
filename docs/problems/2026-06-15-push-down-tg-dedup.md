# Push still down + TG duplicate cards (owner smoke 2026-06-15)

**Date:** 2026-06-15  
**Severity:** P0 push · P1 dedup  
**Reporter:** owner after O250b deploy

## Symptom

1. **No match push** for owner + Monica on **new** TG test card (feed shows high match, «только что»).
2. **Two identical** TG cards in `/lenta/` (same title, budget **228228**, «только что»).

Backfill **rejected** by owner — forward-only fix.

## Push — likely causes (Lead read-only)

| # | Hypothesis | Check |
|---|------------|-------|
| 1 | `push_match_for_lead` runs but **`_send_push_message` fails** (proxy / Bot API / user blocked bot) | log `push:match:fail` · TG API response body |
| 2 | L1 **`visible=0`** or push gate skipped | `grep pipeline:L1.*5177575757` · `visible=` |
| 3 | O250b **not active** in running radar process | VPS `grep _push_km_for_lead_row` · process restart time vs deploy |
| 4 | **`lead_id` missing** at push time | `push:match:lead_missing` |
| 5 | km still below threshold (formula) | O250c `MATCH_PUSH_DEBUG=1` |

**Note:** Cards **are** in feed → `is_public_feed_source` + `is_visible` likely OK for test group on prod.

## TG dedup — root cause (code)

`lead_pipeline._insert_neon_after_gates()`:

1. First insert uses `content_hash=fingerprint` → OK.
2. On **content_hash conflict** (same text, **new** `external_id` = new TG `message.id`):
   - If `(source, external_id)` not in Neon yet → **retry insert with `content_hash=""`**.
   - That bypasses `UNIQUE(content_hash)` → **second visible row** in feed.

Relevant: `src/lead_pipeline.py` ~337–361 · `src/listing_dedup.py`.

Also: `skip_content_dup` skips SQLite fingerprint when `exchange_neon and not lead_exists` (~535–548) — by design for Neon-first path; Neon hash conflict must **abort**, not fall back to empty hash.

**Not:** duplicate `(source, external_id)` from dual acc — that path is protected by UNIQUE.

## Fix direction

- **O250c:** push debug + fix send path if broken.
- **O252:** on content_hash conflict → treat as dup (`dup_abort`), never `content_hash=""` insert; pytest TG same text two msg ids → one Neon row.

## Owner

No backfill. After fix: one new post in `prompt-test` → single card + push to owner + Monica.

---

## Решение (Mechanic 2026-06-15)

**Статус push:** путь **жив** после O250 UUID-fix + restart · **не** env · **не** send_fail.

### Проверено на VPS

| Check | Result |
|-------|--------|
| `.env.site` `MATCH_PUSH=1` | ✅ |
| runtime `/proc/$PID/environ` `MATCH_PUSH=1` | ✅ PID 1692139 |
| O250c code on VPS (`tg_http_request`, `_push_km_for_lead_row`, `push:match:skip`) | ✅ |
| `match_push_log` total | **0** (ни одного успешного send) |
| `MATCH_PUSH_DEBUG=1` + restart radar | ✅ 1 цикл · grep `push:match:skip` |

### DEBUG-цикл (23:40–23:41 UTC)

```
push:match:skip user=8d5afb3d lead=27128 reason=km km=25 thr=60   # Monica
push:match:skip user=164786fe lead=27128 reason=km km=0 thr=80
push:match:skip user=a24ae28c lead=27128 reason=km km=0 thr=70
```

Аналогично lead=27129 (km=17) · lead=27130 (km=25). **Нет** `push:match:fail` · **нет** `push:match:err` после restart с DEBUG.

### TG test card (prompt-test msg=185 → lead **26978**)

- `pipeline:L1 tg:-1005177575757:id=185 visible=1` — **23:06 UTC** ✅
- Push **вызывался** (gate OK) · без DEBUG — **молчаливый skip** (km < thr)
- Neon probe: Monica `push_km=19` · `thr=60` · **pass=False** · `fetch_lead_row OK`
- `grep push:match.*26978` — пусто (DEBUG включён **после** этой карточки)

### Исторический UUID-crash

До O250/restart: каждый L1 → `push:match:err lead=…:'UUID' object is not subscriptable` (последний ~lead **22379**). Сейчас **не воспроизводится**.

### Вывод (push P0)

1. **MATCH_PUSH=1** в runtime — OK.
2. Push **не «down»** — работает, но **все eligible users skip по km** на свежих visible leads.
3. Monica на smoke-карточке: **km=19**, не ≥60 → push корректно не шлёт.
4. Если `/lenta/` показывает **100%**, а push km=19 — **feed vs push parity** (→ `@coder` O250c verify / UI match source).
5. Owner tg `5177575757` в `users` **не найден** — нужен `/start` @rawlead_bot с prod аккаунта.

### Ops (owner)

- `MATCH_PUSH_DEBUG=1` **ещё включён** на VPS — вернуть `MATCH_PUSH_DEBUG=0` после review.
- Smoke: **новый** пост в prompt-test → `grep push:match radar_site.log` · ожидать `push:match:user=` только если km ≥ thr.

### TG dedup (P1)

Fix **O252** в `CODER_PROMPT` · deploy `scripts/deploy-o250c-o252-vps.py`.

**Статус push:** диагностика закрыта · **код-fix не применялся** · forward smoke + O252 deploy.
