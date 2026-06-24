# Решения и мысли владельца (журнал для Lead Architect)

**Назначение:** всё, что владелец сказал в чатах и что **ещё надо довести** в продукте/ops. Новый `@lead-architect` читает **этот файл первым** (после `ROADMAP.md` + `STATUS.md`), не опирается на память прошлых чатов.

**Обновляет:** только **Lead Architect** (по словам владельца или после приёмки). Coder/Designer сюда **не пишут**.

**Связь:** детальное ТЗ → [`CODER_PROMPT.md`](CODER_PROMPT.md) · шаги владельца → [`FOR_YOU.md`](../../FOR_YOU.md) · снимок → [`STATUS.md`](../common/STATUS.md).

---

**Архивы (2026-06-20):** [`OWNER_INTENT_BACKLOG_ARCHIVE.md`](../archive/OWNER_INTENT_BACKLOG_ARCHIVE.md) · [`OWNER_INTENT_JOURNAL_ARCHIVE.md`](../archive/OWNER_INTENT_JOURNAL_ARCHIVE.md) · [`OWNER_INTENT_SECTIONS_ARCHIVE.md`](../archive/OWNER_INTENT_SECTIONS_ARCHIVE.md) · hot **~311 строк**

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
| **O12** | ~~**Оплата — Telegram Stars**~~ **→ superseded 2026-06-10** | **O174:** только **ЮKassa** · Stars UI/бот — убрать |
| **O102-pay** | ~~**ЮKassa отложен**~~ **→ owner подключает 2026-06-10** | § **O174-YOOKASSA** |
| **O105** | ~~**790 ₽ · СБП/crypto/Stars**~~ **→ superseded** | **O174:** **790 ₽/мес** только карта/СБП **ЮKassa** |
| **O107** | ~~**Trial 3 дня бесплатно**~~ **→ superseded** | **O174:** **1 ₽ × 3 дня** (ЮKassa) → **790 ₽/мес** |
| **O116** | **Pre-ads copy: delay только anon + FAQ 3 уровня** | Free TG login = лента без задержки, без черновиков · FAQ accordion 3 группы · strip copy update | § **O116** · W1 PM → W2 Design → W3 Coder |
| **O102-youdo** | **⏸ отменено** «выключить YouDo» — VPS-логи: **0 лидов** из-за 403/баны, не «площадка мёртва» | **→ O103** починить O63-парсеры + прокси YouDo |
| **O103** | **O63 ingest repair** — YouDo + freelance.ru + Пчёл | § **O63-FIX** · другой чат Coder |
| **O72e-10** | **L1/L2/L3 premium** · L3=`google/gemini-2.5-flash` · gate L2 send **≥70%** · judge экономно (pilot→full) | § **O72e-L2-r2** `CODER_PROMPT` |
| **O13** | **Вход в ЛК на rawlead.ru** — без localhost | § **CABINET-PROD-LOGIN** · BotFather domain = `rawlead.ru` |
| **O14** | **Страницы сайта** — не только главная/лента/ЛК | § **SITE-PAGES** · how, pricing, faq, contact (footer уже ссылается) |
| **O15** | **ЛК: навыки** — picker из **полного L1-пула** (`skills_catalog.py`), не только из прошедших заказов; окно **сверху** страницы | § **CABINET-SKILLS-PICKER (L3)** |
| **O16** | **Retention:** лиды старше **2 дней** удалять (не засорять БД) | `purge_old_leads.py` · `FEED_VISIBILITY_DAYS=2` |
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
| **O46** | **Match F2:** `km = matched/lead_tags×100` · «ИДЕАЛЬНО ✦» только при ≥2 тегах лида и полном покрытии · ~~cap навыков **12**~~ → **снят** quiz-first **2026-06-15** | § **PRE-STRESS-PACK O42** · 2026-05-29 |
| **O281** | **YouDo без полного ТЗ — не в ленту и не в L1** (не «угадывать» по заголовку) | § **YOUDO-FULL-TZ-GATE** · откат компромисса O262g (`YOUDO_DETAIL_FETCH=0` + L1 на snippet) |
| **O48** | **Draft reliability:** log 503 · retry · rate limit · UI «Повторить» · scale | § **PRE-STRESS-WAVE-2** · **P0** |
| **O49** | **L2 premium v2:** без «Готов…» · шаги · 9/10 quality | § **PRE-STRESS-WAVE-2** |
| **O50** | **TG push:** полная карточка + callback «Сгенерировать» → draft в TG + ЛК | § **PRE-STRESS-WAVE-2** |
| **O51** | **ЛК grid 2 col** как лента | § **PRE-STRESS-WAVE-2** |
| **O62** | **Draft без порога km:** 0% — можно откликнуться · km только информативен | § **O61** · paid draft на любом lead |
| **O63** | **Новые парсеры:** YouDo · Freelance.ru · FreelanceJob · Пчёл.нет · **cross-source dedup** | § **O63** · **→ волна 2026-06-01** |
| **O72e** | **Judge gate:** L2 ≥4/send **≥70%** · L1 ≥70% · pilot bench 10 ids → full 71 | § **O72e-L2-r2** |
| **O79** | **FL+Kwork 1 мин/цикл на VPS** → **ротация прокси** (`FL_PROXY_URLS`, `KWORK_PROXY_URLS`) · **отдельный пул**, не `TELETHON_PROXY_*` | § **O79** · `.env` на VPS — владелец |
| **O82** | **Match moat:** **совместимость стека** (не «качество заказа») · без чипов «Брать/Сомнительно» на карточке · CTA «Добавь навыки» **только anon без навыков** | § **O82-w1b** · F2+ w2 |
| **O83** | **«Инструменты» в ленте — только auth** (anon не видит L2 tools) | § **O83** · s **O82-w1** |
| **O89** | **Уникальный отклик:** shared pro + flash-lite rephrase per user | § **O89** · после O90+O91 |
| **O90** | **Ingest lag:** `source_published_at` · отчёт биржа→Neon→L1 · `/ops/` | § **O90** |
| **O91** | **Ночной watchdog:** пульс цикла · алерт TG · автоперезапуск · health прокси | § **O91** · **не** второй парсер |
| **O92** | **Skill Tree в ЛК:** 4 ниши → ветки tags (RPG-style) | § **O92** · **✅ v1 deploy 1.11.30** |

