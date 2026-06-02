# SKILLS_TOOLS_CATALOG

Статус: **v0.5** deep research O94 · 2026-06-02 · **✅ approve владельца → @lead-architect → O94-code Coder**  
Предыдущий: ~~v0.4~~ (O93 spike, 3 уровня) → ниже  
Основа: `docs/team/product/SKILLS_TOOLS_RESEARCH_PROMPT.md`  
Параметры v0.5: **4 ниши · full stacks (Py/JS/PHP) · subheads Design/Marketing/Text · figma + ui_ux оба Tier A (убрать из expand) · paid_platform одна полка · typescript Tier B · 3 новых use_case · laravel L3**

---

## v0.5 — Deep research: расширенные стеки + subheads (O94 · 2026-06-02)

> **Гарды:** L1 промпт / judge / Neon-схема — **не меняем**. Только picker-конфиг + EXPAND_MAP в коде.  
> **Решения владельца 2026-06-02:** Q1=B · Q2=A · Q3=A · Q4=A · Q5=A — все приняты, отражены ниже.

---

### Dev — расширенные стеки

#### «По задаче» (use_case)

| picker_group | parent_id | label | tier | expand_to (L3) | v0.5 |
|---|---|---|---|---|---|
| use_case | `telegram_bot_dev` | Telegram-боты | **A** | aiogram, telethon | без изм. |
| use_case | `wordpress_dev` | WordPress | **A** | php, html_css | без изм. |
| use_case | `api_integration` | API интеграции | **A** | — | без изм. |
| use_case | `llm_integration` | ИИ-интеграция | **A** | — | без изм. |
| use_case | `web_scraping` | Парсинг сайтов | **A** | telethon, scrapy | + scrapy NEW |
| use_case | `mobile_dev` | Мобильные приложения | **B** | react_native, flutter | **NEW** |
| use_case | `data_analysis` | Анализ данных | **B** | pandas | **NEW** |
| use_case | `ecommerce_dev` | Интернет-магазины | **B** | woocommerce, opencart | **NEW** |

#### «По технологии» (technology)

| picker_group | parent_id | label | tier | expand_to (L3) | v0.5 |
|---|---|---|---|---|---|
| technology | `python` | Python | **A** | django, fastapi, flask, scrapy | + flask, scrapy NEW |
| technology | `javascript` | JavaScript | **A** | react, vue, nextjs, nodejs, typescript | + vue, nextjs, nodejs, typescript NEW |
| technology | `php` | PHP | **B** | laravel, woocommerce | + laravel, woocommerce NEW |
| technology | `typescript` | TypeScript | **B** | — | **NEW Tier B chip** (видим в «Ещё технологии»; лиды TS → also match js через expand) |

> **typescript:** Tier B самостоятельный чип в «По технологии» + остаётся в javascript expand_to — TS-лиды автоматически матчатся JS-разработчикам.  
> **scrapy:** cross-ref L3 — входит и в python, и в web_scraping.  
> **laravel:** возвращён явным L3 под php (был synonym-only в v0.3, Q3=A).

#### Полный EXPAND_MAP v0.5 (для Coder — заменить v0.4 целиком)

```python
EXPAND_MAP = {
  # --- DEV use_case ---
  "telegram_bot_dev": ["telegram_bot_dev", "aiogram", "telethon"],
  "wordpress_dev":    ["wordpress_dev", "php", "html_css"],
  "web_scraping":     ["web_scraping", "telethon", "scrapy"],
  "api_integration":  ["api_integration"],
  "llm_integration":  ["llm_integration"],
  "mobile_dev":       ["mobile_dev", "react_native", "flutter"],      # NEW
  "data_analysis":    ["data_analysis", "pandas"],                     # NEW
  "ecommerce_dev":    ["ecommerce_dev", "woocommerce", "opencart"],    # NEW
  # --- DEV technology ---
  "python":           ["python", "django", "fastapi", "flask", "scrapy"],
  "javascript":       ["javascript", "react", "vue", "nextjs", "nodejs", "typescript"],
  "php":              ["php", "laravel", "woocommerce"],
  "typescript":       ["typescript", "javascript"],   # Tier B: TS → also match js leads
  # --- DESIGN ---
  "ui_ux":            ["ui_ux", "web_design", "landing_page_design", "mobile_app_design"],
  # figma — Tier A standalone, НЕ в expand ui_ux (Q1=B)
  "figma":            ["figma"],
  "logo_design":      ["logo_design", "brand_identity"],
  "banner_design":    ["banner_design", "motion_design", "video_editing"],
  "brand_identity":   ["brand_identity", "illustration"],
  "video_editing":    ["video_editing", "motion_design"],
  # --- MARKETING ---
  "smm":              ["smm", "content_marketing"],
  "seo":              ["seo", "web_analytics", "technical_seo"],       # technical_seo NEW L3
  "email_marketing":  ["email_marketing", "crm_marketing"],
  "target_ads":       ["target_ads"],   # vk_ads убран из expand (Q4=A standalone)
  "yandex_direct":    ["yandex_direct"],
  "google_ads":       ["google_ads"],
  "vk_ads":           ["vk_ads"],       # standalone Tier B, НЕ дочерний target_ads
  # --- TEXT ---
  "copywriting":      ["copywriting", "sales_copywriting", "email_copywriting", "ux_writing"],
  "article_writing":  ["article_writing", "seo_copywriting", "technical_writing"],
  "translation":      ["translation"],
}
# Теги вне EXPAND_MAP: match по точному совпадению.
```

---

### Design — subhead-группы

**Решение figma / ui_ux (Q1=B, владелец 2026-06-02):**  
`figma` **остаётся Tier A** самостоятельным чипом. `ui_ux` — отдельный Tier A чип. Оба видны в picker.  
Убрать `figma` из `ui_ux` expand_to — нет скрытого дублирования в матче.

