# Lead Product — активный план

**Дата:** 2026-05-24 · с владельцем  
**Принято Lead Architect:** 2026-05-24 — `ROADMAP.md`, `LEAD_DESIGN_PROMPT.md`, ревизия `TASKS`/`STATUS`/`CODER_PROMPT`  
**→ Статус:** § **O221 r7+r8 ✅** (130 cards · deploy prod 2026-06-15) · § **O217** v1 **✅**

---

## § O221-QUIZ-COVERAGE — полное покрытие квиза (**→ now · owner 2026-06-14**)

**Суть запроса owner:** не «добавить JS в dev», а **нигде не было дыр** — квиз должен **измерять** то, что реально в ленте, по **всем 4 нишам**. v1 (56 карточек) = pilot, не coverage.

**Метод:** тот же класс research, что § SKILLS-TOOLS-RESEARCH (E2), но артефакт = **матрица покрытия + пак v2**, не каталог UI.

### Фаза 0 — факты (Lead verify Neon + repo · 2026-06-14)

| Ниша | Tier-A в каталоге | v1 quiz покрывает | Prod-теги ≥30 лидов **без** v1 `skills_on_like` |
|------|-------------------|-------------------|--------------------------------------------------|
| **dev** | 7 | **4/7** (нет js, llm, scraping) | html_css, server_administration, php, tilda_dev, mobile_dev, data_analysis… |
| **design** | 4 | 4/4 Tier-A, но **162** video_editing лидов · **109** illustration · **92** motion | illustration, motion_design, presentation_design, threed_modeling… |
| **marketing** | 6 | **5/6** (нет google_ads) | **146** content_marketing · **51** web_analytics · **33** chatbot_marketing · vk_ads… |
| **text** | 6 | **5/6** (нет translation) | **34** transcription · script_writing · product_description |

**Вывод:** дыры **системные** — 12 quiz-signals ≠ Tier-A ≠ top prod tags. Одного «расширить dev» недостаточно.

### Фаза 1 — Research agent (**@mechanic** · Gemini ~2M · read-only Neon)

**Промпт:** [`QUIZ_COVERAGE_RESEARCH_PROMPT.md`](QUIZ_COVERAGE_RESEARCH_PROMPT.md) *(новый — см. ниже)*

| # | Deliverable |
|---|-------------|
| r1 | **`data/quiz_coverage_matrix.csv`** — строка = canonical tag · cols: niche, tier, prod_lead_cnt, quiz_v1_cards, quiz_v1_skills, gap_class P0/P1/P2 |
| r2 | **`docs/team/product/QUIZ_COVERAGE_GAPS.md`** — human summary: top-10 дыр/нишу + примеры реальных лидов (id, title, tags) |
| r3 | **Signal map v2** — расширить § O217-w: не 3 signal/нишу, а **все Tier-A + top prod P0** (owner approve списка) |
| r4 | **Card budget** — мин. **3 anchor + 1 trap + 1 boundary** на каждый P0 signal · target **~150–200** cards |
| r5 | **Simulation spec** — 100 synthetic quiz paths → expected match vs random prod sample (acceptance для Coder) |

**Не делать в research:** писать JSON карточек (это PM r6) · менять rank.py · менять adaptive (Coder после r5).

### Фаза 2 — PM card pack (**@lead-product** + owner)

| # | Deliverable |
|---|-------------|
| r6 | Pilot **40** cards (10/niche) по matrix P0 — owner «нет WTF» |
| r7 | Full **`data/quiz_cards_v2.json`** + lint tag_id ∈ CANONICAL_TAGS | **✅ 2026-06-15** |
| r8 | Handoff → @lead-architect → Coder § **O221-QUIZ-ADAPTIVE** | ✅ deploy **2026-06-15** |

### Фаза 3 — Code (**@coder**, после r7)

Adaptive niche-deep · shuffle · dedup · CI **`tests/test_quiz_coverage.py`**: every Tier-A tag ∈ ≥2 cards · every P0 prod tag reachable via quiz path simulation.

### Критерий «нигде нет дыр» (owner gate)

1. **Tier-A:** каждый tag из `TIER_A_BY_NICHE` — ≥2 anchor-карточки в v2.  
2. **Prod P0:** каждый tag с ≥5% лидов ниши — signal или `skills_on_like` в квизе.  
3. **Simulation:** median match на 50 random niche-leads после типичного quiz ≥ **40%** (dev/design/marketing/text отдельно).  
4. **UX:** ≥12 unique card_ids на 20-card run · no 4× duplicate (dedup).

**Фаза 1 ✅ (2026-06-15):** [`QUIZ_COVERAGE_GAPS.md`](QUIZ_COVERAGE_GAPS.md) · [`data/quiz_coverage_matrix.csv`](../../../data/quiz_coverage_matrix.csv) · 14 «нулевой match» P0 tags · simulation spec в GAPS § Card budget.

**→ Фаза 2 r6 ✅ (owner 2026-06-15):** pilot **40** принят · **→ r7** full ~130 cards.

**→ r7 ✅ (Lead Product 2026-06-15):** `data/quiz_cards_v2.json` — **130 cards** (40 pilot→v2 + 90 new) · **45 signals** · lint 0 bad tags · dev:32 / design:32 / mkt:33 / text:33 · **→ r8** handoff @lead-architect.

### r8 — Handoff to @lead-architect (→ Coder § O221-QUIZ-ADAPTIVE)

**Файл:** `data/quiz_cards_v2.json` (130 cards, pack_version=v2)

**Что сделать @coder (§ O221-QUIZ-ADAPTIVE):**

| # | Task |
|---|------|
| 1 | Extend `QUIZ_SIGNALS` in `quiz_adaptive.py` — add 35 new signals from v2 (see list below) |
| 2 | Load v2 pack: `_load_json_cards("quiz_cards_v2.json")` — merge alongside v2-pilot (or replace) |
| 3 | `_pick_json_candidate`: pick by signal, shuffle candidates, skip shown_ids |
| 4 | CI: `tests/test_quiz_coverage.py` — every Tier-A tag ∈ ≥2 anchor cards · every P0 tag reachable |
| 5 | Deploy: `quiz_adaptive.py` + `quiz_cards_v2.json` → VPS `/opt/rawlead/` · restart `rawlead-api` |

**New signals to add to `QUIZ_SIGNALS` (v2 additions):**
```
dev: server_administration, javascript, web_scraping, tilda_dev,
     ecommerce_dev, data_analysis, llm_integration, html_css,
     telegram_bot_dev
design: presentation_design, threed_modeling, infographic_design,
        illustration, motion_design, web_design, figma
marketing: marketplace_promotion, chatbot_marketing, web_analytics,
           google_ads, email_marketing, content_marketing, seo,
           yandex_direct, technical_seo
text: translation, transcription, product_description, script_writing,
      seo_copywriting, technical_writing, editing_proofreading,
      article_writing, copywriting, sales_copywriting
```

**Acceptance (Coder):**
- [x] `pytest tests/test_quiz_coverage.py` — Tier-A ≥2 · P0 reachable (**64/64** suite)
- [x] `pytest tests/test_o197_quiz_adaptive.py` — dev 20-pick ≥12 unique
- [ ] VPS smoke: owner retake dev → JS/TG leads match **>0%**

### Owner gate — signals v2 (approve before Coder deploy)

Подтверди **да/нет** по строкам «must» из GAPS § Recommended signals v2 · pilot покрывает только **quiz=N + expand=N + P0**:

| niche | pilot signals (10 cards) | closes zero-match tags |
|-------|--------------------------|------------------------|
| dev | `server_administration`, `javascript`, `web_scraping`, `tilda_dev` | 7 из 7 critical |
| design | `presentation_design`, `threed_modeling`, `infographic_design`, `illustration` | 3 must + illustration P0 |
| marketing | `marketplace_promotion`, `target_ads`, `chatbot_marketing` | marketplace must + target frequency |
| text | `translation`, `transcription`, `product_description` | 3 must (Tier-A translation) |

**Expand-only (не в pilot, owner decide later):** dev `html_css`/`php` ← wordpress_dev · design `motion_design` ← banner_design · marketing `web_analytics` ← seo.

**Coder dependency (r8):** новые `signal` id → расширить `QUIZ_SIGNALS` в `quiz_adaptive.py` **до** lint pilot JSON · иначе `test_o217` падает.

### r6 — Pilot 40 cards · owner spot-check «нет WTF»

Формат = § O217 p3 · `pack_version: "v2-pilot"` · `skills_on_dislike: []` · trap `signal: null`.

| id | type | niche | signal | cx | title | skills_on_like |
|----|------|-------|--------|----|-------|----------------|
| qc2_dev_srv_01 | anchor | dev | server_administration | 2 | Настроить VPS под игровой сервер Rust: установка, автозапуск, бэкапы | server_administration |
| qc2_dev_srv_02 | anchor | dev | server_administration | 3 | Перенести WordPress на новый хостинг: DNS, SSL, миграция БД без даунтайма | server_administration, wordpress_dev |
| qc2_dev_srv_03 | trap | dev | — | 1 | Написать bash-скрипт парсинга цен конкурентов с маркетплейса | web_scraping, python |
| qc2_dev_js_01 | anchor | dev | javascript | 2 | Сендер формы на сайте: валидация, отправка в Telegram без перезагрузки | javascript, api_integration |
| qc2_dev_js_02 | anchor | dev | javascript | 3 | React-лендинг SaaS: адаптив, форма регистрации, интеграция с REST API | javascript, api_integration |
| qc2_dev_js_03 | boundary | dev↔design | javascript | 2 | Анимированный интерактивный прототип лендинга в Figma + экспорт в HTML/CSS | javascript, ui_ux, figma |
| qc2_dev_scrape_01 | anchor | dev | web_scraping | 2 | Спарсить каталог товаров конкурента (500 SKU) в CSV для анализа цен | web_scraping, python |
| qc2_dev_scrape_02 | anchor | dev | web_scraping | 3 | Telethon-бот: мониторинг TG-каналов конкурентов, дайджест новых постов | web_scraping, telegram_bot_dev |
| qc2_dev_tilda_01 | anchor | dev | tilda_dev | 1 | Собрать лендинг на Tilda по готовому макету: 7 блоков, формы, аналитика | tilda_dev |
| qc2_dev_tilda_02 | anchor | dev | tilda_dev | 2 | Интернет-магазин на Tilda: каталог 40 позиций, корзина, оплата ЮKassa | tilda_dev, ecommerce_dev |
| qc2_design_pres_01 | anchor | design | presentation_design | 2 | Pitch deck для инвесторов IT-стартапа: 15 слайдов, единый визуальный стиль | presentation_design |
| qc2_design_pres_02 | anchor | design | presentation_design | 1 | Оформить презентацию для вебинара (40 слайдов) по брендбуку заказчика | presentation_design, brand_identity |
| qc2_design_pres_03 | trap | design | — | 1 | Написать текст выступления спикера к готовым слайдам вебинара | script_writing, copywriting |
| qc2_design_3d_01 | anchor | design | threed_modeling | 2 | 3D-модель упаковки косметики для рендера на маркетплейс (Blender) | threed_modeling |
| qc2_design_3d_02 | anchor | design | threed_modeling | 3 | Low-poly 3D-сцена для мобильной игры: 5 объектов, UV, текстуры | threed_modeling |
| qc2_design_3d_03 | trap | design | — | 1 | Смонтировать 3D-обзор продукта из готовых рендеров в 60-сек видео | video_editing, motion_design |
| qc2_design_info_01 | anchor | design | infographic_design | 2 | Инфографика для карточки товара на WB: преимущества, размерная сетка | infographic_design |
| qc2_design_info_02 | anchor | design | infographic_design | 2 | Серия из 5 инфографик для Ozon: сравнение с конкурентами, USP | infographic_design, banner_design |
| qc2_design_ill_01 | anchor | design | illustration | 2 | Иллюстрации для детской книги: 8 разворотов, единый стиль персонажей | illustration |
| qc2_design_ill_02 | anchor | design | illustration | 1 | Апскейл и ретушь фотографий товаров для каталога (batch 50 шт.) | illustration |
| qc2_mkt_mp_01 | anchor | marketing | marketplace_promotion | 2 | Вывести 20 SKU на Ozon: карточки, SEO-поля, ставки, аналитика продаж | marketplace_promotion |
| qc2_mkt_mp_02 | anchor | marketing | marketplace_promotion | 3 | Стратегия продвижения на Wildberries: внутренняя реклама + акции + A/B фото | marketplace_promotion |
| qc2_mkt_mp_03 | trap | marketing | — | 1 | Сверстать HTML-шаблон email-рассылки для базы подписчиков | email_marketing |
| qc2_mkt_tads_01 | anchor | marketing | target_ads | 2 | Таргет VK Ads для онлайн-школы: 3 креатива, lookalike, пиксель | target_ads |
| qc2_mkt_tads_02 | anchor | marketing | target_ads | 2 | Meta Ads (Instagram/Facebook) для e-commerce: ROAS-оптимизация, 5 ad set | target_ads, smm |
| qc2_mkt_tads_03 | boundary | marketing↔design | target_ads | 1 | Подготовить 10 креативов для таргета: баннеры + тексты по ТЗ маркетолога | target_ads, banner_design |
| qc2_mkt_bot_01 | anchor | marketing | chatbot_marketing | 2 | Воронка Salebot: квиз → сегментация → рассылка оффера в Telegram | chatbot_marketing, email_marketing |
| qc2_mkt_bot_02 | anchor | marketing | chatbot_marketing | 2 | Senler-бот для VK-сообщества: автоответы, сбор заявок, интеграция с CRM | chatbot_marketing |
| qc2_mkt_bot_03 | anchor | marketing | chatbot_marketing | 3 | Чат-бот поддержки на сайте: FAQ, передача оператору, сбор NPS | chatbot_marketing, api_integration |
| qc2_mkt_bot_04 | trap | marketing | — | 1 | Написать 10 SEO-статей для блога интернет-магазина | seo_copywriting, article_writing |
| qc2_text_tr_01 | anchor | text | translation | 2 | Редакционный перевод EN→RU IT-документации (API guide, 40 стр.) | translation, technical_writing |
| qc2_text_tr_02 | anchor | text | translation | 2 | Перевод маркетинговых материалов RU→EN: лендинг + 5 email-писем | translation, copywriting |
| qc2_text_tr_03 | boundary | text↔marketing | translation | 2 | Локализация рекламных креативов для выхода на рынок Казахстана | translation, target_ads |
| qc2_text_tr_04 | trap | text | — | 1 | Вычитать русский текст лендинга без перевода с другого языка | editing_proofreading |
| qc2_text_transcr_01 | anchor | text | transcription | 1 | Транскрибация 90-мин вебинара: таймкоды, спикеры, выделение action items | transcription |
| qc2_text_transcr_02 | anchor | text | transcription | 2 | Расшифровка 20 подкаст-эпизодов + саммари ключевых тезисов для блога | transcription, article_writing |
| qc2_text_transcr_03 | trap | text | — | 1 | Написать сценарий подкаста на основе расшифровки интервью | script_writing |
| qc2_text_pd_01 | anchor | text | product_description | 2 | Описания 100 товаров для Ozon/WB: SEO-ключи, УТП, без воды | product_description, seo_copywriting |
| qc2_text_pd_02 | anchor | text | product_description | 1 | Карточки товаров для интернет-магазина мебели: характеристики + продающий текст | product_description |
| qc2_text_pd_03 | boundary | text↔design | product_description | 2 | Тексты для карточек маркетплейса + ТЗ дизайнеру на инфографику блоков | product_description, infographic_design |

**Acceptance r6:**
- [x] Owner: signals v2 gate **approve** (owner **2026-06-15**)
- [x] Owner: pilot 40 spot-check **«принимаю pilot»** (owner **2026-06-15**)
- [x] PM: все tags ∈ `CANONICAL_TAGS` (Lead verify **2026-06-15** — 33 tags, 0 bad)
- [x] Lead: **40** cards · **10/ниша** · design/marketing/text P0 critical ✅ · dev **5/7** critical signals (→ r7: `data_analysis`, `llm_integration`)

**После r6:** **→ r7** ~130 cards (@lead-product) · **→ r8** `@coder` § **O221-QUIZ-ADAPTIVE** (pilot JSON + `QUIZ_SIGNALS` — **unblocked**).

---

## § O221-QUIZ-POOL-V2 — (merged → § O221-QUIZ-COVERAGE выше)

*Legacy name · см. § O221-QUIZ-COVERAGE.*

**Owner pain:** «шёл в разработку» → лид «JS + TG-бот» **0%** · в квизе **одно и то же** · профиль не покрывает реальные заказы.

**Root (Lead verify):**

| # | Факт |
|---|------|
| 1 | Пак **v1 = 56** карточек (14/ниша) — MVP pilot, не полный охват каталога |
| 2 | Dev signals **только 3:** python · wordpress_dev · api_integration — **`javascript` нет в квизе** |
| 3 | `telegram_bot_dev` — **1** boundary-карточка; типичный dev-профиль после квиза = python/wp/api |
| 4 | Match `lead_coverage_match`: лид с `javascript` + `telegram_bot_dev` vs профиль без них → **0%** (ожидаемо при текущем паке) |
| 5 | Повторы: dedup-баг O220-QUIZ-DEDUP + `_query_card_json` берёт `candidates[0]` — мало вариантов на signal |

**PM deliverables (v2):**

| # | Артефакт |
|---|----------|
| p0 | **Gap audit:** top-20 dev lead_tags на prod (YouDo/FL) vs `skills_on_like` v1 → список **missing signals** |
| p1 | **Расширить signals dev** (owner+PM): минимум **`javascript`**, **`telegram_bot_dev`** (+ php/html_css по audit) — правка § O217-w таблицы |
| p2 | **Матрица v2:** **≥8–12 anchor/signal** · **≥6 trap+boundary/niche** · target **~120–160** cards · `pack_version: "v2"` |
| p3 | **Карточки под реальные паттерны:** TG-бот · парсер · GAS · React-лендинг · CRM-интеграция · не только python/wp |
| p4 | Pilot **30** owner spot-check → Coder lint + deploy |

**Coder (после PM pilot):** `CODER_PROMPT` § **O221-QUIZ-ADAPTIVE** — niche-deep pick · shuffle candidates · dedup strings.

**→ @lead-architect:** после p0 audit — очередь Coder.

---

## § O220-MATCH-PM — низкий % совместимости после квиза (**✅ решение owner 2026-06-14**)

**Канон:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O220-w п.1** · `CODER_PROMPT` § O220-MATCH-PM  
**Параллельно:** Coder § O220-FEED-DRAFT-UX (r0 замок до квиза — **PM не блокирует**)

---