---

## Активные § (индекс)

Детальные спеки — `CODER_PROMPT` / `ROADMAP` / архив §.

| § | Тема | Статус |
|---|------|--------|
| **O280** | Next cutover · E2E 24/24 | ✅ gate |
| **O200** | L2 judge owner bar ≥70%×4 | ✅ 2026-06-18 · auto-tools backlog A9 |
| **M1** | Soft launch TG ads ≤5k ₽ | `LEAD_MARKETING_PROMPT` |
| **O208** | Quiz-first · воронка · hourly cap | prod |
| **O174** | ЮKassa 790₽ · trial 1₽ | prod |
| **O116** | Pre-ads copy/UI | ✅ deploy · детали в архиве § |
| **MIMO-AUDIT** | Wide audit pilot | после O280 · ниже |

## Legacy на ПК (кратко)

| Правило | Суть |
|---------|------|
| **O10** | Legacy ▶ по желанию; **не** должен сам гаситься (баг ✅ `lead_pipeline` import) |
| **ПК после P5** | Оба ■ на ПК; радары на VPS; dogfood — @FLPARSINGBOT |
| **Детали** | [`archive/OWNER_INTENT_SECTIONS_ARCHIVE.md`](../archive/OWNER_INTENT_SECTIONS_ARCHIVE.md) § Legacy |

## Бэклог владельца (архив)

Исторические § O198-w … mobile UX — в [`archive/OWNER_INTENT_BACKLOG_ARCHIVE.md`](../archive/OWNER_INTENT_BACKLOG_ARCHIVE.md). Новые мысли → **Журнал** ниже + при необходимости `CODER_PROMPT`.

