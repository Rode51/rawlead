# Coder — hot queue (active)

**→ Now:** § **O174b-YOOKASSA-PAY** prep ⏸ keys · YouDo ingest monitor

**Archive:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O182b-YOUDO-IMPORT-HOTFIX (**✅ smoke 2026-06-11**)

**Lead verify:** import on VPS · pytest **43/43** · deploy `deploy-o182b-vps.py` · post-deploy **no NameError** · listing still flaky (`health:youdo fail kind=browser` antibot on US slots) — separate from import.

---

## § O182-DELIST-INPROGRESS (**✅ smoke 2026-06-11**)

**Owner pain (2026-06-11):** YouDo **«Выполняется»** — исполнитель выбран, отклик недоступен, страница **жива** · smoke `https://youdo.com/t14827772` · Neon **#16149** `is_visible=true` · last recheck **2026-06-10** → alive.

**Not covered by O181:** «Закрыто для откликов» ≠ status **«Выполняется»** + **«Зарезервировано … ₽»** (SBR escrow).

**Root cause:** `_YOUDO_GONE_MARKERS` has «исполнитель выбран/найден» but page shows **«Выполняется»** without those strings · `__next_data__` → false alive.

**False-positive guard:** do **not** add bare substring `выполняется` — open tasks say «работа выполняется удаленно» in body (regression on live listings).

### t1 — YouDo in-progress / completed detection

Prefer **`__NEXT_DATA__` task status** if present (status enum / `isOpenForOffers` / similar — inspect t14827772 HTML).

Fallback markers (casefold), at least:
- **`зарезервировано`** (SBR reserved — strong in-progress signal)
- **`завершено`** / **`задание завершено`** if YouDo shows completed
- status-chip phrases **without** bare `выполняется` — e.g. regex `>выполняется<` or JSON field only

Tests:
- `test_youdo_in_progress_sbr` — HTML from t14827772 (`Выполняется` + `Зарезервировано` + `__NEXT_DATA__`) → `check_project_page_gone` **True**
- `test_youdo_live_description_not_gone` — body contains «выполняется удаленно» but **no** status/escrow → **False**

Deploy + targeted backfill / recheck · smoke **#16149** delisted · not in `/v1/feed?source=youdo`.

**DoD:** #16149 `source_gone` · pytest green · deploy VPS · owner Ctrl+F5 card gone

**Lead verify:** #**16149** `is_visible=false` · `delist_reason=source_gone` · **not in** feed · markers `isInProcess`/`зарезервировано` on VPS · pytest **21/21** · **ingest regression** → § O182b.

---

**Lead verify (O181):** #**16797** `source_gone` · not in feed · markers on VPS · pytest **19/19** · purge **apply 2026-06-11:** `purge_delisted` **306** + age **964** deleted.

**Backlog:** youdo visible **923** · `source_gone` **3** · nightly timer purges delisted after 1d when `--apply`.

---

## § O180-DELIST-WEB (**✅ smoke 2026-06-11**)

**Lead verify:** #**17048** `is_visible=false` · `delist_reason=source_gone` · **not in** `/v1/feed?source=youdo` (918 scanned) · VPS `checked=80` · markers `page-deleted` on VPS · pytest **18/18**.

**Backlog:** youdo visible **925** · `source_gone` **1** · batch skip **~73/80** (proxy) — scheduled delist + repeat backfill по мере живых proxy.

---

## § O179-YOUDO-WALL (**✅ deploy 2026-06-11**)

Listing OK post-deploy · details → ticket `2026-06-11-youdo-timeout-antibot.md`

---

## § O174b-YOOKASSA-PAY (**prep ⏸**, P0)

**Start when:** owner YooKassa keys **+** `@lead-designer` § **O174-D** + `@lead-product` § **O174-COPY** · **prep now OK** (routes/env stubs, no prod keys).

**Owner decision 2026-06-10:** YooKassa is the **only** payment channel. Drop Stars, crypto, manual SBP/transfers in WP + `@rawlead_bot`.

### Product

| Item | Value |
|------|--------|
| Trial | **1 ₽** · **3 days** Premium · **once per account** · via YooKassa |
| After trial | **790 ₽/month** · **auto-renewal** (YooKassa recurring) |
| Footer (legal) | ✅ O174a |

### t1 — YooKassa backend

- Integrate YooKassa API: create payment (trial 1 ₽, subscription 790 ₽), webhook `payment.succeeded` / recurring · map to existing `subscriptions` / trial flags in Neon (reuse O107 trial fields where possible).
- Env on VPS (owner fills): `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, return URL, webhook secret — document keys in deploy comment only, not in repo.
- Disable or gate legacy: `stars_billing`, `premium_pay` SBP/crypto/Stars paths — **no user-facing entry**.

### t2 — WP pricing + cabinet (**follow O174-D wire + O174-COPY**)

- Redesign `/pricing/` + `pricing-card.php` + `rawlead-cabinet.js` subscription block: **single CTA** → YooKassa checkout (trial vs full price by `trial_used`).
- Remove copy/UI for Stars, USDT/TON, manual SBP, `@rawlead_bot /pay` deep-links for pay.
- Home `pricing-preview` — same single price story (**790 ₽/мес**, trial **1 ₽ / 3 дня**, **автопродление** copy from PM).
- **UI gate:** no ship without Design spec — owner flagged UX regression risk.

### t3 — Bot @rawlead_bot

- Remove pay menu: `pay:sbp`, `pay:crypto`, `pay:stars`, manual approve flows · `/pay` → redirect or inline «Оплата на сайте → rawlead.ru/pricing».
- Keep: auth, support, feed deep-links — **do not break** O165/O170.

### t4 — Copy source

- UI strings from `@lead-product` § **O174-COPY**. Until PM ships: owner numbers only; no Stars/crypto mentions.

**Files:** `src/` billing (new `yookassa_billing.py` or extend `premium_pay.py`) · `api_server.py` webhook route · `wordpress/rawlead-kadence-child/` pricing/cabinet · `config.py` env · tests for trial gate + webhook idempotency

**Do not break:** active subscriptions logic · TG login · `/lenta/` paid access · O168 perf

**DoD:** owner smoke: trial 1 ₽ → 3d Premium → auto-renew 790 ₽ · bot has no crypto/Stars/SBP · FAQ/pricing aligned · footer ✅ O174a

---

## § O168-PRE-ADS-GATES (**✅ accepted 2026-06-10**)

| Gate | Result |
|------|--------|
| load p95 @50 | **1462 ms** ✅ (owner 09:46 UTC) |
| l2_auto | **96.7%** draft/tools ✅ (n=30) |
| l2_send | **80%** live judge ✅ (n=10) |

Full stress parsers/journey — optional; ads gate met.

---

## § O165-TG-TEST-GROUP (**smoke**, P0)

join **3/3** ✅ · owner post in test group → Lead Neon verify

---

## Closed ✅ (hot index)

O181 delist closed · O180 delist smoke · O178 feed · O179 YouDo wall · O177 · O176 trace · O175/175b · O174a · O166–O168 — details → `CODER_PROMPT_ARCHIVE.md`

## Background

O171 ops rebuild · O173 draft stream B+C · O144–O145 deploy ⏸