### Диагноз (из Neon + rank.py · 2026-06-14)

**Neon prod: 2264 видимых лида**

| Метрика | Факт |
|---------|------|
| Лидов с тегами | **90%** (10% без тегов → B) |
| Среднее тегов на лид | **1.8** ← корень проблемы |
| 1–2 тега на лид | **78% всех лидов** |
| Топ-тег (api_integration) | только **8.8%** ленты — лента очень разнородная |

**Почему 8% после квиза:**

| # | Причина |
|---|---------|
| P1 | **Формула user-side precision** — `Σ(weight×match)/Σ(weight)` = «сколько ВСЕХ моих навыков есть в лиде»; при 4 тегах у пользователя и 1 теге у лида (даже совпавшем) → **25%** максимум |
| P2 | **Мало тегов у лидов** — 1.8 avg; лид с 1 тегом физически не может дать >33–50% |
| P3 | **Лиды без тегов** — 10% (217 шт) → `rank.py:112` возвращает 0 немедленно |
| P4 | **Узкий профиль** — 10 карточек квиза дают 2–3 тега, знаменатель мал |

**Потолок без изменений:** ≈ 40–50% даже на идеальных лидах при текущем 1.8 тегов/лид.  
**Цель:** 70–90% на релевантных лидах в топе ленты.

---

### ✅ Решение owner: A + B + C + D + E + F (все леверы)

#### A — Умные подписи вместо сырых цифр (JS/copy, rank.py не трогать)

| raw % | Сейчас | После |
|-------|--------|-------|
| lead без тегов | «0%» | нейтральная серая полоска, без числа |
| 1–24% | «8% совместимости» | «Не ваша ниша» (amber) |
| 25–59% | «40% совместимости» | «Частичное совпадение · 40%» |
| 60%+ | «73%» | «Хорошее совпадение · 73%» |

**Copy breakdown (при клике «?»):**  
> «% — сколько ваших навыков востребовано в этом заказе. Нет тегов или другая ниша — полоска без числа.»

**Файлы:** `rawlead-feed.js` · `rawlead-cabinet.js` · CSS

---

#### B — Лид без тегов → `None`, не 0% (одна строка rank.py)

`keyword_match()`: если `not lead_set` → вернуть `None` (не `0`).  
JS: `null` = серая полоска «–», не «0%».  
**Файлы:** `src/rank.py` · `tests/test_match_push.py` · JS

---

#### C — Квиз 13–15 карточек (шире профиль)

Было 10 → станет 13–15 карточек в первом квизе. Никакого «второго этапа» — просто первый квиз длиннее.  
Профиль: 3–5 тегов вместо 2–3.  
**Файлы:** `src/quiz_adaptive.py` (порог завершения) · `rawlead-quiz.js`

---

#### D — Формула Lead-Coverage Match (лид определяет знаменатель)

**Проблема текущей формулы:** знаменатель = сумма весов ВСЕГО профиля пользователя → лишние навыки штрафуют. Пользователь с `{python, fastapi, figma, copywriting}` на лид `[python, fastapi]` получает **60%** вместо **100%**.

**Правило (owner 2026-06-14):**
> «Если у пользователя есть все что нужно лиду — должно быть 100%, лишние навыки не должны влиять.»

**Новая формула:**
```
score = Σ(user_weight[tag] for tag in lead_tags if user_has(tag))
      / Σ(max(user_weight[tag], REF_W) for tag in lead_tags)
      × 100
```
- Знаменатель = только теги **лида** (не весь профиль)
- `REF_W` = reference weight (≈ 4.0) для тегов лида которых у пользователя нет совсем
- Лишние навыки пользователя → **не влияют**

**Примеры:**

| Профиль пользователя | Теги лида | Score |
|----------------------|-----------|-------|
| `{python:8, fastapi:4, figma:2, copywriting:2}` | `[python, fastapi]` | **100%** ✅ |
| `{python:8, django:4}` | `[python, fastapi]` | **67%** — нет fastapi |
| `{python:4}` | `[python, fastapi]` | **50%** — только половина |
| `{figma:6}` | `[python, fastapi]` | **0%** → «–» |

**Узкие навыки весят больше:** частично решается через квиз — частые свайпы fastapi-задач → вес fastapi растёт. Полная IDF-рарность — отдельная задача после запуска.

**Файлы:** `src/rank.py` (новая функция `lead_coverage_match`) · `tests/test_match_push.py`  
**Не ломает:** текущую `keyword_match` — добавляется рядом; `api_server.py` переключается на новую.

---

#### E — Больше тегов у лидов (fix промпта L1)

Сейчас L1 извлекает 1.8 тега в среднем. Нужно 3–4.  
**Правка:** в промпт L1 добавить полный список CANONICAL_TAGS (51 тег) + инструкцию «от 2 до 5 тегов, не меньше».  
**Эффект:** новые лиды сразу богаче; ретегирование 2264 существующих — опционально (отдельный скрипт).  
**Файлы:** `src/ai_enricher.py` или где L1-промпт · `tests/`

---

#### F — Карта синонимов (скрытые теги, без AI)

Статический словарь в `rank.py`: если у лида есть тег X → для расчёта матча добавить Y, Z (пользователь не видит, только match-алгоритм).

```
wordpress_dev  → [html_css, php]
python         → [api_integration]
smm            → [content_marketing]
ui_ux          → [figma, brand_identity]
video_editing  → [motion_design]
seo            → [content_marketing, article_writing]
copywriting    → [content_marketing, smm, sales_copywriting]
article_writing → [technical_writing, seo_copywriting, seo]
```

**Надёжнее AI:** не галлюцинирует, работает на всех текущих лидах сразу, без переинжестирования.  
**Файлы:** `src/rank.py` (`TAG_SYNONYMS` dict) · `tests/test_match_push.py`

---

### Покрытие по нишам (Neon prod · 2026-06-14 · 2255 visible leads)

| Ниша | Лидов с % | % ленты | Без «–» |
|------|-----------|---------|---------|
| **Design** | 734 | **33%** ✅ | норм |
| **Dev** | 562 | **25%** ✅ | норм |
| **Marketing** | 369 | **16%** ⚠️ | терпимо |
| **Text** | 132 | **6%** ❌ | мало |
| Без ниши вообще | 461 | 20% | «–» всем |

**⚠️ ops-note (не для пользователей):** текстовая ниша слабо представлена в ленте (FL/Kwork дают мало чистых copywriting/article_writing лидов). Копирайтеры после квиза увидят «–» на ~90% карточек. С синонимами F: +~150 лидов из marketing → итого ~280 (12%) — лучше, но всё равно мало. Владелец: наполнять text-нишу активно не планируем на старте — аудитория «против AI», в ленте её мало органически. Приоритет — dev + design + marketing.

---

### Ожидаемый результат после A–F

| Состояние | Топ-лид в ленте |
|-----------|----------------|
| Сейчас | 8% среднее · ≤40% на лучших |
| После A+B | те же % · UI стал понятным |
| После D+F | **70–90%** на релевантных лидах |
| После E | ещё +10–20% coverage за счёт богатых тегов у новых лидов |

---

### Приоритет и порядок

| Приоритет | Что | Эффект |
|-----------|-----|--------|
| **P0** | A + B | UX-чистота сразу |
| **P0** | D + F | 70–90% на топе ленты — **главное** |
| **P1** | E (промпт L1) | Богаче теги на новых лидах |
| **P2** | C (квиз 13–15) | Шире профиль, умеренный эффект |

---

### Handoff → @lead-architect

```
@lead-architect
PM § O220-MATCH-PM ✅ owner OK: все A–F · LEAD_PRODUCT_PROMPT.md § O220-MATCH-PM
Нужно: CODER_PROMPT § O220-MATCH-CODE
Приоритет: B+D+F = P0 · E = P1 · C = P2 · A-min (скрыть «0%» → «–») = P0
D = новая функция lead_coverage_match (знаменатель = теги лида, не весь профиль); api_server переключается на новую; текущую keyword_match не удалять
Text-ниша: low priority на старте (6% ленты); синонимы F покрывают через marketing
```

---

## § O217-QUIZ-SYNTHETIC-PACK — авторские карточки квиза (**→ now · owner 2026-06-14**)

**Канон:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O217-w** · файл (Coder): `data/quiz_cards_v1.json`

**p0 — Аудит каталога v0.5 vs 12 quiz-signals:** все 12 ∈ CANONICAL_TAGS · новых тегов не нужно · `pending_tags` не задействован.

| signal | tag | tier | | signal | tag | tier |
|--------|-----|------|-|--------|-----|------|
| python | `python` | A ✅ | | smm | `smm` | A ✅ |
| wordpress_dev | `wordpress_dev` | A ✅ | | yandex_direct | `yandex_direct` | A ✅ |
| api_integration | `api_integration` | A ✅ | | seo | `seo` | A ✅ |
| ui_ux | `ui_ux` | A ✅ | | copywriting | `copywriting` | A ✅ |
| video_editing | `video_editing` | B ✅ | | article_writing | `article_writing` | A ✅ |
| brand_identity | `brand_identity` | L3→logo_design ✅ | | editing_proofreading | `editing_proofreading` | A ✅ |

**p1 — Schema:** → `OWNER_INTENT.md` § O217-w · `pack_version: "v1"`

**p2 — Матрица пула v1 (~56 карточек):** 4 ниши × (8 anchor + 2 boundary + 4 trap) = 14/нише · Граничные пары: dev↔design · dev↔text · design↔marketing · marketing↔text

**p3 — Pilot 20 карточек · owner spot-check «нет WTF»**

| id | type | niche | signal | cx | title | skills_on_like |
|----|------|-------|--------|----|-------|----------------|
| qc_dev_python_01 | anchor | dev | python | 2 | FastAPI-сервис: вебхуки Stripe → запись в PostgreSQL | python, api_integration |
| qc_dev_wp_01 | anchor | dev | wordpress_dev | 1 | Правки WP-сайта: форма обратной связи + отправка на email | wordpress_dev |
| qc_dev_api_01 | anchor | dev | api_integration | 2 | amoCRM ↔ Google Sheets: двусторонняя авто-синхронизация сделок | api_integration, python |
| qc_dev_boundary_01 | boundary | dev↔design | python | 2 | TG-бот для записи клиентов — inline-кнопки строго по Figma-макету | telegram_bot_dev |
| qc_dev_trap_01 | trap | dev | — | 1 | Написать статью «FastAPI vs Flask»: сравнение с примерами кода | article_writing, technical_writing |
| qc_design_uiux_01 | anchor | design | ui_ux | 2 | Figma-прототип мобильного приложения доставки еды — 5 экранов | ui_ux, figma |
| qc_design_video_01 | anchor | design | video_editing | 2 | Смонтировать 10 Reels из raw-видео: субтитры + переходы в бренд-стиле | video_editing |
| qc_design_brand_01 | anchor | design | brand_identity | 2 | Логотип + фирмстиль (визитки, шаблон презентации) для IT-стартапа | logo_design, brand_identity |
| qc_design_boundary_01 | boundary | design↔marketing | ui_ux | 1 | Шаблоны Stories и постов Instagram в фирменном стиле компании | banner_design, ui_ux |
| qc_design_trap_01 | trap | design | — | 1 | Нарисовать схему архитектуры микросервисов для техдокументации | technical_writing |
| qc_mkt_smm_01 | anchor | marketing | smm | 2 | Вести SMM в ВК и TG: контент-план + 15 постов/месяц | smm, content_marketing |
| qc_mkt_direct_01 | anchor | marketing | yandex_direct | 2 | Яндекс Директ для интернет-магазина: ключи, группы, ставки, UTM | yandex_direct |
| qc_mkt_seo_01 | anchor | marketing | seo | 3 | SEO-аудит + семантическое ядро + рекомендации по структуре (50+ стр.) | seo, technical_seo |
| qc_mkt_boundary_01 | boundary | marketing↔text | seo | 2 | 5 SEO-статей для блога строительной компании — ключи и структура даны | seo_copywriting, article_writing |
| qc_mkt_trap_01 | trap | marketing | — | 1 | Нарисовать макет email-рассылки в Figma (HTML не нужен) | ui_ux, figma |
| qc_text_copy_01 | anchor | text | copywriting | 2 | Продающий лендинг для онлайн-курса: структура + полный текст | copywriting, sales_copywriting |
| qc_text_article_01 | anchor | text | article_writing | 1 | 5 экспертных статей для Хабра о Python-экосистеме, от 3000 слов | article_writing, technical_writing |
| qc_text_edit_01 | anchor | text | editing_proofreading | 2 | Редактура и корректура White Paper (30 стр.) по финтех-продукту | editing_proofreading |
| qc_text_boundary_01 | boundary | text↔dev | article_writing | 2 | Документация для REST API: OpenAPI-спека + руководство разработчика | technical_writing, article_writing |
| qc_text_trap_01 | trap | text | — | 1 | Собрать семантическое ядро в Key Collector — 200 ключей по нише | seo, technical_seo |

**p4 — Правила весов** (per TINDER-ONBOARD): «Взял бы» → `skills_on_like[]: weight += 2.0, interaction_count += 1` · «Не моё» → `weight -= 1.0` · `skills_on_dislike[] = []` для v1 · boundary начисляет обеим нишам, лента ранжирует сама.

**p5 — Adaptive O197 без изменений.** Меняется только источник: `Neon raw_leads → quiz_cards_v1.json` (статичный JSON, загружается при старте API).

**Acceptance:**
- [x] Owner spot-check pilot 20 → **«принимаю»** owner 2026-06-14
- [x] PM spec p0–p5 · pilot table 20 · matrix ~56 — **Lead verify 2026-06-14**
- [ ] `data/quiz_cards_v1.json` — Coder: 56 карточек, all tag_id ∈ CANONICAL_TAGS (CI lint)
- [ ] `POST /v1/quiz/next` source = JSON, not Neon · deprecate `quiz_pool_allowlist.json`

**Handoff → @lead-architect:**
```
@lead-architect
PM pilot ✅ (после owner spot-check): LEAD_PRODUCT_PROMPT.md § O217-QUIZ-SYNTHETIC-PACK
Нужно: CODER_PROMPT § O217-code (swap leads→quiz_cards_v1.json; CI lint tag_id∈CANONICAL_TAGS)
Deprecate: data/quiz_pool_allowlist.json (после deploy O217)
```

---

**Ставка:** **B — Открытая площадка + ИИ-агент по подписке** (согласовано в чате `@lead-product` 2026-05-24, замена ставки A)  
**Vision:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) **v0.12** (Premium 790 ₽ · O105 · O101)

---

## § O199-ONBOARD-COPY — Quiz-first (**⏸ merged → Design § O209-MATCH-EXPERIENCE**)

Copy на экранах — **не PM**, а **Lead Designer** в единой спеке O209. PM оставляет только product rules ниже.

---

## § O208-MONETIZATION — Лимиты · K · воронка auth (**✅ tier freeze · copy → O209**)

**Канон:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O208-B** · O101 · O107 · O116 · O174.

**Owner decisions (зафиксировано):**
- **5 откликов/час** — **все** планы (free, trial, premium). Заменить copy «10/час» в pricing/FAQ/how/home.
- **L3 judge pilot** → финальное **K** (8–12): после K генераций карточка **исчезает из ленты** для новых (inbox у кого уже есть черновик).
- **Не показывать на карточке:** просмотры · «осталось N откликов» — только в FAQ/pricing/429.

**PM workshop — воронка (**✅ freeze owner 2026-06-14**):**

| Tier | Delay | Drafts | Push | Match/rank | Quiz | Hourly | Notes |
|------|-------|--------|------|------------|------|--------|-------|
| **Anon** | **30 мин** | ❌ | ❌ | **flat** (хронол., без km) | promo CTA | — | supersede O11 15 мин |
| **Trial** (первый TG-login) | **instant** | ✅ | ✅ | **full personalized** | ✅ learns | **5/h** | auto 3d бесплатно |
| **Expired-trial / free** | **30 мин** | ❌ | ❌ | **flat** (как anon) | сохранён, не в rank | — | **баннер обязателен** |
| **Premium** | **instant** | ✅ | ✅ | **full personalized** | ✅ learns | **5/h** | 790₽/мес |

**✅ РЕШЕНО (owner 2026-06-14):**
- **Auto-trial** при **первом TG-login** → 3 дня бесплатно
- **Expired-trial = anon-plus-pain:** flat feed + **30 мин** (оба tier одинаково)
- **Баннер expired** — owner согласен 100% (не тихая деградация)
- **Supersedes:** O174 1₽ trial · O107 кнопка · O116 free-TG instant

**Quiz-first guard (Coder brief):** flat = km-sort off · min_match ignored · filter bar hidden/disabled · chronological `published_at` desc.

**Deliverables:**
- [x] Таблица tier × rights — **freeze**
- [x] Copy/UI — **→ Design § O209** (единый поток)
- [ ] Опционально: one-liner vision v0.13 «match-first» — после приёмки O209

**Handoff:** `@lead-designer` § **O209-MATCH-EXPERIENCE** → `@designer` → `@coder`

---

## § O171-ADMIN-RESEARCH — Owner Command Center (**✅ w1 shipped · tail w2 `/status` · 2026-06-13**)

**Owner (O171-w 2026-06-10):** лампы врут — YouDo 🟢 при 0 лидов; FL 🟡 когда биржа жива; `/status` и push не дают «что делать» не-программисту. **→ полное переосмысление `/ops/` + FLPARSING-бота.**

**Канон:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O171-w** · **Уже есть:** O121-D ✅ wireframes прокси + mini-nav → **не дублировать**.

**Scope:** только `/ops/` + @FLPARSINGBOT. Публичные карточки/страницы — **другой чат, out of scope**.

---

### JTBD владельца

| # | Работа (Jobs-to-be-done) |
|---|--------------------------|
| J1 | Понять за 30 сек с телефона: жив ли радар прямо сейчас |
| J2 | Разобрать 🟡/🔴: биржа пустая, парсер сломан или фильтр режет |
| J3 | Получить пуш только при реальном инциденте — не «мусор» |
| J4 | 0 лидов: найти место обрыва в воронке process→fetch→parsed→new→L1→visible |
| J5 | Починить без SSH (restart radar/bot, probe proxy, manual delist) |

---

### IA Owner Command Center — 7 блоков

| # | Блок | Зачем |
|---|------|-------|
| 1 | **Сводка** | 5 ламп «жив/нет» за 5 сек + суммарный диагноз воронки |
| 2 | **Биржи** | FL · Kwork · YouDo · secondary: 🟢🟡🔴 + причина + lag мин |
| 3 | **TG** | acc1/acc2/acc3 join/listen/strikes · Bot API pool O120 failover |
| 4 | **Прокси** | **→ O121-D ✅ уже есть** — 3 группы; wireframes не трогать |
| 5 | **Управление** | radar pause/restart · site · delist — KEEP существующий |
| 6 | **Лиды** | последние N · consumer lag · L1 queue depth |
| 7 | *(мини-нав)* | Сводка · Биржи · TG · Прокси · Управление · Лиды |