## Очередь инженерии

**Не дублировать ROADMAP.** Актуальная очередь:

| Источник | Что |
|----------|-----|
| [`ROADMAP.md`](ROADMAP.md) | волны до M1 ads |
| [`STATUS.md`](../common/STATUS.md) | hot prod + последняя сдача |
| [`TASKS.md`](../common/TASKS.md) | probe, аудит A7+, M1 |
| [`CODER_PROMPT.md`](CODER_PROMPT.md) | § в шапке — единственное ТЗ Coder |

Историческая таблица 2026-05-28 → [`archive/OWNER_INTENT_SECTIONS_ARCHIVE.md`](../archive/OWNER_INTENT_SECTIONS_ARCHIVE.md).

## § MIMO — audit + coder (owner 2026-06-22)

**Решение:** весь кодинг → **MiMo `coder`** (экономия Cursor) · Lead verify/deploy/commit.

| Режим | Конфиг | Выход |
|-------|--------|-------|
| **audit** (default) | `MIMO_RULES.md` | `docs/problems/*-mimo-*.md` |
| **coder** | `MIMO_CODER.md` | diff в repo → Lead verify |

Канон Cursor: `.cursor/rules/mimo.mdc` · handoff: `lead-architect.mdc` § Маршрут.

**Запрещено MiMo:** commit · deploy · `.env` · правка `CODER_PROMPT` (edit deny в jsonc).

**Читать отчёты прогонов:** audit/coder может `data/preprod_*.json` / `*.md`.

---

## Журнал (хронология, кратко)

Полный архив → [`archive/OWNER_INTENT_JOURNAL_ARCHIVE.md`](../archive/OWNER_INTENT_JOURNAL_ARCHIVE.md). Ниже — **с 2026-06-12**.