| picker_group | parent_id | label | tier | expand_to (L3) | v0.5 |
|---|---|---|---|---|---|
| product_web | `ui_ux` | UI/UX дизайн | **A** | web_design, mobile_app_design | figma убрана из expand |
| product_web | `figma` | Figma | **A** | — | Tier A standalone (Q1=B) |
| brand_graphics | `logo_design` | Логотипы & Бренд | **A** | brand_identity, illustration | без изм. |
| brand_graphics | `banner_design` | Баннеры & Реклама | **A** | motion_design, video_editing | без изм. |
| brand_graphics | `presentation_design` | Презентации | **B** | — | без изм. |
| video_motion | `video_editing` | Видеомонтаж | **B** | motion_design | **NEW subhead** |
| video_motion | `motion_design` | Моушн-дизайн | **B** | — | **NEW subhead** |
| video_motion | `threed_modeling` | 3D-моделирование | **B** | — | **NEW subhead** |

**Итого Design subheads:**
- **«Продукт & Web»** (`product_web`): ui_ux, figma · expand → web_design, mobile_app_design
- **«Бренд & Графика»** (`brand_graphics`): logo_design, banner_design · Tier B: presentation_design
- **«Видео & Моушн»** (`video_motion`): Tier B: video_editing, motion_design, threed_modeling

---

### Marketing — subhead-группы

**Решение google_ads / target_ads + vk_ads (Q4=A, владелец 2026-06-02):**  
Все три (`target_ads`, `yandex_direct`, `google_ads`) — Tier A на одной полке «По платформе».  
`vk_ads` — Tier B standalone на той же полке ниже. Убрать `vk_ads` из expand `target_ads`.

| picker_group | parent_id | label | tier | expand_to (L3) | v0.5 |
|---|---|---|---|---|---|
| organic | `smm` | SMM | **A** | content_marketing | **NEW subhead** |
| organic | `seo` | SEO | **A** | web_analytics, technical_seo | technical_seo NEW L3 |
| organic | `email_marketing` | Email-маркетинг | **A** | crm_marketing, chatbot_marketing | **NEW subhead** |
| organic | `marketplace_promotion` | Маркетплейсы | **B** | — | **NEW subhead** |
| paid_platform | `target_ads` | Таргет (Meta/IG) | **A** | — | vk_ads убран из expand |
| paid_platform | `yandex_direct` | Яндекс Директ | **A** | — | standalone |
| paid_platform | `google_ads` | Google Ads | **A** | — | standalone |
| paid_platform | `vk_ads` | ВКонтакте Ads | **B** | — | standalone Tier B (Q4=A) |

> `meta_ads` → синоним `target_ads` (Meta/Facebook/Instagram).  
> `technical_seo` → L3 в expand `seo` (TBD из v0.4 закрыт).

**Итого Marketing subheads:**
- **«Органика»** (`organic`): smm, seo, email_marketing · Tier B: marketplace_promotion
- **«По платформе»** (`paid_platform`): Tier A: target_ads, yandex_direct, google_ads · Tier B: vk_ads

---

### Text — subhead-группы

| picker_group | parent_id | label | tier | expand_to (L3) | v0.5 |
|---|---|---|---|---|---|
| commercial | `copywriting` | Копирайтинг | **A** | sales_copywriting, email_copywriting, ux_writing | **NEW subhead** |
| commercial | `seo_copywriting` | SEO-тексты | **A** | — | **NEW subhead** |
| commercial | `sales_copywriting` | Продающие тексты | **B** | — | Tier B в commercial |
| editorial | `article_writing` | Статьи & Блог | **A** | technical_writing | **NEW subhead** |
| editorial | `technical_writing` | Техдокументация | **A** | — | **NEW subhead** |
| editorial | `editing_proofreading` | Редактура | **A** | — | **NEW subhead** |
| editorial | `script_writing` | Сценарии | **B** | — | Tier B в editorial |
| language | `translation` | Перевод & Локализация | **A** | — | **NEW subhead** |
| language | `ux_writing` | UX-тексты | **B** | — | Tier B в language |
| language | `product_description` | Описания товаров | **B** | — | Tier B в language |

> `subtitles` / `субтитры` → синоним `translation`.

**Итого Text subheads:**
- **«Коммерческий текст»** (`commercial`): copywriting, seo_copywriting · Tier B: sales_copywriting
- **«Редактура & Публикации»** (`editorial`): article_writing, technical_writing, editing_proofreading · Tier B: script_writing
- **«Перевод & Локализация»** (`language`): translation · Tier B: ux_writing, product_description

---

### Merge-таблица v0.4 → v0.5 ✅ (approve владельца 2026-06-02)

#### Новые canonical_tags — все приняты

| canonical_tag | категория | tier | expand-источник | решение |
|---|---|---|---|---|
| `flask` | dev | L3 | python | ✅ |
| `scrapy` | dev | L3 | python + web_scraping | ✅ |
| `pandas` | dev | L3 | data_analysis | ✅ |
| `vue` | dev | L3 | javascript | ✅ (был synonym) |
| `nextjs` | dev | L3 | javascript | ✅ |
| `nodejs` | dev | L3 | javascript | ✅ (был synonym) |
| `typescript` | dev | **Tier B** chip | в javascript expand | ✅ Q2=A: Tier B + в expand js |
| `react_native` | dev | L3 | mobile_dev | ✅ |
| `flutter` | dev | L3 | mobile_dev | ✅ |
| `mobile_dev` | dev | B (use_case) | — | ✅ |
| `data_analysis` | dev | B (use_case) | — | ✅ |
| `ecommerce_dev` | dev | B (use_case) | — | ✅ Q5=A |
| `woocommerce` | dev | L3 | php + ecommerce_dev | ✅ |
| `opencart` | dev | L3 | ecommerce_dev | ✅ |
| `laravel` | dev | L3 | php | ✅ Q3=A: явный L3 |
| `technical_seo` | marketing | L3 | seo | ✅ |
| `meta_ads` | marketing | alias | target_ads | ✅ |
| `subtitles` | text | alias | translation | ✅ |