---

### «Ступени правды» per source

```
process alive → fetch OK → parsed ≥ N → new (дедуп > 0) → L1 done → visible > 0
```

| Ступень | Метрика | Норма |
|---------|---------|-------|
| **process** | radar PID alive · last\_cycle < 15 мин | 🟢 |
| **fetch** | HTTP 200 / browser OK · retry ≤ 3 | 🟢 |
| **parsed** | N карточек за цикл | FL ≥ 5 · Kwork ≥ 5 · YouDo ≥ 5 |
| **new** | parsed − dups | > 0 за 1 ч (норм = пустая биржа) |
| **L1** | ai\_score присвоен · очередь < 50 | 🟢 |
| **visible** | `is_visible=true` новых за 24 ч | ≥ 10; иначе 🟡 |

**Диагноз «0 лидов»:** last 🔴 ступень = место обрыва → человеческий текст в блоке Сводка и пуш.

---

### /status + push (FLPARSING-бот)

**/status — структура ответа:**
```
📊 Радар: жив · цикл 8 мин назад
🔴 FL: fetch timeout (3 попытки) → [Проверить прокси FL]
🟢 Kwork: parsed=12 · new=4 · L1 ok · visible+3
🟡 YouDo: parsed=0 · fetch ok · нет новых (биржа пустая)
🟢 TG: acc2 слушает 127 чатов · acc3 join идёт
🟢 L1: очередь 0 · avg 2.1 с
```

**Push — только при реальном инциденте:**

| Триггер | Текст | Частота |
|---------|-------|---------|
| fetch fail × 3 подряд | `🔴 FL · fetch timeout — проверь прокси` | 1 / 30 мин |
| visible = 0 и parsed > 0 за 3 ч | `🔴 L1 завис — очередь N, visible 0 за 3 ч` | 1 / 1 ч |
| radar молчит > 20 мин | `🔴 Радар молчит > 20 мин — перезапусти` | 1 / 20 мин |
| proxy auto-switch | `FLPARSING · прокси: слот N → слот M` | O120 уже есть |

**Не пушить:** «0 новых» когда биржа пустая (норм), re-check OK, ротация кеша.

---

### Out of scope (O171)

- Публичные страницы, карточки, лента, /quiz/ — **другой чат**
- CRUD URL прокси — O121-w4
- TG join CRUD — O121-w3
- O172-w (Green/Red runbook) — после O171

---

### Acceptance (DoD этого §)

- [x] Wireframes @lead-designer: Сводка + TG · mobile 390
- [ ] /status формат — **tail w2** (не в w1)
- [ ] Push-триггеры согласованы — **tail w2**
- [x] Coder § **O171-OPS-ADMIN-REBUILD** w1 on prod

---

### Handoff → @lead-designer

```
@lead-designer
PM spec: LEAD_PRODUCT_PROMPT.md § O171-ADMIN-RESEARCH
Scope wireframes: (1) Сводка — ступени правды 6 ламп per source (2) TG-блок acc + Bot API pool
Mobile 390: обязательно — владелец чинит с телефона
Не трогать: Прокси (O121-D ✅) · Управление · Лиды
```

---

## § TINDER-ONBOARD — Персонализация через тест (**→ now · 2026-06-13**)

**Концепция зафиксирована с владельцем 2026-06-13.**

**Суть:** вместо статичной открытой ленты — тест-«Тиндер» как путь к персонализации. Анон видит ленту, но без фильтров. Фильтры (ниша, навыки) открываются только после теста. После теста — регистрация → персональная лента.

---

### Новая воронка (замена §0j TWO-SPEEDS анон-части)

```
Анон /lenta/ — все лиды вперемешку, БЕЗ фильтров (нет skills picker, нет категорий)
↓
Промо-полоса: «Настрой ленту под себя — пройди тест (2 мин) →» [/quiz/]
↓
/quiz/ — адаптивный тест (6–20 карточек, анонимно, без регистрации)
↓
Экран результата: «Твой профиль: Дизайн + Видео · ~100 подходящих заказов в неделю»
↓
«Войди через Telegram — открой свою ленту»
↓
Free (TG login): персональная лента + фильтры включены + задержка 15 мин (keep O116-R1)
↓
Premium: мгновенно + ИИ-отклики + push
```

**Ключевое решение владельца (2026-06-13):** анон не блокируется от ленты — он видит лиды. Но фильтры (нишевые, навыков) недоступны — только бесполезный поток. Gate через ценность, не через блокировку.

---

### /quiz/ — страница теста (Adaptive Pool · O197-w · 2026-06-13)

> **Supersedes:** предыдущая версия «ровно 12 карточек (3×4)». Принято owner 2026-06-13 через § O197-w.

**URL:** `/quiz/` (новая страница WP)

**Механика:**
- Кнопки: **«Взял бы» / «Не моё»** (или swipe)
- Прогресс-бар: «6 из ?» (верхняя граница не показывается — убирает давление «ещё N штук»)
- Нет возврата к предыдущей карточке
- Бюджет и источник скрыты — решение только по сути задачи

---

#### Адаптивный пул (O197-w)

**Размер:**

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| **Min (early stop)** | **6 карточек** | ниже — данных не хватает даже при явном профиле |
| **Default (normal stop)** | **10–12 карточек** | типичный случай |
| **Max (forced stop)** | **20 карточек** | при очень неясном стеке; больше — усталость |

**Выборка из Neon:**
- `is_visible=true, ai_score >= 60, created_at > NOW() - 30 days`
- По каждой нише — отдельный pool: Dev / Design / Marketing / Text
- Pool обновляется при каждой сессии (живые лиды, не кешированные ID)
- Бюджет и source — не отображаем

---

#### Алгоритм ветвления

**Confidence per ниша:**

| Событие | Δ confidence ниши карточки |
|---------|---------------------------|
| «Взял бы» | **+2** |
| «Не моё» | **-1** |

Начало = 0 для каждой ниши (Dev, Design, Marketing, Text).

**Фаза 1 — Intro (карточки 1–4):** по одной из каждой ниши, порядок перемешан — разведка всех четырёх направлений. Не пропускаем нишу, даже если пользователь не «зажигается».

**Фаза 2 — Exploit + cross-check (карточки 5+):**
- Если **только один** профиль ≥ 2, остальные ≤ 0 → чистый exploit: следующие карточки из лидера
- Если **два или более** профиля ≥ 1 → **чередуем 2:1**: 2 карточки из лидера, 1 из второго. Цель: честно проверить, не «случайный лайк» ли второй профиль. Так выявляем комбинированные стеки (Text + Dev, Design + Marketing).

**Фаза 3 — Probe (при неопределённости):** если после 10 карточек ни одна ниша не достигла порога — продолжаем, пробуем карточки с другими signal-тегами внутри топ-2 ниш (уточнение стека внутри ниши).

> **Принцип:** алгоритм не форсирует выбор «одной правильной» ниши — комбинированный стек (копирайтер+питон, дизайнер+таргет) — валидный результат, не ошибка.

---

#### Stop rules

| Условие | Порог | Действие |
|---------|-------|----------|
| **Early stop** | ≥ 6 показано · одна ниша ≥ 4 · все остальные ≤ 0 | → стоп (чёткий одиночный профиль) |
| **Normal stop** | ≥ 10 показано · Σ(ниши с confidence ≥ 2) стабилизировался последние 2 карточки | → стоп |
| **Forced stop** | 20 показано | → стоп всегда |
| **Null stop** | ≥ 10 показано · все ниши ≤ 0 | → «не нашли профиль» экран |

**«Стабилизировался»** = множество ниш с confidence ≥ 2 не изменилось за последние 2 ответа. Это универсальный критерий: работает для 1, 2, 3 и 4 активных ниш одинаково.

> **Ключевое:** алгоритм не знает заранее, сколько профилей у пользователя. Он просто останавливается, когда картина перестаёт меняться — будь то 1 ниша или все 4.

---

#### API (stateless — no Redis session)

Сервер не хранит state сессии. Вся история передаётся клиентом в каждом запросе.

| Эндпоинт | Запрос | Ответ |
|----------|--------|-------|
| `POST /v1/quiz/next` | `{history: [{card_id, liked, tags: [...]}]}` | `{card: {...}, done: false}` или `{done: true, profile: {...}}` |
| `GET /v1/quiz/start` | — | первая карточка (история пуста) |

**Deterministic algorithm на сервере:** confidence считается из переданной истории; нет хранимого state на сервере.

**localStorage schema:**
```json
{
  "rawlead_quiz_session": {
    "history": [{"card_id": "...", "liked": true, "tags": ["ui_ux", "figma"]}],
    "started_at": "ISO"
  }
}
```
После TG login: JS POST `/v1/me/tags/import` → импорт в `user_tags` → localStorage чистится.

---

#### Экран результата

Алгоритм универсальный — работает для любого числа ниш (0, 1, 2, 3, 4) без хардкода кейсов.

**Правило отображения:**

Берём все ниши с confidence ≥ 2 → показываем их в порядке убывания. Называем «профиль». Нет хардкода «только 1» или «только 2».

| Ситуация | Copy | CTA |
|----------|------|-----|
| **1 ниша ≥ 2** | «Твой профиль: 🎨 Дизайн (~N заказов/нед)» | «Войти → открой свою ленту» |
| **2 ниши ≥ 2** | «Твой профиль: ✍️ Тексты + 💻 Разработка (~N заказов/нед)» | то же |
| **3+ ниши ≥ 2** | «Широкий профиль: [Ниша1], [Ниша2], [Ниша3] — лента покажет заказы из нескольких направлений (~N заказов/нед)» | то же |
| **Все ниши ≤ 0** (ничего не понравилось) | «Пока не нашли конкретного профиля — посмотри весь поток» | «Смотреть ленту →» + «Пройти снова» |

**Важно:** «Широкий профиль» и «ничего не понравилось» — принципиально разные вещи. Широкий → теги импортируются из всех ниш, лента богатая. Null → профиля нет, лента без персонализации.

**N заказов в неделю** — сумма `is_visible=true` за 7 дней по всем нишам с confidence ≥ 2. Для text отображаем честно (~30/нед).

**Вторая кнопка** (мелко): «Посмотреть ленту без настройки →»

---

#### Import в user_tags — универсальный

При POST `/v1/me/tags/import` → в `user_tags` попадают **теги всех карточек с `liked=true`**, вне зависимости от ниши. Алгоритм выбора «одного профиля» не нужен — лента сама ранжирует по весам.

Примеры:
- Маркетинг + Тексты → `smm`, `copywriting`, `yandex_direct`, `article_writing` — все с весом
- Питон + Дизайн → `python_bot`, `api_integration`, `ui_ux`, `figma`
- Питон + Маркетинг + Тексты → все три пула тегов
- Универсал (все 4 ниши) → все теги лайкнутых карточек из всех ниш

Лента после логина автоматически показывает заказы из всех «понравившихся» направлений — не нужно выбирать «главный» профиль.

---

#### Прогресс-бар UX

Вместо «3 из 12» — индикатор без верхней границы:
- **«Ещё пара карточек»** — если до early stop осталось ≤ 2
- **«Почти готово»** — после 10 карточек
- Без цифры max — пользователь не видит «конец»

---

### Хранение профиля пользователя

**Решение:** расширить существующую таблицу `user_tags` — **не pgvector, не отдельный JSONB**.

Текущая схема: `user_tags (user_id UUID, tag TEXT, weight REAL default 1.0)` — уже правильная структура.

**Добавить два поля:**

```sql
ALTER TABLE user_tags
  ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS interaction_count INT DEFAULT 0;
```

**Диапазон weight:** от **-5** (сильный дизлайк) до **+10** (много подтверждений).

**До регистрации:** результаты теста хранятся в `localStorage` браузера `{rawlead_quiz: {tags: {ui_ux: 4, python: -1, ...}}}`. При TG login: JS POST на `/v1/me/tags/import` → импортируется в `user_tags`. localStorage чистится.

---

### Веса: алгоритм начисления

| Событие | Действие |
|---------|---------|
| Тиндер: «Взял бы» | все теги карточки: `weight += 2.0`, `interaction_count += 1` |
| Тиндер: «Не моё» | все теги карточки: `weight -= 1.0` |
| Отклик «Написать отклик» | все теги: `weight += 3.0`, `interaction_count += 2` |
| Раскрыл карточку (warm/expand) | все теги: `weight += 0.1` (интерес) · **без штрафа** за «посмотрел и ушёл» |
| ~~Раскрыл, не откликнулся~~ | **удалено owner 2026-06-19** — event `expand_no_reply` вырезать из API · browsing без отклика **не** штрафует |
| ~~Карточка 20+ показов~~ | superseded |
| Удалил отклик из inbox | теги: `weight -= 0.5` |

**Scoring обновлённый (`final_rank`):**

```
keyword_match = Σ(weight_i × match_i) / Σ(max_weight_i) × 100   [cap 100]
final_rank = ai_score × 0.6 + keyword_match × 0.4
```

Где `match_i = 1` если тег есть в `lead_tags`, иначе `0`. Теги с `weight ≤ 0` не участвуют в совпадении.

---

### Алгоритм decay (затухание весов)

**Цель:** лента не «застывает» на первом тесте — веса плавно снижаются при неактивности.

**Decay-формула (рассчитывается в Python при запросе /v1/feed):**

```python
days_inactive = (now - last_active_at).days
decay_factor = 0.95 ** (days_inactive / 3)  # -5% каждые 3 дня неактивности
effective_weight = weight * decay_factor
```

| Дни без активности по тегу | Вес 5.0 становится |
|----------------------------|--------------------|
| 3 дня | 4.75 |
| 7 дней | 4.27 |
| 14 дней | 3.64 |
| 30 дней | 2.64 |
| 60 дней | 1.39 |

- Если `effective_weight < 0.5` → тег исключается из ранжирования (но не удаляется из БД)
- Decay считается **на лету** при `/v1/feed` — не сохраняется обратно в БД (избегаем постоянных UPDATE)
- `last_active_at` обновляется при любом позитивном событии (отклик, expanded card)

---

### Анон /lenta/ — новое поведение фильтров

| Состояние | Фильтры |
|-----------|---------|
| **Анон (без теста)** | Фильтры СКРЫТЫ или заблокированы (disabled chips) · вместо них: «Пройди тест — включи фильтры» |
| **Анон (тест пройден, не зарегистрирован)** | — нельзя (localStorage ≠ аккаунт, нет сессии) |
| **Free (TG login, тест есть)** | Фильтры ВКЛЮЧЕНЫ · 15 мин задержка · без «Написать отклик» |
| **Free (TG login, теста нет)** | Фильтры включены, но профиль пустой · промпт пройти тест |
| **Premium** | Всё включено · мгновенно |

**Copy для заблокированных фильтров (anon):**

- Над filter bar: «⚙ Фильтры — после настройки профиля»
- Chips категорий: disabled серые
- CTA: **«Настроить ленту →»** → `/quiz/`

---

### Text-ниша: данные и план

**Факт (Neon, 7 дней):** 1 189 text-лидов всего, только **229 visible** (19.3%), ~33/день. Это мало.

**Решение владельца 2026-06-13:** text-ниша растёт органически через добавление новых источников — не снижать порог ai_score.

**PM action:** при показе результата теста для text-профиля честно сообщать объём («~30 заказов/нед»). Приоритет новых text-источников — в бэклог `OWNER_INTENT`.

---

### Acceptance (DoD этого §) — обновлено O197-w 2026-06-13

- [ ] `/quiz/` — adaptive quiz (6–20 карточек), pool из Neon по нишам, ветвление по confidence, early/normal/forced stop
- [ ] `/v1/quiz/start` + `POST /v1/quiz/next` (stateless, history в body) — deterministic algorithm
- [ ] Прогресс-бар без верхней границы (без «из N»)
- [ ] Экран результата: один лидер / два лидера / null — показывает нишу + объём лидов из Neon за 7 дней
- [ ] Анон `/lenta/` — фильтры disabled до теста, промпт «Настроить ленту →»
- [ ] `user_tags` — добавлены `last_active_at`, `interaction_count`
- [ ] `/v1/me/tags/import` — endpoint для импорта localStorage-профиля
- [ ] `/v1/feed` — keyword_match считается с весами (не бинарно)
- [ ] Decay — реализован в Python, не в SQL

---

### Handoff → @lead-architect

```
@lead-architect
Продуктовая концепция обновлена (O197-w 2026-06-13): LEAD_PRODUCT_PROMPT.md § TINDER-ONBOARD
Нужно:
1. CODER_PROMPT § для /quiz/ adaptive (stateless API /v1/quiz/start + /v1/quiz/next, pool из Neon, confidence algorithm)
2. Изменения /lenta/ фильтров (disabled до теста) + схема user_tags (last_active_at, interaction_count)
3. O195-w1b ⏸ hold — НЕ деплоить 12-карточечный вариант; ждём adaptive
4. Приоритет по ROADMAP: O195-w1b → заменить на O197-adaptive
```

---

## § ASYNC-DRAFT — Отклик без ожидания генерации (**→ now · 2026-06-13**)

**Контекст:** кнопка «Написать отклик» сейчас блокирует UI пока L2 генерирует черновик. Это создаёт конфликт с decay-механикой из TINDER-ONBOARD: пользователь вынужден ждать генерации или вообще не кликает → веса тегов не растут → лента деградирует.

**Решение (решение владельца 2026-06-13):** fire-and-forget UX — кнопка немедленно подтверждает действие, черновик генерируется фоново, пользователь смотрит результат в `/cabinet/` когда удобно.

### Поведение кнопки «Написать отклик» (новое)

| Шаг | Что происходит |
|-----|----------------|
| 1 | Пользователь нажимает «Написать отклик» на карточке в ленте |
| 2 | **Немедленно (< 200ms):** кнопка → «✅ Добавлено в кабинет» · карточка попадает в inbox `/cabinet/` со статусом «Генерируется…» |
| 3 | Пользователь **не ждёт** — может листать ленту дальше или закрыть страницу |
| 4 | `/cabinet/` inbox: черновик появляется по готовности · при ошибке — кнопка «Повторить» |

**Что НЕ меняется:** сама L2-генерация, `lead_draft_jobs` таблица (`status: pending → done/failed`) — они уже работают async. Меняется только UX в ленте: убрать блокирующий spinner, добавить instant-confirmation.

### Copy (новые состояния)

