# Решения и мысли владельца (журнал для Lead Architect)

**Назначение:** всё, что владелец сказал в чатах и что **ещё надо довести** в продукте/ops. Новый `@lead-architect` читает **этот файл первым** (после `ROADMAP.md` + `STATUS.md`), не опирается на память прошлых чатов.

**Обновляет:** только **Lead Architect** (по словам владельца или после приёмки). Coder/Designer сюда **не пишут**.

**Связь:** детальное ТЗ → [`CODER_PROMPT.md`](CODER_PROMPT.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md) · снимок → [`STATUS.md`](../common/STATUS.md).

---

## Как пользоваться (новый Lead)

| Шаг | Действие |
|-----|----------|
| 1 | Прочитать § **«Решения (обязательные)»** — не спорить без нового слова владельца |
| 2 | § **«Очередь правок»** — что в коде/docs ещё не закрыто; сверить с `CODER_PROMPT` § в шапке |
| 3 | § **«Legacy на ПК»** — не просить владельца ▶ Legacy |
| 4 | Новая мысль владельца → **одна строка** в § «Журнал» + при необходимости § в `CODER_PROMPT` / `ROADMAP` |
| 5 | Принято владельцем → перенести в `STATUS` (✅), из очереди убрать или пометить ✅ |

---

## Решения (обязательные) — 2026-05-28

| # | Решение | Следствие для Lead/Coder |
|---|---------|-------------------------|
| **O1** | **Сначала довести сайт**, stress **после дизайна** | PRE-PROD **после** SFW → Design → PM copy → Coder финал (O20); **не** между SFW и дизайнером |
| **O2** | Ставка **Plan B**: `/lenta/` + `/cabinet/` **590–990 ₽/мес** | Vision v0.11; не возвращать «только портфолио» |
| **O3** | **Freelancehunt снят навсегда** | Только `fl`, `kwork`, TG whitelist в `PUBLIC_FEED_SOURCES` |
| **O4** | **Один VPS** (rawlead.ru): WP + API + радары | § **P5-E2-VPS** в `CODER_PROMPT`; PC не 24/7 |
| **O5** | **@FLPARSINGBOT** = dogfood (полный ИИ, черновик); **@rawlead_bot** = Site/подписчики позже | Два бота, два `.env`; Site **не** шлёт биржи владельцу в TG (`SITE_NOTIFY_OWNER=0`) |
| **O6** | Владелец = **подписчик #0** после polish | § **3f-OWNER-BETA** → потом § **3h** биллинг |
| **O7** | Не жечь OpenRouter на старом хвосте L1 | BACKLOG-CLEAR ✅ apply; не replay 1200+ подряд |
| **O8** | Лента «40+ мин» — **баг/очередь**, не норма | FEED-FRESHNESS + Site ▶; верх FL/Kwork &lt; 15 мин в активные часы |
| **O9** | Фильтры Site vs Legacy **разные файлы** | `FILTERS_SITE.md` / `FILTERS_LEGACY.md`; спорные МИМО по scope §0i — не автоправка без Product |
| **O10** | **Legacy ■ на ПК — по желанию**; если ▶ — **не должен сам гаситься** | Баг § **LEGACY-SELF-STOP** в `CODER_PROMPT` · не путать с «держи выключенным» |
| **O11** | **Две скорости:** anon `/lenta/` ~15 мин; платники мгновенно ЛК+TG | §0j · **TWO-SPEEDS-COPY/UI** · код **3r** после 3h |
| **O12** | **Оплата — Telegram Stars** (не ЮKassa) | § **3f-C-STARS** P0 · **O29** · **до Design** |
| **O13** | **Вход в ЛК на rawlead.ru** — без localhost | § **CABINET-PROD-LOGIN** · BotFather domain = `rawlead.ru` |
| **O14** | **Страницы сайта** — не только главная/лента/ЛК | § **SITE-PAGES** · how, pricing, faq, contact (footer уже ссылается) |
| **O15** | **ЛК: навыки** — picker из **полного L1-пула** (`skills_catalog.py`), не только из прошедших заказов; окно **сверху** страницы | § **CABINET-SKILLS-PICKER (L3)** |
| **O16** | **Retention Neon:** лиды старше **7 дней** удалять (не засорять БД) | § **RETENTION-7D** · не трогать users/user_tags/subscriptions |
| **O17** | **Console brand:** `▲ RawLead Architecture by Rode51 ▲` в devtools | § **CABINET-SKILLS-PICKER** l3-7 |
| **O19** | **ЛК UX:** merge guest-навыков после TG-login; avatar в шапке; не путать вход и /start бота | § **LK-UX-POLISH** |
| **O18** | **HTTPS rawlead.ru** — убрать «Не защищено» | § **DEPLOY_VPS.md** § 5b · **✅** certbot |
| **O20** | **Сначала функции сайта + полная приёмка владельцем**; **Design/PM только после ✅ приёмки** | § **SITE-FUNCTIONS-WAVE** · § **SITE-ACCEPT-GATE** · NEO **⏸** · **не параллельно** с Coder |
| **O21** | **Перед трафиком — один прогон «ИИ-тестировщика»** + нагрузочный stress | § **PRE-PROD-UX-AUDIT** + § **PRE-PROD-STRESS** · **после** финала Coder (O20 волна 4) |
| **O22** | **ЛК:** sort + min_match 30–100% | § **LK-FEED-FILTERS** · **⚠️ cabinet-feed отменён → O23** |
| **O23** | **Лента = feed; ЛК = inbox откликов** | § **CABINET-INBOX-O23** · **Free TG без Stars = anon** (15 мин, без кнопки) **✅ владелец** |
| **O24** | **Каталог навыков v0.3:** 4 ниши, 2 уровня, ≤6 тегов → **O46 cap 12**, один `llm_integration`, без абстракций в UI | § **TAGS-V0.3** · **✅ Lead verify 2026-05-28** |
| **O25** | **Синтетические просмотры** на карточке: ~30 «онлайн», выше на delay-ленте, без палева | § **FEED-CARD-UX** f1–f2 |
| **O26** | **100% match** — особое выделение карточки (`keyword_match === 100`) | § **FEED-CARD-UX** · **✅ Lead verify** |
| **O27** | **L2 инструменты** на карточке — не только черновик | § **L2-TOOLS-FIX** · **→ Coder до Design** |
| **O28** | **Push match** в @rawlead_bot подписчикам | § **3f-A4-MATCH-PUSH** · **→ Coder до Design** |
| **O29** | **Stars** — живая оплата (не заглушка) | § **3f-C-STARS** P0 · **→ Coder до Design** |
| **O30** | **Push match:** не top-3 глобально — **каждому paid** при `keyword_match ≥ порог`; порог **настраивает пользователь** (default **60%**, диапазон 30–100) | § **MATCH-PUSH-V2** · отменяет top-K=3 (O28 MVP) |
| **O46** | **Match F2:** `km = matched/lead_tags×100` · «ИДЕАЛЬНО ✦» только при ≥2 тегах лида и полном покрытии · cap навыков **12** | § **PRE-STRESS-PACK O42** · 2026-05-29 |
| **O47** | **L1 tags strict:** Joomla/Bitrix ≠ wordpress_dev · post-validate · golden tests | § **PRE-STRESS-WAVE-2** · **P0 до stress** |
| **O48** | **Draft reliability:** log 503 · retry · rate limit · UI «Повторить» · scale | § **PRE-STRESS-WAVE-2** · **P0** |
| **O49** | **L2 premium v2:** без «Готов…» · шаги · 9/10 quality | § **PRE-STRESS-WAVE-2** |
| **O50** | **TG push:** полная карточка + callback «Сгенерировать» → draft в TG + ЛК | § **PRE-STRESS-WAVE-2** |
| **O51** | **ЛК grid 2 col** как лента | § **PRE-STRESS-WAVE-2** |
| **O62** | **Draft без порога km:** 0% — можно откликнуться · km только информативен | § **O61** · paid draft на любом lead |
| **O63** | **Новые парсеры:** YouDo · Freelance.ru · FreelanceJob · Пчёл.нет · **cross-source dedup** | § **O63** · **→ волна 2026-06-01** |
| **O72e** | **Judge gate:** L2 ≥4/send ≥50% · L1 ≥70% · **O72e-9** hierarchical L1 + A/B | § **O72e-9** |
| **O79** | **FL+Kwork 1 мин/цикл на VPS** → **ротация прокси** (`FL_PROXY_URLS`, `KWORK_PROXY_URLS`) · **отдельный пул**, не `TELETHON_PROXY_*` | § **O79** · `.env` на VPS — владелец |
| **O82** | **Match moat:** **совместимость стека** (не «качество заказа») · без чипов «Брать/Сомнительно» на карточке · CTA «Добавь навыки» **только anon без навыков** | § **O82-w1b** · F2+ w2 |
| **O83** | **«Инструменты» в ленте — только auth** (anon не видит L2 tools) | § **O83** · s **O82-w1** |
| **O89** | **Уникальный отклик:** shared pro + flash-lite rephrase per user | § **O89** · после O90+O91 |
| **O90** | **Ingest lag:** `source_published_at` · отчёт биржа→Neon→L1 · `/ops/` | § **O90** |
| **O91** | **Ночной watchdog:** пульс цикла · алерт TG · автоперезапуск · health прокси | § **O91** · **не** второй парсер |
| **O92** | **Skill Tree в ЛК:** 4 ниши → ветки tags (RPG-style) | § **O92** · **✅ v1 deploy 1.11.30** |

