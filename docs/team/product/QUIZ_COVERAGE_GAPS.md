# Quiz coverage gaps — O221 research (2026-06-15)

**Источники:** Neon prod census (`is_visible=true`, 4 ниши) · `data/quiz_cards_v1.json` (56 cards) · `src/skills_catalog.py` · матрица `data/quiz_coverage_matrix.csv`

**Prod snapshot:** dev 691 · design 767 · marketing 552 · text 209 visible leads

---

## Executive summary

Квиз v1 покрывает **24** уникальных `skills_on_like` из **70** canonical tags и **12** signals (не 3 — в коде `QUIZ_SIGNALS` только 3/нишу, но карточки размазаны по 12 signal-id).

| Ниша | P0 tags (≥5% или ≥30 лидов) | P0 без квиза (`quiz_v1_skill=N`) | Критичные «нулевой match» (нет quiz и нет EXPAND) |
|------|----------------------------|----------------------------------|--------------------------------------------------|
| **dev** | 13 | 9 | **7** (server_admin, javascript, web_scraping, data_analysis, tilda_dev, ecommerce_dev, llm_integration) |
| **design** | 11 | 6 | **3** (presentation_design, threed_modeling, infographic_design) |
| **marketing** | 10 | 3 | **1** (marketplace_promotion) |
| **text** | 8 | 3 | **3** (translation, transcription, product_description) |

**Итого:** 14 canonical tags с частой prod-видимостью **не измеряются квизом** и **не достижимы через EXPAND_MAP** из текущих like-тегов → пользователь после квиза получает **0% match** на лиды с этими тегами. Это не баг match.

**Tier-A без квиза (P1):** `web_design` на dev-лидах (cross-tag), `javascript` на marketing-лидах, `google_ads` — нужны карточки или явное expand-only (owner).

---

## Top P0 gaps — примеры лидов (quiz не даёт тег)

### Dev (691 лидов)

| tag | prod % | quiz v1 | expand? | Пример lead |
|-----|--------|---------|---------|-------------|
| `server_administration` | 14.9% | N | N | **25477** — «Игровой сервер раст» · `server_administration`, `php` |
| `javascript` | 13.5% | N | N | **23456** — «Сендер на сайте» · `javascript`, `web_scraping`, `api_integration` |
| `html_css` | 15.3% | N | Y←`wordpress_dev` | expand-only если пользователь лайкнул WP |
| `php` | 12.3% | N | Y←`wordpress_dev` | expand-only |
| `web_scraping` | 8.7% | N | N | **25467** — «Навести порядок на сайте перед рекламой» · `web_scraping` |
| `data_analysis` | 6.7% | N | N | Tier-A use-case без signal в `QUIZ_SIGNALS` |
| `tilda_dev` | 5.8% | N | N | **25552** — «Сделать сайт на тильде» · `tilda_dev` |
| `ecommerce_dev` | 4.6% (32 лидов) | N | N | интернет-магазины |
| `llm_integration` | 4.6% (32 лидов) | N | N | Tier-A, ИИ-интеграции |

### Design (767 лидов)

| tag | prod % | quiz v1 | expand? | Пример lead |
|-----|--------|---------|---------|-------------|
| `illustration` | 15.0% | N | Y←`brand_identity` | **25555** — «Сделать апскейл фотографии» · `illustration` |
| `motion_design` | 12.3% | N | Y←`banner_design` | **25488** — монтаж Reels/Shorts · `video_editing`, `motion_design` |
| `presentation_design` | 9.3% | N | N | презентации / pitch deck |
| `threed_modeling` | 8.1% | N | N | 3D-моделирование |
| `web_design` | 6.1% | N | Y←`ui_ux` | **25222** — прототип сайта · `ui_ux`, `web_design`, `figma` |
| `infographic_design` | 5.4% | N | N | инфографика WB/Ozon |

Уже в квизе, но P0 по частоте: `video_editing`, `ui_ux`, `brand_identity`, `banner_design`, `logo_design` — нужно **больше anchor** (см. repetition).

### Marketing (552 лидов)

