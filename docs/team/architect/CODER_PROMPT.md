# Coder — горячий контур (активное)

**→ Сейчас:** **O72e freeze done** (send 60.6%) · r11 опционально · **UI/UX → @lead-architect** параллельно

**Gate:** L1 usable ≥70% · L2 combined ≥4.0 · **L2 send ≥70%** · L3 ✅

---

## § O72e-L2-r10 — #12148 stack conflict ✅ (**2026-06-04**)

**Контекст:** единственный FAIL в w2 (10 worst) — judge штрафует за PHP в **tools_required** карточки при NestJS/Nuxt в ТЗ.

**Coder/Lead:** правило «Конфликт tools_required vs Описание» · якорь #12148 (endpoints, webhooks, Nuxt components) · BAD/GOOD · test `test_shared_l2_r10_12148_stack_conflict` · regen #12148.

**Spot judge #12148:** текст отклика без PHP ✅ · judge send **FAIL** — rubric видит PHP в поле tools_required (не в draft). **Не блокер** для freeze при w2 90%.

**VPS deploy:** `deploy-o72e-l2-r9-vps.py` (с grep r10) — после approve.

**Freeze (ласт прогон):**

```powershell
.venv\Scripts\python.exe scripts\regen_shared_reply_drafts.py --profile site --apply --limit 71 --since 2026-06-01 --json-out data/regen_o72e_a_freeze.json

.venv\Scripts\python.exe scripts\preprod_ai_prod_audit.py --profile site --limit 71 --judge --judge-limit 71 --judge-l1 --judge-l1-limit 71 --judge-l3 --judge-l3-limit 25 --judge-since 2026-06-01 --judge-md-out data/preprod_ai_prod_audit_judge_o72e_a_freeze.md
```

---

## § O72e-L2-r9 — L2 send gate ✅ (**2026-06-04**, tests 25/25)

**Сдача Coder:** `l3_human_style.py` + `test_shared_l2_r9_w1_send_gate` · L1 complexity hardening в промпте (было r8) · **#12602 perf tags** — не делали (optional, L1 gate ✅).

**Lead next:** deploy → regen w2 → judge w2.

---

## § O72e-L2-r9 — L2 send gate (spec, archived)

**Judge w1 (2026-06-04, since 2026-06-01, n=40 L2):**

| Метрика | Факт | Gate |
|---------|------|------|
| combined | **4.2** | ✅ ≥4.0 |
| specificity | 3.8 | — |
| universal_helpful | 3.88 | — |
| **send_as_is** | **50%** | ❌ **≥70%** |

L1 ✅ · L3 ✅ (92%). **Блокер — L2:** отклики **короткие**, без **этапов**, **tools_required** не названы или **подменены** (Midjourney не из списка).

**Источник:** [`data/preprod_ai_prod_audit_judge_o72e_a_w1.md`](../../../data/preprod_ai_prod_audit_judge_o72e_a_w1.md) · regen w1: [`data/regen_o72e_a_w1.json`](../../../data/regen_o72e_a_w1.json) (21 id).

**Scope:** только промпт + unittest. **Без** OpenRouter, regen, judge, VPS — Lead после сдачи.

---

### A. L2 — `src/l3_human_style.py` → `build_shared_l2_system`

#### A1. Блок «Структура send-ready» (после Substance-first)

```text
## Структура send-ready (≥4 предложения для «Брать»)
1. **Якорь** — 1 фраза: что именно из title/Описания берёшь (цифра, платформа, объект).
2. **Этапы** — **2–3 шага через «→» или запятую** (не «готов начать» без содержания):
   «анализ ТЗ → макет/код → тест/сдача» — подставь домен из заказа.
3. **Инструменты** — **≥1 имя из tools_required** (Figma, PHP, Excel, Illustrator, TON API…), если релевантно типу заказа (см. creative/text — dev-tools игнорируй).
4. **Финал** — **1 вопрос** по реальному пробелу **или** «По ТЗ учту: A, B, C» без «?».

FAIL send: только вопрос о стеке; «готов присоединиться»; <4 предложений при полном ТЗ.
```

#### A2. Блок «tools_required — жёстко»