#### Изменения существующих тегов

| canonical_tag | было | стало | решение |
|---|---|---|---|
| `figma` | Tier A + в expand ui_ux | Tier A standalone; **убрана из expand ui_ux** | ✅ Q1=B |
| `ui_ux` expand | figma, web_design, … | web_design, mobile_app_design (без figma) | ✅ Q1=B |
| `target_ads` expand | google_ads, yandex_direct, vk_ads | **пусто** (все standalone) | ✅ Q4=A |
| `vk_ads` | Tier B (в expand target_ads) | **Tier B standalone**, не в expand | ✅ Q4=A |
| `typescript` | synonym javascript | **Tier B chip** + в expand javascript | ✅ Q2=A |

#### Новые picker_group (subhead-метки для UI)

| picker_group slug | ниша | лейбл в UI |
|---|---|---|
| `product_web` | design | «Продукт & Web» |
| `brand_graphics` | design | «Бренд & Графика» |
| `video_motion` | design | «Видео & Моушн» |
| `organic` | marketing | «Органика» |
| `paid_platform` | marketing | «По платформе» |
| `commercial` | text | «Коммерческий текст» |
| `editorial` | text | «Редактура & Публикации» |
| `language` | text | «Перевод & Локализация» |

> picker_group — только UI-конфиг; L1 / Neon-схема не меняются.

---

_Статус: **✅ v0.5 approved · 2026-06-02** · Handoff: `@lead-architect` → O94-code Coder_

---

## v0.4 — 3-уровневая иерархия (O93) [legacy]

Статус: **v0.4** spike O93 · 2026-06-02 · Product ✅ → @lead-architect → Coder  
Предыдущий: ~~v0.3~~ (51 тег, 2 уровня) → hierarchy ниже  
Основа: `docs/team/product/SKILLS_TOOLS_RESEARCH_PROMPT.md`  
Параметры v0.4: **4 ниши · 3 уровня · 2 UI-блока (use-case + technology) · parent match expand · L1/judge/Neon не меняем**

### Lead triage + owner rev (2026-06-02)

**Owner: вариант B (PM)** — **не** третий пункт «Гибрид минимальный»:
- dev picker: **«По задаче»** + **«По технологии»** (два subhead)
- **По технологии Tier A:** `python` (→ django, fastapi) **и** `javascript` (→ react)
- use-case Tier A: telegram_bot_dev, wordpress_dev, web_scraping, api_integration, llm_integration
- PM: «гибрид **выше**» в тексте B = два блока из «лучшего варианта», не option «Гибрид»

**PM dedupe (остаётся):** design/marketing parent/child · EXPAND_MAP standalone parents · `technical_seo` TBD.

---

## v0.4 — 3-уровневая иерархия (O93)

> **Legacy v0.3** (таблица ниже) — L1 canonical pool; **не** использовать для O93 picker layout.

### Концепт

| Уровень | Назначение | UI | Match |
|---------|------------|----|-------|
| **1 — Направление** | основной выбор пользователя | Tier A chips, всегда видно | выбор direction = match по всем expand_to |
| **2 — Стек** | опциональное уточнение | раскрывается под direction | — |
| **3 — Инструмент / либа** | узкая настройка, будущий отклик | только после выбора direction | — |

**Guardrail:** Level 1 «virtual» nodes = только UI-конфиг + expand-таблица в коде. L1 пишет canonical_tag на уровне стека/инструмента — не меняется.

---

### UI dev — два блока (owner **вариант B**)

| UI-блок | picker_group | Tier A parent_id | expand_to | L3 под parent |
|---------|--------------|------------------|-----------|---------------|
| **По задаче** | `use_case` | `telegram_bot_dev` | aiogram, telethon | aiogram, telethon |
| | | `wordpress_dev` | php, html_css | — |
| | | `web_scraping` | telethon | telethon |
| | | `api_integration` | — | — |
| | | `llm_integration` | — | — |
| **По технологии** | `technology` | `python` | django, fastapi | django, fastapi |
| | | `javascript` | react | react |

**Tier A dev chips (7):** 5× use_case + `python` + `javascript`.

**Не выбрано:** PM option «Гибрид» (python A, javascript Tier B only).

---

### Expand-таблица design

| parent_id (Level 1, Tier A) | label | expand_to | L2 стек | L3 |
|---|---|---|---|---|
| `ui_ux` | UI/UX дизайн | web_design, landing_page_design, mobile_app_design, figma | — | — |
| `logo_design` | Логотипы & Бренд | brand_identity | — | illustration, threed_modeling |
| `banner_design` | Баннеры & Медиа | motion_design, video_editing | — | — |
| `figma` | Figma | — | — | — |
| `brand_identity` | Фирменный стиль | illustration | — | threed_modeling |
| `presentation_design` | Презентации | — | — | — |

**Tier A design (6 слотов, без изменений):** `figma`, `ui_ux`, `web_design`, `logo_design`, `brand_identity`, `banner_design`

---

### Expand-таблица marketing

| parent_id (Level 1, Tier A) | label | expand_to | L3 |
|---|---|---|---|
| `target_ads` | Таргет & Реклама | google_ads, yandex_direct, vk_ads | — |
| `seo` | SEO | web_analytics, content_marketing | — |
| `email_marketing` | Email-маркетинг | crm_marketing | chatbot_marketing |
| `smm` | SMM | content_marketing | chatbot_marketing |
| `yandex_direct` | Яндекс Директ | — | — |
| `google_ads` | Google Ads | — | — |

**Tier A marketing (6 слотов, без изменений):** `smm`, `target_ads`, `yandex_direct`, `google_ads`, `seo`, `email_marketing`

---

### Expand-таблица text

| parent_id (Level 1, Tier A) | label | expand_to | L3 |
|---|---|---|---|
| `copywriting` | Копирайтинг | sales_copywriting, email_copywriting, ux_writing | — |
| `article_writing` | Статьи & Блог | seo_copywriting, technical_writing | — |
| `translation` | Перевод | — | — |
| `editing_proofreading` | Редактура | — | — |
| `technical_writing` | Технические тексты | — | — |
| `seo_copywriting` | SEO-тексты | — | — |