| Место | Состояние | Copy |
|-------|-----------|------|
| Карточка `/lenta/` | после клика | **«✅ Добавлено в кабинет»** (2 сек, потом серая disabled) |
| `/cabinet/` inbox card | pending | **«⏳ Черновик генерируется…»** |
| `/cabinet/` inbox card | failed | **«Не удалось сгенерировать · [Повторить]»** |
| `/cabinet/` inbox card | done | текст черновика (как сейчас) |

### Acceptance (DoD этого §)

- [ ] Кнопка «Написать отклик»: клик → instant «✅ Добавлено» без ожидания L2
- [ ] `/cabinet/` inbox: состояния `pending` / `failed` / `done` с корректными copy
- [ ] Нет блокирующего spinner в ленте после клика

### Handoff → @lead-architect

```
@lead-architect
Задача: LEAD_PRODUCT_PROMPT.md § ASYNC-DRAFT
Суть: убрать blocking-ожидание L2 из ленты — instant confirmation + async в cabinet
Архитектурно: lead_draft_jobs уже есть; меняется UX в rawlead-feed.js и rawlead-cabinet.js
```

---

## § YOUDO-PREFILTER — Фильтрация оффлайн-задач YouDo до L1 (**→ backlog · 2026-06-13**)

**Контекст (факты из Neon, 7 дней):** YouDo text = 953 лидов, visible только 75 (7.9%). YouDo dev = 476 лидов, visible 60 (12.6%). Причина: YouDo парсер качает ВСЕ задачи платформы включая оффлайн-сервисы — «уколы», «уборка квартиры», «репетитор по футболу», «груминг кошки». ИИ правильно даёт им ai_score=15 («МИМО»), но L1 тратится впустую.

**Распределение YouDo text ai_score:** 75 лидов = score 85 (digital, visible) + 878 лидов = score 15 (оффлайн, МИМО). Нет промежуточных значений — биполярный паттерн.

**Вывод:** порог ai_score снижать не нужно — фильтр работает корректно. Проблема в источнике: YouDo-парсер не ограничен digital-категориями.

**Решение:** добавить pre-filter в YouDo-парсер на уровне ingest — принимать только лиды из digital-категорий YouDo (разработка, дизайн, маркетинг, тексты/переводы). Оффлайн-категории (уборка, красота, здоровье, обучение офлайн) — отсекать до передачи L1.

**Ожидаемый эффект:** YouDo text visible: 7.9% → ~63% (как Kwork). Объём text-ленты вырастет с ~33 до ~130 visible лидов/день.

**PM scope:** только постановка задачи. Реализация — `@coder` через `CODER_PROMPT`.

### Acceptance (DoD этого §)

- [ ] YouDo парсер: pre-filter по digital-категориям платформы до вызова L1
- [ ] Метрика: YouDo text visible % > 50% (замер через 3 дня после деплоя)

### Handoff → @lead-architect

```
@lead-architect
Задача: LEAD_PRODUCT_PROMPT.md § YOUDO-PREFILTER
Суть: YouDo парсер качает оффлайн-услуги → L1 тратится вхолостую; нужен pre-filter по категориям YouDo
Данные: youdo text 953 лидов/нед → только 75 visible; dev 476 → 60 visible
```

---

## § PRODUCT-CANON-AUDIT (**→ backlog · 2026-06-12**)

**Канон:** [`PRODUCT_CANON.md`](PRODUCT_CANON.md) — тарифы, оплата, match, навыки, retention, чеклист страниц §9.

**Задача PM:** пройти каждый URL · отметить противоречия copy/UI · handoff Design/Coder (old→new).

**Owner до ads:** O185 (pay/match/skills/YouDo/security) — не реклама.

---

## § O174-COPY — YooKassa · trial · автопродление (**W1 PM · 2026-06-10**)

**Канон owner:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O174-w**

**Цифры (не менять без owner):**

| | |
|--|--|
| Trial | **1 ₽** · **3 дня** Premium · **1 раз** на аккаунт |
| Далее | **790 ₽/мес** · **автопродление** через ЮKassa |
| Способы | Карта / СБП **только через ЮKassa** |
| Убрать | Stars · USDT/TON · «перевод на телефон» · `/pay` в боте как оплата |

**Deliverables (RU copy, таблица old → new):**

1. **`/pricing/`** — hero, bullets, CTA, мелкий legal про автопродление и отмену
2. **`#pricing-preview`** на главной — те же цифры, короче
3. **`/faq/`** — Q про оплату, trial, автопродление, возврат (без crypto/Stars)
4. **`/cabinet/`** — статусы подписки + одна CTA
5. **Footer legal** — только FIO+ИНН (O174a, без PM)

**Tone:** как O116/O105 — коротко, без юридической простыни; автопродление — явно, но не пугающе.

**Handoff:** approve → `@lead-designer` § O174-D → `@coder` § O174b.

---

## § O116-COPY — Pre-ads: TWO-SPEEDS update + FAQ трёх уровней (**W1 PM · 2026-06-04**)

**Статус:** ✅ W1 PM · **R1–R3 ✅ владелец 2026-06-04** · → **W2 @lead-designer**

**Решения владельца (канон):** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O116** — R1 ✅ · R2 ✅ · R3 ✅

---

### O116-Z1 — Новая модель TWO-SPEEDS (R1)

**Смысл R1:** задержка 15 мин — **только для незалогиненных**. TG-вход (без Premium) = лента сразу, но без кнопки «Написать отклик».

| Сегмент | Было (O11 / O23) | Стало |
|---------|-----------------|-------|
| **Anon** (без TG-входа) | ⏱ 15 мин · без кнопки | ⏱ 15 мин · без кнопки **KEEP** |
| **Free TG login** | ⏱ 15 мин · без кнопки | ✅ **Без задержки** · навыки работают · **без «Написать отклик»** |
| **Premium** | Мгновенно · «Написать отклик» | **KEEP** |

**PM-аргументы за R1:**
1. Воронка для рекламного трафика: anon → TG-вход (бесплатно + лента сразу) → Premium (черновики). Текущий O23 пропускает mid-step.
2. Hook: «Войди через Telegram — лента без ожидания» — конкретный и бесплатный; не «купи».
3. Premium продаётся через черновики + push + inbox, не через blackout ленты.

**PM-риск:** free login без задержки → меньший стимул апгрейдиться ради скорости. Принимается, если value-prop Premium = черновики (R3 обязателен синхронно).

**Не делать:** не убирать delay вообще (anon сохраняем), не давать free login кнопку «Написать отклик».

---

### O116-Z2 — Strip copy (R3, anon + free)

**Anon strip:**

| Вариант | Copy | Куда |
|---------|------|------|
| **A (PM рекомендует)** | **«⏱ Лента с задержкой 15 мин · [Войди — сразу →]»** | → TG login |
| B | «⏱ Лента с задержкой · [Войти через Telegram →]» | → TG login |

**Free login strip:** убрать label задержки. Опц. добавить: **«✅ Лента без задержки · Черновики — Premium →»** → `/pricing/`.

**Paid strip:** KEEP «⏱ Лента с задержкой 15 мин · Premium — сразу, от 790 ₽ →» *(для anon-путешественников на lenta anon)*

**Обновить (O105-Z5):**

| Surface | Было | Стало |
|---------|------|-------|
| `/lenta/` anon strip | «⏱ Лента с задержкой 15 мин · Premium — сразу, от 790 ₽ →» | **Вариант A** → TG login |
| `/lenta/` free strip | (= anon) | **убрать задержку-label** |
| `/cabinet/` free sub | «790 ₽/мес · или 300 ⭐ Stars» KEEP | KEEP |

---

### O116-Z3 — Pricing Feature 1 update (R3, если R1 принят)

«Лента без задержки» перестаёт быть Premium-уникальным. Пересобираем priority bullets:

| Элемент | Было (O105-Z2) | Стало |
|---------|---------------|-------|
| **Feature 1** | «Лента без задержки — заказы под твой стек сразу» | **«Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам»** |
| **Feature 2** | «Уникальный черновик отклика — ИИ пишет…» | **«Лента без задержки и push — заказы появляются сразу при match»** *(на второе место)* |
| Feature 3–5 | KEEP | KEEP |

**Не менять:** payment block · CTA · compare line · slot line.

**Если R1 НЕ принят:** Z3 не применяется, O105-Z2 остаётся как есть.

---

### O116-Z4 — FAQ три уровня (R2)

**Структура: три accordion-группы вместо flat Q1–Q9**

| Уровень | Заголовок | Вопросы (порядок показа) |
|---------|-----------|--------------------------|
| **1 «Начало»** | Начало | Q6 Как начать · Q1 Это автоспам? · Q4 Нужен TG? |
| **2 «Как работает»** | Как работает | Q2 Нетехнические? · Q3 Источники · Q5 Не получу бан? · Q8 Почему лимит 10 откликов? |
| **3 «Premium»** | Premium | Q7 Сервис платный? · Q9 Есть trial? · **NEW Q10** |

**NEW Q10 (если R1 принят):**

**Q:** «Зачем Premium, если лента и так без задержки после входа?»

**A:** «После входа через Telegram — лента сразу. Это бесплатно. Premium даёт: уникальный черновик отклика под твой профиль · push в Telegram при матче · inbox с черновиками · до 10 слотов на горячий заказ.»

**NEW Q10 (если R1 НЕ принят):**

**Q:** «Как убрать задержку 15 минут?»

**A:** «Подключи Premium — лента станет мгновенной. 790 ₽/мес или 300 ⭐ Stars: /pay в @rawlead_bot.»

**Открытые вопросы → Design:**

| # | Вопрос | Рекомендация PM |
|---|--------|-----------------|
| Q1 | Accordion: первая группа раскрыта по умолчанию? | **Да, «Начало»** — для холодного трафика |
| Q2 | Group header: отдельный стиль или просто жирный? | **Bold + muted bg** · Design выбирает |
| Q3 | Mobile 390px: показывать все 3 группы свёрнутыми? | **Да, по умолчанию только «Начало» открыта** |

---

### Acceptance W1 (PM)

- [x] R1 ✅ владелец 2026-06-04 (меняет O11/O23)
- [x] R2 ✅ владелец 2026-06-04
- [x] R3 ✅ владелец 2026-06-04 (Z3 применяется)
- [x] Z1–Z4 copy зафиксированы
- [ ] → **W2 @lead-designer**: strip (Z2) + FAQ accordion (Z4) + pricing F1 (Z3)

**Handoff W2:**

```
@lead-designer
Copy: LEAD_PRODUCT_PROMPT.md § O116-COPY Z1–Z4
Блоки: anon-strip update (Z2) · FAQ accordion 3 уровня (Z4) · pricing Feature 1 swap (Z3, если R1)
```

---

## § O105-COPY — Premium · уникальный отклик · O101 (**✅ PM approve 2026-06-03**)

**Статус:** ✅ **PM approve 2026-06-03** (Playwright-аудит prod + ценовой research) · Copy Z1–Z8 подтверждены · открытые вопросы — ниже · владелец утверждает — `O107-open` § Z8 · **→ @lead-designer D1–D7**.

**На prod сейчас (факт 2026-06-03 после Playwright-аудита):** pricing = 300 Stars (старый O96); trust strip отсутствует; Feature 3 = «Ты решаешь»; FAQ Q7 = Stars; карточки лента = expanded (суть задания видна в collapsed); Trial = нет нигде.

**Решения владельца (канон):** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **O101** · § **O105** · § **O106** · § **O107** (trial 3 дня) — цена 790 ₽, СБП/crypto, 10 слотов, «не выглядишь как бот».

**Tone:** как O96 — уверенный коллега · «ты» · без «!» · честно про лимиты (10 слотов, anti-тык) · **не** пугать, **не** обещать авто-отправку на биржу.

**Цена канон:** **790 ₽/мес** (СБП · crypto) · **300 ⭐ Stars** — альтернативный канал, **не убираем**.

**Внутренние ID (O101, O105) — только в docs/Coder, не в UI.**

---

### PM-аудит prod (Playwright 2026-06-03)

**Что работает хорошо:**
- Лента живая: 174–181 новый заказ за сутки — сильный социальный сигнал
- Дизайн считывается сразу: жёлтый hero, Manrope bold, чёрные CTA
- Filter bar 4 ниши работает корректно
- TWO-SPEEDS strip правильно позиционирует free vs paid
- `/how/` — отличная страница, 5 шагов за 30 сек
- `/cabinet/` anon — чистый login screen без перегруза

**Что плохо / нужно исправить:**

| # | Поверхность | Проблема | Приоритет |
|---|-------------|----------|-----------|
| 1 | `/pricing/` + `#pricing-preview` | Показывает 300 Stars вместо **790 ₽/мес** — несоответствие O105 | **P0** |
| 2 | `/faq/` Q7 | «300 Stars» вместо «790 ₽ или Stars» | **P0** |
| 3 | `/lenta/` карточки (anon) | «Суть задания» видна в collapsed — O106 не выполнен | **P1** |
| 4 | Главная `/` Feature 3 | Title «Ты решаешь» → «Уникальный отклик» per O105-Z1 | **P1** |
| 5 | Главная `/` | Trust strip «Не один текст на всех» **отсутствует** | **P1** |
| 6 | `/cabinet/` free | Нет Trial CTA «Попробовать 3 дня бесплатно» per O107 | **P1** |
| 7 | `/pricing/` | Нет блока 3 способов оплаты (СБП / Crypto / Stars) | **P1** |
| 8 | `/faq/` | Нет Q8 (лимит 10 откликов) и Q9 (пробный период) | **P2** |
| 9 | `/lenta/` мобайл | Filter chips обрезаются на 390px | **P2** |
| 10 | `<title>` `/lenta/` `/faq/` | ndash (–) вместо emdash (—) | **P3** |

**Что не хватает (новые поверхности):**
- **Trial CTA** — нет нигде. Нужен минимум в `/cabinet/` free и `/pricing/`
- **Payment methods** — 3 кнопки (СБП · Crypto · Stars) на `/pricing/`
- **Slot line** — «Осталось N из 10» на карточках ленты
- **Compare line** — «FL.ru PRO — 1 270 ₽ только за отклики» под pricing card

**Ценовой research (2026-06-03):**

| Продукт | Цена | Что даёт |
|---------|------|----------|
| **RawLead Premium** | **790 ₽/мес** | подбор + ИИ-черновик (уник.) + push + без задержки + до 10 слотов |
| FL.ru PRO (базовый) | ~1 270 ₽/мес | только неограниченные отклики |
| FL.ru PRO (Дизайн) | ~4 500 ₽/мес | отклики + каталог |
| 300 Telegram Stars | ~450–570 ₽ | то же что Premium (альт. канал) |

→ 790 ₽ в **1.6× дешевле** базового FL.ru PRO. Строка сравнения обоснована.

---

### O107-open — вопрос владельца (Trial CTA placement)

**Q: Trial CTA на anon-лента (`/lenta/` strip) или только в кабинете?**

- **Вариант A (PM рекомендует):** Только `/cabinet/` free + `/pricing/` hero. Меньше абьюза, выше конверсия на залогиненных.
- **Вариант B:** Ещё в anon strip `/lenta/`. Выше показ, strip длиннее.

**Пока не решено владельцем — Design НЕ рисует trial на lenta.**

---

### O105-Z1 — Лендинг `/` (hero + блок доверия)

| Элемент | Было (O96) | Канон O105 |
|---------|------------|------------|
| Sub (hero) | «…готовит черновик отклика.» | **«ИИ находит заказы под твой стек и пишет черновик отклика — свой у каждого. Не шаблон с полки, не копипаст. Отправляешь ты — своими словами.»** |
| Feature 2 text | «…по смыслу.» | **KEEP** |
| Feature 3 title | «Ты решаешь» | **«Уникальный отклик»** |
| Feature 3 text | «…Откликаешься сам…» | **«Каждый получает свою формулировку — ИИ адаптирует текст под тебя. На бирже не выглядишь как бот — не один шаблон на всех. Пишешь и отправляешь сам — мы не спамим за тебя.»** |
| **NEW** trust strip под features | — | **«Не один текст на всех · Не автоспам · Не бан за шаблон»** (3 chip, desktop; mobile — одна строка: **«Свой черновик у каждого»**) |

---

### O105-Z2 — `/pricing/` и `#pricing-preview` (лендинг)

| Элемент | Было (O96) | Канон O105 |
|---------|------------|------------|
| H1 sub | «Один тариф. Всё включено.» | **KEEP** |
| Карточка title | «ИИ-агент» | **«RawLead Premium»** |
| Цена primary | «300 ⭐ Stars…» | **«790 ₽ / мес»** |
| Цена secondary | — | **«или 300 ⭐ Stars в Telegram (~400–720 ₽)»** |
| Feature 1 | «Лента только с заказами…» | **«Лента без задержки — заказы под твой стек сразу»** |
| Feature 2 | «Черновик… своя формулировка.» | **«Уникальный черновик отклика — ИИ пишет под тебя, не копирует с соседа»** |
| Feature 3 | «Пуш…» | **KEEP** |
| **NEW** Feature 4 | — | **«До 10 персональных откликов на заказ — без толпы одинаковых ботов на одном лиде»** |
| **NEW** Feature 5 | — | **«Лимит в час — защита от случайных кликов (anti-тык)»** *(muted footnote, не главный буллет на mobile)* |
| Payment block title | — | **«Способы оплаты»** |
| Payment row 1 | Stars only | **💳 Банковская карта РФ / СБП — 790 ₽** |
| Payment row 2 | — | **🪙 Crypto — USDT (TRC20) или TON** |
| Payment row 3 | — | **⭐ Telegram Stars — 300 ⭐ / мес** |
| Payment note | «Оплата через Telegram Stars…» | **«СБП и crypto — в @rawlead_bot командой /pay. Stars — там же или кнопка в кабинете.»** |
| CTA primary | «Подключить — 300 ⭐…» | **«Подключить Premium →»** → `/cabinet/` или deep-link бота |
| CTA secondary (under card) | — | **«Смотреть ленту →»** KEEP |

**Сравнение (muted, одна строка под карточкой):** «FL.ru PRO — 1 270 ₽ только за доступ к откликам. RawLead — подбор + уникальный черновик + push.»

---

### O105-Z3 — @rawlead_bot · оплата Premium

**Триггер:** `/pay` · кнопка «Подключить» в кабинете · «Убрать задержку» на anon-ленте.

#### Экран 1 — выбор способа

```
RawLead Premium — ИИ-агент на месяц

📥 Лента без задержки — заказы сразу
✍️ Уникальный черновик отклика под твой профиль
🔒 До 10 откликов на один заказ — без каннибализма

790 ₽ / мес

Выбери способ оплаты:
```

