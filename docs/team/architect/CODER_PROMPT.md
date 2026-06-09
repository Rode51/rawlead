# Coder — горячий контур (активное)

**→ Сейчас:** § **O166-HOME-MATCH-BAR** → § **O167-SORT-SOURCE** → § **O168-PRE-ADS-GATES** · O165 smoke = owner post

**Решение owner 2026-06-09:** **реклама рано** — сначала тесты + L2 + TG smoke + UI

**Архив:** [`CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md)

---

## § O165-TG-TEST-GROUP (**smoke**, P0)

**Статус:** join **3/3** · `chat_id=5177575757` · `tg:-1005177575757` в `PUBLIC_FEED_SOURCES` ✅

**Осталось:** owner пост [Тест Ботов](https://t.me/+Z7HcnIAdSw9kY2U6) (вакансия, не CV) → Lead verify Neon + `/lenta/?source=tg`

**Хвост coder (низкий):** CSV на VPS acc2/acc3 могли остаться `pending` при `join:ok` — синхрон `TG_JOIN_QUEUE_v2.csv` · не затирать secondary при rebuild feed (→ O169 guard)

---

## § O166-HOME-MATCH-BAR (**→ сейчас**, P1)

**Симптом:** главная «ПОСЛЕДНИЕ ЗАКАЗЫ» — % есть (50/100/80), **полоска пустая**.

**Корень:** `.rl-match__fill { width:0 }` раскрывается только при `.rl-match.is-visible`; на live-preview есть `rl-lead-card.is-visible`, **нет** на `.rl-match`.

**Фикс (минимум):** `rawlead.css` — `.rl-live-preview .rl-match__fill { width: var(--match-value); }` **или** `is-visible` на `.rl-match` в `live-preview.php` / `rawlead-scroll.js`

**DoD:** desktop + mobile скрин полоски 50/100/80%

---

## § O167-SORT-SOURCE (**→ после O166**, P1)

**Запрос owner:** фильтр **по биржам** в существующий dropdown «Сортировка» (ПК + mobile sheet), neo-brutalist стиль.

**Сейчас:** `feed-filter-bar.php` — `name=source` chips в `is-visually-hidden` (скрыты); sort только date/match.

**Фикс:** `buildSortOptionsHtml` + mobile sheet — секция «Источник»: Все · FL · Kwork · TG (+ опц. YouDo…) · `state.source` · persist prefs · API `source=` query если есть

**Design:** те же `rl-sort-option` / chip стиль что date/match

---

## § O168-PRE-ADS-GATES (**→ после UI+TG**, P0)

**Контекст:** stress **FAIL** 2026-06-08 — `tier_matrix` · p95 **2601ms** @50 · U10b draft 0/3

| # | Трек |
|---|------|
| g1 | **L2 quality** — forbidden words · tools min_2 · gate send ≥70% regen sample |
| g2 | **Perf** — pooler / feed p95 <2s @50 |
| g3 | **UX journey** 10/10 stable (J4 flake) |
| g4 | **Ingest 24h** — циклы без gap >15 min |

**Не трогать:** ads · portfolio

---

## Закрыто ✅ (2026-06-09)

O164 · O133-TZ · DROP-FH · O163 · O162 · O161 · O160

## Фон

stale-cookie password · O142 split · O144-O145 deploy ⏸