**Tier A text (6 слотов, без изменений):** `copywriting`, `seo_copywriting`, `article_writing`, `translation`, `technical_writing`, `editing_proofreading`

---

### Правила match expand (для Coder)

```
EXPAND_MAP = {
  # dev
  "telegram_bot_dev": ["telegram_bot_dev", "aiogram", "telethon"],
  "wordpress_dev":    ["wordpress_dev", "php", "html_css"],
  "web_scraping":     ["web_scraping", "telethon"],
  "api_integration":  ["api_integration"],
  "llm_integration":  ["llm_integration"],
  "python":           ["python", "django", "fastapi"],
  "javascript":       ["javascript", "react"],
  # design
  "ui_ux":            ["ui_ux", "web_design", "landing_page_design", "mobile_app_design", "figma"],
  "logo_design":      ["logo_design", "brand_identity"],
  "banner_design":    ["banner_design", "motion_design", "video_editing"],
  "brand_identity":   ["brand_identity", "illustration"],
  # marketing
  "target_ads":       ["target_ads", "google_ads", "yandex_direct", "vk_ads"],
  "seo":              ["seo", "web_analytics", "content_marketing"],
  "email_marketing":  ["email_marketing", "crm_marketing"],
  "smm":              ["smm", "content_marketing"],
  # text
  "copywriting":      ["copywriting", "sales_copywriting", "email_copywriting", "ux_writing"],
  "article_writing":  ["article_writing", "seo_copywriting", "technical_writing"],
}
# Теги вне EXPAND_MAP: match по точному совпадению (без expand).
# parent всегда включён в свой expand_to.
```

---

### Acceptance (O93 spike)

- [x] 3-уровневая иерархия зафиксирована (dev — канон; design/marketing/text — dedupe parent/child)
- [x] EXPAND_MAP draft для Coder — static config, не Neon
- [x] Guardrail: L1 / judge / Neon schema не меняем
- [x] Owner **вариант B (PM):** 2 UI-блока · python **и** javascript Tier A в «Пo технологии»
- [x] @lead-architect review spike
- [x] @lead-designer O93-w1 wireframes (`feed-cabinet-mvp` §4.6)
- [x] Coder: keyword_match expand + tree UI /cabinet/ + /lenta/
- [ ] Smoke + E2E (владелец)

---

---

## Навыки v0.3 (51 тег: Dev 15 · Design 13 · Marketing 12 · Text 11)

**Tier A** — основной picker (shows\_in\_ui: yes, max 6 на нишу)  
**Tier B** — блок **«Ещё навыки»** в picker (shows\_in\_ui: tier\_b\_only; UX-copy, не «редкие»)  
**subgroup** — подгруппа внутри ниши (заполнено для dev; в Design/Marketing/Text — прочерк)