| tag | prod % | quiz v1 | expand? | Пример lead |
|-----|--------|---------|---------|-------------|
| `web_analytics` | 9.4% | N | Y←`seo` | GA4/Метрика — match только если user_tags содержит `seo` |
| `chatbot_marketing` | 6.0% | N | Y←`email_marketing` | Senler/Salebot воронки |
| `marketplace_promotion` | 6.0% | N | N | Ozon/WB продвижение |

В квизе: `content_marketing`, `smm`, `seo`, `email_marketing`, `target_ads` (1 card!), `technical_seo`, `yandex_direct`.

### Text (209 лидов)

| tag | prod % | quiz v1 | expand? | Пример lead |
|-----|--------|---------|---------|-------------|
| `translation` | 16.3% | N | N | **25538** — «Редакционные переводы» · `translation`, `editing_proofreading` |
| `transcription` | 14.8% | N | N | **25229** — «Логопед ребёнку 7 лет» · `script_writing`, `transcription` |
| `product_description` | 7.7% | N | N | описания для маркетплейсов |

Tier-A `translation` **полностью отсутствует** в v1 — системная дыра text-ниши.

---

## Quiz v1 repetition — почему 20 карточек «одно и то же»

### Распределение карточек по signal (v1)

| signal | niche | cards | types | skills_on_like |
|--------|-------|-------|-------|----------------|
| `ui_ux` | design | 6 | 4 anchor, 2 boundary | figma, ui_ux, banner_design, content_marketing |
| `python` | dev | 5 | 4 anchor, 1 boundary | python, api_integration, telegram_bot_dev |
| `smm` | marketing | 5 | 4 anchor, 1 boundary | smm, content_marketing, email_marketing, copywriting |
| `copywriting` | text | 4 | 3 anchor, 1 boundary | copywriting, sales_copywriting, script_writing, seo_copywriting |
| `article_writing` | text | 4 | 3 anchor, 1 boundary | article_writing, technical_writing, seo_copywriting |
| `seo` | marketing | 3 | 2 anchor, 1 boundary | seo, technical_seo, article_writing, seo_copywriting |
| `wordpress_dev` | dev | 3 | 2 anchor, 1 boundary | wordpress_dev, api_integration, figma |
| `api_integration` | dev | 2 | 2 anchor | api_integration, python |
| `video_editing` | design | 2 | 2 anchor | video_editing |
| `brand_identity` | design | 2 | 2 anchor | brand_identity, logo_design |
| `yandex_direct` | marketing | 2 | 2 anchor | yandex_direct |
| `editing_proofreading` | text | 2 | 2 anchor | editing_proofreading |

**Проблемы:**

1. **`QUIZ_SIGNALS` в коде = 3/нишу**, а карточек 12 signals → адаптивный роутер после 3-й карточки ниши **застревает на последнем signal** (`pick_signal_for_niche`: `signals[min(count, len-1)]`).
2. **`api_integration` signal — только 2 anchor-карточки**, но `python` signal отдаёт 6 like-тегов с пересечением `api_integration` → частые повторы одного сценария.
3. **`target_ads` — 1 карточка** при 6.9% prod (38 marketing лидов).
4. **`script_writing` — 1 карточка** при 9.6% prod text.
5. Phase-1 shuffle 4 ниш × 1 card = разнообразие ниш, но **не разнообразие навыков** внутри ниши.

---

## Recommended signals v2 (draft — owner approve)

Сигнал = измеряемый «якорь»; на каждый **новый** P0-signal без expand — ≥3 anchor + trap + boundary.

### Dev — добавить / усилить

| signal v2 | закрывает tag(s) | приоритет |
|-----------|------------------|-----------|
| `server_administration` | server_administration | P0 must |
| `javascript` | javascript (+ node ecosystem) | P0 must |
| `web_scraping` | web_scraping (+ telethon expand) | P0 must · уже Tier-A |
| `tilda_dev` | tilda_dev | P0 must |
| `data_analysis` | data_analysis, pandas | P0 must |
| `llm_integration` | llm_integration | P0 must · Tier-A |
| `ecommerce_dev` | ecommerce_dev, woocommerce, opencart | P0 must |
| `html_css` | html_css (или boundary под wordpress_dev) | P0 expand-only OK? |
| усилить `api_integration`, `wordpress_dev`, `python` | дублирующие P0 | +2 anchor each |

### Design — добавить / усилить