| Кнопка | Label |
|--------|-------|
| 1 | **💳 Банковская карта РФ / СБП** |
| 2 | **🪙 Crypto (USDT / TON)** |
| 3 | **⭐ Telegram Stars (300 ⭐)** |
| back | **← Назад** |

#### Экран 2a — СБП

```
Генерация инвойса для User #{user_id}…

Сумма к оплате: 790 ₽

Реквизиты (СБП):
+7XXXXXXXXXX
Т-Банк · Никита

После перевода нажми «Проверить оплату» — сверим автоматически.
```

| Кнопка | Label |
|--------|-------|
| primary | **Проверить оплату** |
| secondary | **Отмена** |

**Состояния кнопки «Проверить оплату»:**

| Статус | Текст бота |
|--------|------------|
| pending | **«Ищем перевод… Обычно до 2 минут.»** |
| not found | **«Платёж пока не видим. Проверь сумму и реквизиты или напиши в поддержку.»** |
| success | **«Premium активен до {date}. Лента без задержки — заходи на /lenta/»** |

#### Экран 2b — Crypto

```
Инвойс User #{user_id}

790 ₽ ≈ {usdt_amount} USDT (TRC20)
или {ton_amount} TON

USDT (TRC20):
{wallet_usdt}

TON:
{wallet_ton}

В комментарии к переводу укажи: RL{user_id}

После перевода — «Проверить оплату».
```

| Кнопка | Label |
|--------|-------|
| primary | **Проверить оплату** |
| copy usdt | **Скопировать адрес USDT** |
| copy ton | **Скопировать адрес TON** |

**v1 copy-note (мелко):** «Оплата с Trust Wallet или MetaMask — скопируй адрес вручную. Авто-открытие кошелька — позже.»

#### Экран 2c — Stars

**KEEP** текущий Stars-flow (O29) — без изменений текста, только добавить в меню /pay как третью кнопку.

---

### O105-Z4 — O101 слоты · карточка `/lenta/` (paid)

| Элемент | Copy |
|---------|------|
| Slot line (N>0) | **«Осталось {N} из 10 черновиков на этот заказ»** |
| Slot line (N=1) | **«Последний черновик на этот заказ»** |
| Slot line (N=0) | карточка **не показывается** в ленте (backend O101) |
| Tooltip слотов | **«На один заказ — до 10 персональных черновиков. Когда места заняты — кнопка отклика серая, заказ остаётся в ленте.»** |
| Paid CTA tooltip (O89+O105) | **«ИИ напишет формулировку под тебя — не как у остальных»** |
| Anti-тыk 429 | **«Слишком много черновиков за час. Подожди или выбери другой заказ.»** |
| Anti-тыk low match | **«Совместимость низкая — черновик недоступен. Попробуй заказ ближе к твоему стеку.»** |

**Не писать:** «N фрилансеров смотрят» · «перегрет» · «дороже» (≠ O100).

---

### O105-Z5 — `/how/` · `/faq/` · anon strip

| Surface | Элемент | Copy |
|---------|---------|------|
| `/how/` шаг 5 | первое предложение | **«Черновик уже готов — для тебя написан отдельно, не скопирован с чужого отклика.»** |
| `/how/` | **NEW** шаг 6 (опц.) | **«На биржу отправляешь сам»** · «RawLead не постит за тебя. Правишь текст — и отправляешь когда удобно.» |
| `/faq/` Q5 | «Не получу ли бан…» | **«Нет. ИИ пишет персональную формулировку под твой профиль — не один шаблон на всех. На бирже не выглядишь как бот. Отправляешь сам, в своё время — автоспама с твоего аккаунта нет.»** |
| `/faq/` Q7 | «Сервис платный?» | **«Лента открыта бесплатно — с задержкой 15 мин. Premium (790 ₽/мес или 300 ⭐) — без задержки, уникальные черновики, push.»** |
| `/faq/` **NEW** Q8 | «Почему лимит 10 черновиков на один заказ?» | **«Чтобы на один hot-заказ не съехалась толпа одинаковых ботов. Каждый отклик — свой. Когда места заняты — кнопка серая, заказ остаётся в ленте.»** |
| `/lenta/` anon strip | TWO-SPEEDS | **«⏱ Лента с задержкой 15 мин · Premium — сразу, от 790 ₽ →»** |
| `/cabinet/` free sub | price | **«790 ₽/мес · или 300 ⭐ Stars»** |
| `/cabinet/` paid active | status | **«✅ Premium активен до {date} · [Пауза] [Оплата]»** |

---

### O105-Z6 — Маркетинговая формула (единая, для всех поверхностей)

**One-liner:** «Заказы под твой стек · черновик свой у каждого · без шаблонного спама»

**Три опоры (bullets):**

1. **Уникальность** — ИИ адаптирует формулировку под профиль; не один текст на десятерых.
2. **Безопасность** — ты отправляешь сам; нет автопостинга; не выглядишь как бот.
3. **Справедливость** — до 10 откликов на заказ; без гонки и аукциона на карточке.

---

### O105-Z8 — Trial 3 дня (**⏳ DRAFT · OWNER_INTENT § O107**)

**Решение владельца:** 3 дня **полного Premium** · **1 раз** на аккаунт · без карты.

| Surface | Copy (черновик) |
|---------|-----------------|
| `/pricing/` · hero pricing | **«3 дня Premium бесплатно — один раз на аккаунт»** |
| `/cabinet/` free | CTA primary: **«Попробовать 3 дня бесплатно»** · secondary: «790 ₽/мес · или 300 ⭐» |
| `/cabinet/` trial active | **«Trial · осталось N дн. · Premium до {date}»** · [Оплатить →] |
| `/lenta/` anon strip | **«⏱ Задержка 15 мин · 3 дня Premium бесплатно →»** *(PM: или оставить только 790 ₽)* |
| Bot после trial start | **«Premium на 3 дня активен. Лента без задержки, черновики — в один клик.»** |
| Bot за 24 ч до конца | **«Завтра trial заканчивается. Продлить — 790 ₽ или Stars: /pay»** |
| Bot после конца | **«Trial закончился. Лента снова с задержкой 15 мин. Premium — /pay»** |
| Trial уже был | **«Trial уже использован. Подключить Premium — /pay»** |
| `/faq/` **NEW** Q9 | **«Есть пробный период?»** → **«Да — 3 дня полного Premium один раз после входа. Без карты. Потом — 790 ₽/мес или Stars.»** |

**Design (добавить в Z7):** badge «Trial · N дн.» · CTA hierarchy: trial > pay · expired state в cabinet.

**PM решает:** trial CTA на anon-ленте или только в кабинете (см. OWNER_INTENT § O107).

---

### O105-Z7 — Design brief (блоки для @lead-designer)

**Зачем:** copy (Z1–Z6) — **что сказать**. Этот раздел — **что нарисовать**: новые блоки, состояния, приоритет mobile.

**Порядок работ:** **PM approve → Design → Architect → Coder.** Judge/regen не блокирует.

#### Карта поверхностей

| # | Поверхность | Приоритет | Связка |
|---|-------------|-----------|--------|
| D1 | Лендинг `/` | **P0** | O105-Z1 trust strip |
| D2 | `#pricing-preview` на лендинге | **P0** | = урезанная D3 |
| D3 | `/pricing/` | **P0** | 3 способа оплаты |
| D4 | `/lenta/` карточка collapsed | **P0** | **O106** + O105-Z4 слоты |
| D5 | `/lenta/` карточка expanded / L3 tray | **P1** | детали по tap |
| D6 | @rawlead_bot `/pay` | **P1** | 4 экрана + 3 состояния |
| D7 | `/cabinet/` блок подписки + **trial badge/CTA** | **P1** | O105-Z8 |
| D8 | `/how/` + `/faq/` | **P2** | текстовые правки, без новых блоков |

#### D1 — Лендинг `/`

| Блок | Статус | Задача Design |
|------|--------|---------------|
| Hero H1 | KEEP | — |
| Hero sub | **CHANGE** | Z1 текст |
| CTA | KEEP | — |
| Features 01–02 | KEEP | — |
| Feature 03 | **CHANGE** | title + body Z1 |
| **Trust strip** | **NEW** | 3 chip под features · mobile: 1 строка |
| Live preview | KEEP | — |
| `#pricing-preview` | **CHANGE** | см. D2 |

**Не добавляем:** отдельную секцию «как работает uniquify» — хватает Feature 3 + trust strip.

#### D2/D3 — Pricing

| Блок | Статус | Задача Design |
|------|--------|---------------|
| Карточка тарифа | **CHANGE** | title «RawLead Premium» · **790 ₽** крупно · Stars мелко |
| Bullets 1–5 | **CHANGE** | Z2 · #5 footnote на mobile |
| **Payment methods** | **NEW** | 3 row (СБП · crypto · Stars) · иконка + label + chevron → бот |
| Compare line | **NEW** | muted под карточкой · FL.ru PRO |
| CTA | **CHANGE** | «Подключить Premium →» |

**Wireframe нужен:** desktop + mobile 390px · порядок: цена → bullets → payment rows → CTA.

#### D4/D5 — Карточка ленты (O106 + O101)

**Collapsed (default) — что видно:**

| Элемент | Показ | Примечание |
|---------|-------|------------|
| Иконка источника + badge ИДЕАЛЬНО | ✅ | как `flow.php` |
| Title | ✅ | max 2 lines |
| Бюджет | ✅ | 1 строка |
| % совместимости + bar | ✅ | без breakdown row |
| **Slot line** | **NEW** | «Осталось N из 10» · muted · tooltip ⓘ |
| CTA | ✅ | fixed height |
| Сложность O97 | ❌ collapsed | → expanded |
| Tags | ❌ collapsed | max 2 chip или → expanded |
| Breakdown «Навыки Y%» | ❌ | → expanded |
| L3 preview | ❌ | только tray по CTA |

**Expanded (tap card / chevron):** сложность · tags полностью · breakdown · (опц.) snippet черновика.

**Состояния:** N=10…2 · N=1 «Последний» · anti-тыk toast · low match disabled CTA.

**Handoff O106:** Designer ведёт wireframe; PM acceptance — «в collapsed ≤ 7 строк контента».

#### D6 — Bot `/pay`

| Экран | Блоки |
|-------|-------|
| 1 Выбор | header · 3 benefit lines · цена · 3 inline-кнопки + Stars + Назад |
| 2a СБП | mono-block реквизиты · «Проверить оплату» · Отмена |
| 2b Crypto | 2 адреса · copy buttons · memo RL{id} · note Trust/MetaMask v1 |
| 2c Stars | KEEP текущий |
| pending / fail / ok | 3 коротких reply-текста Z3 |

**Формат:** ASCII wireframe или 390px mock · NEO не обязателен в TG — читаемость важнее.

#### D7 — `/cabinet/` подписка

| Блок | CHANGE |
|------|--------|
| Free card | «790 ₽/мес · или 300 ⭐» · CTA → /pay |
| Paid strip | «Premium до {date}» · [Оплата] |

#### Открытые вопросы → Design решает, PM approve

| # | Вопрос | Рекомендация PM |
|---|--------|-----------------|
| Q1 | Trust strip — chip или одна полоса? | **3 chip** desktop · **1 line** mobile |
| Q2 | Payment rows на pricing — клик ведёт в бот или modal? | **Deep-link @rawlead_bot /pay** |
| Q3 | Slot line — над или под CTA? | **Над CTA**, muted 11px |
| Q4 | Expanded card — sheet снизу или inline expand? | **Inline expand** (как сейчас tray) · Design выбирает если проще sheet |

#### Acceptance Design (DoD)

- [ ] Wireframe **D1–D4 + D6** в `LEAD_DESIGN_PROMPT.md` или `DESIGNER_PROMPT.md`
- [ ] Mobile 390px для pricing + card collapsed
- [ ] Нет O100-механик (аукцион, FOMO, «N смотрят»)
- [ ] Copy только из O105-Z1–Z6 (не придумывать новый)

---

**Handoff O105 (✅ PM approve 2026-06-03 — передано в Design):**

```
@lead-designer  ← СЕЙЧАС (PM approve получен)
  Copy: § O105-Z1–Z6 (✅ approve)
  Блоки: § O105-Z7
  Открытый вопрос Design: § O105-Z7 § «Открытые вопросы»
  Trial placement: ждёт решения владельца (§ O107-open)

@lead-architect  ← после Design DoD + E2E
  CODER_PROMPT § O105-w1 · O101 · O106-code
```

**Также для @lead-designer — PM-аудит недочётов prod (2026-06-03):**

| Блок дизайна | Что нужно добавить/исправить |
|---|---|
| D4 карточка collapsed | Убрать «Суть задания» из collapsed state — сейчас видна на `/lenta/` |
| D3 `/pricing/` mobile | Filter chips обрезаются на 390px — нужен scroll или max 2 row |
| D7 `/cabinet/` free | Добавить Trial badge/CTA block (после решения O107-open) |
| D1 hero sub | Обновить текст под Feature 3 title (O105-Z1) |

---

## § O96 — Copy-канон (полный pass) · **→ @lead-designer · @coder · 2026-06-02**

**Принято владельцем 2026-06-02.** Scope: лендинг · `/lenta/` · `/cabinet/` · `/pricing/` · `/how/` · `/faq/` · Skill Tree · O97 badge · O89 uniquify.

**Tone:** уверенный зрелый коллега на равных · «ты»-форма · активный залог · без «!» · без корпоративной вежливости · биржи — удобный источник, но с известными неудобствами, мы их решаем · не агрессия к FL/Kwork (партнёры по данным).

---

### O96-Z1 — Лендинг `/`

| Элемент | Текущий prod | Канон O96 |
|---------|-------------|-----------|
| `<title>` | «RawLead – Unfiltered freelance leads» | **«RawLead — Заказы под твой стек»** |
| Анонс-бар | «Радар онлайн · 800+ лидов в неделю · Смотреть ленту →» | **KEEP** |
| H1 | «Заказы под твой стек. Без мусора.» | **KEEP** |
| Sub | «Умный радар фриланса. ИИ находит идеальные совпадения по твоим навыкам и готовит черновик отклика.» | **KEEP** |
| CTA primary | «Смотреть ленту →» | **KEEP** |
| CTA secondary | «Тарифы ↓» | **KEEP** |
| Live preview H2 | «Последние заказы из ленты» | **KEEP** |
| Features H2 | «Один поток вместо десяти вкладок» | **KEEP** |
| Feature 1 title | «Один поток» | **KEEP** |
| Feature 1 text | «Биржи, агрегаторы, Telegram-каналы — всё в одной ленте…» | **KEEP** |
| Feature 2 title | «Нейросеть мэтчит технологии» | **«ИИ читает суть заказа»** |
| Feature 2 text | «Система не просто ищет ключевые слова. ИИ понимает суть заказа…» | **«Система понимает задачу и сверяет с твоим стеком — не по ключевым словам, а по смыслу.»** |
| Feature 3 title | «Ты решаешь» | **KEEP** |
| Feature 3 text | «Подходящий заказ — пуш в Telegram. Откликаешься сам. Мы не пишем заказчикам за тебя.» | **«Подходящий заказ — пуш в Telegram. Откликаешься сам, в удобное время.»** |
| Features footer | «Биржи и чаты — в одном потоке.» | **«Меньше вкладок, больше откликов.»** |
| How section Feature 2 | «Нейросеть мэтчит технологии» | **«ИИ читает суть заказа»** (синхронизировать с feature 2) |

---

### O96-Z2 — `/lenta/` anon

| Элемент | Текущий prod | Канон O96 |
|---------|-------------|-----------|
| TWO-SPEEDS strip | «⏱ Лента обновляется раз в 15 мин · Ускорить →» | **«⏱ Лента с задержкой 15 мин · Убрать задержку →»** → /pricing/ |
| H1 | «Лента заказов» | **KEEP** |
| Counter | «N заказов · M новых сегодня · по дате» | **KEEP** |
| Anon CTA на карточке | «Зарегистрируйтесь, чтобы настроить точный мэтчинг под свой стек и забрать готовый черновик отклика» | **«Это под твой стек? [Войди и проверь →]»** |
| Load more | «Ещё лиды» | **«Показать ещё»** |
| Конец ленты | «Все заказы показаны» | **KEEP** |
| Ошибка сети | — | **«Не удалось загрузить · [Попробовать снова]»** |
| Empty: нет лидов вообще | — | **«Пока нет заказов. Биржи опрашиваются каждые 15 минут.»** |
| Empty: нет лидов в нише | — | **«В этой нише пока нет заказов — попробуй «Все»»** + «Сбросить фильтры» |

---

### O96-Z3 — `/lenta/` logged-in

| Элемент | Канон O96 |
|---------|-----------|
| Status strip | **«N заказов под профиль · [⚙ Изменить навыки]»** |
| Sort — по дате | **«По дате ↓»** |
| Sort — по совместимости | **«По совместимости ↓»** |
| Карточка: match label (навыки есть) | **«Совместимость»** |
| Карточка: breakdown A | **«Навыки: Y%»** *(без «Качество заказа» — owner 2026-06-02)* |
| Карточка: match label (нет навыков) | **«Качество заказа»** |
| Карточка: breakdown B | **«Добавь навыки — увидишь совместимость →»** |
| 100% badge | **«ИДЕАЛЬНО ✦»** **KEEP** |
| Paid CTA | **«Написать отклик»** |
| Paid CTA tooltip (O89) | **«AI адаптирует формулировку под тебя»** |
| Empty: навыков нет | **«Добавь навыки — покажем заказы под твой стек.»** + «Добавить навыки» |
| Empty: нет совпадений | **«Пока нет заказов под твой профиль — попробуй расширить навыки.»** |

---

### O96-Z4 — Skill Tree sheet (⚙, cabinet + lenta)

> **⚠️ Superseded owner 2026-06-15** — manual picker снят · quiz-first · **нет** лимита 12 · канон → `feed-cabinet-mvp` §0.1 · `PRODUCT_CANON` §4.

| Элемент | Канон O96 (archive) |
|---------|-----------|
| Заголовок | ~~«Навыки»~~ → квиз / read-only профиль |
| Счётчик | ~~«Выбрано N / 12»~~ — **removed** |
| Hint / лимит 12 | **removed** |
| Subhead Разработка гр. 1 | **«ПО ЗАДАЧЕ»** |
| Subhead Разработка гр. 2 | **«ПО ТЕХНОЛОГИИ»** |
| L3 tray label | **«Уточнение (необязательно)»** |
| Кнопка сохранить (N=0) | **«Сохранить навыки →»** (disabled) |
| Кнопка сохранить (N≥1) | **«Сохранить навыки →»** |
| Loading | **«Сохраняем…»** |
| Success | **«Навыки сохранены ✓»** |
| Error | **«Ошибка — попробуй снова»** |
| Сбросить | **«Сбросить всё»** |
| Strip empty (после save, 0 навыков) | **«Добавь навыки для совместимости →»** |