| canonical\_tag | category | subgroup | tier | title\_ru | synonyms (internal) | shows\_in\_ui | notes |
|---|---|---|---|---|---|---|---|
| python | dev | — | A | Python | py, питон, python3 | yes | backend, scripts, ML |
| javascript | dev | — | A | JavaScript | js, node.js, nodejs, node, нода, vue, vue.js | yes | покрывает node\_js, vue\_js |
| php | dev | — | A | PHP | пхп, laravel, ларавел | yes | web CMS + frameworks; покрывает laravel |
| wordpress\_dev | dev | Веб | A | WordPress разработка | wp dev, вордпресс разработка, плагин wp | yes | skill, не tool; cross\_niche=yes |
| telegram\_bot\_dev | dev | Боты | A | Telegram-боты | telegram bot, телеграм бот, тг бот | yes | cross\_niche=yes; покрывает telegram\_bot\_marketing |
| api\_integration | dev | — | A | API интеграции | rest api, интеграция api, webhook, sql, postgresql, mysql, база данных | yes | backend integrations + DB; покрывает sql |
| aiogram | dev | Боты | B | aiogram (Python) | aiogram bot, python telegram bot, asyncio telegram, телеграм бот aiogram | tier\_b\_only | **NEW** — Python async TG bot framework |
| telethon | dev | Боты | B | Telethon (юзербот/парсер) | telethon python, userbot, юзербот, парсер tg | tier\_b\_only | **NEW** — Python TG user client |
| react | dev | Веб | B | React | reactjs, реакт | tier\_b\_only | frontend SPA |
| django | dev | Веб | B | Django | джанго, django rest, drf | tier\_b\_only | Python web framework |
| fastapi | dev | Веб | B | FastAPI | фастапи, python api | tier\_b\_only | Python API framework |
| html\_css | dev | Веб | B | HTML/CSS | верстка, вёрстка, frontend markup | tier\_b\_only | markup/styling |
| tilda\_dev | dev | Веб | B | Tilda | tilda site, тильда, tilda разработка | tier\_b\_only | very frequent FL/Kwork |
| llm\_integration | dev | ИИ | B | ИИ-интеграция | openai api, gpt api, langchain, ai integration, claude api, llm, нейросеть, интеграция ai, ai\_integration | tier\_b\_only | **RENAMED** от ai\_integration; max 1 тег ИИ на лид |
| web\_scraping | dev | — | B | Парсинг сайтов | scraping, парсер, сбор данных, веб-скрейпинг | tier\_b\_only | automation tasks |
| figma | design | — | A | Figma | фигма, wireframes, прототипирование | yes | покрывает wireframing |
| ui\_ux | design | — | A | UI/UX дизайн | ui ux, ux/ui, ux audit, user research | yes | покрывает ux\_research |
| web\_design | design | — | A | Веб-дизайн | website design, дизайн сайта, сайт дизайн | yes | landing + corp sites |
| logo\_design | design | — | A | Логотипы | logotype, логотип, лого | yes | most common freelance |
| brand\_identity | design | — | A | Фирменный стиль | брендбук, айдентика | yes | branding |
| banner\_design | design | — | A | Баннеры/креативы | ads creatives, баннеры, рекламные баннеры | yes | ads production |
| landing\_page\_design | design | — | B | Дизайн лендинга | лендинг дизайн, landing design | tier\_b\_only | high-frequency |
| mobile\_app\_design | design | — | B | Дизайн мобильных приложений | app design, mobile ui | tier\_b\_only | product/mobile |
| presentation\_design | design | — | B | Презентации | pitch deck, дизайн презентации | tier\_b\_only | b2b demand |
| motion\_design | design | — | B | Моушн-дизайн | motion, анимация, after effects, ae | tier\_b\_only | often paired with video |
| video\_editing | design | — | B | Видеомонтаж | монтаж видео, edit video, premiere, монтаж reels | tier\_b\_only | social creatives |
| illustration | design | — | B | Иллюстрации | illustration design, иллюстратор | tier\_b\_only | optional niche |
| threed_modeling | design | — | B | 3D-моделирование | 3d model, blender, cinema 4d, 3д моделирование, 3d персонаж, 3d анимация | tier\_b\_only | **RETURNED** — только explainer/character/лого 3D; архвиз = стоп (см. L1-правило ниже) |
| smm | marketing | — | A | SMM | social media marketing, смм, ведение соцсетей | yes | social management |
| target\_ads | marketing | — | A | Таргетированная реклама | таргет, paid social, таргетолог, реклама инстаграм | yes | meta/vk focused |
| yandex\_direct | marketing | — | A | Яндекс Директ | директ, yandex ads, яндекс.директ, я.директ, контекстная реклама | yes | покрывает ppc (RU) |
| google\_ads | marketing | — | A | Google Ads | google adwords, гугл реклама, ppc google | yes | global channel |
| seo | marketing | — | A | SEO | сео, search optimization, продвижение сайта | yes | core inbound |
| email\_marketing | marketing | — | A | Email-маркетинг | рассылки, email рассылка, crm mailings, email automation | yes | покрывает email\_automation (dev) |
| vk\_ads | marketing | — | B | Реклама ВКонтакте | vk ads, реклама вк, вк реклама | tier\_b\_only | был Tier A → **demoted** |
| content\_marketing | marketing | — | B | Контент-маркетинг | контент стратегия, content plan, контент план | tier\_b\_only | editorial + social |
| web\_analytics | marketing | — | B | Веб-аналитика | ga4, аналитика сайта, яндекс метрика | tier\_b\_only | measurement |
| marketplace\_promotion | marketing | — | B | Маркетплейсы | ozon, wb, wildberries, маркетплейс | tier\_b\_only | vertical demand |
| chatbot\_marketing | marketing | — | B | Маркетинг-боты | senler bot, salebot funnels, чат-бот воронка | tier\_b\_only | tg/vk funnels; cross\_niche=yes |
| crm\_marketing | marketing | — | B | CRM-маркетинг | crm сегментация, lifecycle email, ретаргетинг | tier\_b\_only | retention |
| copywriting | text | — | A | Копирайтинг | тексты, writing, текст на заказ | yes | broad commercial text |
| seo\_copywriting | text | — | A | SEO-копирайтинг | seo тексты, оптимизированные тексты | yes | search content |
| article\_writing | text | — | A | Статьи/блог | blog posts, лонгриды, статьи | yes | editorial |
| translation | text | — | A | Перевод | localization, перевод текстов, локализация | yes | ru-en and more |
| technical\_writing | text | — | A | Технические тексты | документация, technical docs, техническое задание | yes | it/docs |
| editing\_proofreading | text | — | A | Редактура и корректура | proofreading, вычитка, корректура | yes | polish content |
| sales\_copywriting | text | — | B | Продающие тексты | sales pages, рекламные тексты, продающий текст | tier\_b\_only | funnels/landing |
| script\_writing | text | — | B | Сценарии | video script, сценарий reels, сценарий ролика | tier\_b\_only | media content |
| product\_description | text | — | B | Описания товаров | ecom карточки, карточки товаров, marketplace text | tier\_b\_only | ecommerce |
| email\_copywriting | text | — | B | Тексты для email | email sequence, письмо-воронка | tier\_b\_only | retention copy |
| ux\_writing | text | — | B | UX-райтинг | microcopy, тексты интерфейсов | tier\_b\_only | product/ui |

---

## Merge-таблица v0.2 → v0.3

| v0.2 canonical\_tag | v0.3 статус | Замена / примечание |
|---|---|---|
| ai\_integration | **→ RENAMED** | `llm_integration` (расширены synonyms: gpt, claude, langchain) |
| node\_js | → удалён | synonym → `javascript` |
| laravel | → удалён | synonym → `php` |
| vue\_js | → удалён | synonym → `javascript` |
| sql | → удалён | synonym → `api_integration` |
| docker | → удалён | только в таблице Инструменты |
| email\_automation | → удалён | synonym → `email_marketing` (marketing) |
| ppc | → удалён | synonyms → `yandex_direct` + `google_ads` |
| wordpress\_marketing | → удалён | cross\_niche: `wordpress_dev` |
| telegram\_bot\_marketing | → удалён | cross\_niche: `telegram_bot_dev` |
| influencer\_marketing | → удалён | вне scope §0i |
| conversion\_rate\_optimization | → удалён | нишевый |
| vk\_ads | **Tier A → B** | существует, понижен |
| ux\_research | → удалён | synonym → `ui_ux` |
| wireframing | → удалён | synonym → `figma` |
| typography | → удалён | нишевый |
| threed\_modeling | **RETURNED → Tier B** | explainer/character/лого 3D — в пуле; архвиз — стоп |
| naming | → удалён | нишевый |
| transcription | → удалён | borderline scope (см. FILTERS стоп-лист) |
| resume\_cv\_writing | → удалён | вне scope §0i |
| aiogram | **NEW** | Python async Telegram bot framework |
| telethon | **NEW** | Python Telegram user client / парсер |

