# Coder — горячий контур (активное)

**→ Сейчас:** фон post-launch — **perf gate** · **O133** TZ (после ads) · split god-files **O142/O143**

**Закрыто:** O121-w2b **код ✅** · O158 deploy ✅ · Wave 2 owner **✅**

**Deploy:** `scripts/deploy-o158-vps.py`

**Архив DoD:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O158-MATCH-UX — дубли push · шкала совместимости · deep link ?lead=

**Owner P0** · скрин 2026-06-08 · бэклог [`OWNER_INTENT.md`](OWNER_INTENT.md) § O158-w

### 1. Дубли TG push (один заказ, 3 сообщения)

**Симптом:** Freelance.ru `/task/view/2245` · Match 82% · текст слегка разный между push.

**Корень:** `match_push_log` dedup только `(user_id, lead_id)`. При смене snippet → новый `content_hash` → **новая строка `leads`** (тот же URL) → новый push. См. `push_match_for_lead` · `pg_storage.record_listing`.

**Fix (минимум):**
- Перед send: dedup по `(user_id, source, external_id)` **или** нормализованный `url` (без query).
- Опц.: `match_push_log` колонка `order_url` + unique `(user_id, order_url_hash)`.
- Verify Neon: `SELECT id, external_id, url, content_hash FROM leads WHERE url LIKE '%2245%'`.

**Файлы:** `src/match_push.py` · `sql/` migration если нужна · `tests/test_match_push.py`

### 2. Пустая шкала на /lenta/ (подпись «N%» есть)

**Симптом:** регресс O147 — owner verify § O147-w п.2.

**Корень:** `syncMatchFill` сбрасывает `width:0` inline, ждёт IO/rAF; на collapsed карточках полоска не доезжает.

**Fix:**
- После `insertAdjacentHTML` / `observeLeadCards` — `syncMatchFill` для **всех** карточек в viewport сразу (не только IO).
- Или: не ставить inline `width:0` если `--match-value` уже задан; опираться на CSS `.rl-feed-list .rl-lead-card .rl-match__fill { width: var(--match-value) }`.
- Smoke: Premium logged-in · `/lenta/` · полоска = подписи N%.

**Файлы:** `wordpress/.../assets/js/rawlead-feed.js` · bump theme · deploy WP

### 3. Deep link `/lenta/?lead={id}` — нет совместимости

**Корень:** `focusLeadCard` → `GET /rawlead/v1/leads/{id}` → API `GET /v1/leads/{id}` — **`keyword_match` не считается** (нет user tags). WP callback **не** пробрасывает Bearer (`rawlead-api.php` ~851).

**Fix:**
- API: в `get_lead` при Bearer — `_load_user_tags` + `keyword_match` в `_row_to_item`; или новый `GET /v1/me/leads/{lead_id}`.
- WP: `rawlead_api_get(..., $request)` для `/leads/{id}` с user headers.
- JS: `leadDetailApiUrl` — auth endpoint если logged in.

**Файлы:** `src/api_server.py` · `wordpress/.../inc/rawlead-api.php` · `rawlead-feed.js` · pytest API

### DoD

- [x] pytest match push dedup + lead detail km **7/7**
- [x] theme deploy · `deploy-o158-vps.py` **2026-06-08**
- [x] owner smoke ⏸ — `/lenta/` полоски · TG «Лента»

---

## § O155-EXTERNAL-PULSE — Healthchecks.io dead man's switch

**Owner принял:** внешний ping после ok-cycle · **дополнение** к O91 watchdog (не замена).

### Задача

После **успешного** site-cycle (`run_cycle` завершился, `radar_profile=site`) — fire-and-forget GET:

```text
GET $HEALTHCHECKS_SITE_URL   # https://hc-ping.com/<uuid> или /success
```

