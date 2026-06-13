# Coder — hot queue (active)

**→ Now:** § **O195-TINDER-ONBOARD-w1** · § **O196-ASYNC-DRAFT** (parallel)

**O194 ✅** verify 2026-06-13 · **O193 ✅ O191 ✅ O190 ✅** → archive

**Archive:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O195-TINDER-ONBOARD-w1 (**→ now · 2026-06-13**)

**Goal:** `/quiz/` WP page (12 real Neon leads, Tinder UX) + localStorage profile + DB migration + two new API endpoints.

**Product spec:** `docs/team/product/LEAD_PRODUCT_PROMPT.md` § TINDER-ONBOARD

**t1 — DB migration (Neon):**
```sql
ALTER TABLE user_tags
  ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS interaction_count INT DEFAULT 0;
```

**t2 — `GET /v1/quiz/cards`** (no auth):
- 3 cards per category (dev / design / marketing / text): `is_visible=true, category=X, ai_score >= 60 ORDER BY created_at DESC LIMIT 3`
- Fallback if < 3 results: relax to `ai_score >= 45`
- Strip from response: `budget`, `source`, `url` — title + snippet + lead_tags only

**t3 — `POST /v1/me/tags/import`** (auth required):
- Body: `{"tags": {"ui_ux": 4.0, "python": -1.0, ...}}`
- Upsert `user_tags`: weight from payload · `last_active_at = NOW()` · `interaction_count = 1`

**t4 — WP `/quiz/` page:**
- New template `template-parts/rawlead/quiz.php` + `js/rawlead-quiz.js`
- 12 cards shown sequentially (not all at once); progress bar «N из 12»
- Buttons: **«Взял бы»** → all card tags `+2.0` · **«Не моё»** → `-1.0`
- Weights accumulated in `localStorage {rawlead_quiz: {tags: {tag: weight, ...}}}`
- No budget, no source, no external URL on cards
- Result screen: top-2 niches by like-count + weekly volume estimate; CTA → TG login + muted «Посмотреть ленту →» `/lenta/`
- After TG login success: auto-POST `/v1/me/tags/import` from localStorage, then clear key

**DoD:**
- `/quiz/` renders 12 cards from real Neon leads (no budget/source)
- TG login from result screen → tags in Neon `user_tags`
- `user_tags` schema has `last_active_at` + `interaction_count`
- pytest: `/v1/quiz/cards` returns 12 (3/category, budget absent); `/v1/me/tags/import` upserts correctly

**Files:** `src/api_server.py` · `src/pg_storage.py` · `wordpress/rawlead-kadence-child/template-parts/rawlead/quiz.php` · `wordpress/rawlead-kadence-child/js/rawlead-quiz.js`

---

## § O195-TINDER-ONBOARD-w2 (**after w1 deploy · same ticket**)

**Goal:** anon `/lenta/` filter lockout + weighted scoring with decay in `/v1/feed`.

**t1 — Anon filter lockout (`rawlead-feed.js`):**
- No JWT → category chips disabled (grey); skills picker hidden
- Replace filter area with promo strip: `«⚙ Фильтры — после настройки профиля · [Настроить ленту →]»` → `/quiz/`
- Logged-in users: filters unchanged

**t2 — Weighted `keyword_match` in `/v1/feed` (`api_server.py`):**
```python
now = datetime.utcnow()
effective = {}
for tag, weight, last_active in user_tags_rows:
    decay = 0.95 ** ((now - last_active).days / 3)
    eff = weight * decay
    if eff > 0.5:
        effective[tag] = eff

if not effective:
    keyword_match = 50.0  # neutral fallback — no degraded ranking for new users
else:
    keyword_match = min(
        sum(effective.get(t, 0) for t in lead_tags) / sum(effective.values()) * 100,
        100.0,
    )
final_rank = ai_score * 0.6 + keyword_match * 0.4
```

**t3 — Weight delta endpoint + triggers:**
- `POST /v1/me/tags/weight_delta {lead_id, delta, interaction_count_delta?}` → update `user_tags.weight` + `last_active_at`
- `rawlead-feed.js`: expanded card → `delta +0.1`; «Написать отклик» click → `delta +3.0, ic_delta 2`
- `rawlead-cabinet.js`: delete from inbox → `delta -0.5`

**DoD:**
- Anon → disabled chips + promo strip on `/lenta/`; logged-in → filters active as before
- Empty `user_tags` → `keyword_match = 50` (not 0); no degraded rank for new users
- Smoke: 3 expand events → `user_tags.weight` updates visible in Neon

**Files:** `wordpress/rawlead-kadence-child/js/rawlead-feed.js` · `src/api_server.py` · `src/pg_storage.py`

---

## § O196-ASYNC-DRAFT (**parallel with O195-w1 · 2026-06-13**)

**Goal:** «Написать отклик» → instant UI confirmation (< 200ms); draft generates in background.

**Context:** `lead_draft_jobs` already has `status pending/done/failed`. **Only UX changes** — no L2 logic change.

**t1 — `rawlead-feed.js`:**
- On click: fire `POST /v1/leads/{id}/draft` (existing endpoint); do **not** await inline
- Immediately: button text → `«✅ Добавлено в кабинет»`, disabled; **no spinner, no page block**
- On fetch error → non-blocking toast `«Ошибка, попробуй снова»`

**t2 — `rawlead-cabinet.js` inbox card states:**
- `pending`: `«⏳ Черновик генерируется…»` + poll every 10s until `done/failed`
- `failed`: `«Не удалось сгенерировать · [Повторить]»`
- `done`: draft text as now

**DoD:**
- Button changes < 200ms on click; no blocking wait
- `/cabinet/` shows `pending → done/failed` with correct copy
- No regression on existing draft display or L2 generation

**Files:** `wordpress/rawlead-kadence-child/js/rawlead-feed.js` · `wordpress/rawlead-kadence-child/js/rawlead-cabinet.js`

---

## § O186-SECURITY-AUDIT (**→ backlog**)

Pentest JWT/IDOR/webhook/draft — deliver `docs/problems/…-security-audit.md`

---

## Backlog (not now)

**YOUDO-PREFILTER:** YouDo parser → pre-filter digital categories only → text visible 7.9%→~63% · spec: `LEAD_PRODUCT_PROMPT.md` § YOUDO-PREFILTER

---

## Closed ✅ (hot index)

O194 · O193 · O191 · O190 · O189 · O185-* · O174* · O182* · O178 · O176 · O175 · O168 → archive

## Background

O171 · O173 · O188 (radar auto-join, no Coder unless stuck) · [`PRODUCT_CANON.md`](../product/PRODUCT_CANON.md)