---

## Изменения L1-промпта (для `AI.md` → `@coder`)

### Пул и лимит
1. **max 6 тегов на лид** (было: max 5)
2. **Список разрешённых тегов** обновить: добавить `aiogram`, `telethon`, `threed_modeling`; заменить `ai_integration` → `llm_integration`
3. **Удалить из пула:** все canonical_tag из merge-таблицы со статусом «удалён» (18 штук)

### Правила категоризации (нужно прописать явно в промпте)

| Правило | Что делает L1 |
|---------|---------------|
| **Ниша обязательна** | Каждый лид получает ровно одну category: `dev` / `design` / `marketing` / `text`. Если сомнение — выбрать ближайшую, не оставлять пустой |
| **Телеграм-бот** | Если ТЗ про разработку бота → `telegram_bot_dev` (dev). Если про воронку/рассылку в TG → `chatbot_marketing` (marketing) |
| **WordPress** | Если разработка/кастомизация темы/плагина → `wordpress_dev` (dev). Если «сделать сайт на WP» без кода → `web_design` (design) |
| **3D-моделирование** | Персонаж, анимация логотипа, explainer → `threed_modeling` (design). Архитектурная визуализация, интерьер, ландшафт → **стоп, не тегировать** |
| **ИИ-интеграция** | Работа с openai/gpt/claude/langchain/llm → только `llm_integration` (не добавлять `api_integration` одновременно) |
| **Парсинг** | Парсинг сайтов/данных → `web_scraping` (dev). Юзербот/парсер Telegram → `telethon` (dev) |
| **Таргет vs SMM** | «Настроить таргет/директ/ads» → `target_ads` или конкретный канал. «Вести соцсети/контент» → `smm` |
| **Копирайт vs SEO-текст** | Нет упоминания SEO → `copywriting`. Явно SEO-текст/продвижение → `seo_copywriting` |

### Правило «один ИИ-тег»
Если в лиде есть openai/gpt/langchain/claude → ставить только `llm_integration`, не добавлять `api_integration` одновременно.

### Инструменты (L2 карточки — отдельно от тегов)
L1 **не выдаёт инструменты как теги** — инструменты (Figma, Photoshop, After Effects, Premiere и т.д.) попадают в поле `tools_required` карточки, **не** в `lead_tags`. Таблица инструментов ниже — только для L2-контекста.

---

## ⚠️ Критические находки (валидация шаг 3, 2026-05-27, архив)

| Проблема | Влияние | Кто чинит |
|----------|---------|-----------|
| L1 пишет рус. теги (`яндекс.директ`), canonical — EN (`yandex_direct`) → match = 0% | Match сломан для marketing/text у всех | @coder: добавить synonym map в `keyword_match` ИЛИ обновить L1-промпт выводить canonical_tag → `AI.md` |
| `text` category содержит 3D/Blender/парсинг; `dev` — нейминг, описания | Пользователь-копирайтер видит 3D-заказы | @coder: уточнить границы категорий в L1-промпте (`AI.md`) |
| `tilda` и `vk_ads` отсутствуют в каталоге | Частые реальные заказы → 0 match | Добавлено ниже в v0.2 |

## Как пользоваться фильтром, чтобы не резать ленту

Выбирай **до 6** ключевых навыков под текущий тип заказов. Больше чипов — лента сузится; оптимум **4–6** Tier A.

## Навыки v0.2 (архив, заменён v0.3 выше)