---

## § O90 — Ingest lag (биржа → Neon → лента)

**Решение владельца 2026-06-02:** нужна статистика «когда на бирже» vs «когда у нас» и почему бывают провалы/пачки.

| Метрика | Формула |
|---------|---------|
| **ingest_lag** | `created_at - source_published_at` |
| **l1_lag** | `l1_completed_at - created_at` |
| **feed_lag** | `l1_completed_at - source_published_at` (полный путь) |

**Колонки Neon:** `sql/016_leads_ingest_timestamps.sql` · парсеры пишут `source_published_at` · L1 — `l1_completed_at`.

**Отчёт:** `scripts/ingest_lag_report.py` · p50/p95 по `fl`/`kwork`/`tg` · карточка `/ops/`.

**Не путать** с O11 (15 мин задержка anon ленты) — это product delay, не lag парсера.

---

## § O91 — Uptime: пока владелец спит

**Решение владельца 2026-06-02:** подстраховка от «радар молчал 3 ч → пачка → отписки».

| Слой | Решение | Зачем |
|------|---------|--------|
| **Пульс** | SQLite `status_main_last_cycle_at` + Neon `MAX(created_at)` | видеть «живой fetch», не только `systemctl active` |
| **Watchdog** | `rawlead-ingest-watchdog.timer` **каждые 5 мин** → TG владельцу | gap цикла >15 мин · 0 вставок >20 мин · L1 backlog >120 |
| **Авторестарт** | `systemctl restart rawlead-radar` если gap >25 мин и **не** пауза | hung process не ловит `Restart=on-failure` |
| **Прокси** | TCP probe pool (как Telethon) + skip мёртвых в `exchange_proxy` | все 4 упали → алерт, не тихий 0 |
| **Внешний** | UptimeRobot → `GET /health` API (опц.) | VPS жив, API отвечает |

**❌ Не делаем сейчас:** второй полный парсер на том же VPS (те же прокси/IP — не даёт отказоустойчивости). **Опц. v2:** cold standby VPS в другом DC — после GTM.

**❌ Не делаем:** постоянная Sonnet/ИИ «как админ» — дорого; правила + дешёвый watchdog.

**Прокси-страховка (владелец):** см. § **O91-proxy** в `CODER_PROMPT.md` · `DEPLOY_VPS.md`.

---

## § O89 — Reply uniquify (anti-ban + маржа)

**Решение владельца 2026-06-01:** оставить **один тяжёлый** запрос при парсинге (`leads.reply_draft`, Gemini pro, O57/O72e). При клике платного юзера **«Написать отkлик»** — не отдавать тот же текст всем: прогон через **самую дёшевую** сетку (OpenRouter: `gemini-2.5-flash-lite` или аналог ~4o-mini) с жёстким промптом **rephrase-only**.

**Промпт-ядро (черновик для Coder):**

> Ты — рандомизатор откликов. Возьми готовый экспертный текст и перепиши: другая структура предложений, синонимы, другое приветствие (но «Здравствуйте!» допустимо). **Полностью сохрани** техническую суть, стек из ТЗ, ключевые вопросы заказчику. **Запрещено:** цена, срок, бюджет, «от X ₽». На выходе — уникальная формулировка, живой язык.

