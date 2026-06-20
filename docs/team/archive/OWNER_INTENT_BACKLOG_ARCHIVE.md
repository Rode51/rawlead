# OWNER_INTENT — бэклог (архив)

Перенесено из hot OWNER_INTENT.md 2026-06-20 (audit A5). Актуальные решения — § «Решения (обязательные)» + журнал в hot.

## Бэклог владельца (группы · приоритет Lead)

**Правило:** запись в чат → сюда; **код** — когда этап активен в `ROADMAP` / шапка `CODER_PROMPT`. Срочно — только по слову «сейчас».

**Правило:** запись в чат → сюда; **код** — когда этап активен в `ROADMAP` / шапка `CODER_PROMPT`. Срочно — только по слову «сейчас».

### § O198-w — Quiz complexity + curated pool (**P0 product · 2026-06-13**)

**Скелет идеи:**

**1. Complexity-preference в профиле пользователя**
Пользователь выбирает «предпочтительная сложность» — влияет на `final_rank`. Логика:
- Пул карточек квиза → только `complexity IN (1,2)` (ясные ТЗ, конкретные задачи)
- Если пользователь **лайкает cx=1** → в ленте буст заказам с cx=1–2
- Если лайкает cx=2 (стандарт) → нейтральный вес по сложности
- cx=3–4 в ленте **не блокировать**, но ранжировать ниже

**2. Ресёрч пула (Lead Neon 2026-06-13)**

Важный вывод: **cx=4 в базе = 0** (`ai_reasons->>'complexity'=4` не встречается). Все лиды cx=1–3 или NULL (NULL = L1 не вернул, default=2). Значит антиспам-фильтрация по complexity работает через cx=3 (несколько систем / монолит — сложные) и нужно выбирать cx=1–2.

| signal | кандидаты cx1-2 (sc≥85) |
|--------|------------------------|
| python | 22141, 22049, 22047, 21914, 21696 |
| wordpress_dev | 22283, 22022, 21813, 21788, 21784 |
| api_integration | 22305, 22264, 22111, 21744 |
| ui_ux | 22390, 22336, 22170, 22091 |
| video_editing | 22338, 22327, 22304, 22268, 22186 |
| brand_identity | 22341, 22246, 22172, 22101, 21995 |
| smm | 22356, 22117, 22092 |
| yandex_direct | 21677, 21571, 21488, 21318 |
| seo | 22276, 22275, 22233, 21765 |
| copywriting | 21483 ⚠, 21127, 20846, 20665 |
| article_writing | 22388, 22011, 21554 |
| editing_proofreading | 22213, 22209, 21726, 21627 |

⚠ `id=21483` «Написать положительный отзыв» — сомнительный контент, исключить из пула.
⚠ `id=22251` SMM «Возьму проект» — это объявление исполнителя, не заказ → исключить.
⚠ `id=21419` «**Ищут редактора»** — asterisk в заголовке, слабый.

**3. Решения owner (2026-06-13)**
- **cx_pref** — автоматически из лайков квиза (отдельный вопрос не нужен)
- **Ранк** — мягкий множитель · cx=3 не скрывать
- **→ @coder:** § **O198-COMPLEXITY-RANK** (`CODER_PROMPT`)

**4. Архитектура (Lead)**
- Pool: `complexity IN (1,2)` + exclude `{21483, 22251, 21419}`
- `cx_pref` → тег `__cx_pref` в `user_tags`
- `final_rank *= max(0.80, 1.0 - abs(lead_cx - cx_pref) * 0.10)`

**→ @lead-product:** закрыто owner 2026-06-13 · **→ CODER_PROMPT § O198 ✅**

### § O197-w — Quiz adaptive: большой пул + ветвление (**P0 product**, owner **2026-06-13**)

**Скелет идеи (не ТЗ):** фиксированные **12 карточек — недостаточно**. Нужна **большая база** реальных лидов из Neon и **адаптивный** квиз: **следующая карточка зависит от предыдущих ответов** («Взял бы» / «Не моё»). Если стек пользователя **неясен** — показываем **больше** карточек; если профиль **сошёлся** — **ранний стоп** (число min/max — решит Product).

| Слой | Что | Кто |
|------|-----|-----|
| **1 Product** | Правила ветвления: какие теги/ниши probe дальше · порог «достаточно ясно» · min/max карточек · экран результата · не ломать веса/decay из § TINDER-ONBOARD | **→ @lead-product** **сначала** |
| **2 Architect** | Модель пула (Neon: curated pack по signal-тегам + fallback) · API `next card` (session state) · что в localStorage до TG login | Lead после PM § |
| **3 Coder** | Реализация после PM+Architect | **⏸** § O195-w1b **hold** |

**Lead (2026-06-13):** 12 ID из Neon — не финал, а **seed/examples** для пула. `pending_tags` (redis, websocket, nestjs…) — расширение **каталога SKILLS**, не quiz-карточек; в Product § отдельно.

**Supersedes (частично):** `LEAD_PRODUCT_PROMPT` § TINDER-ONBOARD «ровно 12 карточек» · `CODER_PROMPT` § O195-w1b до обновления PM.

**→ @lead-product:** переписать § TINDER-ONBOARD блок `/quiz/` — adaptive tree + pool size + stop rules.

**→ Lead Architect:** после PM — § в `CODER_PROMPT` (data/API), не раньше.

**Superseded (owner 2026-06-14):** Neon allowlist (O216b) — **временный мост** до § **O217-w** (синтетический пак PM).

### § O217-w — Quiz synthetic card pack (**P0 product · owner 2026-06-14**)

**Решение owner (принято Lead):**

| # | Решение |
|---|---------|
| 1 | Квиз-карточки — **авторские**, не вакансии Neon · **гибрид с leads ❌** |
| 2 | PM пишет текст + **ground truth** теги из каталога · Design — длина/UX карточки |
| 3 | Три типа: **якорные** · **граничные** (2 ниши) · **ловушки** (обманчивые) |
| 4 | Сложность **1–3** на карточку (для cx_pref / soft rank O198) |
| 5 | Match % после квиза — **без отдельного disclaimer**; профиль → match по навыкам как есть |
| 6 | Каталог навыков — **расширить сейчас**, если для пака не хватает id (lint «карточка ↔ catalog» позже в коде) |
| 7 | Адаптив O197 **не ломать** — меняется только **источник карточек** |

**Зачем:** вакансии с бирж = шум; квиз = **измеритель профиля**. Тонкая настройка match.