| canonical_tag | category | tier | title_ru | synonyms | shows_in_ui | notes |
|---------------|----------|------|----------|----------|-------------|-------|
| python | dev | A | Python | py, питон | yes | backend automation, scripts |
| javascript | dev | A | JavaScript | js, джаваскрипт | yes | web frontend |
| react | dev | A | React | reactjs, реакт | yes | dedup reactjs/react |
| node_js | dev | A | Node.js | node, нода | yes | backend js |
| php | dev | A | PHP | пхп | yes | web legacy + wp |
| wordpress_dev | dev | A | WordPress разработка | wp dev, вордпресс разработка | yes | skill, не tool |
| laravel | dev | A | Laravel | ларавел | yes | php framework |
| telegram_bot_dev | dev | A | Telegram-боты | telegram bot, телеграм бот | yes | cross-niche dev/marketing |
| api_integration | dev | A | API интеграции | rest api, интеграция api | yes | backend integrations |
| sql | dev | A | SQL | postgresql, mysql, скл | yes | db queries |
| web_scraping | dev | B | Парсинг сайтов | scraping, веб-скрейпинг, парсер, сбор данных | tier_b_only | automation niche |
| docker | dev | B | Docker | докер | tier_b_only | often tool in L2 too |
| django | dev | B | Django | джанго | tier_b_only | python framework |
| fastapi | dev | B | FastAPI | фастапи | tier_b_only | python api |
| vue_js | dev | B | Vue.js | vue, вью | tier_b_only | frontend alt |
| html_css | dev | B | HTML/CSS | верстка, frontend markup | tier_b_only | common, but still useful |
| ai_integration | dev | B | Интеграция AI | openai api, llm integration | tier_b_only | growing demand |
| tilda_dev | dev | B | Tilda разработка | tilda, тильда, tilda site | tier_b_only | very frequent on FL/Kwork |
| email_automation | dev | B | Email-автоматизация | email рассылка, email integration, шаблоны писем | tier_b_only | dev side of email |
| ui_ux | design | A | UI/UX дизайн | ui ux, ux/ui | yes | base design tag |
| web_design | design | A | Веб-дизайн | website design, дизайн сайта | yes | landing + corp sites |
| figma | design | A | Figma | фигма | yes | skill + tool |
| landing_page_design | design | A | Дизайн лендинга | лендинг дизайн, landing design | yes | high-frequency |
| mobile_app_design | design | A | Дизайн мобильных приложений | app design, mobile ui | yes | product/mobile |
| banner_design | design | A | Баннеры/креативы | ads creatives, баннеры | yes | ads production |
| brand_identity | design | A | Фирменный стиль | брендбук, айдентика | yes | branding |
| presentation_design | design | A | Презентации | pitch deck, дизайн презентации | yes | b2b demand |
| logo_design | design | A | Логотипы | logotype, логотип | yes | common freelance request |
| motion_design | design | B | Моушн-дизайн | motion, анимация | tier_b_only | often paired with AE |
| video_editing | design | B | Видеомонтаж | монтаж видео, edit video | tier_b_only | social creatives |
| ux_research | design | B | UX-исследования | user research, ux audit | tier_b_only | product depth |
| wireframing | design | B | Вайрфреймы | прототипирование, wireframes | tier_b_only | early stage |
| typography | design | B | Типографика | шрифты, type design | tier_b_only | support skill |
| illustration | design | B | Иллюстрации | illustration design, иллюстратор | tier_b_only | optional niche |
| threed_modeling | design | B | 3D-моделирование | 3d model, blender, 3д моделирование | tier_b_only | explainer/character 3D only; архвиз — стоп |
| smm | marketing | A | SMM | social media marketing, смм | yes | social management |
| target_ads | marketing | A | Таргетированная реклама | таргет, paid social, таргетированная реклама | yes | meta/vk focused |
| vk_ads | marketing | A | Реклама ВКонтакте | vk ads, реклама вк, вк реклама, вконтакте реклама | yes | dominant RU social ads |
| yandex_direct | marketing | A | Яндекс Директ | директ, yandex ads, яндекс.директ, я.директ | yes | ru core channel |
| google_ads | marketing | A | Google Ads | google adwords, гугл реклама | yes | global channel |
| seo | marketing | A | SEO | сео, search optimization | yes | core inbound |
| ppc | marketing | A | PPC | контекстная реклама, paid search | yes | performance marketing |
| email_marketing | marketing | A | Email-маркетинг | рассылки, crm mailings | yes | retention/acquisition |
| content_marketing | marketing | A | Контент-маркетинг | контент стратегия, content plan | yes | editorial + social |
| web_analytics | marketing | A | Веб-аналитика | ga4, аналитика сайта | yes | measurement |
| marketplace_promotion | marketing | B | Продвижение маркетплейсов | ozon, wb, wildberries | tier_b_only | vertical demand |
| influencer_marketing | marketing | B | Инфлюенсер-маркетинг | блогеры, influencer ads | tier_b_only | campaign niche |
| crm_marketing | marketing | B | CRM-маркетинг | сегментация crm, lifecycle | tier_b_only | retention |
| conversion_rate_optimization | marketing | B | CRO/конверсия | оптимизация конверсии, cro | tier_b_only | paired with analytics |
| chatbot_marketing | marketing | B | Маркетинг-боты | senler bot, salebot funnels | tier_b_only | tg/vk funnels |
| wordpress_marketing | marketing | B | WordPress (маркетинг) | wp сайт, wordpress сайт | tier_b_only | cross-niche dev/marketing |
| telegram_bot_marketing | marketing | B | Telegram-боты (маркетинг) | telegram bot, телеграм бот, тг бот | tier_b_only | cross-niche dev/marketing |
| copywriting | text | A | Копирайтинг | тексты, writing | yes | broad commercial text |
| seo_copywriting | text | A | SEO-копирайтинг | seo тексты, оптимизированные тексты | yes | search content |
| sales_copywriting | text | A | Продающие тексты | sales pages, рекламные тексты | yes | funnels/landing |
| editing_proofreading | text | A | Редактура и корректура | proofreading, вычитка | yes | polish content |
| article_writing | text | A | Статьи/блог | blog posts, лонгриды | yes | editorial |
| technical_writing | text | A | Технические тексты | документация, technical docs | yes | it/docs |
| translation | text | A | Перевод | localization, перевод текстов | yes | ru-en and more |
| script_writing | text | A | Сценарии | video script, сценарий reels | yes | media content |
| product_description | text | B | Описания товаров | ecom карточки, marketplace text | tier_b_only | ecommerce |
| naming | text | B | Нейминг | brand naming, название бренда | tier_b_only | branding niche |
| email_copywriting | text | B | Тексты для email | email sequence, письмо-воронка | tier_b_only | retention copy |
| ux_writing | text | B | UX-райтинг | microcopy, тексты интерфейсов | tier_b_only | product/ui |
| transcription | text | B | Транскрибация | speech-to-text, расшифровка | tier_b_only | service niche |
| resume_cv_writing | text | B | Резюме/CV | cv writing, резюме на заказ | tier_b_only | personal services |

## Инструменты