**Архитектура (целевая):**

| Слой | Когда | Модель | Куда |
|------|-------|--------|------|
| **Base** | ingest / regen shared | Gemini **pro** | `leads.reply_draft` (один на lead) |
| **Uniquify** | **каждый** paid, **1-й** клик на lead | **flash-lite** / mini | `user_lead_replies.reply_draft` (**per user**) |

**❌ Неверная модель:** «первый юзер = base, остальные = rephrase».  
**✅ Верная:** base **не отдаётся** юзеру как финал (кроме fallback при fail mini). Юзер A и B **оба** получают **свой** rephrase от **одного** `leads.reply_draft`.

**Concurrency (не задваивать):**

| Сценарий | Поведение |
|----------|-----------|
| **Два разных юзера**, один lead, одновременно | Два flash-lite → две строки `user_lead_replies` (PK `user_id+lead_id`) · тексты разные |
| **Один юзер**, двойной клик / два таба | Lock или job `ON CONFLICT DO NOTHING` на `(user_id, lead_id)` · второй ждёт poll · **один** rephrase |
| **Shared base ещё пуст** | `lead_draft_jobs` — один pro на lead · затем uniquify per user |
| **Повторный клик** | Cache из `user_lead_replies` — **без** LLM |

**Variation seed:** `user_id` (+ `lead_id`) в промпт mini.

**Код сейчас:** `materialize_shared_draft_for_user` — **копия** shared без LLM → риск одинаковых откликов на бирже.

**Guardrails (обязательно):** те же validators O72e (Здравствуйте, ban price/deadline, cliche) · retry 1× при fail · fallback = shared (лучше копия, чем мусор).

**Copy / UX (Product + Design):** везде акцент **«уникальный отклик»** — `/lenta/` кнопка/tooltip · `/pricing/` · `/how/` · post-login · не пугать «все получают одно и то же». Формулировка честная: *«AI адаптирует формулировку под вас»*, не «пишет с нуля по вашему резюме» (profile rephrase — опционально v2).

**Экономика:** ~$0.001–0.003 за клик vs ~$0.05–0.15 full L2 · маржа сохраняется.

**Gate:** не ломать O72e — judge меряет **base** shared; uniquify — отдельный smoke (5 пар base→rewrite, Sonnet «send не хуже»).

**Handoff:** § **O89** в `CODER_PROMPT.md` · copy → `@lead-product` · UI → `@lead-designer`.

---

## § O92 — Skill Tree профиля (UX-first, без риска для L1)

**Решение владельца 2026-06-02:** в `/cabinet/` заменить плоский список навыков на дерево:
- 4 корня: dev / design / marketing / text
- внутри — подветки и canonical-tag чекбоксы
- payload в API остаётся массивом slug (`["yandex_direct","smm"]`)

**Критично (guardrail v1):**
- **не менять** L1 prompt / sanitize / judge / модели
- **не менять** схему Neon
- это только UI-подача + UX выбор навыков

**Почему не «магия»:** дерево повышает качество ввода юзера, но «идеальный» match достигается только с контролем шума и метриками.

**Статус O92 v1 (2026-06-02):** deploy `1.11.30` — **interim**, не финальный UX. Не переносить в `/lenta/` до O93.

**План по шагам (legacy O92):**
1. ~~UI-tree~~ interim принят
2. ~~Ограничения max 12~~ ✅
3. ~~Telemetry~~ ✅
4. A/B — **отложено** до O93
5. Веса/auto-priorities — после O93

---

## § O93 — Настоящее Skill Tree (направление → стек → инструменты)

**Решение владельца 2026-06-02 (финал):** текущий O92 — «каша» (направления, языки и библиотеки на одном уровне). Пример: выбрал «Telegram-боты» — **не должен** отдельно тыкать `aiogram`/`Telethon` для match.

**Целевая модель (3 уровня):**

| Уровень | Примеры | Роль в match | UI |
|---------|---------|--------------|-----|
| **1. Направление** | WordPress разработка, Telegram-боты, Парсинг, Техническое SEO | **основной выбор** — достаточно для match | всегда видно |
| **2. Стек** | Python, JavaScript, PHP, Django, FastAPI | опциональное уточнение | раскрывается под направлением |
| **3. Инструменты/библиотеки** | aiogram, Telethon, Figma (tool) | **не обязательны** для match; для узкой настройки / будущего отклика | только после выбора направления |

**Правила match (обязательно в O93):**
- Выбор **направления** автоматически покрывает дочерние canonical-теги в `keyword_match` (parent → children expand на бэке).
- Дочерние теги **не показываются** на верхнем уровне picker (L3 под раскрытием parent).
- L1 / judge / Neon schema **не меняем** на первом этапе O93 — меняем **каталог-метаданные + match + UI**.

**Решение владельца 2026-06-02 (rev · PM вариант B):**

Picker dev — **два блока**. PM: «B — две группы (по задаче + по технологии, **гибрид выше**)» = лучший вариант из спора, **не** третий пункт «Гибрид минимальный».

| Блок UI | Содержимое | Зачем |
|---------|------------|-------|
| **По задаче** | Telegram-боты, WordPress, Парсинг, API, ИИ… | «я делаю ботов / сайты» |
| **По технологии** | **Python** + **JavaScript** Tier A | «просто Python/JS-разработчик» |

- Python → django, fastapi · JavaScript → react (expand на бэке)
- **Не выбрано:** «Гибрид» (только python Tier A, javascript Tier B)

**Стоп-лист до O93:**
- ❌ O92 parity в `/lenta/`
- ❌ O92b rollout новых тегов в UI-tree
- ❌ GTM / soft ads

**Порядок:** PM+Design spike (каталог v0.4 hierarchy) → Coder (match expand + tree UI cabinet+feed) → smoke → E2E.

**Статус O93 (2026-06-02):** deploy `1.12.0` — dev tree в `/cabinet/` + `/lenta/`; match expand на бэке; design/marketing/text — **плоский picker** (expand-таблицы в коде есть, UI нет).

---

## § O93.1 — UX: авто-раскрытие L3

**Запрос владельца 2026-06-02:** при клике на L1 (Python, Telegram-боты…) **сразу** показывать дочерние чипы — **не** отдельная стрелка ▾.

