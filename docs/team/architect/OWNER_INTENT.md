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
| **O38** | **Gemini audit + вся AI-логика** перед stress · strong agent | `problems/2026-05-29-gemini-full-audit.md` |

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
| 2026-05-29 | **O38 scope+** | Mechanic: код + ИИ + **docs drift** + **product drift** (`PRODUCT_VISION` §0d vs prod) | **→ Mechanic** |
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