| Правило | Значение |
|---------|----------|
| Env | `HEALTHCHECKS_SITE_URL` — пусто = **no-op** |
| Когда ping | конец `run_cycle` после `record_cycle_summary` · **не** на паузе |
| Fail | silent · не ломать цикл |
| Grace на HC | owner ставит **15 min** в UI Healthchecks |

Success ping: **любая** web-биржа из `PUBLIC_FEED_SOURCES` без `fetch_error` **или** живой `tg_main` (пульс ≤5 мин). Fail ping (опц. `HEALTHCHECKS_SITE_FAIL_URL`): **все** опрошенные web упали **и** TG-монитор мёртв. **Не** «только FL/Kwork» — см. § **O141-EXCHANGE-PARITY**.

### Watchdog timer (deploy checklist)

В `deploy-o155-o156-vps.py` или `DEPLOY_VPS.md`: проверка

```bash
systemctl is-enabled rawlead-ingest-watchdog.timer
```

### Файлы

`src/main.py` · `src/healthchecks.py` (новый, ~30 строк) · `.env.example` · `docs/ops/DEPLOY_VPS.md`

**DoD:**

- [x] ping · pytest **5/5** · deploy ✅ · HC URL в VPS `.env`

---

## § O156-YOUDO-HUMAN — один residential, меньше банов (**P0 owner**)

**Owner:** residential уже есть · второй не потяну · «надо больше человечности» · так быть не должно.

### Корень (Lead triage)

| Проблема | Где |
|----------|-----|
| Листинг — **browser**, detail — **`exchange_get` httpx** | `youdo_parser.fetch_project_page_html` → 403 → ban **всех** слотов за 2 удара |
| `fetch_listing_html_browser_slots` — **перебор всех** слотов за один цикл | 3× cold browser за минуту = antibot |
| `_fetch_youdo_ephemeral` — **новый** Chromium каждый раз, без cookies | холодная сессия |
| Jitter 200–800 ms | слишком быстро для YouDo |

Trace O152: чередование `html http=403 ban=3600` + редкий `browser_goto http=200` — browser **может**, httpx **убивает** pool.

### A. Browser-only для YouDo (default ON при `EXCHANGE_LISTING_BROWSER=1`)

`YOUDO_BROWSER_ONLY=1` (default **1** если listing browser enabled):

- **Не** вызывать `exchange_get` для youdo listing **и** detail
- Detail через Playwright (reuse § B session или тот же persistent context)

### B. Warm human path (Playwright)

В `_fetch_youdo_*` (или `fetch_youdo_listing_human`):

```text
1. pick_browser_user_agent (не только _DEFAULT_UA)
2. viewport 1366×768 · locale ru-RU · timezone Europe/Moscow
3. goto https://youdo.com/ · wait 2–5s random
4. опц. page.mouse.wheel(0, 400) · wait 1–2s
5. goto listing URL · wait selector a[data-id]
6. jitter YOUDO_JITTER_MS (default 2000–8000) перед стартом
```

**Persistent profile** per proxy slot (`youdo_{host:port}`) — default **`YOUDO_EPHEMERAL=0`**. Ephemeral только если env=1 (legacy node-proxy).

### C. Один слот за цикл — не жечь pool

`YOUDO_ONE_SLOT_PER_CYCLE=1` (default **1**):

- Listing: только **active** slot из `exchange_primary_proxy_url("youdo")`
- **Не** loop all slots в `fetch_listing_html_browser_slots` для youdo
- Fail → cooldown (§ D), **не** cascade на slot 2/3 в том же цикле

### D. Cooldown после antibot

После `YoudoListingError` / antibot HTML / browser fail:

- SQLite settings `youdo_cooldown_until` = now + **`YOUDO_COOLDOWN_MIN`** (default **30**)
- `fetch_listing_projects`: if cooldown active → skip с log `youdo:skip cooldown N min`
- `/ops/` what_happened: «cooldown до HH:MM»

### E. Мягче баны для youdo

Env per-source override (или hardcode youdo):