---

### O96-Z5 — `/cabinet/` anon

| Элемент | Текущий prod | Канон O96 |
|---------|-------------|-----------|
| H1 | «Кабинет» | **KEEP** |
| Sub | «Войди через Telegram — навыки, отклики и уведомления в одном месте.» | **«Настроишь навыки — лента покажет заказы под твой стек. Черновик отклика — за один клик.»** |
| CTA primary | «Войти через Telegram» | **KEEP** |
| CTA secondary | «Или войти через @rawlead_bot →» | **KEEP** |

---

### O96-Z6 — `/cabinet/` free (вошёл, нет подписки)

| Элемент | Канон O96 |
|---------|-----------|
| Subscription block title | **«ИИ-агент»** |
| Subscription sub | **«Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.»** KEEP |
| Subscription price | **«300 ⭐ Stars / мес»** |
| Subscription CTA | **«Подключить →»** |
| Locked inbox title | **«Мои отклики»** |
| Locked inbox text | **«Черновики откликов — с подпиской ИИ-агент.»** |
| Locked inbox CTA | **«Тарифы →»** |
| Skills strip empty | **«Добавь навыки для совместимости →»** |

---

### O96-Z7 — `/cabinet/` paid

| Элемент | Канон O96 |
|---------|-----------|
| Subscription active | **«✅ ИИ-агент активна · [Пауза] [Управление]»** |
| Inbox title | **«Мои отклики (N)»** |
| Counter logged-in | **«N заказов под профиль»** |
| Inbox card expand | **«▼ Показать черновик»** / **«▲ Скрыть»** |
| Draft placeholder | **«Черновик появится после анализа»** |
| Draft O89 note (muted, под черновиком) | **«AI адаптирует формулировку под тебя»** |
| [Скопировать] | **«Скопировать текст»** |
| [Удалить] | **«Удалить из кабинета»** → confirm: **«Удалить?»** |
| Inbox empty (paid) | **«Откликнулся на ленте — черновик появится здесь.»** + «На ленту →» |

---

### O96-Z8 — `/pricing/`

| Элемент | Текущий prod | Канон O96 |
|---------|-------------|-----------|
| `<title>` | «Тарифы – RawLead» | **«Тарифы — RawLead»** (дефис→тире) |
| H1 | «Тарифы» | **KEEP** |
| Sub (дублирует карточку) | «Тариф ИИ-агент — 300 Telegram Stars/мес (~400–720 ₽)» | **«Один тариф. Всё включено.»** |
| Карточка title | «ИИ-агент» | **KEEP** |
| Цена | «300 ⭐ Stars / мес — при покупке Stars в Telegram это примерно 400–720 ₽ (зависит от пакета).» | **«300 ⭐ Stars в месяц — примерно 400–720 ₽ при покупке в Telegram.»** |
| Карточка sub | «Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.» | **KEEP** |
| Feature 1 | «Персональная лента по твоим навыкам» | **«Лента только с заказами под твой стек»** |
| Feature 2 | «Черновик отклика за одну кнопку» | **«Черновик отклика — ИИ пишет, ты правишь. Для каждого — своя формулировка.»** |
| Feature 3 | «Push в Telegram при новом матче» | **«Пуш в Telegram — только при хорошем совпадении»** |
| Payment note | «Оплата через Telegram Stars — @rawlead_bot /pay или кнопка «Оплатить Stars» в кабинете.» | **KEEP** |
| CTA | «Подключить — 300 ⭐ в Telegram →» | **KEEP** |
| Secondary links | «Вход в кабинет →» · «Смотреть ленту →» | **KEEP** |

---

### O96-Z9 — `/how/`

| Элемент | Текущий prod | Канон O96 |
|---------|-------------|-----------|
| `<title>` | «Как работает – RawLead» | **«Как работает — RawLead»** (дефис→тире) |
| H1 | «Как работает» | **KEEP** |
| Sub | «Три шага: от радара до твоего отклика» | **«Пять шагов: от биржи до твоего отклика»** |
| Шаг 1 title | «Указываешь навыки» | **KEEP** |
| Шаг 1 text | «Выбери свою нишу и добавь теги…» | **«Выбери нишу и добавь теги — дизайн, разработка, маркетинг, тексты. Чем точнее профиль, тем лучше совместимость.»** |
| Шаг 2 title | «Настраиваешь фильтры» | **«Настраиваешь профиль»** |
| Шаг 2 text | «Минимальная совместимость, источник, категория. Система запоминает твой профиль…» | **«Профиль хранит твои навыки. Лента автоматически подбирает заказы — менять настройки каждый раз не нужно.»** |
| Шаг 3 title | «Радар следит 24/7» | **KEEP** |
| Шаг 3 text | «Десятки источников проверяются автоматически. Дубликаты, спам…» | **KEEP** |
| Шаг 4 title | «Нейросеть мэтчит технологии» | **«ИИ читает суть заказа»** |
| Шаг 4 text | «Система не просто ищет ключевые слова…» | **«Система понимает задачу, решает, что нужно для её выполнения, и сверяет с твоим стеком.»** |
| Шаг 5 title | «Ты откликаешься сам» | **KEEP** |
| Шаг 5 text | «Готовый черновик отклика — поправить и отправить вручную…» | **«Черновик уже готов — для тебя написан отдельно. Поправь детали и отправь. Мы не пишем заказчикам за тебя.»** |
| Conclusion | «Один поток вместо десятка вкладок. Ты тратишь время на работу, а не на мониторинг.» | **KEEP** |

---

### O96-Z10 — `/faq/`

| Q | Заголовок | Канон ответа |
|---|-----------|-------------|
| 1 | «Это автоматическая рассылка заказчикам?» | **«Нет. RawLead только находит заказы и присылает тебе уведомление. Писать заказчикам — сам, в удобное время. Никакого автоспама.»** KEEP |
| 2 | «Подходит ли для нетехнических специалистов?» | **«Да. RawLead работает с четырьмя нишами: разработка, дизайн, маркетинг, тексты. Добавь свои навыки — ИИ найдёт подходящие заказы под твой профиль.»** |
| 3 | «Какие источники поддерживаются?» | **«FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет, Telegram-каналы. База расширяется.»** |
| 4 | «Нужен ли мой основной аккаунт Telegram?» | **«Да — для входа через кнопку на сайте или команду /login в @rawlead_bot. Аккаунт нужен только для авторизации, ничего без твоего ведома не отправляется.»** |
| 5 | «Не получу ли бан на бирже?» | **«Нет. Отклики пишешь ты — своими словами, в своё время. RawLead только подбирает заказы и черновик. Автоспама с твоего аккаунта нет.»** *(заменяет VPS, owner 2026-06-02)* |
| 6 | «Как начать пользоваться?» | **«Открой ленту заказов — регистрация не нужна. Чтобы настроить навыки и получать черновики откликов, войди через Telegram в кабинете.»** |
| 7 | «Сервис платный?» | **«Лента открыта бесплатно — смотри заказы без регистрации. Кабинет с ИИ-агентом (навыки, черновики, push) — 300 ⭐ Stars в месяц.»** |

---

### O96-Z11 — O97 Badge сложности (Концепт 2)

**Решение владельца 2026-06-02: Концепт 2 — emoji + слово + tooltip.**

| N | Badge | Tooltip (hover) |
|---|-------|-----------------|
| 1 | 🟢 Один вечер | «Скрипт, один файл, понятное ТЗ — вечер работы.» |
| 2 | 🟡 Проект | «Типовая архитектура — FastAPI, лендинг, бот. Понятно с первого прочтения.» |
| 3 | 🟠 Система | «Несколько компонентов или монолит с нормальным ТЗ. Потребует время на разбор.» |
| 4 | 🔴 Без норм ТЗ | «Нет нормального ТЗ, «сделайте красиво» или каша в описании. Риск на тебе.» |

**Расположение на карточке:** между match-bar и тегами (после breakdown row).  
**Copy «Сложность»:** label перед badge — «Сложность:» (Manrope 11px/600, muted).

---

### O96-Z12 — O89 Uniquify micro-copy

| Surface | Место | Copy |
|---------|-------|------|
| Карточка /lenta/ paid | Tooltip/note под кнопкой «Написать отклик» | **«AI адаптирует формулировку под тебя»** |
| /cabinet/ черновик | Muted note под текстом черновика | **«AI адаптирует формулировку под тебя»** |
| /pricing/ Feature 2 | Расширение описания | **«Для каждого — своя формулировка.»** (добавить к Feature 2) |
| /how/ Шаг 5 | Первое предложение | **«Черновик уже готов — для тебя написан отдельно.»** |

---

### O96-Z13 — Общие состояния (все страницы)

| Состояние | Copy |
|-----------|------|
| Загрузка initial | (skeleton, без текста) |
| Ошибка сети | **«Не удалось загрузить · [Попробовать снова]»** |
| Ошибка сохранения навыков | **«Ошибка — попробуй снова»** |
| Ошибка draft | **«Не удалось получить черновик · [Повторить]»** |
| FAB tooltip | **«Нашли ошибку?»** |
| Report bug modal title | **«Сообщить об ошибке»** |
| Report bug label | **«Что случилось?»** |
| Report bug placeholder | **«Опиши кратко — поможем разобраться»** |
| Report bug success | **«Спасибо. Посмотрим.»** |

---

**Handoff O96 ф2:**

```
@coder § O96-code
Copy: LEAD_PRODUCT_PROMPT.md § O96-Z1–Z13
UI: feed-cabinet-mvp.md §4.8 · §4.9 · §4.10 · §7.7
Deploy: 1.17.0 · O97 API (difficulty) → § O97-code после smoke
```

---

## § O94-v0.5 — Каталог навыков: research все 4 ниши (**✅ 2026-06-02**)

**Результат:** [SKILLS_TOOLS_CATALOG.md](SKILLS_TOOLS_CATALOG.md) **v0.5** · approve владельца 2026-06-02 · Q1=B · Q2=A · Q3=A · Q4=A · Q5=A.

| # | Deliverable | Статус |
|---|-------------|--------|
| 1 | 4 ниши: use-case + technology + L3 expand без parent/child каши | ✅ |
| 2 | Dev stacks: flask, scrapy, vue, nextjs, nodejs, typescript Tier B, react_native, flutter, laravel | ✅ |
| 3 | Design/Marketing/Text: subhead-группы (product_web, brand_graphics, video_motion, organic, paid_platform, commercial, editorial, language) | ✅ |
| 4 | Dedupe: figma + ui_ux оба Tier A (figma убрана из expand ui_ux); paid_platform — одна полка | ✅ |
| 5 | Merge-таблица approved | ✅ |

**Handoff: @lead-architect → O94-code Coder** (EXPAND_MAP v0.5 + picker_group subheads Design/Marketing/Text).  
**Параллельно:** Coder делает **O93-w2** (авто-L3 + лента modal) **без** новых тегов.

**Статус:** **✅ v0.5 сдан + approve владельца 2026-06-02** → handoff **O94-code** + **O94-L1** (см. `CODER_PROMPT`).

---

## § TAGS-V0.3 — каталог навыков (**O24, ✅ Product 2026-05-28**)

**Deliverable:** [`SKILLS_TOOLS_CATALOG.md`](SKILLS_TOOLS_CATALOG.md) **v0.3** — 51 тег, merge-таблица, L1-правила.

**Handoff:** `@coder` · `CODER_PROMPT.md` § **TAGS-V0.3** · **AI.md** v0.3 (t3-2).

---

## § MARKET-INTEL-B — Пивот B зафиксирован (2026-05-28)

**Источник:** [`MARKET_INTEL.md`](MARKET_INTEL.md) · согласовано с владельцем 2026-05-28.

### Решения владельца

| Параметр | Было | Стало |
|----------|------|-------|
| **Цена подписки** | «от 300 ₽/мес» | **590–990 ₽/мес** |
| **Позиционирование** | «ИИ-агент по подписке» | «Дешевле FL.ru PRO (1 270 ₽), умнее агрегаторов» |
| **Пивот C (эксклюзивные лиды)** | не определён | **отменён** — не нужна сложность |

### Новые фазы (добавлены в `PRODUCT_VISION.md` §4)

| Фаза | Срок | Суть |
|------|------|------|
| **3x Бадж «Горячий»** | **немедленно** (до/с P5) | `created_at < 5 мин` → красный badge; 0.5 дня Coder |
| **3f кнопка «Написать отклик»** | после PRE-PROD | **владелец = подписчик #0** → потом 3h; см. `CODER_PROMPT` § **3f-OWNER-BETA** |
| **3p Пауза подписки** | после 1-го платящего | `subs.paused_until TIMESTAMP` + крон; −30% churn |
| **3q Freemium hook** | после 50 юзеров | «3 матча бесплатно → потом реши» (не «149 ₽ триал») |

### Для `@lead-architect` → `@coder`

> **Задача 3x — Бадж «Горячий»:**
>
> На карточке лида в `/lenta/` и `/cabinet/`: если `NOW() - created_at < 5 минут` → показать badge «Горячий» (красный/оранжевый).
>
> - Бэкенд: `created_at` уже в `raw_leads`. В `/v1/feed` добавить поле `is_hot: bool` (или дать `created_at` и считать на фронте).
> - JS: badge-компонент в `rawlead-feed.js` / `rawlead-cabinet.js`.
> - CSS: один стиль `.rl-badge-hot` в `rawlead.css`.
> - Приоритет: **до** P5/деплоя или параллельно.

> **Задача 3p — Пауза подписки (после 1-го платящего):**
>
> - Neon: добавить `subs.paused_until TIMESTAMPTZ` (nullable).
> - Логика: если `paused_until > NOW()` — лид не получает платные функции Direction D, но данные сохраняются.
> - Крон / проверка при запросе: при `paused_until < NOW()` — возобновлять автоматически.
> - UI: кнопка «Пауза подписки» в `/cabinet/` — отложено до биллинга.

---

---

## FILTERS_SITE — критерии для /lenta/ под §0i (2026-05-27)

**Источники SITE:** только `fl`, `kwork` (+ TG whitelist) — **без** freelancehunt (2026-05-28).  
**Проблема:** `FILTERS_SITE.md` сейчас клон LEGACY: дизайн/маркетинг токены стоят в **стопе**, хотя для SITE они — целевые ниши §0i.

### Что убрать из СТОП в FILTERS_SITE (vs LEGACY)

| Токен (сейчас в стопе) | Почему убрать |
|------------------------|---------------|
| `figma`, `фигма` | ключевой токен Дизайн-ниши |
| `видеомонтаж`, `смонтировать`, `монтаж рилс` | Дизайн & Видео ниша |
| `motion design` | Дизайн & Видео ниша |
| `иллюстратор` | дизайн-задачи для сайтов/соцсетей |
| `фотошоп`, `photoshop` | дизайн-инструмент → в L1 |
| `логотип`, `баннер`, `дизайн макета`, `отрисовать` | Digital design → в L1 |
| `таргетолог`, `настройка таргет` | Маркетинг & SMM ниша |
| `ведение инстаграм` | SMM ниша |

### Что оставить в СТОП (одинаково SITE + LEGACY)

- Fraud: накрутка, лайки, отзывы за товар, самовыкуп, капча, крипта, mlm, казино
- Плагиат: дипломная, курсовая, реферат, контрольная, решебник, ниир, магистерск
- Оффер исполнителя: делаю сайты, предлагаю услуги, моё портфолио
- Рекрутинг: оклад от, в офисе, трудовой договор, hr-менеджер
- TG-спам: addlist, залетай в канал, полезная папка, зарегистрируйтесь в боте
- Безопасность: взлом, ddos, фишинг, слив базы
- Вне scope §0i: виртуальный ассистент, va , диктор, озвучка, голос за
- Не Digital freelance: 1с, битрикс, bitrix, сисадмин, windows server
- Не Design scope: рендеринг интерьер, архитектурная визуализация, ландшафтный дизайн
- Не Marketing scope: обзвон, холодные звонки
- Не Text scope: ручная транскрибац, расшифровка аудио вручную

### Берём (белый список — SITE расширяет на все 4 ниши)

| Ниша | Токены добавить/оставить |
|------|--------------------------|
| **Разработка & Код** | python, fastapi, django, webhook, api интеграц, телеграм бот, tg бот, скрипт, парсер, wordpress, html, css |
| **Дизайн & Видео** ← NEW | figma, ui/ux, ui ux, reels, shorts, монтаж, motion, after effects, premiere, анимация, видеомонтаж |
| **Маркетинг & SMM** ← NEW | таргет, контекст, яндекс директ, google ads, seo, smm, senler, salebot, прогрев, таргетолог |
| **Тексты & Переводы** ← NEW | копирайт, рерайт, локализац, редактур, субтитр, transcription, seo текст |

### Только L1 ai_score (пограничные — ИИ решает)

| Кластер | Почему L1, а не стоп |
|---------|----------------------|
| `логотип`, `баннер`, `дизайн макета` без web-контекста | Digital design vs полиграфия — L1 по ТЗ |
| `3d модел` без уточнения | character/explainer (в scope) vs архвиз (стоп) — L1 |
| `продвижение`, `реклама` без digital-канала | online vs offline — L1 |
| `автоматизация` без tech-контекста | Excel/бот (в scope) vs ручной труд (стоп) — L1 |
| `фотошоп`, `photoshop` | дизайн-инструмент — L1 |

**Порог L1 для SITE (в `ai_analyze.py` / PROFILE.md):**

| Ниша | MIN_AI_SCORE |
|------|-------------|
| Разработка & Код | **40** (конкретные ТЗ) |
| Дизайн & Видео, Маркетинг, Тексты | **50** (меньше конкретики → ИИ сомневается) |

### Для `@lead-architect` → `@coder`

> **Задача:** синхронизировать `docs/ops/FILTERS_SITE.md` и `src/filters.py` (SITE-профиль) под продуктовое решение выше.
>
> 1. В `FILTERS_SITE.md` убрать из стопа 8 токенов дизайн/маркетинг-ниш (таблица выше).
> 2. В `FILTERS_SITE.md` расширить белый список «Берём» блоками Дизайн, Маркетинг, Тексты.
> 3. В `src/filters.py` — профиль `site` использует FILTERS_SITE, а не FILTERS. Проверить что стоп-список обновлён.
> 4. Порог `MIN_AI_SCORE` для нетехнических ниш в site-профиле: `50` (см. `AI.md` / `ai_analyze.py`).
> 5. TG-секцию в FILTERS_SITE оставить (для будущего TG allowlist SITE), но она не применяется к fl/kwork/fh ingest.