**Решение Lead:** принять. O93-w1 изначально требовал второй клик — это лишний шаг; меняем только UX (CSS/JS), match expand не трогаем.

**→ Coder** (hotfix после E2E smoke или параллельно, ~1 PR).

---

## § O94 — Каталог v0.5: research + все 4 ниши в tree

**Запрос владельца 2026-06-02:**
1. Почему двухблочный tree только в **Разработке** — нужно **связать** каталог, match и UI для design / marketing / text.
2. **Deep research** — нормально заполнить таблицу (не 2 фреймворка под Python «на глаз»).
3. Стеки людей разные — расширить L2/L3 из рынка + `pending_tags`, не ломая UX (лимит чипов, parent dedupe).

**Почему O93 был только dev:** сознательный pilot на самой «кашистой» нише; expand для design/marketing уже в `EXPAND_MAP`, но без PM dedupe (parent/child overlap в v0.4) и без wireframes — риск повторить O92.

**Решение Lead:**
| Шаг | Кто | Что |
|-----|-----|-----|
| 1 | **PM + research** | `SKILLS_TOOLS_RESEARCH_PROMPT.md` → **каталог v0.5**: L1/L2/L3 по 4 нишам; Python/JS стеки (Flask, Vue, Node→JS, pandas…); dedupe design/marketing; что Tier A vs L3-only |
| 2 | **Owner gate** | approve таблицу v0.5 (не auto в Neon) |
| 3 | **Design** | wireframes subheads для design/marketing/text (где 2 блока уместны — «по задаче» / «по инструменту») |
| 4 | **Coder** | `EXPAND_MAP` + `L3_BY_PARENT` + picker API + UI все ниши; O92b только **approved** теги |
| 5 | **O93.1** | авто-раскрытие L3 (можно раньше v0.5) |

**Стоп до v0.5 approve:** массовое добавление L3 в UI без research (иначе снова «каша» и шум в match).

**Связка (единая цепочка):** research → `SKILLS_TOOLS_CATALOG.md` → `skills_catalog.py` (entries + expand + L3) → `rank.py` expand → picker cabinet+feed → L1 judge aliases.

**Статус v0.5 (2026-06-02):** **✅ approve владельца** → **O94-code** (@coder) → **O94-L1** (промпт + targeted bench, не full O72e).

---

## § E2E-UX-WALK — прогон «обычный пользователь» (Playwright MCP)

**Запрос владельца 2026-06-02:** агент открывает браузер, «щупает» UI как фрилансер — не только tree, но **скорость, поиск кнопок, выбор навыков**.

**Когда:** после **O93-w2b deploy** (modal на prod); повтор после **O94-code**.

**Инструмент:** MCP `user-playwright` (`browser_navigate`, `browser_click`, `browser_snapshot`, `browser_network_requests`).

**Сценарий (390×844 + desktop 1280):**

| # | Шаг | Метрика / вопрос |
|---|-----|------------------|
| 1 | `/lenta/` cold load | TTFB, первый paint, «20 заказов» видно ≤3 с |
| 2 | Найти «Навыки» без подсказки | ≤2 с, ≤2 взгляда (filter bar) |
| 3 | Открыть modal | full sheet, counter 0/12, scroll niches |
| 4 | Разработка → Python | L3 **сразу** без ▾ |
| 5 | Применить 3 навыка | badge на триггере, match % на карточках |
| 6 | Сортировка | «Дата ▾» → «По совместимости ▾», порядок меняется |
| 7 | `/cabinet/` login flow (guest → login) | навыки modal parity с лентой |
| 8 | Mobile sheet «Фильтр» | навыки **не** только внутри sheet — отдельный modal |

**Deliverable:** `docs/problems/` или секция в `STATUS` — таблица find/blocker/P0–P2. **Не** правки кода в том же чате — triage → Coder.

**Lead 2026-06-02 (prod до deploy):** dropdown 420px · «Сортировка ▾» · «Навыки ▾ ▾» — подтверждено Playwright.

---

## § O92b — Auto-learning только с human gate

**Проверка 2026-06-02 (Neon):** есть рабочий baseline `public.pending_tags` (`tag`, `category`, `first_seen_at`, `seen_count`) — это уже контур сбора кандидатов из L1 unknown tags.

**Решение владельца/Lead:** не делать full-auto запись в canonical каталог. Держим premium-качество через semi-auto pipeline:
1. Сбор кандидатов (`pending_tags`) и ранжирование
2. Очистка/нормализация (`alias_to_existing`, typo, шум)
3. Ручной approve owner/lead
4. Только approved идут в каталог и в Skill Tree
5. После rollout — smoke/judge check

**Зачем:** избежать шумовых/ложных тегов и деградации matching.

---

## Legacy сам гасится после ▶ (баг, 2026-05-28)

**Не путать** с O10: владелец **хочет** ▶ Legacy, но пульт через **~15 с** снова **■**.

| Шаг | Что происходит |
|-----|----------------|
| 1 | ▶ → `radar_control` поднимает `neon_legacy_consumer.py` → в `radar_legacy.log` строка `neon:старт` |
| 2 | Воркер **падает** или **не попадает** в `count_radar_workers` за 15 с |
| 3 | `radar_control` считает старт провалом → **Stop** всех → на пульте снова **■** |
| 4 | В логе — серия `neon:старт` без стабильных `neon:цикл` |

**Корень (проверено 2026-05-28):** в `neon_legacy_consumer.py` **не было import** `process_legacy_neon_listing`, `short_err` → **NameError на 1-м цикле** → процесс умирает → пульт ■. **Исправлено:** `from lead_pipeline import …`.

**Прочие причины:**

- `data/radar_legacy_exchanges.log`: **`ValueError: sleep length must be non-negative`** (старый traceback; в `src` уже `max(0, …)`).
- Пульт **не пересобран** → старый `desktop.exe` без фиксации скролла.
- Два ярлыка / orphan `pythonw` → гонка и `neon:дубль`.

**Что делать владельцу:** `scripts\rebuild-pult.bat` → `stop-radar-desktop-full.vbs` → один ярлык Legacy → ▶ → смотреть красный баннер (текст ошибки старта) и `data\radar_legacy_exchanges.log`.

**Coder:** § **LEGACY-SELF-STOP** · § **PULT-LOG-SCROLL-STICK** в `CODER_PROMPT.md`.