- `YOUDO_HTTP_STRIKES=4` (default 4 vs global 2) — httpx если где-то останется
- **Не** ban slot на browser antibot HTML — только cooldown + invalidate profile

### F. Trace

`exchange:trace stage=warm_home` · `stage=listing` · `stage=detail` · `cooldown_skip`

### Файлы (O156)

`exchange_browser_fetch.py` · `youdo_parser.py` · `exchange_proxy.py` · `tests/test_youdo_human.py` · `scripts/deploy-o155-o156-vps.py`

**DoD O156 (A–F):**

- [x] pytest **6/6** · deploy ✅

**→ O157 ниже**

---

## § O157-YOUDO-TRAFFIC — экономия residential (**P0 owner 2026-06-08**)

**Owner:** ~**1 GB / 2 дня** · human (O156) **да**, но **трафик режем** · второй прокси нет.

### Корень

| Прожор | Где |
|--------|-----|
| Detail browser **на каждый** новый lead | `ingest_with_l1` ~491 → `_resolve_ingest_body` **без** порога 300 (legacy ~983 — есть) |
| Листинг **каждый** secondary-цикл | `SECONDARY_FETCH_EVERY_N_CYCLES=1` |
| warm_home + listing | 2 navigation |
| JS/CSS не в abort | только image/font/media |

### A. Detail только если snippet короткий

`YOUDO_DETAIL_MIN_CHARS=300` — **site path** в `_resolve_ingest_body`:

```python
if source == "youdo" and len(base) >= min_chars:
    return base, None
```

Опц. `YOUDO_DETAIL_FETCH=0` — never detail.

### B. Реже листинг YouDo

`YOUDO_FETCH_EVERY_N_CYCLES=4` — счётчик SQLite `youdo_fetch_cycle_n` · skip log `youdo:skip fetch_every_n`.

До deploy owner: `SECONDARY_FETCH_EVERY_N_CYCLES=4` в `.env` (грубо, все secondary).

### C. Warm home реже

`YOUDO_WARM_TTL_MIN=45` — skip `warm_home` если тот же profile < N min назад · trace `warm_home_skip`.

### D. Lean abort (youdo only)

Block: `stylesheet`, `xhr`, `fetch`, `websocket`, analytics CDN · allow `document` (+ min `script` если нужен SSR).

### E. Trace / ops

Опц. `bytes_est` в trace · target **< ~200 MB/нед** YouDo (owner eyeball residential stats).

### Файлы

`lead_pipeline.py` · `exchange_browser_fetch.py` · `youdo_parser.py` · `main.py` · `tests/test_youdo_traffic.py`

**DoD:**

- [x] pytest **7/7** (`test_youdo_traffic.py`) · deploy ✅
- [ ] owner: residential traffic ↓ · `/ops/` **Сбросить баны** YouDo (0/3 alive post-deploy)

---

## § O153-CARD-CHIPS — +n только collapsed (**hot, owner 2026-06-08**)

**Симптом:** раскрытая карточка показывает **+2** вместо всех навыков.

**Корень (Lead verify):** O149 убрал flip · `syncCardChips` мёртв:

```javascript
// сломано — face--front больше нет
card.querySelector(".rl-feed-card__face--front > .rl-chips")
```

`expandCard` вызывает `syncCardChips(..., true)` → **no-op** · остаётся `renderTagChips(item, 2)`.

**Стало:**

```javascript
var chips = card.querySelector(".rl-chips");
chips.innerHTML = renderTagChips(item, expanded ? null : 2);
```

| Состояние | Теги |
|-----------|------|
| collapsed | max **2** + `+n` |
| expanded | **все** · без `+n` |

Проверить **cabinet** (`rawlead-cabinet.js`) — тот же паттерн если есть.

**Файлы:** `rawlead-feed.js` · опц. `rawlead-cabinet.js` · **1.18.48**

**DoD:**