| Дата | Мысль / запрос | Kуда ушло |
|------|----------------|----------|
| 2026-06-23 | **YouDo IMAP:** без UID-курсора — **last N + dedup PG** (owner **B**) | § **YOUDO-IMAP-ONLY** обновлён |
| 2026-06-23 | **YouDo:** старый listing/браузер **стоп** · чинить **только почту** · реклама live | **§ YOUDO-IMAP-ONLY** P0 |
| 2026-06-23 | **Квиз:** переделка в **стороннем cloud** (не MiMo/Cursor) | § **QUIZ-REDESIGN** |
| 2026-06-22 | **Экономия:** весь кодинг → MiMo `coder` · Cursor Lead = verify/deploy | `mimo.mdc` · `MIMO_CODER.md` |
| 2026-06-22 | **M1 реклама live** · YouDo 22.06: O281 скрыл ленту → restore · listing `parsed=50` жив | `problems/2026-06-22-youdo-m1-day.md` · YOUDO-DETAIL P0 |
| 2026-06-22 | **YouDo:** вернуть snippets в ленту (ServicePipe detail) | **YOUDO-RESTORE-SNIPPETS** ✅ |
| 2026-06-22 | **Лента:** фильтр TG включается сам — prefs v3 | **FEED-FILTER-TG-STUCK** ✅ |
| 2026-06-22 | **YouDo:** нельзя тащить заказы только из заголовка — без полного ТЗ не в ленту | **O281** · § **YOUDO-FULL-TZ-GATE** |
| 2026-06-22 | **YouDo t14881683:** Тильда в ТЗ, на карточке `wordpress_dev` | § **L1-TILDA-TAGS** ✅ |
| 2026-06-22 | **Лента:** F5 сбрасывает фильтры · **Квиз:** слишком короткий | § **FEED-QUIZ-POLISH** ✅ |
| 2026-06-20 | **PRE-ADS:** сначала **MiMo audit** → Lead triage → **@coder** § PRE-ADS-GATE · **M1 реклама** параллельно | `CODER_PROMPT` § PRE-ADS-GATE · `MIMO_RULES` |
| 2026-06-16 | **Soft launch M1** — TG ads test · РФ · все фрилансеры · budget **≤5k ₽** (старт 2–3k) · trial · параллельно инженерии · owner мониторит | **§ M1** `LEAD_MARKETING_PROMPT` · `@lead-marketing` |
| 2026-06-16 | **Роль Lead Marketing** — кампании, UTM, KPI; понимает квиз-first + trial | `.cursor/rules/lead-marketing.mdc` · `docs/team/marketing/` |
| 2026-06-16 | **YouDo O260 DC-first** — slot1=DC · node max 1 при dc_alive=0 · hard reset при банах на DC | **§ O260** ✅ prod |
| 2026-06-15 | **O225 match floors v2** — primary niche **20%** · secondary **10%** · trial без замка · floor не ломается от draft на чужую нишу | **§ O225** `@coder` |
| 2026-06-15 | **O224-B expand-no-reply** — штраф **только** «раскрыл и не откликнулся», не за просмотр в ленте · `expand_no_reply −0.05` | **§ O224-B** `@coder` ✅ |
| 2026-06-15 | **O224 match UX** — chips · bar · 20% category · gold 100% | **§ O224** `@coder` |
| 2026-06-15 | **YouDo t14857148** — перевозка → L1 WordPress | **§ O223** ✅ |
| 2026-06-15 | **«Все парсеры упали»** — triage: FL 🔴 · Kwork fresh=0 · YouDo/TG OK | Lead clear bans ✅ · [`2026-06-15-parsers-fl-unstable.md`](../../problems/2026-06-15-parsers-fl-unstable.md) · **O222** P0 |
| 2026-06-15 | **O221 deploy prod** — 186 cards · coverage CI · dedup on VPS | Lead `deploy-o217-quiz-vps.py` ✅ · owner quiz smoke |
| 2026-06-15 | **O221 r6 pilot 40** — owner **«принимаю pilot»** + signals v2 approve | **→ @coder** § **O221-QUIZ-ADAPTIVE** · **→ @lead-product** r7 ~130 |
| 2026-06-13 | **L2 Option B** — подкрутить playbooks до full regen · **все 4 cat send ≥80%** (не 60%) · pilot r1 mkt 60% — не проходит owner bar | **§ O200-L2-CAT-80** · parallel L2 chat |
| 2026-06-13 | **L2 чат отдельно** | O200 ≠ O201/O199/concept · pilot 40 в L2-чате | § **O200** · `TASKS` две линии |
| 2026-06-13 | **L2 pilot 40** — 10×4 cat сначала · judge balanced → full regen только после PASS + «да» | **§ O200-L2-CATEGORY-WAVE** · `CODER_PROMPT` |
| 2026-06-13 | **Complexity в quiz** — cx_pref автоматически · мягкий rank · § O198 → @coder | **§ O198-w** · CODER_PROMPT § O198 |
| 2026-06-13 | **Quiz adaptive** — большой пул Neon · следующая карточка от ответов · 6–20 карточек · PM spec ✅ → **§ O197** `@coder` | **§ O197-w** · `CODER_PROMPT` § O197-QUIZ-ADAPTIVE |
| 2026-06-12 | **FL listing — вариант B** · subprocess worker как YouDo · **не** httpx-primary · **`tz_session` не трогать** | **§ O193-w** · Coder после O190 t0j ✅ |
| 2026-06-12 | **VPS апгрейд** — **4 GB / 2 vCPU** (было 2 GB / 1 vCPU) · camoufox + FL Chromium + L1 ×3 + tg_main влезают без OOM · до рекламы | owner сделал 2026-06-12 19:30 UTC+8 |
| 2026-06-12 | **Stability first** — заморозить antibot-эксперименты после t0e; ingest SLA 48h; deploy-gate: smoke + grep после каждого деплоя | **§ O192-STABILITY** (Coder) после t0e |
| 2026-06-12 | **YouDo proxy mix** — owner: **DC primary + residential fallback** (не только RU res) · **не** реже listing (`fetch_every_n` ↑) · node-proxy **общий трафик** на пул — число слотов ≠ экономия GB | **§ O191-w** после O190 ingest ✅ |
| 2026-06-12 | **YouDo RU proxy list** — owner прислал экспорт node-proxy RU ×25 (gate…10000–10024) для `YOUDO_PROXY_URLS` | owner ops → `.env.site` + `deploy-youdo-residential-vps.py` · Coder t0d — smoke failover |
| 2026-06-12 | **YouDo P2 camoufox** — после O189 ❌ · owner: Firefox ok если прикрыть хвосты patchright/t6 | **§ O190** t0b |
| 2026-06-12 | **Аудит логики** — owner: «может Sonata проверит» / баг в join-очереди | Lead verify O188 → v2/v3 рассинхрон · **Mechanic** TG state или **@coder** O188 fix · не O186 security |
| 2026-06-12 | **YouDo P1 patchright** — owner «давай пробовать» после Mechanic CDP analysis | **§ O189** ✅ code · ❌ ingest |
| 2026-06-13 | **O201-w** ops только пароль + кнопка «Админка», без cabinet | § O201-OPS-SIMPLE-GATE |
| 2026-06-13 | **TG listen gap** — 115 done но ~10 listen · join+listen parallel · log chain · 150+ | § **O190-TG-JOIN-LISTEN-CHAIN** |
| 2026-06-13 | **TG allowlist ✅ Option A** — расширить файл под всю очередь `done` · **не B** (anon отдельно не режем; spam/L1 = качество) | § **O190** t2 allowlist expand |
| 2026-06-13 | **План до ads (owner)** — волна 1 TG (t2b+O207) → **2 O208** quiz-first UI/copy/воронка (без ручных навыков) → **3 perf** → **4 L2 70%×4** → **5 stress финал** → ads | `ROADMAP` § волны |
| 2026-06-13 | **Гейт ads:** L2 **≥70%** по 4 категориям (не 60%) + O207 TG funnel + stress green | `ROADMAP` O72e |
| 2026-06-13 | **Концепция quiz-first** — подогнать UI/UX/тексты/воронку; старые фильтры навыков в UI убрать | § **O208** · O199 PM+Design |
| 2026-06-13 | **Perf сайта** — долго грузится; оптимизация после O208 scope | Design § O199 optimization |
| 2026-06-13 | **TG t3c ✅** — test group мгновенно; owner принял | § **O206 t3c** |
| 2026-06-13 | **Биржи «как TG»** — push нет у FL/Kwork; цель: ужать lag цикла + health в ops (не магия instant) | backlog **ingest SLA** |
| 2026-06-14 | **FL proxy restore** — 194.226 были **неоплачены**, не мёртвы; owner оплатил · pool **4/4** восстановлен · удаление 2 слотов **откат** | problems/2026-06-14 |
| 2026-06-14 | **O216 r1 уточнение:** квиз-карточки = **курация Neon** (универсальные лиды по 4 нишам), не только «убрать диджитал» — убрать и **чужие сферы** (медицина, юриспруденция, …) | CODER_PROMPT § O216 |
| 2026-06-14 | **O215 design polish** — Perf **отложен**; owner довёл вид через **BrowserSync** с @designer | DESIGNER_PROMPT § O215 |
| 2026-06-14 | **O220 ✅ code** match A–F + feed r0–r7 · pytest 48/48 | deploy ⏳ theme **1.19.00** |
| 2026-06-14 | **O208-B1 amend** — hourly cap **10/ч** (was 5, env never set) | § O208-B · owner |
| 2026-06-14 | **O218 Playwright** — quiz E2E multi-user · mobile+desktop · gate до ads | § **O218-w** · `TASKS` **65** |
| 2026-06-13 | **O208-B monetization** — **5 откликов/час всем** (вкл. premium) · L3 judge → K · убрать просмотры+слоты с карточки · PM воронка (trial 3д → без match-фильтра) | § **O208-B** · PM § O208-MONETIZATION |
| 2026-06-13 | **TG filter по данным** — доказать воронку · sample audit · filter lab | § **O207** |
| 2026-06-13 | **acc1 handler deaf** — test group msg=70 only acc2 `не_слушаем`; acc1 ready but 0 handler events | § **O206 t3b** → **t3c** |
| 2026-06-13 | **TG в ленте ~15/3нед** — listen 64, принято 548/мес, visible ~4% · L1/AI+filter | § **O206** |
| 2026-06-13 | **TG listen = все вступившие** — allowlist автозаполнение при join · filter не режет file→5 · качество = L1 на ingest, не pre-listen | § **O190-AUTO-ALLOWLIST-LISTEN** |
| 2026-06-13 | **TG spam-кнопка** — только владелец · корпус в БД · потом жёстче `tg_spam_filter` | § **O202** |
| 2026-06-13 | **Пульт TG на русском** — подсказки при наведении · не объяснять в чате | § **O203-OPS-TG-RU** |
| 2026-06-13 | **Свечение карточки** при генерации отклика — вернуть glow+полоску | § **O203-FEED-DRAFT-GLOW** |
| 2026-06-13 | **acc3 авторизация** — владелец **без телефона** · Coder/Mechanic на VPS | § **TG-ACC3-SESSION** · `TELEGRAM_ACCOUNTS.md` |
| 2026-06-13 | **O199-w smoke UX** — feed P0 · quiz PM+Design | ⏸ после O201 tail |
| 2026-06-13 | **O198+O171 deploy ✅** Lead verify · theme 1.18.76 · `/ops/` summary+TG on prod | `STATUS` · `TASKS` · `CODER_PROMPT` archive |
| 2026-06-13 | **O171-D ✅** Design wireframes summary+TG · Coder § O171-OPS-ADMIN-REBUILD | `CODER_PROMPT` · `TASKS` **32** |
| 2026-06-12 | **TG wave 4:** 127 чатов · **10 join/час** · split acc1/2/3 | **§ O188** · v3 ✅ deploy |
| 2026-06-12 | **С рекламой не торопимся** — стабильности парсинга нет (YouDo 🔴, TG мало) · ускорять парсеры не приоритет | **ads ⏸** подтверждено · очередь: YouDo t6c → TG join/чаты → **O187-stability** (ingest SLA) · не speed-up |
| 2026-06-17 | **P288 v3 ✅ mood** | Owner sign-off Recraft · terracotta · spiral tiles · §3.1 freeze | Design → Coder · [`premium-scroll-brief.md`](../../design/portfolio/premium-scroll-brief.md) |
| 2026-06-12 | **Smoke price 10 ₽** | prod smoke subscription ✅ owner · revert **790** | **✅ O185 t1b** |
| 2026-06-12 | **Trial → buy 790 during trial** | сейчас «Уже есть Premium» | O185 t1 |
| 2026-06-12 | **Match logic** | больше навыков ≠ ниже % · Python job + Py+Java user = 100% | O185 t4 + PRODUCT_CANON §3 |
| 2026-06-12 | **Reset btn visibility** | кнопка после повторного фильтра без F5 | **✅ O185-t5b-reset-btn** |
| 2026-06-12 | **PRODUCT_CANON.md** | единый файл лимитов/тарифов для PM audit | `@lead-product` |
| 2026-06-12 | **TG AuthKey owner PC** | случайный вход с ПК → session refresh VPS only | **→ Mechanic** |
| 2026-06-12 | **Neon 80%** | автоочистка — **есть** (7d purge timer); не менять политику — verify timer | O185 t8 |
| 2026-06-12 | **Cabinet copy** | убрать «Premium — оплата… Push — /start…» | O185 t2 |
| 2026-06-12 | **Avatar broken** | фото в шапке кабинета | O185 t3 |
| 2026-06-12 | **YouDo again broken** | закрыть навсегда | O185 t6 + Mechanic |
| 2026-06-12 | **O174c trial smoke ✅** | owner **1 ₽** → Premium в `/cabinet/` · Neon trial до **15.06** · payment **#6 succeeded** | **O174d** ⏸ |
| 2026-06-12 | **MiMo Code (Xiaomi)** | terminal agent (fork OpenCode) + MiMo-V2.5 · **аудит репо** как альтернатива O38/Gemini · см. § **MIMO-AUDIT** · **после O280 cutover** или параллельно на копии без secrets | backlog → owner pilot |
| 2026-06-11 | **O174 defer cancel/autopay** | красная «Отменить» + recurring **после первых пользователей** | **O174d** backlog |
| 2026-06-11 | **Webhook ЛК ЮKassa** | URL ✅ · events `payment.succeeded` + `payment.canceled` · backend live POST 200 | owner retest pay |
| 2026-06-11 | **`.cursorignore`** | нет в repo · ~8.9 GB `desktop/src-tauri/target` · → Coder t0 | token hygiene |
| 2026-06-11 | **O174b smoke FAIL** | 1₽ YooKassa succeeded · Neon pending · webhook/confirm gap | § O174b-HOTFIX |
| 2026-06-11 | **O182 delist in-progress** | YouDo **«Выполняется»** / SBR «Зарезервировано» — не откликнуться · smoke `t14827772` / #16149 | **→ @coder** § O182 |
| 2026-06-11 | **O181 delist closed** | YouDo «**Закрыто для откликов**» + purge delisted · smoke #16797 | **✅ smoke** · purge apply **306+964** |
| 2026-06-11 | **O180 delist** | Мёртвые/удалённые на ленте — delist web + backfill | **✅ smoke** #17048 |
| 2026-06-07 | **L2 voice O128 B** | план по ТЗ · без «опыта» · бизнес-вопросы | § **O128** → @coder |
| 2026-06-07 | **Stress edge cases** | S3-pre Neon pool · S4-pre proxy cascade · S1-b skills_mismatch | `PREPROD_STRESS_RUN.md` |
| 2026-06-07 | **O130 ICQ AI Portfolio** | Концепт Y2K-ICQ + LLM-секретарь · **пока идея** | § **O130** · после ads · см. P-PORTFOLIO |
| 2026-06-08 | **O135–O138 launch tail** | draft L2-only · feed sort · parsed/fresh `/ops/` | § **O135–O138** ✅ deploy |
| 2026-06-08 | **O146 draft card UX** | flip один раз · pending не стоп · btn gold shimmer | § **O146** → @coder |
| 2026-06-08 | **O141 exchange parity** | detail all web · TG labels | § **O141** ✅ deploy |
| 2026-06-08 | **O142–O143 split god-files** | ai_analyze → `src/ai/` · api_server → routers · **после ads** | § **O142** · § **O143** · P2 |