**PM deliverables → `LEAD_PRODUCT_PROMPT` § O217-QUIZ-SYNTHETIC-PACK` (hot ≤80 строк):**

| # | Артефакт |
|---|----------|
| p0 | **Аудит каталога:** `SKILLS_TOOLS_CATALOG.md` v0.5 vs 12 quiz-signals (ниже) · список **новых tag_id** или Tier A/B · что взять из `pending_tags`/накопленного |
| p1 | **JSON schema** `quiz_cards_v1` (поля ниже) · версия пака |
| p2 | **Матрица пула v1:** 4 niche × 3 signal × **8–12** карточек + **4–6 ловушек/niche** · cx 1–3 внутри |
| p3 | **Pilot 20 карточек** (5/niche) — owner spot-check «нет WTF» |
| p4 | **Правила весов:** `skills_on_like[]` / `skills_on_dislike[]` · связь с import в `user_tags` |
| p5 | **Stop/adaptive** — без изменений O197 unless gap found |

**Quiz signals (канон API, не менять без PM+Architect):**

| niche | signals |
|-------|---------|
| dev | python · wordpress_dev · api_integration |
| design | ui_ux · video_editing · brand_identity |
| marketing | smm · yandex_direct · seo |
| text | copywriting · article_writing · editing_proofreading |

**Schema карточки (draft для PM):**

```json
{
  "id": "qc_dev_python_01",
  "pack_version": "v1",
  "card_type": "anchor|boundary|trap",
  "niche": "dev",
  "signal": "python",
  "complexity": 2,
  "title": "…",
  "task_summary": "…",
  "skills_on_like": ["python", "django"],
  "skills_on_dislike": [],
  "boundary_with": null,
  "notes_pm": "optional reviewer hint"
}
```

**Файл (Coder позже):** `data/quiz_cards_v1.json` · CI lint: все tag_id ∈ `CANONICAL_TAGS`.

**Порядок:** O216 deploy + tier smoke **можно параллельно PM pilot** · **Coder O217-code** только после PM pilot ✅ + Lead § `CODER_PROMPT`.

**→ @lead-product:** § **O217-QUIZ-SYNTHETIC-PACK** в `LEAD_PRODUCT_PROMPT.md` · p0 audit каталога **первым**.

**→ Lead Architect:** после PM pilot — API swap off `leads` · deprecate `quiz_pool_allowlist.json`.

### § O218-w — Playwright UX/quiz E2E перед рекламой (**owner 2026-06-14**)

**Запрос owner:** перед ads — автоматические **Playwright**-прогоны с **имитацией человека**: UI/UX + **квиз** (разные сценарии, **разные пользователи**, без путаницы state) · **mobile + desktop**.

**Зачем:** ручной tier smoke не ловит регресс «Monica увидела trial, anon — locked bar», смешение `localStorage`, retake vs first profile, импорт tags в Neon.

**Scope (→ @coder § O218-PLAYWRIGHT-QUIZ-E2E):**

| # | Сценарий | Viewport | Изоляция |
|---|----------|----------|----------|
| j1 | Anon: exit mid-quiz → reopen intro | desktop + **390** | fresh context |
| j2 | Anon: complete → result modal → «ещё раз» | desktop + 390 | fresh context |
| j3 | Anon complete → TG login → tags in Neon | desktop | **отдельный** test user (не Monica одновременно с j4) |
| j4 | Retake finish → profile update; retake abandon → first kept | desktop | fresh localStorage |
| j5 | **Trial** Monica: real match % bar · **anon**: locked bar | desktop + 390 | `PREPROD_ACCOUNTS` · reset sub между прогонами |
| j6 | Cabinet «Пройти тест заново» | desktop | logged-in context |
| j7 | Synthetic cards visible (`source=synthetic`, PM title substring) | desktop + 390 | — |

### § O220-w — Feed smoke batch (**owner 2026-06-14 · после O219**)

| # | Симптом | Куда |
|---|---------|------|
| 0 | **Owner:** вошёл в ЛК/ленту **до квиза** → на совместимости **замок**, не 50% · после квиза → реальный % | **Coder O220 r0** (решение owner, PM не блокирует) |
| 1 | **Match ~50% везде** (до r0) → после reload 8% | **→ @lead-product** опционально — post-quiz low % |
| 2 | В развёрнутой карточке «Сложность» вплотную к «СУТЬ ЗАДАНИЯ» | Coder O220 r4 |
| 3 | Можно нажать **>5 откликов разом** — нужен concurrent cap | Coder O220 r2 |
| 4 | Ушёл со страницы во время генерации — вернулся, **анимация пропала** | Coder O220 r3 (`PENDING_DRAFTS` не restore) |
| 5 | **Mobile expanded:** заголовок обрезан (свёрнутый — OK) | Coder O220 r5 |
| 6 | **Лимит 5/ч не работает** → owner: **поднять до 10/ч** + UI везде | **amend O208-B1** · Coder O220 r1 |
| 7 | **Страница оплаты** не грузится (`yoomoney.ru` timeout) | Coder r7 probe · `@mechanic` если URL OK |

**Lead verify:** `DRAFT_HOURLY_LIMIT` default **0** на prod · 50% = `EMPTY_PROFILE_KEYWORD_MATCH` без tags в Neon.

**→ @lead-product:** § **O220-MATCH-PM** — **✅ owner OK 2026-06-14**  
**→ @coder:** § **O220-MATCH-CODE** (reopened) · § **O220-FEED** r0–r7 ✅

### § O220-match-ui — карточки лента ≡ ЛК (**owner 2026-06-14**)

| # | Запрос |
|---|--------|
| 1 | **Лента и ЛК — один вид карточки**; в ЛК **только** плашка «ОТКЛИК ✓» |
| 2 | **Без текстовых подписей match** — убрать «Не ваша ниша», «Частичное совпадение · N%», «Хорошее…», «–», «?» · **только полоска** (owner **отменяет** PM § A band copy) |
| 3 | Убрать мусор `"` под bar (следствие `renderMatchBreakdown`) |
| 4 | PM § **O220-MATCH-PM** ✅ по **формуле** — **`lead_coverage_match`** · UI bar only ✅ 2026-06-14 |

**Lead verify:** `renderMatchBreakdown` строка заканчивается `"></div>"'` · cabinet без `rl-match-bar` / `rl-row--match-tier` · ticket [`2026-06-14-match-ui-stray-quote.md`](../../problems/2026-06-14-match-ui-stray-quote.md)

**→ @coder:** `CODER_PROMPT` § **O220-MATCH-CODE** · `TASKS` **69**, **77**

### § O219-w — LK UX + match bars + auto-trial + quiz URL (**owner 2026-06-14**)

**Запрос owner (batch, до @coder):**

| # | Что |
|---|-----|
| 1 | ЛК: убрать жёлтый квадратик под шапкой |
| 2 | ЛК: **скрыть** ручные навыки (chips Figma/SMM…) — quiz-first |
| 3 | «Пройти ещё раз» — нормальная кнопка **под** «Отклики с ленты…», не чёрный chip |
| 4 | Лента anon: **полоска совместимости с замком** на карточках |
| 5 | Trial + Premium: реальный % · expired/anon: замок |
| 6 | Monica: **полный wipe** из Neon → проверить auto-trial при первом TG-login |
| 7 | `/quiz/` → канон **`/lenta/#quiz`** (редirect, не две точки входа) |
| 8 | Спрятать badge «synthetic» на карточках квиза |

**Lead verify:** anon bar не виден из-за CSS `display:none` на `.rl-row--auth-only` · auto-trial **не реализован** в `auth_telegram`/`bot-complete` · retake = `rl-cabinet-tag` (чёрный).

**→ @coder:** § **O219-CABINET-QUIZ-UX-BATCH** · `TASKS` **66**

**Техника:**
- **Отдельный browser context на persona** (anon A / anon B / Monica / owner JWT) — **не** один storage
- Mobile: viewport **390×844**, touch-friendly taps
- Assert: DOM + API (`/wp-json/rawlead/v1/quiz/*`) + optional Neon read tag count per user
- Артефакт: `data/preprod_quiz_e2e.json` + скрины при fail
- Не дублировать O37c pixel-audit — фокус **quiz lifecycle + tier bars**