| signal v2 | закрывает tag(s) | приоритет |
|-----------|------------------|-----------|
| `illustration` | illustration | P0 |
| `motion_design` | motion_design | P0 |
| `presentation_design` | presentation_design | P0 must |
| `threed_modeling` | threed_modeling | P0 must |
| `infographic_design` | infographic_design | P0 must |
| `web_design` | web_design | P0 / expand ui_ux |
| `figma` | figma (Tier-A, 12 prod design) | P1 direct |
| усилить `video_editing`, `ui_ux`, `brand_identity` | +anchor | repetition fix |

### Marketing — добавить / усилить

| signal v2 | закрывает tag(s) | приоритет |
|-----------|------------------|-----------|
| `marketplace_promotion` | marketplace_promotion | P0 must |
| `chatbot_marketing` | chatbot_marketing | P0 |
| `web_analytics` | web_analytics | P0 / expand seo |
| `google_ads` | google_ads | P1 Tier-A |
| усилить `target_ads` | 1→≥3 cards | P0 frequency |
| `email_marketing` | chatbot expand path | +boundary |

### Text — добавить / усилить

| signal v2 | закрывает tag(s) | приоритет |
|-----------|------------------|-----------|
| `translation` | translation | P0 must · Tier-A |
| `transcription` | transcription | P0 must |
| `product_description` | product_description | P0 must |
| `script_writing` | script_writing | +2 anchor |
| `seo_copywriting` | direct Tier-A | +1 anchor |

---

## Card budget v2 + simulation spec

### Минимум на P0 signal (без expand-only)

| card_type | count | role |
|-----------|-------|------|
| anchor | ≥3 | разные контексты одного навыка |
| trap | ≥1 | похожий заказ, другой тег |
| boundary | ≥1 | соседний навык, не этот |

**~25 новых signals** × 5 cards ≈ **125** новых карточек + ревизия 56 v1 (убрать дубли, выровнять traps) → **целевой пакет ~170–200**.

### Pilot r6 (40 cards — 10/ниша)

Фокус только **quiz=N + expand=N + P0**:

| niche | 10 cards на signals |
|-------|---------------------|
| dev | `server_administration`, `javascript`, `web_scraping`, `tilda_dev` (2–3 each) |
| design | `presentation_design`, `threed_modeling`, `infographic_design`, `illustration` |
| marketing | `marketplace_promotion`, `target_ads` (+2), `chatbot_marketing` |
| text | `translation`, `transcription`, `product_description` |

### Simulation (pseudo-code)

```text
FOR path IN 1..100:
  history = simulate_quiz_v2(adaptive_router, card_pool_v2, seed=path)
  user_tags = tags_from_liked_cards(history)
  user_expanded = expand_user_tags_for_match(user_tags)

  sample_leads = random_visible_leads(n=50, categories=profile_niches(history))

  FOR lead IN sample_leads:
    lead_tags = canonical_tags(lead.lead_tags)
    overlap = lead_tags ∩ user_expanded
    match_pct = f(overlap, lead_tags, user_tags)  # текущая формула match

  RECORD per-niche: mean_match, pct_zero_match_on_P0_tags, tags_never_imported

ACCEPT v2 IF:
  - pct_zero_match_on_P0_tags < 15% (vs baseline v1 ~40%+ на translation/video_editing/server_admin)
  - each new P0 signal appears in ≥60% paths where niche selected
```

---

## Matrix notes

- Колонка `niche` = **категория лида** (prod census bucket).
- `catalog_niche` = категория тега в `SKILLS_TOOLS_CATALOG`.
- Cross-tags (e.g. `javascript` на design-лидах) — отдельные строки с prod% внутри ниши ленты.
- Полная матрица: `data/quiz_coverage_matrix.csv` (121 rows, все Tier-A + top-30 prod/niche).

---

## Handoff

```
@lead-product
Mechanic § O221-QUIZ-COVERAGE research ✅
Read: docs/team/product/QUIZ_COVERAGE_GAPS.md
Matrix: data/quiz_coverage_matrix.csv
Next: pilot 40 cards (10/niche) on P0 gaps · then quiz_cards_v2.json
Owner: approve signals v2 table § «Recommended signals v2» before card writing
```