```text
## tools_required — сверка перед ответом
- Прочитай tools_required (первые 3). **Каждый релевантный** — **назови по имени** в отклике.
- **Запрещено** инструмент **не из** tools_required и не из Описания (пример FAIL: Midjourney в отклике, если только Figma/HTML в tools).
- **design-tools** (Figma, Illustrator, Photoshop, PowerPoint, Excel) — **называй** даже в text/design, если в tools_required и нужны для работы (книга → Excel для структуры; презентация → PowerPoint).
- **dev-tools** (PHP, WordPress, Python) — только если заказ **tech/dev**; в creative/text — правило #8772.
- **Стек из Описания:** не подменяй (если в ТЗ NestJS+ Nuxt — не пиши только PHP; если PHP в tools — назови PHP).
```

#### A3. Domain-якоря w1 (добавить в Specificity + BAD/GOOD)

| id | Заказ | Что добавить в промпт |
|----|-------|------------------------|
| **#9366** | TON mini app | TON API, смарт-контракты, NFT metadata, Web Apps — **не** только «какой стек?» |
| **#10442** | AI дизайн сайта | Figma + **HTML/CSS** из tools; Midjourney **только** если в tools/Описании; вилка Figma vs вёрстка |
| **#11332** | WP каталог | PHP, таксономии, фильтры/поиск, API если в ТЗ; этапы: анализ референса → тема → навигация |
| **#10001** | WP верстка по фото | этапы: разбор фото-макета → вёрстка → интеграция; Elementor vs классическая тема |
| **#9875** | книга/редактура | **Excel** для структуры глав; этапы: записи → структура → редактура → шлифовка |
| **#12148** | Яндекс Доставка | стек **как в ТЗ** (Nuxt/NestJS); API методы, webhooks, ЛК — не выдумывай другой стек |
| **#10291** | сайт-визитка | SEO для .ru, формы (PHP/JS), этапы; не только «тексты готовы?» |
| **#10009** | Elementor+Woo | каталог, корзина, checkout, платежи — **этапы**, не только LCP/CLS |
| **#9328** | презентация 17 слайдов | PowerPoint + Photoshop/Figma для графики; процесс согласования; тематика слайдов |
| **#9320** | акварель открытки | Illustrator/Photoshop, CMYK, вылеты под печать |

**Примеры GOOD (кратко, вставить в BAD/GOOD):**

```text
GOOD (#11332): «…Настрою каталог на WordPress: кастомная тема или доработка, таксономии категорий и районов, фильтры и поиск. PHP для кастомных полей, если понадобится API — подключу. Сначала разберу референс → затем шапка и навигация. Где посмотреть референс?»

GOOD (#9875): «…Соберу записи в структуру книги: в Excel — план глав, затем редактура и шлифовка мыслей. Подскажите объём записей и формат — текст, аудио или заметки?»

GOOD (#10442): «…Сгенерирую концепции по ТЗ, соберу макет в Figma и при необходимости HTML/CSS. На выходе нужен только Figma или готовая вёрстка?»
```

**BAD w1 (добавить):**

```text
BAD (#10442): «Midjourney → Figma» без HTML/CSS из tools и без вилки выхода.
BAD (#11332): «оформлю каталог, где референс?» — нет PHP, этапов, фильтров.
BAD (#9366): «готов к бэкенду mini app, какой стек?» — нет TON/NFT якорей.
BAD (универсальный): «По задаче всё понятно, готов начать» — нет этапов и tools.
```

---

### B. L1 — лёгкий touch (`src/ai_analyze.py` → `_LITE_SYSTEM_HEAD`)

**Только если Coder видит быстрый win без раздувания:**

1. **complexity пустой** — r8 уже есть; добавить в post-validate: если complexity null → **2** (fallback в коде, не только промпт). Файл: место нормализации L1 JSON.
2. **#10362** видеоурок SEO в WP admin → **text/marketing**, не dev.
3. **#12602** performance → теги `performance_optimization` / `image_optimization`, не `web_scraping`.

**DoD L1 (опционально):** 1–2 assert в `test_l1_complexity_canon.py` или `test_l1_pipeline.py`.

---

### C. Тесты — `tests/test_l3_human_style.py`