- [x] expand → все chips видны
- [x] collapse → снова 2 + `+n`
- [x] deploy theme

---

## § O154-GRID-NEIGHBOR — сосед не дёргается при collapse (**hot, owner 2026-06-08**)

**Симптом:** закрываешь раскрытую карточку → **соседняя** в сетке 2× **растягивается** и визуально «закрывается» тоже.

**Корень (Lead verify, повтор O52e):** в `rawlead.css` ~2892–2899 снова живут правила:

```css
.rl-feed-list:has(.rl-lead-card.is-expanded) { align-items: start; }
.rl-feed-list:has(.rl-lead-card.is-expanded) .rl-lead-card:not(.is-expanded) {
  height: auto;
  align-self: start;
}
```

Пока **есть** expanded — сосед `height: auto`. При collapse `:has` пропадает → соседи снова `height: 100%` + grid `stretch` → **скачок высоты** + `margin-top: auto` на chips выглядит как раскрытие/закрытие.

**Acceptance (U2, portfolio-w2):** expand/collapse **только** на кликнутой карточке · сосед **не меняет** высоту/контент.

| # | Fix |
|---|-----|
| g1 | **Удалить** `.rl-feed-list:has(.rl-lead-card.is-expanded)` и дочерние rules на **соседей** |
| g2 | `.rl-feed-list .rl-lead-card` → **`height: auto`** (убрать `height: 100%` ~2916, ~2973) · `min-height: 300px` оставить |
| g3 | Grid: **`align-items: start`** вместо `stretch` (~2885) — строка не тянет соседа под expanded |
| g4 | Expand/collapse — только `.rl-lead-card.is-expanded` (body grid 0fr→1fr, title clip) |
| g5 | Smoke 2 col desktop: expand A → B **статичен** · collapse A → B **статичен** · `/lenta/` + `/cabinet/` |

**Ref:** archive § **O52e** · [`portfolio-w2-acceptance.md`](../../problems/2026-05-25-portfolio-w2-acceptance.md) U2.

**Файлы:** `rawlead.css` · **1.18.48** (вместе с O153)

**DoD:**

- [x] collapse expanded → сосед **без** анимации высоты
- [x] ряд collapsed-карточек — ровная сетка, без «дыр» от stretch
- [x] deploy theme

---

## § O152-EXCHANGE-TRACE — детальный лог бирж + TG

**Owner:** «нельзя уже» — на `/ops/` красное без понятной причины · нужен **trace каждого источника**.

### A. Structured trace (journal + файл)

На **каждый fetch-цикл** по источнику (`fl`, `kwork`, `youdo`, `tg`, …):

```text
exchange:trace source=youdo stage=browser_goto proxy=gate...:10002 ms=12400 http=403 ban=3600 err=antibot
```

| Поле | Зачем |
|------|--------|
| `source` | fl / youdo / tg |
| `stage` | proxy_pick · goto · html · parse · L1 |
| `proxy` | host:port (mask user) |
| `ms` | wall time |
| `http` / `err` | 403 / timeout / antibot |
| `parsed` / `fresh` / `new_ids` | итог цикла |

**Файл:** `data/exchange_trace.jsonl` — append, rotate 7d · **не** git.

### B. `/ops/` UI

На карточке биржи — **«Последний trace»** (5–10 строк из jsonl или health) · полный `last_error_short` без обрезки в tooltip.

**FL лампа:** если `last_ok_at` свежее `last_error_at` → **не** 🔴 (fix `status_level` / `build_ops_exchange_row`).

### C. TG

Строка на сообщение уже есть — добавить в `/ops/` tg-card: **last 3 pipeline lines** из journal/jsonl.

### D. Forbidden hosts

Добавить **`OPENROUTER_HTTP_PROXY`** в `_EXCHANGE_POOL_FORBIDDEN_ENV` — не спамить skip acc2 в логах бирж.