**Порядок:** после owner tier smoke (FOR_YOU) · **до** stress/GTM · параллельно Perf ok.

**→ @coder:** `CODER_PROMPT` § **O218-PLAYWRIGHT-QUIZ-E2E** (после tier smoke).

### § O168-w2 — L2: ложное «ТЗ обрывается» (**P0**, owner **2026-06-10**)

**Кейс:** [FL #5508904](https://www.fl.ru/projects/5508904/vyikachat-bazu-retseptov-iz-igryi.html) — в ТЗ: «Рецепты хранятся **на сервере игры**». Черновик: «фраза «Рецепты хранятся на…» **обрывается**» — **ложь**, снижает send_as_is.

**→ Coder:** § O168 **g1c** — validator + prompt + test fixture

### § O174-w — ЮKassa · единственная оплата (**P0**, owner **2026-06-10**)

**Решение owner:** подключает **ЮKassa** · отказ от Stars, crypto, ручных переводов/SБП в боте и на сайте.

| # | Что |
|---|-----|
| **Legal footer** | Нижняя панель сайта: **Храмовских Никита Евгеньевич** · ИНН **384903841000** (самозанятый) |
| **Pricing / ЛК** | Одна оплата — **ЮKassa** (карта / СБП через кассу) · убрать Stars, USDT/TON, «перевод на телефон» |
| **Бот @rawlead_bot** | Убрать `/pay` ветки crypto · Stars · manual SBP · оставить поддержку/лента/deep-link на сайт |
| **Trial** | **1 ₽** → **3 дня** Premium (1× на аккаунт) · далее **790 ₽/мес** **автопродление** (recurring ЮKassa) |
| **Owner** | Ключи ЮKassa в `.env` VPS · webhook URL → API · **договор ✅ 2026-06-11** · ждём shop_id + secret |
| **Порядок** | **1)** footer ✅ owner **2026-06-10** · **2)** ЮKassa на проверке — **prep** код/копирайт · **3)** ключи owner · **4)** включить оплату |
| **O175** | **Фильтр бирж (multi) + ЛК откликов + пагинация 10** | § **O175-w** |

**Supersedes:** O12 Stars-only · O105 manual pay · O107 free trial · O105-w2 crypto.

**→ @coder:** § **O175** **сейчас** · § **O174b** prep ⏸ keys · **→ @lead-product:** § **O174-COPY** · **→ @lead-designer:** § **O174-D**

### § O175-w — Фильтры ленты + inbox ЛК (**P0**, owner **2026-06-10**)

| # | Что |
|---|-----|
| **Multi биржа** | Чекбоксы · несколько источников одновременно |
| **7 дней** | По выбранной бирже — все лиды за **7 дней**, не только «только что» |
| **Inbox** | Отклик из ленты → **сразу в `/cabinet/`** |
| **Пагинация ЛК** | **10** карточек сразу · дальше «Показать ещё» |

**→ @coder:** § **O175-FEED-INBOX**

### § O168-w3 — p95 запас **1500 ms** @50 VU (**P0**, owner **2026-06-10**)

**Решение owner:** gate **<2000** — мало запаса; load **2013** «в вакууме» · **цель ads: p95 ≤1500 ms** @50 VU.

**→ Coder:** § O168 **g2b** (feed index / lighter JSON / gzip / VPS CPU) после или параллельно закрытию <2000.

### § O171-w — Админка /ops/ + FLPARSING (**P1**, owner **2026-06-10** · research kickoff **2026-06-13**)

**Симптом:** лампы врут — YouDo 🟢 при 0 лидов; FL 🟡 когда биржа жива, просто нет новых заказов; `/status` и push не дают «что делать» не-программисту.

**Решение owner:** полное переосмысление `/ops/` + admin-бота (**Owner Command Center**).

**Scope split (owner 2026-06-13):** параллельный чат «концепция» = **логика карточек + новые публичные страницы** · **админку не трогаем** · O171 отдельная линия.

**Deep research — канон (Lead 2026-06-13):**
- **Не** новый файл в корне docs без согласия.
- **→ @lead-product:** § **O171-ADMIN-RESEARCH** в `LEAD_PRODUCT_PROMPT.md` (hot ≤80 строк): JTBD владельца · IA 5–7 блоков · метрики «ступени правды» (process→fetch→parsed→new→L1→visible) · формат `/status` и push · **не** дублировать O121-D wireframes прокси.
- **→ @lead-designer:** wireframes после PM § (mobile 390 · сводка 30 сек · биржи/TG/прокси).
- **→ @lead-architect:** нарезка волны Coder после Design · **не** параллельно O198 deploy без решения owner.

**Уже есть:** O121 § · O121-D ✅ (прокси wireframes) · частичный код `/ops/` (`owner_admin.py`).

**→ Coder:** § **O171-OPS-ADMIN-REBUILD** — **после** PM + Design spec (не после O168-only gate)

**→ Coder:** § **O201-OPS-SIMPLE-GATE** — **→ now (owner 2026-06-13)** · O199/O200 **pause**

### § O201-w — Ops вход только пароль + кнопка «Админка» (**P0**, owner **2026-06-13**)

**Боль:** `/ops/` требует Telegram-кабинет в том же браузере · Cursor не работает · `?key=` неудобно.

**Решение owner:** личная **кнопка «Админка»** на сайте → `/ops/` · **только пароль** (hash в `.env`) · cookie 30d · **без** привязки к `/cabinet/`. Заход **откуда угодно** (Chrome на телефоне).

**Не:** bcrypt «для красоты» если compare_digest уже ок — достаточно `RAWLEAD_OPS_KEY` в `.env.site` + форма `/ops/login` (уже есть в API). Убрать блок «войди в кабинет».

**→ @coder:** § **O201-OPS-SIMPLE-GATE** (единственный hot до owner OK)

**Tail owner 2026-06-13:** «Админка» только создатель · убрать из ЛК · `/ops/` не грузится · wrong password пускает → § **O201-TAIL-OPS-FIX**

### § O199-w — Smoke onboarding UX (**P0–P1**, owner **2026-06-13** post-deploy)

**Решения owner:** `/ops/` только Chrome (не Cursor) · **P0** лента logged-in «Не удалось загрузить» · убрать manual skills · quiz UX + promo → Design · copy quiz-first → PM · toast «появится в ЛК» на отклик · audit learning loop.

**→ @coder** § **O199-FEED-ONBOARD-FIX** · **→ @lead-product** § **O199-ONBOARD-COPY** · **→ @lead-designer** § **O199-QUIZ-UX**

### § O172-w — Green/Red ops-runbook (**P2**, owner **2026-06-10**, согласовано)

Cron runbook Green без LLM; Red → тикет. **После** O171.

**→ Coder:** § **O172-OPS-GREEN-RED**

### § O173-w — Draft wait UX B+C (**P1**, owner **2026-06-10**)

Token-stream L2 + второй юзер без общего стрима · O160-w факты **❌** · см. § **O173-DRAFT-WAIT-UX** · **после O168**

### § O191-w — YouDo: DC primary + residential fallback (**P1**, owner **2026-06-12**)

**Owner:** попробовать **наши обычные (DC) прокси** первым слотом · **residential** — подстраховка на retry · общий трафик node-proxy — **не** резать число слотов ради «экономии» · listing **не** реже (наоборот — свежесть важнее).