---

## Legacy на ПК — когда держать ■

| Ситуация | Действие |
|----------|----------|
| Качаешь только `/lenta/` | Достаточно **Site ▶** |
| Нужен dogfood @FLPARSINGBOT на ПК | **Legacy ▶** (после фикса self-stop) |
| После **P5-E2-VPS** | Оба ■ на ПК; радары на сервере |

**После P5-E2-VPS:** на ПК `stop-radar-desktop-full` → оба ■; на VPS `rawlead-radar` + `rawlead-radar-legacy`; управление dogfood — **/status /pause** в @FLPARSINGBOT.

---

## Бэклог владельца (группы · приоритет Lead)

**Правило:** запись в чат → сюда; **код** — когда этап активен в `ROADMAP` / шапке `CODER_PROMPT`. Срочно — только по слову «сейчас».

### Сейчас по плану (после Legacy ✅)

| # | Этап | Что | Кто |
|---|------|-----|-----|
| 2 | **E-vps** | P5-E2-VPS — радары на сервер, ПК не 24/7 | **@coder** |
| 3 | **E-polish** | Волны A → B → C ниже | @coder + @designer |
| 4 | **E-3f** | ИИ-агент «Написать отклик» | **@coder** |
| 5 | **E-stress** | PRE-PROD-STRESS | после polish |

### Волна A — быстрый UX ленты (**E-polish**, P1)

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

## Очередь инженерии (roadmap, не чат)

| Приоритет | Что | Где ТЗ | Статус (2026-05-28) |
|-----------|-----|--------|---------------------|
| **P0** | **Legacy ▶ не гасится** | § LEGACY-SELF-STOP | **✅** import `lead_pipeline` |
| **P0** | Пульт: скролл логов | § PULT-LOG-SCROLL-STICK | код ✅ · rebuild ⏳ |
| **P0** | Site+TG + Legacy consumer **на VPS** | § **P5-E2-VPS** | **✅ код** · деплой — владелец |
| **P0** | **Пауза раздельно** Site vs FLPARSING | P5-E2 **e4** | **✅** `radar_paused_site` / `radar_paused_legacy` |
| **P1** | ИИ-агент «Написать отклик» + push | § **3f-OWNER-BETA** | после живой ленты на проде |
| **P1** | Биллинг 590–990 ₽ | § **3h** | после 1-го внешнего юзера / сценария #0 |
| **P1** | PRE-PROD-STRESS S1–S6 | `PRE_PROD_GATE.md` | **после** E-polish + VPS |
| **P2** | TG в фильтре ленты (`source=tg`) | § TG-FEED-SOURCES | код ✅ |
| **P2** | Freemium · пауза подписки | ROADMAP 3p, 3q | после 1-го платящего |
| **P1** | **O63** парсеры YouDo · Freelance.ru · … | § **O63** | **→ w1 сейчас** |
| **P0** | **O82** Match UX v2 — breakdown + живой % | § **O82** | **→ после O63-w1 · до рекламы** |
| **P2** | **O11** задержка 15 мин на anon `/lenta/` vs instant TG paid | ROADMAP · Product | после 3f + биллинг |

**Волна 2026-05-28 принята Lead** — детали: [`STATUS.md`](../common/STATUS.md) · [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md).

---

## Журнал (хронология, кратко)