---

## § SKILLS-TOOLS-RESEARCH — до Design и PM (2026-05-27)

**Промпт (как проводить):** [`SKILLS_TOOLS_RESEARCH_PROMPT.md`](SKILLS_TOOLS_RESEARCH_PROMPT.md) — механика match, «не терять вакансии», шаги, шаблон таблицы, вопросы для спора с владельцем.

**Зачем:** в ЛК и на `/lenta/` нужен **большой** осмысленный каталог навыков и инструментов по 4 специализациям §0i — не только top-50 тегов из уже попавших в Neon лидов (`GET /v1/skills/catalog`).

**Кто:** владелец + **@lead-product** (структура и приоритеты); опционально @coder — выгрузка/таблица для импорта.

| # | Готово когда |
|---|--------------|
| r1 | По каждой нише (dev, design, marketing, text): списки **навыков** (чипы match) и **инструментов** (отдельно от навыков, для L2 «Инструменты») |
| r2 | Правила: синонимы RU/EN, Tier A/B/C, что в UI vs только L1; дедуп |
| r3 | Источники зафиксированы (FL/Kwork, 10 реальных лидов, FILTERS_SITE, AI.md, опрос владельца) |
| r4 | Артефакт: `docs/team/product/SKILLS_TOOLS_CATALOG.md` — **согласовано с владельцем** |
| r5 | Handoff → @lead-designer § PRE-LAUNCH-UX v2 (E3 в [`TASKS.md`](../common/TASKS.md)) |

**Статус r1–r5: ✅ E2 закрыт (2026-05-27)**

| # | Статус |
|---|--------|
| r1 | ✅ Tier A/B по 4 нишам + инструменты в `SKILLS_TOOLS_CATALOG.md` |
| r2 | ✅ Синонимы RU/EN, Tier, shows_in_ui, дедуп |
| r3 | ✅ 25 реальных лидов из Neon, FILTERS_SITE, AI.md |
| r4 | ✅ Подтверждено владельцем 2026-05-27 |
| r5 | ✅ → @lead-designer E3 |

**Доп. задача E2b** (до Design, параллельно): § CANONICAL-TAGS выше → @lead-architect → @coder.

**Блокер:** без r1–r5 Design рисует UI под урезанный каталог.

---

## § CANONICAL-TAGS — L1 из пула + pending_tags (2026-05-27) — **E2b, перед E3**

**Решение владельца:** L1 тегирует заказы только из canonical_tag пула (`SKILLS_TOOLS_CATALOG.md`). Теги вне пула → `pending_tags` (не в UI). Catalog растёт органически.

**Почему важно до Design:** без этого match % = 0% для marketing/text у всех пользователей. Design нарисует фильтр — он не будет работать.

### Для `@lead-architect` → `@coder`

> **Задача E2b — L1 canonical pool + pending_tags**
>
> **Контекст:** `docs/team/product/SKILLS_TOOLS_CATALOG.md` — таблица навыков, колонка `canonical_tag`. L1 сейчас пишет произвольные теги на русском → match = 0% для нерусских canonical.
>
> **1. Neon — новая таблица `pending_tags`:**
> ```sql
> CREATE TABLE IF NOT EXISTS pending_tags (
>   id SERIAL PRIMARY KEY,
>   tag TEXT NOT NULL,
>   category TEXT,
>   first_seen_at TIMESTAMPTZ DEFAULT NOW(),
>   seen_count INT DEFAULT 1,
>   UNIQUE(tag)
> );
> ```
>
> **2. `docs/team/architect/AI.md` — промпт `analyze_lite`:**
> - Добавить блок «Разрешённые теги» — полный список `canonical_tag` из каталога (dev/design/marketing/text)
> - Инструкция: «выбирай теги **строго** из списка; если навык не покрыт — не добавляй»
> - Максимум 5 тегов на заказ
>
> **3. `src/pg_storage.py` или `src/ai_analyze.py`:**
> - После получения тегов от L1: разделить на `known` (есть в canonical_tag пуле) и `unknown`
> - `known` → `lead_tags` (как сейчас)
> - `unknown` → INSERT INTO `pending_tags` (ON CONFLICT → `seen_count + 1`)
>
> **4. `src/api_server.py`:**
> - `GET /v1/skills/catalog` — отдавать из хардкодированного каталога (или отдельной таблицы `skills_catalog`), **не** из агрегации `lead_tags`
> - Анон `/lenta/` навыки: **только сортировка** (не OR-фильтр). Параметр `skills=` меняет `final_rank`, но не убирает заказы из выдачи
>
> **5. Acceptance:**
> - Лид с «яндекс.директ» в тексте → `lead_tags` содержит `yandex_direct` (из пула), а не `яндекс.директ`
> - Лид с `tilda` → `pending_tags` увидит `tilda` (пока не в пуле) с `seen_count`
> - `GET /v1/skills/catalog` → теги из каталога, не из агрегации
> - Анон выбрал навыки → заказы остаются все, match-заказы выше

---

## § DESIGN-DIRECTION — новое направление (2026-05-27)

**Решение владельца ✅ 2026-05-28:** пересобрать визуальный стиль + структуру страниц (революция). Текущий REFERENCE (editorial B2B, Linear/Notion) — отменён.

**Аудитория:** фрилансер 25–35, работает в Telegram и на телефоне.

**Новое направление: «Рабочий инструмент»** — тёплый, прямой, mobile-first. Не SaaS, не биржа — как хорошее приложение.

### Product-бриф для @lead-designer

| Параметр | Новое |
|----------|-------|
| **Атмосфера** | Тёплый и практичный — «это работает», не «мы платформа» |
| **Фон** | Тёплый белый `#FAFAF8` (не холодный `#FFFFFF`) |
| **Шрифт** | Только **Manrope** — убрать Unbounded (слишком агрессивный для аудитории) |
| **Акцент** | Один цвет — **Indigo `#4F46E5`** вместо чёрных CTA (тёплый, отличается от FL/Kwork) |
| **Карточки** | Мягкая тень + больший border-radius — как мессенджер-карточка, не жёсткая рамка |
| **Mobile** | Mobile-first: большие зоны касания, минимум скролла, навигация снизу опционально |
| **Иконки категорий** | Простые line-иконки для dev / design / marketing / text |
| **Анимации** | Сохранить принцип (ease-out, no layout reflow), упростить — меньше «театра» |

### Тон голоса (Product канон — передать в REFERENCE)

- Прямой, активный залог: «ИИ убрал мусор», не «заказы были отфильтрованы»
- Без восклицательных знаков
- Mobile-метки: «Дизайн» вместо «Дизайн & Видео» в узком контейнере
- Кнопки называют действие: «Смотреть ленту», «Войти в кабинет» — не «Попробовать»

### Scope

**Эволюция (рекомендую):** новые токены + шрифты + карточки + mobile-first — структура страниц остаётся. ~3–4 дня Designer + Coder.

**Революция (если нужна новая структура страниц):** сказать Lead Designer явно — добавит к плану отдельный этап.

### Для `@lead-designer`

> Обнови `docs/design/wp/REFERENCE.md` под новое направление «Рабочий инструмент»:
> 1. Новые токены (см. таблицу выше) — фон, акцент, шрифт
> 2. Карточки — мягкая тень вместо жёсткой рамки
> 3. Mobile-first компоненты (лента, фильтры, кабинет)
> 4. Тон голоса — зафиксировать в REFERENCE §«Голос»
> 5. После: Coder обновляет CSS-переменные и компоненты

---

## § PRE-LAUNCH-UX — копирайт (**после** Design, 2026-05-27)