`test_shared_l2_r9_w1_send_gate`:

- assert «Структура send-ready» или «≥4 предложения» в body
- assert «tools_required — сверка» / «не из tools_required»
- assert якоря: `#11332` + PHP; `#9875` + Excel; `#10442` + HTML/CSS
- assert BAD «готов начать» без этапов

**DoD:** `pytest tests/test_l3_human_style.py tests/test_l1_complexity_canon.py -q` — все зелёные (≥24).

---

### D. Не трогать

- L3 `build_uniquify_system` — PASS 92%
- Модели, Neon, judge/regen скрипты
- O105 pay · O114 · O115

---

### E. После сдачи (Lead)

1. Deploy VPS: `l3_human_style.py` (+ `ai_analyze.py` если B) → restart `rawlead-api rawlead-radar`
2. Lead: **regen w2** worst 21–30 из judge w1 top-10 → **judge w2** (только `--lead-ids`, не full 78)
3. Gate w2: send **≥70%** → иначе r10

**Accept ids для regen w2 (из worst L2 w1):**  
9366, 10442, 11332, 10001, 9875, 12148, 10291, 10009, 9328, 9320

---

## § O72e-A — Фаза A (**активно**)

**Цикл:** regen w1 ✅ (21) → judge w1 ❌ send 50% → **§ O72e-L2-r9** → regen w2 → judge w2.

**Coder:** § **O72e-L2-r9** выше.

**Не делать:** stress · vault · regen 71 · full judge 78 без «да».

---

## § O105-w1-r3 — pay hotfix bot-poll (**→ @coder**, P0 prod)

**Симптом (owner 2026-06-04):** `?start=pay_crypto` → счёт Stars 300 ⭐, нет «Изменить способ оплаты».

**Root cause (Lead verify):**
1. **`rawlead-bot-poll.service`** не рестартился при deploy — процесс держал **старый** `telegram_control.py` + `STARS_PRICE_XTR=300` (config кэшируется при старте `bot_poll_main.py`).
2. **`.env.site`:** дубликат `STARS_PRICE_XTR=300` и `600` — dotenv брал **300**.

**DoD:**
1. Deploy **всегда** `systemctl restart rawlead-bot-poll` вместе с radar/api.
2. Env: **одна** строка `STARS_PRICE_XTR=600` в `.env` + `.env.site` (dedupe awk).
3. Smoke: `?start=pay_crypto` → crypto-экран + «← Изменить способ оплаты»; `?start=pay_stars` → intro 600 ⭐, не invoice сразу.
4. Verify pricing href содержит `start=pay_crypto`.

**Не делать:** менять UX-канон O105.

---

## § O114-vacancy — не показывать вакансии (**→ @coder**, P0)

**Решение владельца 2026-06-04:** вакансии/найм в штат **не нужны** — не в `/lenta/`, не в L2, не в judge-выборке фриланса.