| tool_label | category | tier | title_ru | related_skills | notes |
|------------|----------|------|----------|----------------|-------|
| VS Code | dev | A | VS Code | javascript, python, node_js | IDE |
| PyCharm | dev | B | PyCharm | python, django, fastapi | IDE |
| Postman | dev | A | Postman | api_integration, testing_api | API testing |
| Docker | dev | A | Docker | docker, devops_basics | L2 infrastructure |
| GitHub | dev | A | GitHub | git_workflow, code_review | repo collaboration |
| GitLab | dev | B | GitLab | git_workflow, ci_cd | alt repo |
| WordPress | dev | A | WordPress | wordpress_dev, php | CMS platform |
| Shopify | dev | B | Shopify | ecommerce_dev, theme_customization | ecommerce platform |
| Figma | design | A | Figma | figma, ui_ux, wireframing | design core |
| Adobe Photoshop | design | A | Adobe Photoshop | banner_design, photo_editing | raster graphics |
| Adobe Illustrator | design | A | Adobe Illustrator | brand_identity, illustration | vector graphics |
| Adobe After Effects | design | B | Adobe After Effects | motion_design, animation | motion/video |
| Adobe Premiere Pro | design | B | Adobe Premiere Pro | video_editing, montage | video editing |
| Canva | design | A | Canva | social_creatives, quick_design | fast production |
| Framer | design | B | Framer | prototyping, landing_page_design | interactive prototypes |
| Meta Ads Manager | marketing | A | Meta Ads Manager | target_ads, ppc | ads platform |
| Google Ads | marketing | A | Google Ads | google_ads, ppc | ads platform |
| Яндекс Директ | marketing | A | Яндекс Директ | yandex_direct, ppc | ads platform |
| Google Analytics 4 | marketing | A | GA4 | web_analytics, conversion_rate_optimization | analytics |
| Яндекс Метрика | marketing | A | Яндекс Метрика | web_analytics, seo | analytics ru |
| Ahrefs | marketing | B | Ahrefs | seo, keyword_research | seo suite |
| Semrush | marketing | B | Semrush | seo, competitor_research | seo suite |
| Senler | marketing | B | Senler | chatbot_marketing, crm_marketing | vk ecosystem |
| Salebot | marketing | B | Salebot | chatbot_marketing, funnel_automation | bot funnels |
| Google Docs | text | A | Google Docs | copywriting, editing_proofreading | text collaboration |
| Notion | text | A | Notion | content_planning, technical_writing | knowledge workflows |
| Grammarly | text | B | Grammarly | editing_proofreading, translation | language quality |
| ChatGPT | text | B | ChatGPT | ideation, draft_generation | assistant tool |
| DeepL | text | B | DeepL | translation, localization | translation |
| Otter.ai | text | B | Otter.ai | transcription, editing_proofreading | transcription |

## Глоссарий UX (для Design + Product)

| Термин в UI | Значение для пользователя |
|-------------|---------------------------|
| Специализация | В какой нише ищешь заказы (можно 1-2) |
| Навыки | Что умеешь; влияет на совместимость и на фильтр |
| Совместимость | Насколько заказ похож на твой профиль, не оценка качества |
| Применить | Уточнить ленту по выбранным навыкам (может скрыть часть заказов) |
| Ещё навыки | Расширенный список Tier B (кнопка в picker; развёрнуто → «Свернуть») |
| Редкие навыки | Узкие теги, чаще нужны ИИ для разметки, чем UI-чипы |

## Вопросы на подтверждение с владельцем

1. Нужны ли группы синонимов уже в v1 `keyword_match` или оставляем точное совпадение canonical tag.  
   **Решение v1:** оставляем точное совпадение canonical tag.  
   **Комментарий:** синонимы нужны в research/L1 для нормализации в canonical, но не как отдельная логика match в API.
2. Для публичной `/lenta/` навыки работают только как сортировка или как фильтр тоже.  
   **Решение v1:** как фильтр тоже (AND не вводим; текущая логика OR по пересечению сохраняется).
3. Как обрабатываем кросс-нишевые навыки (`wordpress_dev`, `telegram_bot_dev`) при выборе двух специализаций.  
   **Решение v1 (рекомендация):**\n+   - кросс-нишевые теги помечаем `cross_niche=yes`; \n+   - при выборе нескольких специализаций показываем объединение навыков выбранных ниш (OR); \n+   - кросс-нишевые навыки показываем отдельным блоком «Сквозные навыки», чтобы их было легко найти.
4. Инструменты в ЛК как поле профиля или только отображение в L2 карточки.  
   **Решение v1:** инструменты не добавляем в профиль пользователя; показываем в L2 карточки (`tools_required`).  
   **Почему:** профиль держим простым (специализации + навыки), инструменты остаются контекстом конкретного заказа.  
   **v2 опция:** позже можно добавить «Любимые инструменты» как подсказку для генерации отклика.

## Вопрос к владельцу — финальный (нужен ответ для r4)

**Q: Анон на /lenta/ выбирает навыки — фильтр или сортировка?**
**Решение владельца (2026-05-27): Б — только сортировка.** Все заказы остаются в ленте, заказы с совпавшими тегами выше. Лента никогда не пустеет.
_Текущий код: OR-фильтр → нужно изменить под сортировку для анона. Задача @coder (см. ниже)._

**Q: Кросс-нишевые навыки (wordpress, telegram_bot) — дублировать в несколько ниш?**
**Решение владельца (2026-05-27): да, дублируем.** Навык показывается во всех релевантных нишах.

## Задачи для @coder (по итогам валидации + решений владельца)

| # | Задача | Файл | Приоритет |
|---|--------|------|-----------|
| 1 | L1-промпт: тегировать из canonical_tag пула (этот каталог) — только теги из списка, строго | `docs/team/architect/AI.md` → промпт `analyze_lite` | P0 |
| 2 | L1-промпт: уточнить границы категорий (text ≠ 3D, dev ≠ нейминг) | `docs/team/architect/AI.md` | P0 |
| 3 | Анон /lenta/: навыки — только сортировка (не OR-фильтр) | `src/api_server.py`, `src/rank.py` | P1 |
| 4 | pending_tags таблица: теги от L1 не из пула → в очередь, не в UI | Neon + `src/pg_storage.py` | P1 (если владелец выбрал вариант Б) |

_Передать через @lead-architect → CODER_PROMPT._

## Чеклист приёмки

- [x] По каждой нише есть Tier A (8-15 навыков).
- [x] Нет дублей canonical tags и мусорных общих чипов.
- [x] Для Tier A/B заполнены `synonyms` и `shows_in_ui`.
- [x] Ясно разделены skills (match/filter) и tools (L2 context).
- [x] Подтверждено на 25 реальных лидах (шаг 3 research, 2026-05-27).
- [x] Ответ владельца: анон /lenta/ — **сортировка** (Б).
- [x] Ответ владельца: кросс-нишевые — **дублируем**.
- [x] Ответ владельца: L1 canonical pool — **пул + pending_tags (Б)** (2026-05-27).
- [x] Владелец подтвердил каталог (r4) ✅ 2026-05-27 → handoff @lead-designer.