**Когда:** после согласования макета с владельцем ([`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § PRE-LAUNCH-UX v2). **Перед P5 / трафиком** (E4 в [`TASKS.md`](../common/TASKS.md)).

**Решение владельца (2026-05-27):** **нет** «закрытого тестирования», «оставьте заявку», «ранний доступ», waitlist. Продукт открыт: лента `/lenta/`, кабинет, dogfood владельца в TG. Тест — автоматом + лично владельцем, **не** отдельная маркетинговая фаза.

| # | Задача |
|---|--------|
| c1 | Подписи filter-bar: специализация, навыки, «Сбросить», «Совместимость N%» |
| c2 | Лента: заголовок, empty states, подсказки при 0 match |
| c3 | «Сообщить об ошибке»: заголовок, placeholder, success/thank you |
| c4 | **Убрать closed beta / early access:** FAQ, контакты, тариф, CTA — живые формулировки («Смотреть ленту», «Войти в кабинет», связь TG/email). См. список файлов ниже |
| c5 | Mobile: короткие версии тех же строк |
| c6 | Handoff → @coder (не дублировать в чат — только в этом файле + DESIGN addendum) |

**Где сейчас старый копирайт (Product правит канон строк → Coder в WP):**

| Файл | Что убрать/заменить |
|------|---------------------|
| `wordpress/rawlead-landing/content/faq.html` | «Идёт закрытое тестирование… Оставьте заявку… раннего доступа» |
| `wordpress/rawlead-landing/content/contact.html` | «оставьте заявку через форму» (если нет реальной формы — честный контакт) |
| `wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-preview.php` | «Ранний доступ», «участники раннего доступа» |
| `wordpress/rawlead-kadence-child/inc/marketing.php` | subtitle contact «Ранний доступ — Telegram или форма» |
| `wordpress/rawlead-kadence-child/functions.php` | CTA «Ранний доступ» на inner pages |

**Не путать:** § SKILLS-TOOLS `tier_b_only` / `early stage` — теги каталога, не маркетинг.

---

### Канон строк PRE-LAUNCH-UX copy (c1–c4) — E4 · 2026-05-28

Голос: активный залог · без «!» · **«ты»-форма** · кнопка = конкретное действие · мобайл = короткая метка.

---

#### c1 — Filter bar

**Специализация — категории:**

| Chip | Desktop | Mobile (< 375px) | API slug | Иконка |
|------|---------|------------------|----------|--------|
| — | Все | Все | — | — |
| 1 | Разработка | Код | `dev` | `</>` |
| 2 | Дизайн | Дизайн | `design` | `✦` |
| 3 | Маркетинг | SMM | `marketing` | `◎` |
| 4 | Тексты | Тексты | `text` | `Aa` |

**Кнопка «Навыки»:**

| Состояние | Текст |
|-----------|-------|
| Ничего не выбрано | «Навыки ▾» |
| N навыков выбрано | «Навыки · N ▾» |
| Заголовок панели | «Навыки» |
| Секция (ниша выбрана) | «По нише «{Ниша}»:» |
| Секция (все) | «Популярные навыки:» |
| Ещё навыки | Кнопка expand Tier B в picker; развёрнуто → «Свернуть» (не «редкие навыки») |
| Кнопка «Применить» | «Применить» |
| Tooltip «Применить» | «Порядок изменится. Заказы не исчезнут.» |
| Ссылка «Сбросить» в панели | «Сбросить» |

**Кнопка «Сортировка»:**

| Состояние | Текст |
|-----------|-------|
| По умолчанию | «Сортировка ▾» |
| Активна сортировка | «По совместимости ▾» |
| Вариант 1 | «Новые сначала» |
| Вариант 2 | «По совместимости» |

**Кнопка «Сбросить фильтры» (filter bar, появляется при активных фильтрах):** «Сбросить фильтры»

**Match на карточке (match-bar):** «Совместимость N%»

---

#### c2 — Лента: заголовки и empty states

**Заголовки страниц:**

| Страница | H1 | Счётчик (обычный) | Счётчик (навыки выбраны) |
|----------|----|-------------------|--------------------------|
| `/lenta/` | «Лента заказов» | «N заказов» | «N заказов · по совместимости» |
| `/cabinet/` | «Мои отклики» | — | — |

**Empty states:**

| Ситуация | Страница | Текст | CTA |
|----------|----------|-------|-----|
| Нет лидов вообще | `/lenta/` | «Пока нет заказов. Биржи обновляются каждые 15 минут.» | — |
| Нет лидов по категории | `/lenta/` | «В этой нише пока нет заказов — попробуй «Все»» | «Сбросить фильтры» |
| Inbox пуст (paid) | `/cabinet/` | «Здесь появятся заказы, по которым ты написал отклик на ленте.» | «На ленту →» |
| Inbox locked (free) | `/cabinet/` | «Черновики откликов — с подпиской ИИ-агент.» | «Тарифы →» |
| Нет навыков в профиле | `/cabinet/` | «Добавь навыки — на ленте точнее подберём заказы» | «Добавить навык» |
| Конец списка | `/lenta/` | «Все заказы показаны» | — |
| Конец inbox | `/cabinet/` | «Все отклики показаны» | — |
| Ошибка сети | обе | «Не удалось загрузить» | «Попробовать снова» |

**Подсказки анону при выбранных навыках** (лента не пустеет, только сортируется):
- Бейдж под filter bar после «Применить»: «Сортировка по совместимости»
- Tooltip «Применить»: «Порядок изменится. Заказы не исчезнут.»

---

## § TWO-SPEEDS-COPY — две скорости ленты (**O11**, для PM при наполнении сайта)

**Канон:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) §0j · решение владельца **O11**. **В коде пока нет** — тексты закладываем на design/copy волне; не обещать «мгновенно» на бесплатной ленте.

### Смысл одной фразой

**`/lenta/`** — единственная лента. **Anon/free:** ~15 мин, без отклика. **Paid:** мгновенно + «Написать отклик» на карточке → попадает в **inbox `/cabinet/`**.

### Где прописать (обязательно)

| Страница | Место | Черновик |
|----------|-------|----------|
| **`/lenta/`** (anon) | info-strip | «Новые заказы появляются через 15 мин. [Подписка](/pricing/) — без задержки.» |
| **`/lenta/`** (paid) | на карточке | кнопка **«Написать отклик»** |
| **`/cabinet/`** | заголовок inbox | «Мои отклики» (не «Мои заказы» / не match-лента) |
| **`/cabinet/`** | empty | «Здесь появятся заказы, по которым вы написали отклик на ленте.» |
| **`/pricing/`** | таблица | Скорость + «Черновик отклика в один клик» |
| **`/how/`** | шаг | лента → (paid) отклик → inbox в ЛК |

### Тон

- Без стыда и без «вы второго сорта» — **честно и коротко**
- Не путать с «биржи парсятся каждые 15 мин» (это про empty state c2 — **техническое** сообщение при пустой ленте)

---

#### c3 — «Сообщить об ошибке»

| Элемент | Текст |
|---------|-------|
| FAB tooltip | «Нашли ошибку?» |
| Заголовок modal / sheet | «Сообщить об ошибке» |
| Label поля | «Что случилось?» |
| Placeholder textarea | «Опиши кратко — поможем разобраться» |
| Поле URL (авто, readonly) | «Страница: {url}» |
| Кнопка отправки | «Отправить» |
| Success (автозакрытие 2с) | «Спасибо. Посмотрим.» |

---

#### c4 — Убрать closed beta / early access

**Правило:** нигде нет «закрытое тестирование», «ранний доступ», «оставьте заявку», «по приглашению».

| Файл | Было | Стало |
|------|------|-------|
| `faq.html` | «Идёт закрытое тестирование» / «Оставьте заявку на ранний доступ» | **Q:** «Как начать пользоваться?» **A:** «Откройте ленту заказов — регистрация не нужна. Кабинет — войдите через Telegram.» |
| `faq.html` | вопрос «Как попасть в бета-тест?» | **Q:** «Сервис платный?» **A:** «Лента открыта бесплатно. Кабинет с ИИ-агентом — по подписке. Тариф появится при запуске.» |
| `contact.html` | «оставьте заявку через форму» | «Напишите нам — в Telegram или через форму» · под формой: «Или напрямую →» [Telegram] |
| `pricing-preview.php` | CTA «Ранний доступ» | «Войти в кабинет →» → `/cabinet/` |
| `pricing-preview.php` | «участники раннего доступа получают специальные условия» | «Подписка — 300 ⭐ Stars / мес» |
| `pricing-preview.php` | Badge «Ранний доступ» | убрать badge |
| `marketing.php` subtitle contact | «Ранний доступ — Telegram или форма» | «Свяжитесь с нами — Telegram или форма» |
| `functions.php` inner pages CTA | «Ранний доступ» | «Смотреть ленту» |

---

#### c6 — Handoff → @lead-architect → @coder (E5)

> **Задача Coder — PRE-LAUNCH-UX copy:**
>
> Канон строк — `docs/team/product/LEAD_PRODUCT_PROMPT.md` § «Канон строк PRE-LAUNCH-UX copy (c1–c4)».
>
> **c1** — filter bar: метки категорий (desktop/mobile), кнопки «Навыки», «Сортировка», «Сбросить фильтры», подписи в панели навыков, match «Совместимость N%».
>
> **c2** — заголовки `/lenta/` + `/cabinet/`, все empty states, счётчик лидов (обычный + при выбранных навыках), tooltip «Применить».
>
> **c3** — modal «Сообщить об ошибке»: заголовок, label, placeholder, success «Спасибо. Посмотрим.» (без «!»), FAB tooltip.
>
> **c4** — замена в WP-файлах: `faq.html`, `contact.html`, `pricing-preview.php`, `marketing.php`, `functions.php` — точная таблица выше.
>
> Все строки — в PHP-шаблонах и JS (не в чате). Поверхности: `/lenta/`, `/cabinet/`, лендинг `/`.

**«Для кого» (лендинг):** 4 карточки ниш — канон строк в § «Канон «Для кого» — 4 карточки» (v0.10) · согласовано владельцем 2026-05-29. Live preview feed — **не дублировать** на главной.

**Статус c1–c4 + TWO-SPEEDS:** ✅ обновлён 2026-05-29 · «ты»-форма · Stars 300 ⭐ · 4 ниши · **→ E5** Coder

---

## Vision v0.10 — 4 категории Digital-специалистов (2026-05-26)

**Аудитория уточнена:** Digital-специалисты, 4 ниши — Разработка & Код · Дизайн & Видео · Маркетинг & SMM · Тексты & Переводы. Канон — `PRODUCT_VISION.md` **§0i**.

**Для `@lead-architect` (передать):**

> Vision обновлён до **v0.10**. Аудитория «все фрилансеры» → 4 конкретные ниши (§0i).
>
> 1. **`docs/ops/FILTERS.md`** — передать `@coder`: расширить стоп-слова по дропам каждой категории (1С/Битрикс/сисадмин; 3D рендеринг интерьеров; обзвоны/лайки/капча; дипломы/рефераты/ручная транскрибация). Расширить белый список словами ниш дизайна, маркетинга, текстов.
> 2. **`docs/ops/PROFILE.md`** — передать `@coder`: рекомендовать порог `ai_score` 50–55 для нетехнических ниш (дизайн, маркетинг, тексты) — меньше конкретики в ТЗ, ИИ чаще сомневается.
> 3. **Skills catalog в `/lenta/`** — передать `@coder`: теги сгруппировать по 4 категориям для UX.
> 4. **TG-каналы при расширении** — только с явной модерацией (атрибут источника). Сырые чаты без правил — не в публичную ленту.
> 5. **`STATUS.md`** — снять паузу ⏸, обновить Vision track: v0.10 ✅.
> 6. **Волна 2 копирайт (если не принято)** — обновить блок «Для кого» под 4 категории (было 3 карточки IT/Дизайн/Маркетинг — теперь 4). Канон строк — ниже.

### Канон «Для кого» — 4 карточки (замена блока «Волна 2», v0.10)

| # | Заголовок | Подтекст | Теги-примеры |
|---|-----------|----------|--------------|
| 1 | **Разработка & Код** | Боты, парсеры, FastAPI, веб — один поток вместо десятка вкладок. | Python · бот · парсер · автоматизация |
| 2 | **Дизайн & Видео** | UI/UX, Reels, монтаж, motion — заказы точно по вашим навыкам, без шума. | Figma · UI · монтаж · анимация |
| 3 | **Маркетинг & SMM** | Таргет, SEO, SMM, воронки — ИИ убирает нерелевантное до того, как вы открыли ленту. | таргет · SEO · SMM · контекст |
| 4 | **Тексты & Переводы** | Копирайтинг, локализация, редактура — только заказы под ваш профиль. | копирайт · перевод · редактура · субтитры |

---

## Волна 2 — продающие тексты (**→ сейчас**, Lead Design ✅ 2026-05-25)

**UX канон:** [`REFERENCE.md`](../../design/wp/REFERENCE.md) §3.1–3.2, §3.7 (W2: nav, hero, `#pricing-preview`).

**Владелец 2026-05-25:** тексты «не очень» + продукт **для всех фрилансеров**, не только IT (`PRODUCT_VISION` v0.9.3).

| Шаг | Действие | Статус |
|-----|----------|--------|
| 1 | Lead Design OK | ✅ |
| 2 | **@lead-product** — канон строк (hero, подзаголовок, «Для кого» 3 карточки **без** узкого IT, тариф, CTA) | **→ сейчас** |
| 3 | Согласование с владельцем | ✅ 2026-05-25 |
| 4 | Lead Architect → `CODER_PROMPT` § W2 | ✅ 2026-05-25 |
| 5 | **@coder** — nav/hero/якорь + тексты в теме | **→ сейчас** |

**Обязательно в копирайте:** FL/Kwork/TG/агрегаторы — **заказы для любой ниши**; skills в `/lenta/` — не «только dev».

---

## Волна 2 — канон строк (Lead Product, 2026-05-25)

> **Статус:** ✅ согласовано владельцем 2026-05-25 — передано Lead Architect (шаг 4)  
> **Файлы:** [`docs/archive/wp-skeleton/`](../../archive/wp-skeleton/) — переписаны полностью

### Hero

**H1:** Лиды без шума *(зафиксировано REFERENCE.md §3.2 — не меняем)*

**Подзаголовок** *(обновлено 2026-05-29: NEO-BRUTALIST голос, «ты»-форма)*:
> Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.

---

### Манифест — тёмная полоса (§3.4)

*(было: «Не сидите на бирже. Решайте по карточке в телефоне.» — «по карточке в телефоне» намекает на мобильное приложение)*

**Новый:**
> «Перестаньте мониторить. Начните откликаться.»

---

### Функции 01 · 02 · 03 (§3.5)

| # | Заголовок | Подтекст |
|---|-----------|----------|
| **01** | Один поток | Биржи, агрегаторы, Telegram-каналы — всё в одной ленте. Не нужно переключаться между вкладками и чатами. |
| **02** | ИИ-разбор | Каждый заказ оценивается до того, как вы его видите. Шлак, спам, реферальные схемы — не доходят до ленты. |
| **03** | Вы решаете | Подходящий заказ — пуш в Telegram. Откликаетесь сами. Мы не пишем заказчикам за вас. |

---

### Блок «Для кого» — 3 карточки (§3.6)

*(было: «Разработчики и верстальщики на Cursor / WordPress» — IT-only)*

| # | Заголовок | Подтекст | Примеры тегов |
|---|-----------|----------|----------------|
| 1 | **Дизайн и визуал** | Логотипы, UI/UX, иллюстрации, видеомонтаж — заказы точно по вашим навыкам, без шума дизайн-чатов. | дизайн · UI · иллюстрация · видео |
| 2 | **Тексты и маркетинг** | Копирайт, SMM, таргет, переводы, SEO — ИИ убирает нерелевантное ещё до того, как вы открыли ленту. | копирайт · SMM · таргет · SEO |
| 3 | **Разработка и автоматизация** | Сайты, боты, скрипты, интеграции — один поток вместо десятка вкладок. | разработка · бот · автоматизация |

---

### Тариф — карточка `#pricing-preview` (§3.7)

*(было: три тарифа Старт/Про/Команда — устарело с v0.8; сейчас один)*

| Поле | Канон |
|------|-------|
| **Название** | ИИ-агент |
| **Цена** | 300 ⭐ Stars / мес |
| **Подзаголовок** | *Для любой ниши — дизайн, тексты, код, маркетинг. ИИ знает твои теги.* |
| **Что включено** | Персональная лента по вашим навыкам · ИИ-оценка каждого заказа · Черновик отклика за одну кнопку · Рыночная цена заказа · Push в Telegram при новом матче |
| **CTA** | «Войти в кабинет →» → `/cabinet/` |
| **Badge** | — |
| **Строка под карточкой** | *Оплата через Telegram Stars прямо в боте.* |
| **Ссылка под карточкой** | «Смотреть ленту →» → `/lenta/` |

---

### CTA (сводно, UX без изменений)

| Место | Текст кнопки | Куда |
|-------|--------------|------|
| Hero primary | Смотреть ленту | `/lenta/` |
| Hero secondary | Смотреть тарифы ↓ | `#pricing-preview` |
| Шапка pill | Попробовать | `/lenta/` |
| Тариф | Войти в кабинет → | `/cabinet/` |
| Под тарифом | Смотреть ленту → | `/lenta/` |

---

### Страница «Как работает» (how.md)

- Шаг 1 переименован: *«Выбираете источники»* → **«Указываете навыки»** (профиль первичен)
- Список тегов: убрано «сайты, WordPress, боты» → **«дизайн, копирайт, разработка, маркетинг или любая другая специализация»**
- Убрана техническая сноска про Python/движок
- Добавлен вывод-мантра: *«Один поток вместо десятка вкладок. Вы тратите время на работу, а не на мониторинг.»*

### FAQ

- Вопрос «Подходит ли для WordPress-фрилансера?» → **«Подходит ли для нетехнических специалистов?»** (ответ: да, любая ниша)
- «Какие биржи? — FL.ru и Kwork» → **«Биржи, агрегаторы, Telegram-каналы; база расширяется»**
- Вопрос «Нужен ли VPS — с ПК на старте» → **«Нет. Сервис облачный»**

### Контакты

- Поле формы «WP / Python / дизайн» → **«дизайн / тексты / маркетинг / разработка / другое»**
- Убран блок «Для заказов на сайт» — не релевантен продукту RawLead

---

## Цель

Довести **uisness** до MVP первого контура — **открытая лента заказов на WP** (анон) + **персональный ЛК на Neon** (single-user пока, SaaS-ready) + **ИИ-агент** (рыночные цены, черновик отклика, push в TG). Параллельно — **личный ROI** через TG-бот владельца как dogfood.

**Ставка A (Контур 1 + витрина услуг) — отменена.** Витрина услуг (5 услуг на FL.ru, страница `/uslugi`, GitHub README, Habr-статья) — **отложены до выпуска MVP** или до подтверждения, что подписка не работает.

---

## Scope

| В scope | Вне scope |
|---------|-----------|
| WP `/feed` — открытая лента (anon, фильтры, поиск, сортировки) | Витрина услуг `/uslugi` на WP, FL.ru профиль с услугами, Habr-кейс — **до MVP** |
| WP `/cabinet` — персональная лента (пока `user_id=1`, владелец) | TG Login Widget (auth) — отложен до multi-user |
| Neon SaaS-ready схема: `raw_leads` + `users` + `user_tags` + `is_visible` | Биллинг (ЮKassa) — после 1-го внешнего юзера |
| ИИ-модерация на ingest (`is_visible`, `lead_tags`, `ai_score`) | Multi-user (регистрация, JWT) — после ИИ-агента работает на владельце |
| Парсеры **сайтов-агрегаторов** (§0h) | Habr/площадки напрямую (3j) — по ROI |
| TG raw в публичной ленте | **❌** — только владелец, потом 3k |
| ИИ-агент: рыночная цена + черновик отклика + push в TG (на владельце) | Тарифная сетка (один тариф «всё включено» 300–500 ₽/мес в MVP) |
| Анализ рынка для подписчиков (статистика тегов/бюджетов) — после ИИ-агента | Контент-маркетинг (Habr посты, SEO, рассылки) — до MVP |
| Vision v0.9: §0c (один поток + 4 направления вывода), §0d (горизонты B), §0e (3 ICP), §0f (главный продукт = подписка) | Mobile app, отдельный сайт-визитка, юристы до выручки |

---

## Готово когда (acceptance ставки B = MVP)

| # | Критерий | Источник проверки | Статус |
|---|----------|---------------------|--------|
| 1 | **Радар** — стабилен, минимум 50 валидных лидов/день после ИИ-модерации, < 30% шлака | счётчики в логе + личный TG-бот владельца | ⏳ |
| 2 | **Neon SaaS-ready схема**: `raw_leads`, `users`, `user_tags`, `subscriptions` с `user_id` во всех запросах | `sql/001_neon_schema.sql` + ревью | ⏳ |
| 3 | **WP `/feed`** — открытая лента, фильтры (источник, бюджет, теги), поиск, сортировки (новые/по rank), без регистрации | URL `radarzakaz.local/feed` (или продакшн) | ⏳ |
| 4 | **WP `/cabinet`** — владелец (user_id=1) видит match'и по своим тегам, sorted by `final_rank` | URL `/cabinet` | ⏳ |
| 5 | **ИИ-агент**: на карточке кнопка «Сгенерировать отклик» + расчёт рыночной цены работают; push в TG-бот владельца при новом match | живая проверка на владельце | ⏳ |
| 6 | Ingest **3i**: парсеры сайтов-агрегаторов (список от владельца) | Neon счётчики | ⏳ после волны 2 |
| 6b | **3k:** TG raw не в публичной ленте | `/lenta/` без owner_raw | ⏳ |
| 7 | **Личный ROI**: ≥ 3 закрытых заказа владельцем (≥ 3 500 ₽ каждый) — параллельный канал, не блокирует MVP | финансовый чек | ⏳ (продолжается) |
| 8 | `PRODUCT_VISION.md` v0.9 — зафиксировано | git diff | ✅ 2026-05-24 |

**После MVP** — пересмотр (см. ниже).

---

## Срок и пересмотр

Жёсткого таймера **нет** (заказов 0, юзеров 0 — таймер бессмысленный).

**Триггер пересмотра** (что наступит раньше):

- **Все 7 acceptance критериев выполнены** (MVP готов) → ретро + следующая инициатива (биллинг + multi-user + регистрация ИЛИ side-канал «услуги на FL.ru»)
- **6 недель после MVP** без платящих → **активация side-канала** (5 услуг на FL.ru, см. `PRODUCT_VISION.md` §0f) + Habr-кейс владельца

---

## Связь с vision

`PRODUCT_VISION.md` v0.5 → v0.6 → v0.7 → v0.8 → **v0.9** (последняя итерация 2026-05-24, **смена ставки A → B**):

- §0 Северная звезда — переписана: 3 канала ценности (dogfood / открытая лента / подписка)
- **§0a SaaS-ready с дня 1** — добавлено: `user_id` во всех таблицах, никаких хардкодов владельца
- §0b — целевая Neon-архитектура (без изменений с v0.4)
- **§0c — переписано целиком**: один поток + ИИ-модерация + 4 направления вывода (Direction A/B/C/D); поле `contour` отменено
- **§0d — пересмотр горизонтов под ставку B**: 0–2 нед / 2–4 нед / 1–3 мес / 3–6 мес; **5 пунктов acceptance MVP**
- **§0e — переписано**: 3 ICP, новые метрики (валидных лидов/день, % шлака, конверсии anon→free→paid)
- **§0f — переписано**: главный продукт = подписка ИИ-агент; 5 услуг → side-канал, активируется при триггере
- **§0g — упрощено**: всё после MVP, существующие активы переиспользуются как часть MVP, не как «портфолио»
- **§4 фазы — переписаны под B**: 3b / 3c / 3d / 3e / 3f → 3g / 3h
- §6 — расширены запреты (витрина услуг до MVP, переговоры с площадками, юристы, контент-маркетинг, тарифная сетка, хардкод владельца, поле `contour`)

---

## Декомпозиция (не ROADMAP — его пишет Lead Architect)

| Трек | Кому | Артефакт | Что от меня (Lead Product) |
|------|------|----------|----------------------------|
| Vision v0.9 | **Lead Product** (я) | `PRODUCT_VISION.md` | ✅ зафиксировано |
| Фазы под ставку B | **`@lead-architect`** | `ROADMAP.md` (по vision v0.9) | резюме ниже |
| **3b Neon SaaS-ready схема** | `@lead-architect` → `@coder` | `CODER_PROMPT.md` + `sql/` + `NEON_SCHEMA.md` | acceptance #2 |
| **3c REST API + WP `/feed`** | `@lead-architect` → `@coder` | `CODER_PROMPT.md` | acceptance #3 |
| **3d WP `/cabinet` single-user** | `@lead-architect` → `@coder` (заменяет старый § B) | `CODER_PROMPT.md` | acceptance #4 |
| **3e Habr Career парсер** | `@lead-architect` → `@coder` | `CODER_PROMPT.md` | acceptance #6 |
| **3f ИИ-агент** | `@lead-architect` → `@coder` | `CODER_PROMPT.md` | acceptance #5 |
| **UX `/feed` + `/cabinet`** (стиль REFERENCE E на новых страницах) | **`@lead-designer`** | `LEAD_DESIGN_PROMPT.md` → `DESIGNER_PROMPT.md` | резюме ниже |
| **Контур 1 dogfood** — закрытие заказов владельцем | владелец (читает свой бот) | `FOR_YOU.md` | параллельно MVP |

---

## Резюме для `@lead-architect` (передать в чате)

> Vision обновлён до **v0.9**, ставка сменилась с **A → B**. Старая модель «два контура» отменена.
>
> 1. **Перепиши `ROADMAP.md`** под новый список фаз 3b–3h (см. `PRODUCT_VISION.md` §4). Активные **сейчас**: 3b (Neon SaaS-ready) → 3c (REST + `/feed`) → 3d (`/cabinet` single-user) → 3e (Habr Career) → 3f (ИИ-агент). Всё ради **MVP первого контура** (5 пунктов §0d).
> 2. Поле `raw_leads.contour` (`owner` | `saas`) — **отменить** в схеме. Заменить на `is_visible` (после ИИ-модерации). См. `PRODUCT_VISION.md` §0c.
> 3. **Жёсткий constraint §0a SaaS-ready с дня 1**: каждая таблица с пользовательскими данными в Neon — с `user_id` (даже если =1 пока); никаких `OWNER_TG_CHAT_ID` хардкодов в логике агента/уведомлений/тегов; `/v1/...` API всегда принимает user-context.
> 4. `CODER_PROMPT.md` сейчас содержит § B (WP `/cabinet` MVP с JSON-фикстурой) — **переписать** под `/cabinet` через REST к Neon (single-user `user_id=1`).
> 5. Добавить новый трек: **Habr Career парсер** в `src/`. Только web-парсинг открытых URL, без API-переговоров.
> 6. **Не делать в этой инициативе**: TG Login Widget / биллинг ЮKassa / multi-user / SOURCES_SAAS.md / каталог услуг `/uslugi` / контент-маркетинг — всё после MVP. Файл `docs/ops/SOURCES_SAAS.md` можно архивировать.
> 7. [`PORTFOLIO.md`](PORTFOLIO.md) — устарел под v0.9: апдейт **после MVP** (зона Lead Architect).
> 8. STATUS.md — после каждой фазы синхронизировать с acceptance #1–#7 этого файла.

## Резюме для `@lead-designer` (передать в чате)

> Vision **v0.9** §0c — твоя зона на двух новых страницах WP. Каталог услуг `/uslugi` и FL.ru профиль — **выкинуты** из активного скоупа (см. §0g, всё после MVP).
>
> 1. **WP `/feed`** (открытая лента, anon) — стиль REFERENCE E (Unbounded/Manrope, светлый), токены **строго из** `DESIGN_SYSTEM.md` v1. Карточка лида: заголовок + источник + бюджет + теги + ai_score; фильтры (источник, бюджет min/max, теги); сортировка (новые / по rank); поиск по тексту. Бесконечный скролл или пагинация.
> 2. **WP `/cabinet`** (single-user, владелец = `user_id=1`) — те же токены; в карточке дополнительно **полоса match %** (синяя из REFERENCE), `final_rank` числом; страница «Мои теги» (8–12 chip, добавлять/удалять); кнопка «Сгенерировать отклик» (для §0c Direction D — после §0e ИИ-агент).
> 3. **Visual feedback ИИ-агента**: в карточке кнопка показывает рыночную цену («дёшево / нормально / дорого по рынку»), черновик отклика в модалке, индикатор «push отправлен в TG».
> 4. **Лендинг главная** — пока **не трогаем** (тексты «Тарифы» останутся как есть до запуска подписки; пересмотр — после MVP).
> 5. **Не делаем сейчас**: `/uslugi` страница, FL.ru тексты, Habr-статья, GitHub README, отдельный сайт-визитка, продающие тексты — всё после MVP.
>
> Что **уже сделано и переиспользуется**: WP лендинг ✅, пульт Tauri ✅ (внутренний), PNG-карта ✅ (внутренняя), DESIGN_SYSTEM ✅, REFERENCE.md ✅. Позиционирование владельца — пока не делаем витрину, поэтому позиционирование = «продукт работает»; маркетинг-тексты — после MVP.

---

_После выполнения acceptance #1–#7 — Lead Architect обновит `ROADMAP`/`STATUS`/`PORTFOLIO`, файл закроется или заменится новой инициативой (multi-user + биллинг ИЛИ side-канал «услуги на FL.ru», по результатам ретро MVP)._