| Дата | Мысль / запрос | Куда ушло |
|------|----------------|-----------|
| 2026-05-28 | Довести сайт, stress потом | O1, ROADMAP, FOR_YOU |
| 2026-05-28 | Убрать Freelancehunt | O3, § DROP-FREELANCEHUNT |
| 2026-05-28 | Лента stale ~40 мин, очередь L1 ~1253 | O7–O8, BACKLOG-CLEAR, FEED-FRESHNESS |
| 2026-05-28 | Радар на VPS, FLPARSING = пульт в TG, PC не 24/7 | O4–O5, P5-E2-VPS |
| 2026-05-28 | Legacy **сам гасится** после ▶ — баг, не «держи ■» | § Legacy сам гасится |
| 2026-05-28 | Пульт: при скролле логов не уезжать вниз | § PULT-LOG-SCROLL-STICK |
| 2026-05-28 | Записать все мысли для нового Lead | этот файл |
| 2026-05-28 | Coder доработал — Lead проверяет | STATUS § 2026-05-28; backlog ~102 без L1 |
| 2026-05-28 | Legacy ✅; triage бэклога; A1/A2/B1/C1 | § Бэклог владельца |
| 2026-05-28 | Убрать «N лидов за 7 дней» | **A1** · E-polish |
| 2026-05-28 | Mobile UX пересобрать | **C1** · E-polish · Designer |
| 2026-05-28 | UX: навыки закрыть кликом снаружи; sticky Применить; how/faq/contact только footer; CTA «Вход в ЛК» | **D1** · § LENTA-HEADER-UX |
| 2026-05-28 | Оплата — **Telegram Stars**, не касса РФ на старте | **O12** · § 3f-C-STARS |
| 2026-05-28 | ЛК на prod → localhost; только 3 страницы | **O13–O14** · § CABINET-PROD-LOGIN · SITE-PAGES |
| 2026-05-28 | Ревизия docs — STATUS/TASKS без дублей | TASKS_HISTORY 2026-05-28 |
| 2026-05-28 | Лента 15 мин free vs instant TG paid — тексты PM/Design | **O11** · TWO-SPEEDS-COPY/UI |
| 2026-05-28 | ЛК = inbox откликов; «Написать отклик» на `/lenta/` для paid; L2 сценарий | **O23** · § CABINET-INBOX-O23 |
| 2026-05-28 | Free TG без Stars = anon (15 мин, без кнопки) до оплаты | **O23** · подтверждено владельцем |
| 2026-05-28 | Теги v0.3: 4 ниши, picker 2 уровня, max 6, llm_integration, без каши | **O24** · § TAGS-V0.3 · принято |
| 2026-05-28 | Product v0.3 финал 51 тег → Coder + AI.md | **O24** · SKILLS_TOOLS_CATALOG v0.3 |
| 2026-05-28 | Сначала все функции сайта, дизайнер/PM потом | **O20** · § SITE-FUNCTIONS-WAVE |
| 2026-05-28 | **Ждём:** полная приёмка функций на prod → потом PM и Design (**не параллельно**) | **O20** · § SITE-ACCEPT-GATE |
| 2026-05-28 | Stress и ИИ-прогон сайта — **после дизайнера**, один раз перед трафиком | **O21** · PRE-PROD-UX-AUDIT + k6 |
| 2026-05-28 | ЛК: sort по времени; min match 30–100%; скрыть 0% overlap | **O22** · § LK-FEED-FILTERS |
| 2026-05-28 | Picker Tier B → copy **«Ещё навыки»** / **«Свернуть»** (не «редкие») | design · TAGS t3-4 |
| 2026-05-28 | Просмотры: eye icon, рост по age, не 36 на «только что» | **O25b** · § FEED-CARD-UX |
| 2026-05-28 | Карточка: 100% match — особое выделение | **O26** · § FEED-CARD-UX · ✅ Lead verify |
| 2026-05-28 | **До Design:** L2 tools на карточке, push бота, Stars — не заглушка | **O27–O29** · § PRE-DESIGN-BLOCKERS |
| 2026-05-28 | **Push:** не top-3 — всем paid при match ≥ порога; порог user (default 60%) | **O30** · § MATCH-PUSH-V2 |
| 2026-05-28 | **Gate ✅** — функции сайта приняты на prod; старт Design + PM | **O20** · § SITE-ACCEPT-GATE |
| 2026-05-29 | В ленте «только Kwork» — проверить FL fetch + L1→visible; не путать с «парсер мёртв» | **O31** · § FEED-FRESHNESS · § FL-VISIBILITY-CHECK |
| 2026-05-29 | **Pipeline:** dedup→filter→Neon→L1 parallel, **без очереди** на новых; drain off site | **O34** · § PIPELINE-INSTANT-O34 |
| 2026-05-29 | ~~Instant feed O33~~ | заменено **O34** |
| 2026-05-29 | **`/status` пересобрать** — читаемый, блоками, правильный бот | **O32** · § BOT-STATUS-V2 |
| 2026-05-29 | **План дня:** UI/UX волна 2 · TG-регистрация · stress · аудит Gemini 2M | **O35–O38** · см. § «План дня» ниже |
| 2026-05-29 | **Ускорить ленту, но стабильно** | **O39** ✅ deploy · цикл **~71 с** |
| 2026-05-29 | **Stress не сейчас** — сначала Wave 2 UI/UX | **O35** · O37 ⏸ |
| 2026-05-29 | **Хвост 153 без L1** — clear по возрасту, не токенами ИИ | **O40** · § BACKLOG-TAIL-CLEAR · параллельно Design |
| 2026-05-29 | **Wave 2 prod ✅** — сначала добить вопросы с Designer, потом дальше (stress/Coder) | **O35f** · O37 ⏸ до UI OK |
| 2026-05-29 | **Wave 2 недостаточно** — белая карточка на жёлтом «ущербно»; хочет Gumroad-level; hero + card preview пересобрать | **O41** · → @lead-designer Wave 3 brief |
| 2026-05-29 | **Радар молчал ~42 мин** — CRLF deploy/*.sh exit 127 | **✅ fix Lead ops** · STATUS INCIDENT |

### План дня владельца (2026-05-29)

| # | Намерение | Lead-решение | Кто | Когда |
|---|-----------|--------------|-----|-------|
| **O35** | Wave 2 UI/UX theme | Coder v1.9.0 + deploy VPS | **✅ prod** |
| **O35f** | Вопросы по UI с Designer | @lead-designer / @designer | **→ сейчас** |
| **O37** | Stress test | § PRE-PROD-STRESS | **⏸ после O38** |
| **O38** | Полный аудит Gemini ~2M | [`problems/2026-05-29-gemini-full-audit.md`](../../problems/2026-05-29-gemini-full-audit.md) | **⏸ после приёмки O42–O45** |

**Порядок (обновлено 2026-05-29):** **O42–O45** Coder → **приёмка владельца** → **O38 audit** → **O37 stress**.

**Не параллелить в Coder:** один чат = одна задача (`SCALE.md`).

*Дописывай новые строки снизу; не удаляй старые без согласия владельца.*

| 2026-05-29 | **PRE-STRESS-PACK** | Match F1–F4 · Push · L2 · `/ops/` admin | **O42–O45** → приёмка → **O38** → O37 |
| 2026-05-29 | **O52c отменено** | ИДЕАЛЬНО ✦ только ≥2 тега (F2) — 100% с 1 тегом без ✦ OK |
| 2026-05-29 | **Wave-2 accept** | O52–O58 · theme v1.10.9 | **✅ закрыта** |
| 2026-05-29 | **D-O39 ✅** | Design prod as-is · docs sync (feed-cabinet, REFERENCE) | **принято** |
| 2026-05-30 | **O37b** | tools пусто после draft · test-акки (не yandex влад.) · @rawlead_bot · UX review ПК/моб | **✅ b1** · b4 **❌** |
| 2026-05-30 | **O37c код** | ux_audit U1–U10 + LLM | **✅ Lead verify** |
| 2026-05-30 | **O37c-a** | mint JWT acc1 | **✅ Lead verify** |
| 2026-05-30 | **D-O40** | mobile rebuild brief | **✅ Lead verify** |
| 2026-05-30 | **WAVE-UX-MOBILE** | код v1.11.4 M1–M5 | **✅ Lead verify** |
| 2026-05-30 | **O68** | «Отклик ✓» — вниз карточки, не в шапке | **→ Coder** |
| 2026-05-30 | **S6 ✅** | владелец приёмка глазами | **принято** |
| 2026-05-30 | **Owner draft 9/10** | 1 draft завис · 1 разбор недоступен · soft ads после O72 | **⚠️** |
| 2026-05-30 | **O75** | Лента: delist закрытых + скрыть **>7 дней** | **→ backlog** |
| 2026-05-30 | **O74** | TG push: **прямая ссылка** на заказ на бирже | **→ backlog** |
| 2026-05-30 | **O63** | YouDo · FL.ru · FreelanceJob · Пчёл.нет | **backlog** |
| 2026-05-30 | **O72+** | Аудит разборов ИИ + **подгон промпта** по отчёту | **→ Coder** |
| 2026-05-30 | **O73** | Heatmap (Metrika/Clarity) до масштабирования рекламы | **📋 backlog** |
| 2026-05-30 | **Реклама проекта** | после owner 5× draft + O72 baseline | **⏸** |
| 2026-05-31 | **O72b tools** | **не** auto-expand canonical 51; tools ≠ skills; правим **метрику аудита** + KNOWN_TOOLS whitelist | **✅ Lead verify** |
| 2026-05-31 | **O72c judge** | **Sonnet 4** (`OPENROUTER_MODEL_JUDGE`) · env Lead · O76 UX перед рекламой | **✅ код · ❌ L2 gate** |
| 2026-05-31 | **O77 views** | Hot-лиды: **медленный** набор просмотров · &gt;1ч быстрее · «я первый» | **📋 backlog** |
| 2026-05-31 | **O78 admin** | Web admin-кабinet владельца (users, leads, radar) | **📋 backlog** |
| 2026-05-31 | **GTM: нулевая сеть** | Нет знакомых · нет своего TG-канала · пост «друзьям» не применим | **FOR_YOU** § нулевая сеть · **→ @lead-product** GTM без аудитории (не срочно) |
| 2026-05-31 | **P-PORTFOLIO** | Личное портфолио VPS · параллельно soft ads RawLead | **после** O72d+O76 · RawLead · Crystal Debt · **Михалыч** (= умный чат-бот, WIP) |
| 2026-05-31 | **Фриланс + недоделки** | Владелец: проекты сырые · вопрос «есть ли шанс на FL» | честная оценка в `FOR_YOU` § портфолио · не блокер гейтов RawLead |
| 2026-05-31 | **O72 старые лиды** | Старые в Neon **не важны** для запуска · можно **убить** перед полным launch · regen 80 — **не** цель | Учиться на выборке → **промпт** · гейт = **новые** лиды после deploy VPS |
| 2026-05-31 | **O72 цикл владельца** | Ждём **новые** лиды → тест (глаза + опц. judge) → правим промпт если надо · **не** regen старых | План B combined **≥4** (жёстче автоматических 3.5/70%) |
| 2026-06-01 | **O72e gate ≥4** | Combined **минимум 4** на L1 **и** L2 · старые вакансии не переписываем · OpenRouter пополнен | § **O72e** · regen **❌ отменён** |
| 2026-06-01 | **FL/Kwork прокси** | Опрос **каждую минуту** — крутить **разные** прокси, не спамить с одного IP | § **O79** · код round-robin есть · **env VPS + failover** — Coder |
| 2026-06-01 | **Карта 5 прокси** | Закрепление acc/bot + pool бирж · failover | `DEPLOY_VPS.md` § карта · **пароли только VPS `.env`** |
| 2026-06-01 | **Приоритет O63 > реклама** | Парсеры важнее soft ads · **но** сначала Coder **добивает O80+O72e-2** · потом **по шагам** w1→w2 | OWNER_INTENT · CODER § O63-w1 |
| 2026-06-01 | **Лендинг «один поток»** | Секция непонятна — **не карточка заказа**, а **иллюстрация сути** + источники; с Design | § **D-O81** |
| 2026-06-01 | **ИИ-аудит вместо глаз** | Playwright U1–U10 + LLM rating + **оценка отклика/инструментов** на карточках | § **O80** · **✅** |
| 2026-06-01 | **Match % — не moat** | F2 = 33/67/100 пачками · ai_score 3 корзины · UI без breakdown · «надо чинить, переиграть рынок» | § **O82** · **до рекламы** |
| 2026-06-01 | **Tools anon** | На `/lenta/` без входа — **убрать «Инструменты»** из карточки | § **O83** · **✅** |
| 2026-06-01 | **O63-w2 URL** | FreelanceJob `…/projects/` · Пчёл `pchel.net/jobs/` · **только новые**, не архив | § **O63-w2** |
| 2026-06-01 | **Лендинг flow mobile** | На 390px карточки **вылетают из логотипа** (fly-out), не просто появляются | § **O81-w1** f5 |
| 2026-06-01 | **Match UI v2** | Не «Качество заказа» / не «Брать✓» на карточке — **% совместимости стека** · «Добавь навыки» **только anon без выбранных навыков** | § **O82-w1b** |
| 2026-06-01 | **L2 промпт владельца** | «Senior Freelance Acquisition Agent» — **канон духа** shared draft · **без** срока/цены в reply_draft | § **O72e-3** |
| 2026-06-01 | **L1 модель — A/B** | Менять **можно**, но **после** промпта p4 · только дешёвые (`flash-lite`→`flash`→`deepseek`) · Sonnet на L1 **нет** · gate = `l1_usable ≥70%` / $ per lead | § **O72e-3** p10–p12 |
| 2026-06-01 | **QA-автомат O72e-4** | **`qa_prompt_loop.py` ✅ код** · **`--apply` ⏸** (бюджет ~$8) | § **O72e-4** |
| 2026-06-01 | **O72e-5 full** | owner `--full`: combined **4.06** · send **39%** · L1 **36%** FAIL · regen 28/28 · bug `_render_md` | § **O72e-5** · **O72e-6** follow-up |
| 2026-06-01 | **O85 login fix** | JS → WP REST proxy (не 127.0.0.1) · bot `/login` · theme **v1.11.20** | § **O85** · retest TG |
| 2026-06-01 | **O86 bot silence** | Подписчикам **только** match-лиды + вход; ошибки/auth — **mute**, log owner | § **O86** · P0 |
| 2026-06-01 | **O78 admin** | Web-пульт простыми словами: визиты, радар, здоровье · база `/ops/` O45 | § **O78** |
| 2026-06-01 | **O72e-6 тон отклика** | «Здравствуйте!» + **глагол выполнения** (Сделаю/Настрою/Адаптирую…) · **❌** «Заинтересовал…» · **❌** «беру в работу» | § **O72e-6** · решение владельца |
| 2026-06-01 | **O88 mobile login** | Вход в **Safari/Chrome**, не TG WebView · poll на странице | § **O88** · P0 |
| 2026-06-01 | **O72e-8 L1 v2** | Убрать Брать/МИМО из L1 → `feed_visible` · replay L1 в `--full` · A/B flash-lite / gemini-2.0-flash / 4o-mini · gate на **свежих** `--judge-since 2026-06-02` | § **O72e-8** · **@coder 2026-06-02** |
| 2026-06-01 | **O72e full** | L2 PASS (4.15/67%) · L1 FAIL (47%) | log `161825Z` |
| 2026-06-02 | **O90 ingest lag** | `source_published_at` + отчёт + `/ops/` | § **O90** · после O72e-9 |
| 2026-06-02 | **O91 watchdog** | timer 5 мин · TG алерт · автоперезапуск · proxy probe | § **O91** · после O72e-9 |
| 2026-06-02 | **O72e-8 gate owner** | Full **FAIL** L1 **33%** · L2 **3.94**/61% · log `063753Z` · L1=deepseek | § **O72e-9** |
| 2026-06-02 | **O72e-9 L1 premium** | PDF research: **4 тега** · **primary_category** · few-shot RU · fix sanitize · A/B Qwen/Mistral/flash-lite | § **O72e-9** · **@coder P0** |
| 2026-06-02 | **O72e-9 gate PASS** | Full `075032Z`: combined **4.10** · send **61.9%** · L1 usable **87.0%** · category_ok **91.3%** | **следом O90+O91 → O89** |
| 2026-06-02 | **Прокси +3–4 IP** | только `FL_PROXY_URLS`/`KWORK_*` · RU/KZ/DE · не трогать `TG_PROXY` | `DEPLOY_VPS.md` |
| 2026-06-02 | **O92 Skill Tree** | ЛК: 4 ниши + ветки тегов; **v1 UI-only**, API payload прежний, **L1 без изменений** | interim deploy 1.11.30 |
| 2026-06-02 | **O93-w2** | авто-L3 · лента = modal как ЛК | **→ @coder** |
| 2026-06-02 | **O94-v0.5** | research каталог 4 ниши + стеки | **→ @lead-product** |
| 2026-06-02 | **O93 picker вариант B** | 2 блока; python **и** javascript Tier A в «По технологии»; не option «Гибрид» | **✅ deploy 1.12.0** |
| 2026-06-01 | **O81-w1c flow cards** | Fly-out ✅ · owner **принял** | **✅** |
| 2026-05-31 | **Crystal Debt хостинг** | Сервер лежит · платить не хочет · доделает **потом** | P-PORTFOLIO: **только скрины**, подпись MVP/paused · не врать «live demo» |
| 2026-05-31 | **P-PORTFOLIO v2** | Дизайн: **labs.rawlead.ru** брутализм + wow как [richardekwonye.com](https://www.richardekwonye.com/) | `LEAD_DESIGN_PROMPT` § D-P-PORTFOLIO |
| 2026-05-31 | **P-PORTFOLIO ИИ v3** | **Не** МИМО/БРАТЬ по ТЗ заказчика — обидит. **Да:** «куда встроить ИИ в ваш бизнес» + демо на **пресете** | FOR_YOU · CODER § p5 |
| 2026-05-30 | **O71 ✅** | HTTPS api · k6 0% fail · shared draft 12/12 | **Lead verify** |
| 2026-05-30 | **O37 load ❌** | k6 https 404 · matrix ≠ site path | **→ O71** |
| 2026-05-30 | **O37c re-run** | 8→2 critical · mobile green | **✅** |
| 2026-05-30 | **O69 ✅** | sort count · «Ещё навыки» · 2 ниши · v1.11.14 prod | **принято** |
| 2026-05-30 | **O69** | count sort mismatch · «Ещё навыки» · 2 ниши пусто | **→ Coder P0** |
| 2026-05-30 | **O37c-filters ✅** | v1.11.12 prod · Lead verify | **принято** |
| 2026-05-30 | **O64–O67** | L1/status breakdown · delist · Legacy poll · ИИ draft | **→ Coder** |
| 2026-05-30 | **Legacy lag** | visible в ленте часами · FLPARSINGBOT поздно · poll ~10 мин | **O66** |
| 2026-05-30 | **Delist** | снятый с биржи заказ → пропадает из ленты | **O65** |
| 2026-05-30 | **O37c-filters** | bar: 4 специализации · «Фильтры» → навыки по нише · chip **is-active** · **Coder deploy сразу** | **→ Coder P0** |
| 2026-05-30 | **Радар жив** | VPS active · FL 90/cycle · новых 0 (dup+filter) · Kwork 0 · TG ok | **не паника** · O63 если Kwork |
| 2026-05-30 | **Local-first gate** | theme local → deploy once | **принято** |
| 2026-05-30 | **O37-UX** | 11/11 yandex-cdp — gaps: tools, bot, test accounts | **✅** |
| 2026-05-30 | **O62** | Draft: убрать блок 0% km | **✅** § O61 |
| 2026-05-30 | **O60** | Приёмка: anon badge · limit · live preview · FL | **✅** |
| 2026-05-29 | **O38 scope+** | Mechanic: код + ИИ + **docs drift** + **product drift** | **✅** |
| 2026-05-29 | **O56+O57 deploy** | async · shared draft · v1.10.8 · pro model VPS | **✅** |
| 2026-05-29 | **O57 SHARED DRAFT** | Один L2 на lead · всем один черновик · cache `leads.reply_draft` | **→ O56+O57** |
| 2026-05-29 | **O56 accept v5** | Async draft · uniform collapsed · expand after reply | **O56** |
| 2026-05-29 | **O54 accept v3** | Сосед не растягивается · черновик без срока/цены | **✅ v1.10.6** |
| 2026-05-29 | **O53 accept v2** | Карточка in-cell · ₽ not Р · decode HTML · ЛК = лента без глаза | **✅ v1.10.5** |
| 2026-05-29 | **Match формула A** | % от тегов **лида** · cap 6→**12** | **O42** ✅ F2 |
| 2026-05-29 | **Admin /ops/** | VPS · только owner TG | **O45** ✅ scope |
| 2026-05-29 | **WAVE-4-MICRO** | FAB → окно чата (stub ok) · навыки ленты ≠ ЛК · «Мои навыки» на ленте · modal ЛК по центру · убрать hero-счётчик | → `CODER_PROMPT` § WAVE-4-MICRO |

---

## Что Lead **не** делает (напоминание)

- Не просить ▶ **Legacy на ПК** (O10).
- Не возвращать Freelancehunt (O3).
- Не открывать stress до polish (O1).
- Не дублировать ТЗ в чат — только `CODER_PROMPT.md` + копипаст `@coder`.

---

_Lead Architect · журнал владельца · 2026-05-28_