**Файлы:** `exchange_proxy.py` · `exchange_browser_fetch.py` · `exchange_health.py` · `radar_cycle_log.py` · `owner_admin.py` · parsers (fl/youdo/kwork)

**DoD:**

- [x] pytest exchange_health / trace (**12/12** local)
- [x] deploy VPS (`deploy-o152-exchange-trace-vps.py`) · jsonl пишется
- [ ] owner smoke `/ops/` — «Последний trace» · FL lamp после ok-fetch
- [ ] YouDo 403 → trace с proxy + ban (ждём цикл или «Сбросить баны»)

---

## § O151-OR-ACC2-UX ✅ (deploy 2026-06-08)

**DoD:** L2 `use_draft_proxy=bool(openrouter_proxy_urls())` · acc2 in `OPENROUTER_HTTP_PROXY` · hideFeedBanner · no «ИИ пишет…» · **1.18.47** · pytest **7/7**

**Owner smoke:** `/lenta/` Ctrl+F5 — нет пустой плашки · expand → отклик без hint

---

## § O150-DRAFT-UX-POLISH ✅ (deploy 2026-06-08)

**Owner smoke после O148/O149 deploy (theme 1.18.45):** один отклик «ИИ не успел» · skeleton вместо «Суть задания» · плашка не в стиле · шрифты прыгают.

| # | Симптом | Решение |
|---|---------|---------|
| 1 | «Сложный бриф…» поздно | **`DRAFT_BTN_SLOW_MS = 20000`** (было 40s) |
| 2 | При генерации — **серые skeleton**, пропала суть | **Не** затирать `.rl-feed-card__body-inner` · оставить `renderExpandedBody(item)` · pending = btn shimmer + опц. «ИИ пишет отклик…» **внизу**, без `showDraftBodySkeleton` |
| 3 | Плашка «ИИ не успел — повторите» — не наш дизайн | `.rl-feed-banner` neo-brutalist: `border 2px #0a0a0a` · `box-shadow 4px 4px 0` · фон `#f5f5f0` · **«Повторить»** = `.rl-btn.rl-btn--ghost` |
| 4 | Шрифты **прыгают** при загрузке | `preload` Manrope (+ Unbounded если hero) woff2 в `functions.php` · `font-display: swap` |
| 5 | «ИИ не успел» слишком часто | poll `data.status === "failed"` → сразу banner · timeout → «Сложный бриф…» + retry · **1 auto-retry** если последний GET `pending` · опц. `DRAFT_POLL_MAX_MS = 180000` · BE: `use_draft_proxy=False` default direct |

### A. Pending body (главный UX)

**Удалить вызовы** `showDraftBodySkeleton` на inflight (`runDraftFetchForCard`, `syncDraftGeneratingUi`).

```text
Клик «Написать отклик» → expand
  · body: task_summary / meta как до клика
  · кнопка: «Генерируем…» → через 20s «Сложный бриф, ИИ полирует отклик...»
  · ready: inject reply в renderExpandedBody
```

### B. Banner `#rl-feed-error`

Единый стиль feed + cabinet · `role="alert"` · retry читаем на mobile.

### C. Fonts FOUT

`wp_head`: preload Manrope w400 woff2 crossorigin · проверить Kadence не подменяет `--font-main`.

### D. Меньше ложных fail

`pollDraftStatus`: if `failed` → throw с `data.error` · не крутить poll до 150s молча.

**Файлы:** `rawlead-feed.js` · `rawlead.css` · `functions.php` · опц. `ai_analyze.py` · **1.18.46**

**DoD:**

- [ ] expand + pending → **видна «Суть задания»**, нет серых полос
- [ ] 20s → «Сложный бриф…» на кнопке
- [ ] banner neo-brutalist · retry кликабелен
- [ ] fonts: нет заметного FOUT `/lenta/` (Ctrl+F5 ×2)
- [ ] deploy theme + API if BE touched

---

## § O148-DRAFT-OR — Pre-warm · UX · таймауты

