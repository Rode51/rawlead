# OWNER_INTENT — журнал (архив)

Полная хронология до сжатия hot 2026-06-20. Новые строки — в hot § «Журнал».

## Журнал (хронология, кратко)

| Дата | Мысль / запрос | Kуда ушло |
|------|----------------|-----------|
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
| 2026-06-09 | **TG лента:** много рекламы услуг · жёстче L1+pre-filter только для TG | **§ O170-TG-L1-FILTER** P0 |
| 2026-06-09 | **O169** secondary выпали из feed после O165 deploy — восстановить YouDo/FRU/… | **§ O169-SECONDARY-FEED** ✅ deploy |
| 2026-06-09 | **Реклама рано** · stress/L2 сначала · TG тест-группа · home match bar · sort по биржам | **§ O165–O168** · CODER_PROMPT |
| 2026-06-09 | **Реклама рано** — stress/L2/TG/UI сначала | **§ O168-w** · ads ⏸ |
| 2026-06-09 | TG test group +Z7HcnIAdSw9kY2U6 · 3 акка · вакансия owner | **§ O165-w** |
| 2026-06-09 | Главная match bar пустой · sort по биржам в dropdown | **§ O166-w** · **O167-w** |
| 2026-06-09 | Freelancehunt **окончательно** убрать отовсюду | **§ DROP-FREELANCEHUNT** · CODER_PROMPT |
| 2026-06-09 | TZ smoke: cookies Kwork+FL · VPS deploy · потом O164 | **§ O133-TZ-SMOKE** |
| 2026-06-04 | **O116-W4** ✅ код · prod deploy ⏸ · email на contact — хвост R3 | **§ O116** W4 |
| 2026-06-04 | **O116-b2** ✅ prod 1.18.13 · flip + `+n` · Lead verify | **§ O116** D5 |
| 2026-06-04 | **O116 CABINET tail** ✅ 1.18.12 · R2 copy ЛК · FAQ trial без кнопки | **§ O116** R2 |
| 2026-06-04 | **O116 CABINET** ✅ Lead verify+deploy · ЛК без паузы/trial · toolbar inbox · total counter | **§ O116** D9 · `deploy-o116-mkt-vps.py` |
| 2026-06-04 | **O116 MKT** ✅ Lead verify · prod **1.18.11** · Neon 018 · ticker+FAQ | **§ O116** · `deploy-o116-mkt-vps.py` |
| 2026-06-04 | **O116 R1–R3:** prefs Neon+local · delay только anon · support→TG владельцу «тикет N» | **§ O116** решения |
| 2026-06-04 | **UI/UX pre-ads:** лента flip/glow, toolbar %, ticker, copy pricing/faq/how, ЛК без паузы, contact+support, hourly 10 | **§ O116** · TASKS · CODER после PM+Design |
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
| 2026-05-31 | **P-PORTFOLIO** | ~~brutalism labs~~ | **❌ superseded → P288** |
| 2026-06-17 | **P288 v3 ✅ mood** | Owner sign-off Recraft · terracotta · spiral tiles · §3.1 freeze | Design → Coder · [`premium-scroll-brief.md`](../../design/portfolio/premium-scroll-brief.md) |
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
| 2026-06-03 | **Прокси каскад + FLPARSING** | sticky slot · баны SQLite · **алерты и /status прокси** только @FLPARSINGBOT · не @rawlead_bot | `KAK_ETO` · `FOR_YOU` § два бота · `DEPLOY_VPS.md` |
| 2026-06-03 | **O99 ingest human + fast path** | ✅ browser fetch · hot L1 · secondary/2 · HTTP 403×2 ban · VPS deploy | § **O99** · Lead verify `STATUS` |
| 2026-06-03 | **O101 cap K** | ✅ лимит L3/lead · индикатор слотов · judge подобрать K · anti-тык | **📋** · § O101 · после E2E |
| 2026-06-03 | **O100 Светофор** | Динам. цена + FOMO на карточке | **❌ отклонено владельцем** — «превращаемся во FL.ru», не moat · см. § O100 |
| 2026-06-03 | **Эквайринг** | ЮKassa **не сейчас** — нет бюджета | **O102-pay** · Stars по **O12** |
| 2026-06-03 | **O105 Premium 790₽** | СБП вручную + USDT/TON + Stars · бот «Проверить оплату» · Trust/MetaMask v2 | § **O105** · после E2E |
| 2026-06-03 | **O106 карточка minimal** | Меньше инфо на preview · слоты O101 · детали по tap | § **O106** · design → coder |
| 2026-06-03 | **Copy уникальный отклик** | Главная + pricing + бот | **O89 copy** · @lead-product параллельно judge |
| 2026-06-03 | **O107 Trial 3 дня** | Бесплатный Premium 1× на аккаунт · явная активация · заменяет 3q на запуске | § **O107** · PM + O105-w1 |
| 2026-06-04 | **O72e budget** | **≤ ~$3/день** на judge+regen · pilot→full **один раз** · regen 71 / qa `--full` **запрещены** без «да» | § **O72e-L2-r6** |
| 2026-06-04 | **O72e full judge ⏸** | Pilot r7 **PASS** (combined 4.3 / send 80%) · **full 71 и stress — когда придёт время**, не сейчас | § O72e · после E2E/vault |
| 2026-06-04 | **VPS scale ⏸** | Playwright+radar на одном VPS — **ок до первых юзеров** · тогда **2-й VPS worker** или **апгрейд тарифа** (не сейчас) | § O110-worker backlog |
| 2026-06-04 | **FL proxy bans ⏸** | FL банит DC IP **per-source** (Kwork на тех же IP жив) · сброс SQLite bans — **временно** · нужно: **FL-only IP** + 2×403→ban + опц. 1 residential в `FL_PROXY_URLS` (**не** merge с YouDo) | **O110-fl-proxy** · § O99 #4–5 · `TASKS.md` |
| 2026-06-04 | **E2E S6** | Владелец прошёл первый обход ✅ · финальный UI/UX — после тестов | **→** launch wave |
| 2026-06-04 | **Launch wave** | **O105-w1** pay · **O112-support** (FAB stub) · **O113-seo** | после финального UX · `TASKS.md` |
| 2026-06-04 | **O114 вакансии** | **Не показывать** найм/штат — pre-filter + L1 + backfill Neon | **P0 @coder** · judge 63% частично из-за вакансий в выборке |
| 2026-06-04 | **Фаза A — ИИ first** | L1/L2/L3 gate до stress/pay-code · owner параллельно pay/UI · stress после send ≥70% | `TASKS.md` O72e-A |
| 2026-06-03 | **L1/L2/L3 premium** | Judge full: L1/L3 ✅ · L2 send **40.8%** FAIL | **O72e-10** r1 |
| 2026-06-03 | **Датчики бирж O104** | Админка `/ops/` + `/status`/push **@FLPARSINGBOT**: кто жив, причина, lag биржа→Neon→лента · cooldown 30 мин | **→ @coder P0** · § O104 |