*Дописывай новые строки снизу.*

## Что Lead **не** делает (напоминание)

- Не просить ▶ **Legacy на ПК** (O10).
- Не возвращать Freelancehunt (O3).
- Не открывать stress до polish (O1).
- Не дублировать ТЗ в чат — только `CODER_PROMPT.md` + копипаст `@coder`.

---

## § O128 — L2 voice: процесс вместо «опыта» (**✅ B**, 2026-06-07 → Coder)

**Боль:** отклик пишет «имею опыт / делал похожее» → заказчик просит кейсы, которых у random юзера RawLead нет.

**Решение владельца — вариант B:**

| # | Правило |
|---|---------|
| 1 | **Запрет:** «я эксперт», «имею опыт», «уже делал», «N проектов», «делал похожее» |
| 2 | **✅ Можно:** «По ТЗ вижу…», «Для реализации [боль] выстрою: [шаги]» — план, не резюме |
| 3 | **Запрет вопросов-подстройки:** «какой стек/язык предпочитаете?» — стек из ТЗ + обоснование |
| 4 | **1–2 вопроса** по **бизнес-логике / edge case** из ТЗ |

**→ Coder:** § **O128-L2-VOICE** в `CODER_PROMPT.md` · deploy L2 stack · **не** mass regen.

---