**Owner (финал):** L2 на всю ленту ❌ · flash-base ❌ · **pre-warm premium expand ✅** · btn **>40s** → «**Сложный бриф, ИИ полирует отклик...**» · OR proxy unset.

```text
Ingest: L1 only
Expand (premium): POST …/draft/warm → 1× pro → leads.reply_draft (cap DRAFT_WARM_HOURLY_CAP=30)
Клик: warm ready → L3 · иначе cold L2 pro
```

### A. Pre-warm — **1× L2 на lead, не на юзера**

`POST /v1/me/leads/{id}/draft/warm` · premium only · **не** пишет `user_lead_replies`.

| Состояние `leads.reply_draft` / job | Ответ | LLM |
|-------------------------------------|-------|-----|
| **Уже есть** текст | **204** | **0** |
| Job **pending** (`lead_draft_jobs` / warm future) | **202** | **0** (ждёт тот же job) |
| Пусто, job не идёт | старт **одного** warm | **1× pro** |
| Cap `DRAFT_WARM_HOURLY_CAP=30` исчерпан | **429** | **0** · FE silent |

**10 premium смотрят одну карточку:** L2 **один раз** на `lead_id` · остальные expand → 204/202 без токенов.

**Reuse:** тот же dedupe что draft click — `lead_draft_jobs` ON CONFLICT lead_id · `_lead_worker_running(lead_id)`.

**После warm:** любой premium клик → **L3 flash only** (не L2), пока не fail warm.

FE: `state.warmRequested[id]` once/session · **бек — источник истины**.

### B. Кнопка

0–40s «Генерируем…» · >40s «Сложный бриф, ИИ полирует отклик...» · poll 150s.

### C. tools — **убрать лишний LLM** (owner 2026-06-08)

**Факт:** L1 (`AiLiteAnalysis`) **не** пишет `tools_required` — только `lead_tags` (чипы навыков).  
**UI «Инструменты»** в expand — **только после** `reply_draft` (`rawlead-feed.js` ~1005). До клика tools в карточке **не видны**.

**`analyze_lead_tools`** — отдельный **pro**-вызов «верни tools JSON» перед L2. L2 уже получает **title + task_summary + description** — стек может взять из текста (промпт: «§1 стек из текста выше»).

**Стало (warm + cold click):**

| Было | Стало |
|------|--------|
| `analyze_lead_tools` (pro) если tools пуст | **`tools_from_tz_text(title, body, task_summary)`** — regex, **0 LLM** |
| tools в промпт L2 | optional hint · пусто OK |
| после L2 ready | persist `tools_required` из tz heuristic для UI блока |

**Не вызывать** `analyze_lead_tools` на hot path draft/warm. Backlog `fetch_leads_missing_tools` — опц. оставить offline.

### D. cold · infra

**DoD:** warm on premium expand · post-warm click <20s · btn copy · anon no warm.

**Файлы:** `api_server.py` · `draft_async.py` · `match_push.py` · `rawlead-feed.js`

---

## § O149-NO-FLIP — убрать 3D flip · inline expand

**Owner:** flip **выкинуть**, UX **с нуля** — без `rotateY`, без front/back.

### Новый UX

1. Collapsed — как сейчас
2. «Написать отклик» → **expand in-place** · btn shimmer · body skeleton
3. Ready → `renderExpandedBody` в `.rl-feed-card__body-inner` · btn «Отклик ✓»
4. Collapse OK — draft в state, re-expand показывает текст

**Удалить:** `showDraftFlip`, `lockDraftFlip`, `syncFlipHeight`, flip DOM/CSS.

**Оставить:** `draftInflight`, poll не отменять, btn shimmer O146, O147 match bar + trial hide.

**Файлы:** `rawlead-feed.js` · `rawlead.css` · `style.css` **1.18.45+** · deploy VPS.

**DoD:** нет flip в DOM · draft = полный expand · deploy · owner smoke 1×.