**Lead:** экономия GB — не `fetch_every_n` ↑ и не меньше слотов, а **меньше байт на fetch** (detail skip, delist реже) + DC дешевле residential когда camoufox пропускает.

**Порядок:** только **после** O190 ingest DoD (`fetch_end parsed>=50`) · smoke DC slot → env order DC→RU → deploy · rollback RU-only одной строкой.

**→ @coder:** § **O191-YOUDO-PROXY-MIX** (в `CODER_PROMPT` после t0d-ingest ✅)

### § O210-FL-PROXY-TIER — DC + residential fallback (**owner 2026-06-14**)

**Проблема:** FL на DC-прокси · при antibot **часто 0/4 alive** · не «один бан = все», но **httpx fallback за один цикл** может пройти все слоты (2×403 каждый).

**Решение owner:**
- **Tier-1:** `FL_PROXY_URLS` — обычные DC (как сейчас)
- **Tier-2:** residential (node-proxy RU) — **только когда tier-1 `alive==0`** · TTL бана DC **1ч** — сами вернутся
- **Не** держать FL постоянно на residential (трафик/деньги)

**YouDo (тот же принцип):** DC **первый слот** · residential **только slot_retry/ban** — см. **O191-w** · не listing 24/7 на res.

**Coder:** § **FL-PROXY-STABILITY** · `FL_PROXY_URLS_RESIDENTIAL` env · отключить/ограничить httpx multi-ban cascade на FL.

### § O211-w — Ops карточки: «сегодня в ленте» vs misleading 0/0 (**owner 2026-06-14**)

**Симптом:** `/ops/` карточки FL/YouDo показывают `parsed 0 · new 0`, хотя в ленте заказы есть · «Разбор» красный при живом ingest.

**Причина (код):**
- `parsed` = карточек **в последнем цикле** (не «сегодня»)
- `new` = вставки в Neon **за 1 час** (не «сегодня» · не «в ленте»)
- `visible_24h` уже считается в SQL, но **не в строке** под карточкой
- `lag` = минут с последней **вставки** в БД (336 мин ≈ 5.5 ч без новых FL)

**Решение owner:** в meta строке карточки — **`сегодня N`** (или `за 24ч`) + tooltip что значит каждый шаг лестницы.

**→ @coder:** § **O207** — t1 log baseline → t2 history sample (10/chat) → t3 filter replay · owner labels before rule changes.

---

### § O193-w — FL listing: subprocess worker (**P1**, owner **2026-06-12**)

**Контекст:** O190 t0i — YouDo listing через `scripts/youdo_fetch_worker.py` (отдельный процесс) снял asyncio contamination в uvicorn-процессе. FL listing сейчас in-process Playwright + httpx fallback в том же цикле.

**Решение owner (вариант B, не A):**

| | Вариант | Статус |
|---|---------|--------|
| **A** | FL listing **httpx-primary**, browser только fallback | **❌ отклонено** |
| **B** | FL listing → **`fl_fetch_worker.py`** subprocess (паттерн как YouDo worker) | **✅ принято** |

**Границы:**
- **`tz_session.py` не трогать** — скачивание ТЗ (auth cookies / persistent profile) отдельно от listing crawl
- Kwork — **не в этом решении**; аналог B возможен позже отдельным §

**Lead:** process isolation = упрощение стабильности radar-цикла, не over-engineering.

**Порядок:** только **после** O190 ingest DoD (`fetch_end parsed>=50` + `health:youdo ok`) · зафиксировать subprocess-паттерн на YouDo · затем FL worker · **O191** (YouDo proxy mix) не блокируется — параллельно или после FL по приоритету ingest SLA

**→ @coder:** § **O193-FL-SUBPROCESS-WORKER** (в `CODER_PROMPT` после t0j ✅)

### § O165-w — TG smoke: группа «Тест Ботов» (**P0**, owner **2026-06-09**)