**Сейчас:** L1 уже пишет `feed_visible=false` для вакансий, но **протекает** (#7049, #6943, #7240 в judge r8-30).

**DoD:**

1. **Pre-L1** (title+body): стоп-фразы из `FILTERS_DEEP_RESEARCH` §3 — `оклад от`, `трудовой договор`, `полная занятость`, `пришлите резюме`, `вакансия`+контекст штата, `з/п от`+найм; **не** резать «разовый проект» без маркеров штата.
2. **L1** `_LITE_SYSTEM`: явный блок **VACANCY → feed_visible=false всегда** + якоря (Digital Marketing Lead, сценарист в штат, копирайтер вакансия, анкета HR).
3. **Neon backfill:** `is_visible=false`, `ai_verdict=МИМО` для уже видимых лидов с маркерами вакансии (скрипт ops, без regen).
4. **Тесты:** `tests/test_vacancy_filter.py` — 5 positive freelance / 5 negative vacancy.

**Не делать:** Habr Career / VC jobs в `PUBLIC_FEED_SOURCES` (парсеры не включать).

---

## § O115-tg-feed — TG в ленту для тестов (**→ @coder**, P0)

**Решение владельца 2026-06-04:** TG **давно** должен быть в `/lenta/` — на нём же гонять judge/качество ИИ, не только FL/Kwork.

**Факт:** `PUBLIC_FEED_SOURCES` уже 21× `tg:-100…` (local + VPS `.env.site`) · Neon **17 visible** tg · **последний insert ~07:02 UTC** — мало свежих, нужен health-check.

**DoD:**

1. **VPS verify:** `rawlead-radar` · tg_main acc1/2/3 · `radar_site_tg.log` без silent fail · `/status` показывает tg.
2. **Ingest:** новые посты из монитор-chats → Neon `source=tg:peer` · `is_visible` по L1 · карточка в `/lenta/` с badge TG.
3. **Smoke:** ≥1 новый tg-lead за 24 ч на prod · Lead curl feed API `source` like `tg:%`.
4. **Judge hook:** после O114 — pilot 10 ids **только `source LIKE 'tg:%'`** (отдельный прогон, не смешивать с FL).

**Не блокер O114:** можно параллельно, но оба P0 до UI/рекламы.

---

## § O105-w1 — Premium pay (**→ @coder**, перед рекламой)

**Env (owner 2026-06-04, `.env` + VPS `/opt/rawlead/.env`):**

| Key | Пример |
|-----|--------|
| `PAY_PREMIUM_RUB` | `790` |
| `PAY_RATE_MODE` | `at_payment_moment` |
| `PAY_SBP_PHONE` | `+79249966496` |
| `PAY_SBP_BANK` | `T-Bank` |
| `PAY_BTC_ADDRESS` | bc1q… |
| `PAY_ETH_ADDRESS` | 0x7a94… |
| `PAY_USDT_TRC20_ADDRESS` | TV9F… |
| `PAY_USDT_ERC20_ADDRESS` | 0x7a94… (same wallet ok) |
| `PAY_TON_ADDRESS` | UQD7… |
| `PAY_CRYPTO_MEMO_PREFIX` | `RL` → memo `RL{user_id}` |
| `PAY_APPROVE_BOT` | `legacy` → approve в **@FLPARSINGBOT** |

**UX:** канон § O105 + wireframes O105-D в `LEAD_DESIGN_PROMPT.md`.

**DoD:**

1. `/pay` и `?start=pay` → **меню 3 кнопки** (СБП · Crypto · Stars), не сразу Stars.
2. СБП/Crypto → pending row Neon · экран «Проверить оплату» · курс **на момент оплаты** (API или ручной snapshot в сообщении).
3. Owner approve: **FLPARSING** inline «✅ User #123 Premium 30d» / «❌ Отклонить» → `subscriptions` как Stars.
4. Crypto экран: показать **все** сети owner дал (BTC, ETH, USDT TRC20/ERC20, TON) + copy buttons.
5. Stars — **не ломать** `stars_billing.py`.

**Не в w1:** ЮKassa · WalletConnect · авто TronGrid (→ O105-w2).

---

## § O110-fl-proxy — FL 403 / pool_exhausted (**⏸ backlog**)

**Триггер:** FL `alive=0/4` **>2×/сутки** после `clear-vps-proxy-bans.py` · или ingest FL мёртв **>24 ч**.

| # | Задача | DoD |
|---|--------|-----|
| 1 | Env: **`FL_PROXY_URLS`** — отдельный пул (1–2 новых DC IP), Kwork не трогать | `fetch:fl alive≥2/4` 24 ч |
| 2 | Код: **2× http_403 подряд** на `fl:host` → ban (O99 #4) | unit test · меньше «все 4 за один заход» |
| 3 | Опц.: **1** node-proxy в `FL_PROXY_URLS` (не `YOUDO_PROXY_URLS`) | fallback только FL · owner budget |

**Не делать:** merge residential в общий `EXCHANGE_PROXY_URLS` · не трогать YouDo-пул без «да».

---

## § O72e-L2-r8 — L1 + L2 prompt (**✅ 2026-06-04**)

**Цель:** максимум качества **без API** — только промпт + unittest. Regen/judge — Lead/owner после сдачи.

### A. L1 — `src/ai_analyze.py` → `_LITE_SYSTEM_HEAD`

**Проблема (full 71):** ~11 id с **пустым complexity**; редко dev вместо design (#9520).

**Вставить** после строки про `complexity — целое 1–4` (одним блоком):

```text
**COMPLEXITY — жёстко (FAIL если пропуск):**
- Поле complexity **обязательно в каждом JSON** — целое 1, 2, 3 или 4. **Никогда null, never omit.**
- Если сомневаешься — ставь **2** (типовой проект с ясным ТЗ), не оставляй пустым.
- Якоря «complexity пустой» из аудита:
  · Google/YouTube Ads, VK таргет, SMM месяц, Power BI отчёт → **2**
  · транскрипция+перевод часового видео → **2**
  · написание/редактура книги, крупный редакторский объём → **3**
  · лидgen 4000 заявок с валидацией → **3**
  · «разместить готовые посты по списку» без создания контента → **1**
- **design vs dev:** «макет страницы / UI в Figma / 3 версии (desktop, mobile)» **без кода** → primary_category **design**, complexity **2** — не dev.
```

**DoD L1:** `tests/test_l1_pipeline.py` или новый `test_l1_complexity_canon.py` — assert substring `Никогда null` / `обязательно в каждом JSON` в `_LITE_SYSTEM`.

---

### B. L2 — `src/l3_human_style.py` → `build_shared_l2_system`

**Проблема #8772 (pilot r7):** judge видит PHP/WP в `tools_required` и ставит send=False, хотя в draft нет tech-слов.

**Добавить** в блок «Тип заказа» (text/design) **одну фразу-шаблон**:

```text
- **creative/text (#8772 и аналоги):** если в tools_required есть PHP/WordPress/Python, а заказ — **рассказ, статья, копирайт, перевод** — **одной короткой фразой** поясни: «Задача творческая, технические теги карточки к тексту не относятся» (или эквивалент); **не называй** PHP/WP/Python в отклике; вопрос — только **объём (знаки/слова)** или **формат файла (doc/pdf)**.
```

**Обновить GOOD (#8772)** — добавить эту фразу в пример:

```text
GOOD (#8772): «Здравствуйte! Задача творческая — технические теги карточки к тексту не относятся. Напишу рассказ про маму Лену: посёлок, платье в краске, беседка. Все 4 пункта ТЗ учту. Подскажите объём — в знаках или словах?»
```

**#8752 (с reconcile r6↔r7):** judge r7 хочет TG/API **если** в `tools_required`. Правило:

```text
- **учебная платформа (#8752):** функционал из **Описания** (экзамены, видео, адаптив, Yii2/Python). **Telegram/API** — **одной фразой**, только если **и** в Описании **и** в tools_required есть telegram/api; иначе **не добавляй**.
```

Обновить BAD/GOOD #8752 под это правило.

**DoD L2:** `tests/test_l3_human_style.py` — дополнить `test_shared_l2_r7_fixes` или `test_shared_l2_r8`: assert «творческая» + «теги карточки» в body; assert правило #8752 telegram.

---

### C. Не трогать

- L3 `build_uniquify_system` — уже PASS
- Модели, Neon, judge, regen-скрипты
- **Не** запускать OpenRouter из Coder-чата

---

### D. После сдачи (Lead)

1. Deploy VPS: `l3_human_style.py` + `ai_analyze.py` → `/opt/rawlead/src/` · restart `rawlead-api rawlead-radar`
2. Owner (когда скажет): regen worst ids · pilot · full 71

---

## Закрыто — сводка

| § | Статус |
|---|--------|
| **O72e-L2-r9** | ✅ tests 25/25 · **→ deploy + regen w2** |
| O72e-L2-r8 | ✅ tests 24/24 · VPS deploy |
| O114-vacancy | ✅ code+tests · backfill dry-run 12 |
| O115-tg-feed | ⚠️ ingest OK · judge tg pilot ⏸ |
| O72e-L2-r7 | ✅ pilot r7 PASS 4.3/80% |
| O72e-L2-r6 | ✅ pilot r6 |
| O109 | ✅ 1.18.6 |

Очередь: [TASKS.md](../common/TASKS.md)

---

## Правило hot-файла

**≤ ~120 строк** · DoD → `archive/CODER_PROMPT_ARCHIVE.md`