**O147 § flip — superseded by O149** (match bar + trial — keep).

---

## § O147-FEED-FLIP-MATCH — flip full card · match bar · trial CTA (архив)

**Owner verify 2026-06-08 (скрины):** O146 частично — три регресса.

### A. Flip — карточка «урезаная», не как обычный expand

**Симптом:** после flip черновик в узком скролл-боксе (~половина карточки), не как полный expand.

**Корень (Lead read-only):**

| | |
|--|--|
| CSS | `.rl-feed-card__face--back { max-height: min(70vh, 520px); overflow-y: auto; position: absolute }` — обрезает оборот |
| O146 | удалён `syncFlipHeight()` — flip-inner не тянется по высоте front |
| Разметка | back обёрнут в `.rl-feed-card__body--draft-back` с grid 0fr/1fr — другой layout чем front expand |

**Стало:**

1. После `rl-lead-card--draft-done` + `is-expanded` — **тот же visual**, что expand до flip: полная высота контента, без `max-height` ловушки на back.
2. Вернуть **sync высоты** flip-inner от front (или убрать absolute back → back = тот же `.rl-feed-card__body` expand path).
3. **Не** менять one-way flip lock и inflight poll из O146.

### B. Шкала совместимости пустая на карточках ленты

**Симптом:** подпись «50% / 80% / 100% Совместимость» есть, **полоска серая** (fill = 0).

**Корень:**

| | |
|--|--|
| CSS | fill width завязан на `.is-visible` (стр. ~3039) + base `width:0` · race с IO |
| JS | `observeLeadCards` только добавляет `is-visible`, **не** триггерит fill |

**Стало:**

1. В `observeLeadCards` / IO callback: после `is-visible` — `syncMatchFill(card)` (width из `--match-value` / `keyword_match`).
2. CSS: один канон для feed/cabinet — `width: var(--match-value, 0%)` **без** зависимости только от `.is-visible`; анимация через rAF 0→target.
3. `renderCompatMatchBar`: inline `--match-value` + `data-match-pct` (cabinet parity с feed).
4. Regression: collapsed card на `/lenta/` premium — bar заполнен до клика.

### C. Убрать «Попробовать 3 дня» для Premium / Trial

**Симптом:** в `/cabinet/` при **Premium beta** (и trial) видны обе кнопки: trial + «Продлить».

**Стало (`rawlead-cabinet.js` + при необходимости CSS):**

```text
showTrialCta = status === "free" && !trial_used && !effective_access && !is_trial
```

Дополнительно **жёстко скрыть** trial если `status ∈ {active, beta, trial}` **или** `effective_access`.

| Статус | Trial CTA | Pay CTA |
|--------|-----------|---------|
| free (no trial) | ✅ | Подключить |
| trial | ❌ | Оплатить 790 ₽ |
| active / beta | ❌ | Продлить |

Feed `cardUpsellHtml` — уже `""` при `hasPaidAccess()`; проверить нет других «3 дня» на ленте.

### Файлы

| | |
|--|--|
| `wordpress/.../assets/js/rawlead-feed.js` | syncMatchFill · observeLeadCards · flip height |
| `wordpress/.../assets/css/rawlead.css` | back face height · match fill rules |
| `wordpress/.../assets/js/rawlead-cabinet.js` | trial CTA guard |
| `style.css` | bump **1.18.40** |
| deploy theme VPS | |

**Не трогать:** draft API · L2 · match_push SQL.

### DoD

- [x] syncMatchFill · syncFlipHeight · trial hide · theme **1.18.44** deploy VPS
- [ ] owner smoke: flip full · match bar · cabinet trial (Ctrl+F5)

---

## § O146-DRAFT-CARD-UX — flip · pending · кнопка

**Решение owner (2026-06-08):**