| 2026-06-12 | **Smoke price 10 ₽** | prod smoke subscription ✅ owner · revert **790** | **✅ O185 t1b** |
| 2026-06-12 | **Trial → buy 790 during trial** | сейчас «Уже есть Premium» | O185 t1 |
| 2026-06-12 | **Match logic** | больше навыков ≠ ниже % · Python job + Py+Java user = 100% | O185 t4 + PRODUCT_CANON §3 |
| 2026-06-12 | **Reset btn visibility** | кнопка после повторного фильтра без F5 | **✅ O185-t5b-reset-btn** |
| 2026-06-12 | **PRODUCT_CANON.md** | единый файл лимитов/тарифов для PM audit | `@lead-product` |
| 2026-06-12 | **TG AuthKey owner PC** | случайный вход с ПК → session refresh VPS only | **→ Mechanic** |
| 2026-06-12 | **Neon 80%** | автоочистка — **есть** (7d purge timer); не менять политику — verify timer | O185 t8 |
| 2026-06-12 | **Cabinet copy** | убрать «Premium — оплата… Push — /start…» | O185 t2 |
| 2026-06-12 | **Avatar broken** | фото в шапке кабинета | O185 t3 |
| 2026-06-12 | **YouDo again broken** | закрыть навсегда | O185 t6 + Mechanic |
| 2026-06-12 | **O174c trial smoke ✅** | owner **1 ₽** → Premium в `/cabinet/` · Neon trial до **15.06** · payment **#6 succeeded** | **O174d** ⏸ |
| 2026-06-12 | **MiMo Code (Xiaomi)** | terminal agent (fork OpenCode) + MiMo-V2.5 · **аудит репо** как альтернатива O38/Gemini · см. § **MIMO-AUDIT** · **после O280 cutover** или параллельно на копии без secrets | backlog → owner pilot |
| 2026-06-11 | **O174 defer cancel/autopay** | красная «Отменить» + recurring **после первых пользователей** | **O174d** backlog |
| 2026-06-11 | **Webhook ЛК ЮKassa** | URL ✅ · events `payment.succeeded` + `payment.canceled` · backend live POST 200 | owner retest pay |
| 2026-06-11 | **`.cursorignore`** | нет в repo · ~8.9 GB `desktop/src-tauri/target` · → Coder t0 | token hygiene |
| 2026-06-11 | **O174b smoke FAIL** | 1₽ YooKassa succeeded · Neon pending · webhook/confirm gap | § O174b-HOTFIX |
| 2026-06-11 | **O182 delist in-progress** | YouDo **«Выполняется»** / SBR «Зарезервировано» — не откликнуться · smoke `t14827772` / #16149 | **→ @coder** § O182 |
| 2026-06-11 | **O181 delist closed** | YouDo «**Закрыто для откликов**» + purge delisted · smoke #16797 | **✅ smoke** · purge apply **306+964** |
| 2026-06-11 | **O180 delist** | Мёртвые/удалённые на ленте — delist web + backfill | **✅ smoke** #17048 |
| 2026-06-07 | **L2 voice O128 B** | план по ТЗ · без «опыта» · бизнес-вопросы | § **O128** → @coder |
| 2026-06-07 | **Stress edge cases** | S3-pre Neon pool · S4-pre proxy cascade · S1-b skills_mismatch | `PREPROD_STRESS_RUN.md` |
| 2026-06-07 | **O130 ICQ AI Portfolio** | Концепт Y2K-ICQ + LLM-секретарь · **пока идея** | § **O130** · после ads · см. P-PORTFOLIO |
| 2026-06-08 | **O135–O138 launch tail** | draft L2-only · feed sort · parsed/fresh `/ops/` | § **O135–O138** ✅ deploy |
| 2026-06-08 | **O146 draft card UX** | flip один раз · pending не стоп · btn gold shimmer | § **O146** → @coder |
| 2026-06-08 | **O141 exchange parity** | detail all web · TG labels | § **O141** ✅ deploy |
| 2026-06-08 | **O142–O143 split god-files** | ai_analyze → `src/ai/` · api_server → routers · **после ads** | § **O142** · § **O143** · P2 |