**Запрос:** все **3 acc** (acc1/acc2/acc3) в [https://t.me/+Z7HcnIAdSw9kY2U6](https://t.me/+Z7HcnIAdSw9kY2U6) · owner напишет вакансию · смотрим ленту.

**→ Coder:** § **O165-TG-TEST-GROUP** · join + listen + `PUBLIC_FEED_SOURCES`

**→ Owner:** после deploy/join — пост в группу · «вижу / не вижу» в `/lenta/`

### § O166-w — Главная: шкалы совместимости пустые (**P1**, owner **2026-06-09**)

**Симптом:** блок «ПОСЛЕДНИЕ ЗАКАЗЫ» — цифры 50/100/80%, полоски серые без fill.

**→ Coder:** § **O166-HOME-MATCH-BAR**

### § O167-w — Лента: биржи в выпадающей сортировке (**P1**, owner **2026-06-09**)

**Запрос:** FL · Kwork · TG в **существующем** dropdown «Сортировка» · mobile + desktop (не отдельный hidden fieldset).

**→ Coder:** § **O167-FEED-SOURCE-SORT**

### § O168-w — Реклама рано: stress + L2 (**P0**, owner **2026-06-09**)

**Решение:** ads **после** green stress + L2 quality · вчера stress FAIL (tier_matrix · p95) · L2 «хромает».

**→ Coder:** § **O168-PRE-ADS-GATES** после O165–O167

### § O165-w — TG smoke: группа «Тест Ботов» (**P0**, owner **2026-06-09**)

**Запрос:** [https://t.me/+Z7HcnIAdSw9kY2U6](https://t.me/+Z7HcnIAdSw9kY2U6) — **все 3 акка** join+listen · owner напишет вакансию → проверим Neon + `/lenta/`.

**Решение owner:** реклама **рано** — сначала TG + тесты + L2.

**→ Coder:** § **O165-TG-TEST-GROUP**

### § O166-w — Главная: шкалы совместимости пустые (**P1**, owner **2026-06-09**)

**Симптом:** live-preview карточки — % есть, bar grey empty.

**→ Coder:** § **O166-HOME-MATCH-BAR**

### § O167-w — Сортировка по биржам в dropdown (**P1**, owner **2026-06-09**)

**Запрос:** FL/Kwork/TG в выпадающую «Сортировка» (ПК + mobile), не отдельная полоса.

**→ Coder:** § **O167-SORT-SOURCE** · source chips сейчас `is-visually-hidden`

### § O168-w — До ads: stress + L2 (**P0**, owner **2026-06-09**)

**Факт:** `preprod_stress_v2` FAIL tier_matrix + p95 · U10b draft fail · L2 gate 71.8% но quality хромает.

**→ Coder:** § **O168-PRE-ADS-GATES** после O165–O167

### § O162-w — L2 отклики: PDF/файлы/инструменты (**P0**, owner **2026-06-09**)

**Симптом (скрин + [FL #5508756](https://www.fl.ru/projects/5508756/oformit-gotovuyu-prezentatsiyu.html)):** черновик «из приложенного PDF», «юридический документ» — в ТЗ **нет** PDF/Word/вложений; в tools — `telegram_bot_dev` + `powerpoint` (бот не из ТЗ).

**Корень Lead (read-only):**

| # | Причина |
|---|---------|
| 1 | O108 `reply_attachment_claim_reason` ловит в основном «вижу … pdf/zip», **не** «приложенного PDF», «из PDF-файла» |
| 2 | На **последней** попытке L2 attach-check **пропускается** → bad draft уходит в Neon |
| 3 | `sanitize_tools_for_tz` **не** режет `telegram_bot_dev` без маркеров TG в тексте |
| 4 | FL-аккаунт **не** причина этого кейса — на листинге нет файла; модель **додумала** |

**Owner:** тренинг L2 в Cursor (Sonnet), не OpenRouter сейчас · проверить качество откликов · спросил про FL-аккаунты для выкачивания ТЗ.

**→ Coder:** § **O162-L2-GROUNDING** (валидаторы + tools guard + fail last attempt) **до** массового regen.

**→ Owner + Lead:** бенч 10–15 лидов в Cursor по rubric judge (в т.ч. #5508756).

### § O163-w — TG: сырой forward без ленты (**P0**, owner **2026-06-09**)

**Симптом:** @FLPARSINGBOT — «Forwarded from …»: реклама ботов, CV «ищу проекты». В `/lenta/` **нет** (ok), но raw forward **есть** (плохо).

**Корень:** лента = `feed_visible AND public_feed` (TG не в PUBLIC_FEED_SOURCES) · бот = только `feed_visible` · `forward_listing_to_owner` **до** карточки · L1 не режет promo/CV.

**Решение owner:** пересылать **только** то, что в ленте · **формат как биржи** (карточка, без raw forward).

**→ Coder § O163-TG-NOTIFY** после/рядом O162.

### § O160-w — Факты на плашке ожидания отклика (**❌ отменено**, owner **2026-06-10**)

**Было:** крутить «интересные факты» пока генерируется отклик.

**Решение owner 2026-06-10:** **не делаем** — вместо этого § **O173** (**B** token-stream + **C** второй юзер).

### § O173-DRAFT-WAIT-UX (**P1**, owner **2026-06-10** · **после O168**)

**Цель:** не отпугивать пустым спиннером · **OpenRouter `stream=True`** + SSE на фронт.

| Трек | Что | UX |
|------|-----|-----|
| **B** | Стрим L2 (первый на свежий лид) | Текст **по буквам** (~200–500 ms до первых слов) · SSE `GET …/draft/stream` · validate + commit в Neon **после** полного текста |
| **C** | Второй юзер на свежий лид | «Уже генерируют…» пока L2 · потом **его** L3 (можно тоже стрим) · **не** общий поток L2 с первым |

**Кэш / L3 (канон):**

| В базе | Действие |
|--------|----------|
| **`user_lead_replies`** для этого юзера | Уже **его** текст → **сразу** (plain или simulate stream), L3 **не** повторять |
| Только **`leads.reply_draft`** (общий L2) | **Сначала L3** → save → show · следующий клик = сразу |
| Ничего | L2 stream (1× на лид) · 1-й юзер · 2+ → C |

**Не делаем:** O160-w факты · A-only этапы без стрима · fan-out queue · L3 «на лету» из L2-stream.

**→ @coder:** § **O173** в `CODER_PROMPT` когда O168 green · **→ @lead-designer:** карточка под поток текста + copy строки C.

### § O158-w — Match UX + дубли push (**P0**, owner **2026-06-08**)

**Симптомы (скрин TG + /lenta/):**

1. **TG:** один заказ Freelance.ru (`/task/view/2245`) — **3 push подряд**, Match 82%, текст слегка разный («Перенос» / «Перенести»).
2. **Лента:** подпись «N% Совместимость» есть, **полоска пустая** (регресс O147, owner verify 2026-06-08).
3. **Deep link** из TG «Лента» → `/lenta/?lead=…` — **% совместимости нет** (или 0%), хотя в push было 82%.

**Корень Lead (read-only):**

| # | Причина |
|---|---------|
| 1 | Dedup push только `(user_id, lead_id)` в `match_push_log`; при смене текста заказа — **новый `content_hash` → новый `lead_id`**, тот же URL → новый push. Два вызова `push_match_for_lead` (L1 pool + conveyor) — ок для одного id, не для дублей строк. |
| 2 | `syncMatchFill` ставит inline `width:0` и ждёт IO/rAF; на collapsed карточках полоска остаётся пустой при живой подписи (§ O147). |
| 3 | Deep link: `GET /v1/leads/{id}` **без** `keyword_match` · WP `/rawlead/v1/leads/{id}` **не** пробрасывает Bearer. |

**→ Coder:** § **O158-MATCH-UX** в `CODER_PROMPT`. **✅ deploy 2026-06-08**

### § O156-w — YouDo human + external pulse (**P0**, owner **принял 2026-06-08**)

**Owner:** residential один · второй не потяну · «больше человечности» · PM2 **не** · Healthchecks **да**.

**Корень Lead:** browser listing ok · **httpx detail** жжёт pool 403 · перебор 3 слотов за цикл · cold ephemeral browser.

**→ Coder:** § **O155-EXTERNAL-PULSE** + § **O156-YOUDO-HUMAN**

**→ Owner после deploy:** Healthchecks.io check grace 15m · `HEALTHCHECKS_SITE_URL` в `.env` VPS

### § O152-w — Стабильность бирж /ops/ (**P0**, 2026-06-08)

**Owner:** YouDo/FL 🔴 · trace · **карточки: +n при expand + сосед дёргается при collapse**.

**→ Owner:** smoke `/ops/` (trace + лампы) · YouDo «Сбросить баны» если 🔴

**→ Coder:** § **O147-FEED-FLIP-MATCH** · hotfix после O146 verify

### § O147-FEED-FLIP-MATCH — flip full · match bar · trial (**→ active**, 2026-06-08)

**Owner verify (скрины):**

1. **Flip** — карточка урезаная в скролл-боксе; должна выглядеть как обычный expand.
2. **Match bar** — «Совместимость N%» есть, полоска пустая на collapsed cards.
3. **Cabinet** — Premium/trial: убрать «Попробовать 3 дня» (оставить только Продлить / Оплатить).

**→ Coder:** § `CODER_PROMPT` O147.

### § O146-DRAFT-CARD-UX — flip lock · pending · кнопка (**✅ код · accept ⏸**, 2026-06-08)

**Owner:** flip **один раз** и остаться на черновике · poll не прерывать при expand/collapse · кнопка pulse + gold shimmer.

**Корень:** `finishDraftFlip` снимает `--draft-flip` → yo-yo.

**→ Coder:** § `CODER_PROMPT` O146 · theme deploy.

### § O145-FEED-CAT — Premium + category (**✅ deploy 2026-06-08**)

**Verify Lead:** pytest **2/2** · wide scan 500 + slice · `deploy-o145-feed-cat-vps.py`

**Deploy:** `python scripts/deploy-o145-feed-cat-vps.py` → **rawlead-api**.

**Owner smoke:** Premium · дата · Маркетинг → несколько карточек.

### § O144-RFP-COMPLY — L2 «идеи в отклике» (**✅ код 2026-06-08** · deploy ⏸)

**Verify Lead:** pytest **10/10** · `deploy-o144-rfp-vps.py` → api + radar + legacy.

**Owner smoke:** Kwork HoReCa → 2–3 идеи в отклике.

### § O142-SPLIT-AI — разнести `ai_analyze.py` (**P2 · post-ads**, 2026-06-08)

**Что это:** рефакторинг **без смены поведения** — один файл ~2140 строк (L1 + L2 + L3 + OpenRouter + валидация) → пакет **`src/ai/`** (или эквивалент):

| Модуль | Зона |
|--------|------|
| `l1_analyze.py` | разметка L1, tags, judge hooks |
| `l2_draft.py` | черновик отклика, guards (`vague`, Veluna) |
| `l3_human_style.py` | уже отдельно — только импорты |
| `openrouter_client.py` | HTTP, retry, proxy |

**Зачем:** Coder и человек не теряются в «простыне ИИ»; новые L2-guard — в `l2_draft`, не +100 строк в monolith.

**Не сейчас:** до ads не трогаем — риск регресса L1/L2 на launch path.

**→ Coder:** отдельный § Lead · pytest golden L1/L2 · **zero** изменений API/Neon.

### § O143-SPLIT-API — routers из `api_server.py` (**P2 · post-ads**, 2026-06-08)

**Что это:** рефакторинг **без смены контракта** `/v1/*` — FastAPI monolith ~2260 строк → routers:

| Router | Эндпоинты |
|--------|-----------|
| `feed.py` | `/v1/feed`, delay, sort |
| `draft.py` | draft async, poll |
| `me.py` | tags, profile |
| `auth.py` | JWT, Telegram login |

`api_server.py` остаётся thin entry: `app.include_router(...)`.

**Зачем:** Site API читаем для Coder/ревьюера; новые роуты не +200 строк в один файл.

**Не сейчас:** Wave 2 / ads не блокируются.

**→ Coder:** отдельный § Lead · e2e feed + draft smoke · импорты/deploy script checklist.

### § O141-EXCHANGE-PARITY — все биржи = FL/Kwork (**✅ deploy 2026-06-08**)

**Решение owner:** полное ТЗ + качественные отклики + TG push **со всех** бирж в `PUBLIC_FEED_SOURCES`.

**Coder ✅:** `exchange_detail.py` dispatch · detail parsers youdo/freelance_* / pchyol · `lead_pipeline` unified · legacy re-fetch if body<300 · `telegram_notify` → `SOURCE_LABELS` · L2 Veluna guard · `SECONDARY_FETCH_EVERY_N_CYCLES` default **1**.

**Verify Lead:** pytest **18/18** · deploy **`deploy-o141-exchange-parity-vps.py` ✅ 2026-06-08**

### § O140-L2-YOUDO-TZ — (**влито в O141** § D)

**Симптом owner:** YouDo «Сделать бота в телеграмме» · L2: «Подскажите, что именно должен делать бот?» — при том что на бирже (или в полном ТЗ) Veluna Whisper AI: aiogram, PostgreSQL, RAG, админка…

**Корень (Lead):**
1. **`_resolve_ingest_body`** — detail fetch только **FL + Kwork**; **YouDo** = только `listing_snippet` с карточки (1–2 строки).
2. L1 `task_summary` = «Разработка Telegram-бота…» — L2 **не видит** 7 пунктов ТЗ.
3. Промпт O128 уже запрещает «что должен бот?», но без «Описания» модель fallback.

**→ Coder (2 волны):**
- **A** `youdo_parser.fetch_project_detail` + wire в `lead_pipeline._resolve_ingest_body` (как FL).
- **B** L2: расширить `_REPLY_DRAFT_VAGUE_RE` + пример GOOD для **AI companion / Veluna-class** ботов (aiogram 3, Postgres, Redis, admin, RAG) · retry если вопрос «что должен бot» при `telegram_bot_dev` в tools и title∋бот.

**Не:** mass regen · смена модели L2.

### § O139-FL-PINNED-FRESH — закреп FL (**✅ deploy 2026-06-08**)

**Симптом:** O134 prefix-stop + закреп FL → `fresh=0` при 26 новых на странице.

**Fix ✅:** `listing_fresh` filter unseen · `fl_parser` full page scan · test `test_trim_pinned_known_new_below`.

**Verify Lead:** pytest **17/17** · VPS `listing:fl parsed=30 fresh=26` (14:49 UTC).

### § O138-PARSER-OBS — parsed vs fresh (**✅ deploy 2026-06-08**)

**Симптом:** `/ops/` 🟢 при `скачано 0` — непонятно: парсер мёртв или O134 fresh-only.

**Coder ✅:** `listing:fl parsed=N fresh=M` · `last_parsed_cards` · red при parsed=0 · `/ops/` listing line · `exchange_parse_smoke.py`.

**Verify:** pytest **7/7** · `deploy-o138-vps.py` ✅

**Не закрыто (опц.):** cron smoke `--write-health` 15m · TG visible 6% — продукт/L1, не O138.

### § O137-FEED-SORT — Premium pagination (**✅ deploy 2026-06-08**)

**Симптом:** 10 заказов по дате при 75 new/day · 6 по match ≥50%.

**Fix:** `sort=time` без min_match + SQL offset; match scan 500 rows.

### § O136-DRAFT-TRACE — observability отклика (**✅ deploy 2026-06-08**)

**Суть:** `draft:trace` stages · L2 skip warnings · uvicorn app log INFO.

### § O131-PERF — perf перед Wave 2 rerun (**✅ deploy 2026-06-07**)

**Решение владельца:** перед следующим полным stress/journey — четыре пункта:

| # | Что | Кто |
|---|-----|-----|
| A | L2 hot path: меньше ретраев · fast path если `reply_draft` уже в Neon · poll 120s | @coder |
| B | Neon **pooler** в `DATABASE_URL` на VPS | **owner** + guard script @coder |
| C | Параллельный boot `/lenta/` (`rawlead-feed.js`) | @coder |
| D | `/v1/feed`: меньше scan · `today_count` в одном запросе | @coder |

**Порядок:** O131 deploy ✅ → rerun stress/journey → ads.

**Deploy Lead 2026-06-07:** `deploy-o131-vps.py` · theme **1.18.35** · load@20 p95 2549 ms (gate ⏸).

### § O133-TZ-DOWNLOADER — акк только на скачивание ТЗ (**P1**, 2026-06-08)

**Идея владельца:** по одному аккаунту FL + Kwork **только для download ТЗ**; listing-парсинг — как сейчас (proxy/browser anon). Если на карточке есть вложение → отдельный login-session качает файл → меньше риск бана.

**Сейчас:** `tz_attachments.py` → `skipped_auth` / «нужен вход на биржу» без cookies.

**Аккаунты owner 2026-06-09:** FL `hramovskihn@yandex.ru` · Kwork `AltCgamer43@yandex.ru` — в локальном `.env` (`FL_TZ_*` / `KWORK_TZ_*`). **На VPS** — те же ключи в `/opt/rawlead/.env` после deploy O133.

**→ Coder после O162/O163:** login → `FL_TZ_SESSION` / `KWORK_TZ_SESSION` (cookies или Playwright persistent profile) · rate limit · **не** использовать для listing crawl.

### § O134-INGEST-SLA — FL/Kwork ≤5 мин (**P1**, 2026-06-08)

**Факт Neon 7d:** Kwork measurable lag p50 **~182 мин** (≤6h sample) · **0/253** within 5 min · FL `source_published_at` **NULL** (метрика сломана). L1 после insert p50 **9s**. Radar cycle **75–181s** + OOM + dup resync ~180/цикл.

**→ Coder:** fix FL/Kwork `published_at` · ingest SLA в `/ops/` · fresh-only listing path.

### § O135-DRAFT — отклик Premium (**✅ deploy 2026-06-08**)

**Симптом:** «ИИ не успел — повторите» · lead #15146 · L2+L3 > 120s poll.

**Coder ✅:** 1-й user **L2-only** (`first_user_l2_only`) · 2-й+ L3 (`fast_shared`) · `draft_async` restart после API reload · `OPENROUTER_HTTP_PROXY` / `OPENROUTER_PROXY_URLS` (отдельно от TG/FL pool).

**Owner ops (опц., без новых покупок):**
```env
# 1-й слот YOUDO_PROXY_URLS (residential RU) — скопировать URL отдельно
OPENROUTER_HTTP_PROXY=http://user:pass@host:port
# fallback: TELETHON_PROXY_ACC2, ACC3 — не TG_PROXY_URL / acc1 bot
# OPENROUTER_PROXY_URLS=...
```
Smoke: `/lenta/?lead=15146` → отклик **< 90s**. Хуже direct — unset.

### § O127 — Финальный UI unify: лента + фильтры + карточка (**P0**, 2026-06-07)

**Запрос владельца:** функции ок, **вид не устраивает** — фильтры у anon/free/premium **выглядят по-разному**; карточки не «красиво и понятно»; нужен **финальный прогон Design**, потом owner руками в BrowserSync.

**Не:** полный ребренд NEO · не новый маркетинг-сайт.

**Да:** одна **дизайн-система filter bar** (одинаковый chrome, разные **возможности** по tier) · одна **карточка** `/lenta/` = `/cabinet/` · mobile 390px · психология (F-pattern, thumb-zone, один primary CTA).

**Тепловые карты:** на нулевом трафике — **эвристики + clarity review** (Design); после soft ads — Hotjar/MS Clarity опц. **O21 UX-audit** — после Coder-волны O127.

| Волна | Кто | Артефакт |
|-------|-----|----------|
| **O127-D** | @lead-designer | ✅ **2026-06-07** · `feed-cabinet-mvp` §9 |
| **O127-WP** | @coder | **→ сейчас** · одна волна CSS/JS/PHP |
| **O127-owner** | владелец | BrowserSync хвост |

**Порядок:** **O127-D** → **O127-WP** → owner tail → **O21** stress → ads. **O126** category (API) — параллельно, не блокирует Design.

**Решение Lead:** точечный Coder (O124-w2) **не заменяет** Design-pass — копим регресс «три разных filter bar».

### § O123 — UI/UX хвост O116 (**архив**, 2026-06-05)

**Контекст:** владелец сверил длинный список правок — **~80% уже в prod (O116)**. O123 = **остаток** до E2E walkthrough.

**w1 — быстрые (copy + мелкий WP, до trial):**

| # | Что | Статус |
|---|-----|--------|
| 1 | How/FAQ: везде **«10 откликов в час»**, не «на заказ» | ⏳ |
| 2 | Убрать **feed-strip** «15 мин / без задержки» для free на `/lenta/` | ⏳ |
| 3 | `flow.php`: caption «Меньше вкладок…» **ниже** (отступ) | ⏳ |
| 4 | ЛК: у **active Premium** — только «Продлить», без trial CTA; **expired** — «Возобновить» | ⏳ частично |
| 5 | JS: убрать мёртвый **`paused`** UX (если API ещё отдаёт) | ⏳ |

**w2 — после w1 (feed polish):**

| # | Что |
|---|-----|
| 1 | Убрать или упростить **demo-карточки** в `flow.php` (анимация) |
| 2 | Prefs: **merge localStorage ↔ Neon** надёжнее при login (не IP — device+browser ok) |
| 3 | Badge stack / niche в шапке карточки — polish по макету |
| 4 | Ticker CTA: опционально «Смотреть ленту» → как на pricing |

**Не в O123:** O107 trial backend · O105 pay logic · O121 ops.

**→ Coder:** § O123-w1 в `CODER_PROMPT` после O105 smoke

### § O121 — Web-админка `/ops/` · TG · прокси · Neon (**план**, 2026-06-05)

**Решение владельца (уточнение):** **не Tauri desktop** — всё в **админке на сайте** (`/ops/`), с браузера: поднять radar · сменить прокси · добавить TG-группу на acc · сколько чатов слушают · что уходит в Neon.

**Tauri `desktop/`** — legacy ПК, **не** цель O121.

| Блок | Функции |
|------|---------|
| **TG acc1/2/3** | Добавить группу/ссылку **на аккаунт** · список **куда вступили** · pending join · listen N чатов · статус ready/ошибка |
| **Прокси** | CRUD слотов: Bot API · Telethon accN · FL/Kwork/YouDo pool · **не** светить пароли в UI (mask + rotate) |
| **Probe** | Кнопка «Проверить» — TCP + **HTTPS** до Telegram / FL / Kwork (как `probe_all_proxies.py`) |
| **Failover** | Видеть active slot · ручной switch · auto-failover on/off · история переключений · алерт |
| **Радар** | pause/restart на `/ops/` · + bot-poll restart |

**Где сейчас:** **`/ops/` на сайте** (`owner_admin.py` + WP proxy) — health, control, лиды, support. **Tauri** — legacy ПК. Join/proxy — CSV + `.env` + CLI.

**Порядок (Lead, обновлено 2026-06-05 — решение владельца):**

**Ads + portfolio — последние.** Админка **до** рекламы: без панели владелец не может чинить FL/прокси сам.

### § O130 — ICQ AI Portfolio (**P2 · концепт**, 2026-06-07)

**Запрос владельца:** интерактивное AI-портфолио в стиле **ICQ 2000-х** (узкий UI, пиксель-иконки, звук `message.mp3`) · контакты = проекты (RawLead, Crystal Debt, FastAPI/Supabase, «Верстка Фigma/Битрикс — в бане») · чат с LLM-«секретарём» Никиты на базе Markdown RAG · FastAPI `/api/v1/chat/icq` · deploy на отдельный домен.

**Статус:** **концепт, не активировать** — владелец «ещё подумаем». Код **после** O129 v2 sign-off + soft ads (как **P-PORTFOLIO**).

**Связь:** эволюция **P-PORTFOLIO** / **Михалыч** · возможная замена brutalism `labs.rawlead.ru` (Design § D-P-PORTFOLIO v4) — **выбор владельца позже**.

| Фаза | Scope | Оценка Lead |
|------|-------|-------------|
| **v0** | HTML+Tailwind ICQ UI · звук · клик → окно чата (mock) | **1–2 дня** @coder |
| **v1** | FastAPI POST chat · OpenRouter · system prompt + **curated** KB (не весь repo) | **+2–3 дня** |
| **v2** | rate limit · deploy `labs.*` · Crystal Debt = скрины only (сервер paused) | **+1 день** |

**Lead замечания (зафиксировать до ТЗ):**
- **Neon**, не Supabase — один стек с RawLead; RAG = статические `.md` в репо или отдельная папка `portfolio-kb/`.
- **WebSockets не нужны** на v1 — обычный POST + typing indicator достаточно.
- **Публичный чат = расход OpenRouter** — лимит req/IP, без логов/секретов в KB.
- **ИИ-тон:** «куда встроить ИИ в бизнес» (P-PORTFOLIO ИИ v3 ✅) · **не** МИМО/БРАТЬ по ТЗ гостя.
- **«В бане» контакт** — easter egg / humor OK; не обещать live demo Crystal Debt.

**→ Design (когда созреет):** реф `image_4dbbb9.png` · ICQ vs brutalism — **A / B / гибрид** с владельцем.

| Волна | Что | Кто |
|-------|-----|-----|
| **spec** | Wireframes `/ops/`: сводка · боты · биржи · **прокси** · ingest | @lead-designer |
| **w1** | Прокси **read-only**: таблица слотов · статус/бан · probe · **ручной switch** | @coder |
| **w2** | Auto-failover **on/off** · clear ban · rotate (без plaintext в UI) | @coder |
| **w3** | TG acc + Neon ingest | @coder |
| **w4** | Proxy CRUD полный | позже |

1. ~~O117 + O120~~ ✅
2. **O121-spec** — **→ сейчас**
3. **O121-w1** — после spec
4. **O121-w2** — после w1

**Не в v1:** публичный URL ops без auth · root shell из UI.

**→ Coder:** после **O121-spec** от Design

### § O122 — Delist / «мертвые» ссылки на ленте (**план**, 2026-06-05)

**Боль владельца:** на `/lenta/` попадают заказы, по ссылке — **редirect на биржу**, карточки уже нет (сняли / нашли исполнителя).

**Уже есть (O65, код):**

| Механизм | Как работает | Ограничение |
|----------|--------------|-------------|
| **`delist_checker.py`** | Раз в **~1 ч** (`main.py`) · **20** visible лидов за проход · FL + Kwork GET · маркеры «заказ закрыт», «исполнитель найден», HTTP 404 | **Медленно** при большой ленте · **не** TG/YouDo |
| **`feed_retention` (O75)** | Скрыть visible **старше 7 дней** | Не ловит свежие «мертвые» ссылки |
| **O109** | Kwork: убран ложный маркер `"404"` в HTML | Были false positive; **false negative** (redirect без маркера) — возможны |
| **`/ops/`** | Кнопка «Скрыть» у лида вручную | Не массовый recheck URL |

**Grace:** первый recheck не раньше **6 ч** после L1 (`delist_checker`).

**Пробелы (O122):**

| # | Улучшение |
|---|-----------|
| 1 | **Чаще/больше batch** — env `DELIST_BATCH_LIMIT` / interval · приоритет **свежие** visible с `url` |
| 2 | **Redirect** — если финальный URL ≠ карточка / нет body-маркеров «живой» страницы → `source_gone` |
| 3 | **FL/Kwork** — расширить маркеры («архив», «закрыт для откликов»…) · лог `delist:lead=` |
| 4 | **Web `/ops/` (O121)** — «Проверить ссылки» · last run · `checked/delisted` · ручной прогон |
| 5 | **Опционально** cron на VPS отдельно от цикла бирж (если radar pause) |

**Связь:** O121 W2 «Neon ingest» + кнопка delist · не дублировать O65 — **усилить** backend, UI в O121.

**→ Coder:** после O117/O120 или параллельно w1 O121 · отдельный § когда согласуешь приоритет.

### Сейчас по плану (**Launch path**, 2026-06-05)

| # | Этап | Что | Статус |
|---|------|-----|--------|
| 1 | **Infra** | O117 Kwork timeout · O120 TG failover · O121-w0 ops | ✅ **2026-06-05** |
| 2 | **Monetization** | O105-w1 pay smoke · O107 trial 3 дня | **→ @coder** |
| 3 | **Quality** | O122 delist мёртвые ссылки | backlog P1 |
| 4 | **Launch gate** | E2E owner · stress/vault | после pay/trial |
| 5 | **GTM** | soft ads | после gate |

**E-polish волны A/B/C** ниже — **архив** (большая часть закрыта O116). Новые UX — через O121/O122/O113, не дублировать D1/L1.

### Сейчас по плану (архив E-polish, до O116)

| ID | Задача | Этап | Кто | Заметка |
|----|--------|------|-----|---------|
| **A1** | Убрать «**N лидов за 7 дней**» | E-polish | @coder | `rawlead-feed.js` · канон copy: «N лидов · по совместимости» — `LEAD_PRODUCT` c2 |
| **A2** | Пульт: скролл логов/статуса (sticky) | E-polish | @coder | § PULT-LOG-SCROLL-STICK · `rebuild-pult.bat` |

### Волна B — ЛК / данные (**E-polish**, P1, важнее A для доверия)

| ID | Задача | Этап | Кто | Заметка |
|----|--------|------|-----|---------|
| **B1** | **Навыки «общие для всех»** | E-polish | @coder | **✅ 2026-05-28** · v1.7.5 |
| **D1** | **UX ленты + шапка** | E-polish | @coder | § **LENTA-HEADER-UX** |
| **L1** | **ЛК: вход на prod (rawlead.ru), не localhost** | E-polish / 3f | @coder | § **CABINET-PROD-LOGIN** · **P0** |
| **L2** | **Страницы how/pricing/faq/contact** | E-polish | @coder | § **SITE-PAGES** |
| **L3** | **ЛК: навыки picker + retention 7d + console brand** | E-polish / 3f | @coder | § **CABINET-SKILLS-PICKER** · § **RETENTION-7D** |
| **B3** | **Бот: стоп процессов + admin-клавиатура только владельцу** | E-polish | @coder | § **BOT-OWNER-CONTROLS** · после D1 |
| **B2** | ЛК, регистрация, тексты c1–c4 | E-polish | — | **✅ E5** |

**Порядок E-polish:** **B1** ✅ → **D1** → **B3** → **A1** → **C1**.

### Волна C — mobile

| ID | Задача | Этап | Кто |
|----|--------|------|-----|
| **C1** | Mobile UX пересбор | E-polish | @lead-designer → @coder |

### § C1 — Mobile UX сайта (NEO + E-polish)

**Не путать:** это **не** «Контур 1» (Legacy-радар / @FLPARSINGBOT) и **не** отдельный «Conversion 1».  
**C1** = **Wave C, пункт 1** в E-polish — **mobile-first пересбор WP-сайта** rawlead.ru.

**Область:** `/lenta/`, `/cabinet/`, лендинг `/`, `/how/`, `/pricing/`, `/faq/` — viewport **390×844** (iPhone-class).

**Не в scope C1:** desktop-пульт Tauri (`desktop/`), Legacy/Site радары, TG-бот UI.

| Поверхность | Что проверить / пересобрать |
|-------------|----------------------------|
| **`/lenta/`** | sticky header + filter bar; горизонтальный скролл категорий; sheet «Навыки» / «Сортировка»; карточки 1 col; thumb-zone кнопок; FAB «Сообщить об ошибке» не перекрывает контент |
| **`/cabinet/`** | skills modal **сверху** (не bottom sheet); inbox компактный список; блоки подписка/уведомления stack на узком экране |
| **Лендинг** | hero readable; CTA «Смотреть ленту» / «Войти в кабинет»; без горизонтального скролла страницы |
| **TG-login** | виджет не обрезан; после login — redirect в `/cabinet/` без поломки layout |
| **Touch** | min tap target ~44px; dropdown/sheet закрывается tap outside (см. D1) |

**Канон mobile:** [`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § структура `/lenta/` · [`REFERENCE.md`](../../design/wp/REFERENCE.md) v4 · NEO-BRUTALIST tokens.

**Handoff Coder:** после CSS-спеки в `DESIGNER_PROMPT.md` → § **PRE-LAUNCH-UX** (mobile чек-лист u2).

**Решение владельца (журнал 2026-05-28):** «Mobile UX пересобрать» — в рамках NEO, не отдельный продуктовый pivot.

---