1. **Flip один раз** — после готовности черновика карточка **остаётся на обороте** (черновик), **не** переворачивается обратно.
2. **Pending не прерывается** — клик по карточке / expand / collapse **не останавливает** poll `fetchDraft` / `pollDraftStatus`.
3. **Кнопка «Написать отклик»** пока ИИ пишет — **пульс + золотое свечение** (бегущий блик по кнопке), не только рамка карточки.

**Корень (Lead read-only):** `finishDraftFlip()` **снимает** `rl-lead-card--draft-flip` → CSS возвращает `rotateY(0)` · yo-yo. `toggleCardExpand` / `runDraftFetchForCard` сбрасывают flip/pending при interact.

### A. Flip lock (`rawlead-feed.js` + `rawlead.css`)

| Было | Стало |
|------|--------|
| `finishDraftFlip` удаляет `--draft-flip` | После **одной** анимации → класс **`rl-lead-card--draft-on-back`** (transform 180deg **без** reverse) · `--draft-flip` только на время анимации |
| collapse карточки | снять `--draft-on-back` + `--draft-flip` · показать front (как сейчас collapse) |

**Reduced motion:** как сейчас — front hide / back static, без 3D.

### B. Inflight draft (`rawlead-feed.js`)

- `state.draftInflight[leadId] = { startedMs }` на POST → delete on ready/fail.
- **Не** отменять fetch при `toggleCardExpand`, document click outside, `syncFlipHeight`.
- `runDraftFetchForCard`: не сбрасывать другую карточку если у неё `draftInflight[id]`.
- По ready: `state.itemsById[id].reply_draft` → `updateCardDraft` **даже если collapsed** (DOM both faces); flip **один раз** если expanded.
- Кнопка: класс **`is-generating`** на `.rl-feed-card__reply-btn` на время inflight · текст «Генерируем…» · **disabled** только против double-click, не против collapse.

### C. Кнопка pending (`rawlead.css`)

На `.rl-feed-card__reply-btn.is-generating` (или `.rl-lead-card--draft-pending .rl-feed-card__reply-btn`):

- `animation`: лёгкий **pulse** scale 1 → 1.03
- **Золотой блик**: pseudo `::after` + `@keyframes rl-draft-btn-shimmer` (gradient `#facc15` / amber, `background-position` sweep)
- Карточный `rl-draft-glow` — ослабить или оставить тонкую рамку; **акцент на кнопке**

Токены: `--rl-accent` / `#facc15` · `prefers-reduced-motion: reduce` → только opacity pulse, без shimmer.

### D. Тесты / journey

| | |
|--|--|
| `tests/test_o146_draft_card.js` | опц. pure JS extract flip state machine — **или** только manual |
| Playwright | `ux_journey.py` J4: после fix — body-inner visible на design expand · J5/J6 не регресс |

### Файлы

| Только |
|--------|
| `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` |
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` |
| `wordpress/rawlead-kadence-child/style.css` — bump version |
| `scripts/deploy-wp-theme-vps.py` (или существующий theme deploy) |
| `docs/team/common/STATUS.md` → Сделано |

**Не трогать:** `api_server` draft API · L2 · `match_push`.

### Как проверить

1. Premium `/lenta/` → «Написать отклик» → карточка **flip один раз** → черновик на обороте **остаётся**
2. Во время «Генерируем…» — **свернуть/развернуть** карточку → через ~30s черновик **всё равно** появляется
3. Кнопка **пульсирует + золотой блик** пока pending
4. `preprod_playwright/ux_journey.py` → J4 + J5 pass

### DoD

- [ ] flip lock · inflight poll · button shimmer
- [ ] theme deploy VPS
- [ ] J4/J5 smoke owner или journey green

---

## Сводка

| § | Статус |
|---|--------|
| O144–O145 | deploy ✅ |
| Wave 2 | draft_burst ✅ · journey 9/10 |
| O146 | код ✅ · **accept ⏸** (3 регресса) |
| **O147** | **→ active** |

---

_Lead **2026-06-08** · owner card UX_
