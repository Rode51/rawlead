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
| **O46** | **Match F2:** `km = matched/lead_tags×100` · «ИДЕАЛЬНО ✦» только при ≥2 тегах лида и полном покрытии · ~~cap навыков **12**~~ → **снят** quiz-first **2026-06-15** | § **PRE-STRESS-PACK O42** · 2026-05-29 |
| **O47** | **L1 tags strict:** Joomla/Bitrix ≠ wordpress_dev · post-validate · golden tests | § **PRE-STRESS-WAVE-2** · **P0 до stress** |
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
| **Внешний** | **O155** Healthchecks.io ping после ok-cycle (grace 15m) | VPS мёртв / цикл завис — алерт **вне** VPS |

**✅ Owner 2026-06-08:** O155 принят · PM2 **не** · YouDo = O156 human, не второй residential.

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

### § O148-w — Pre-warm shared draft (**✅ owner 2026-06-08**)

**Не:** L2 на все visible-лиды в ingest · **не** flash вместо pro.

**Да:** premium раскрыл карточку → фон **1× pro** → `leads.reply_draft` · cap **`DRAFT_WARM_HOURLY_CAP=30`** · клик чаще = L3 only.

**UX:** inflight >**40s** → кнопка «**Сложный бриф, ИИ полирует отклик...**».

**→ Coder:** § **O148-DRAFT-OR** в `CODER_PROMPT.md`.

### § O150-w — Draft UX polish (**owner 2026-06-08 smoke**)

**Симптомы:** «ИИ не успел — повторите» на одном лиде · skeleton вместо сути · плашка розовая не в стиле · FOUT шрифтов.

**Решения владельца:**

| Тема | Решение |
|------|---------|
| Медленный отклик | btn **>20s** (не 40s) → «**Сложный бриф, ИИ полирует отклик...**» |
| Pending UI | **как раньше** — суть задания на месте, **без** серых skeleton-полос |
| Ошибка | плашка под **neo-brutalist** · «Повторить» читаемо |
| Шрифты | preload / убрать прыжок при загрузке |
| Частота fail | максимально сократить (retry · poll failed · direct OR) |

**→ Coder:** § **O150-DRAFT-UX-POLISH** в `CODER_PROMPT.md`.

### § O151-or-45152 — smoke acc1 proxy для OR (**❌ не держим**, 2026-06-08)

**Owner:** попробовать `45.152.197.25:8000` (acc1 TG) как `OPENROUTER_HTTP_PROXY`.

**Smoke VPS:**

| Тест | Результат |
|------|-----------|
| flash-lite через proxy | **200** · ~1.1s |
| pro (64 tok) proxy vs direct | **200** · **2.2s vs 2.1s** — **без выигрыша** |
| cold L2 lead **19231** | client timeout **180s** · сервер **доделал позже** (579 симв.) |
| ранее acc1 для TG HTTPS | **ReadTimeout** (тикет 2026-06-05) |

**Решение Lead:** `OPENROUTER_HTTP_PROXY` **unset** → **direct** (backup `.env.site.bak-or-ab-direct`). Следующий кандидат smoke — **acc2 US `38.154.16.60`**, не acc1.

### § O151-or-acc2 — smoke acc2 для OR (**2026-06-08**)

**Setup:** `OPENROUTER_HTTP_PROXY` ← `TELETHON_PROXY_ACC2` (`38.154.16.60:8000`) · **только env**, TG не трогали.

| Тест | acc2 | direct |
|------|------|--------|
| flash-lite | 1.3s ✅ | — |
| pro 64 tok | **2.7s** ✅ | **5.3s** ✅ |

**Cold L2 #19233:** timeout 185s · pending 3+ min — **не валидно**: после O150 L2 идёт `use_draft_proxy=False` → draft **не** через acc2.

**Вывод:** acc2 **быстрее** на коротком OR; на full draft **не тестировали** · env **unset** (direct). Чтобы acc2 влиял на draft — нужен `use_draft_proxy=True` когда `OPENROUTER_HTTP_PROXY` задан (§ O151 Coder).

**Owner 2026-06-08:** **берём A** + UX: пустая `#rl-feed-error` убрать · «ИИ пишет отклик…» убрать.

**Deploy Lead 2026-06-08:** `patch-vps-openrouter-from-acc2.py` · theme **1.18.47** · L2 draft через **38.154 US** (отдельный env, TG не трогали).

---

## § O100 — «Светофор» (**отклонено**, 2026-06-03)

**Идея:** динамическая цена отклика от `click_count` + FOMO 🟢🟡🔴 на карточке.

**Решение владельца:** **не берём** — «так мы сами превращаемся во FL.ru»; публичная гонка за один лид = биржевая механика, не moat RawLead.

**Почему Lead согласен:**

| Светофор | FL.ru / биржа | RawLead (vision §0, канал 3) |
|----------|---------------|-------------------------------|
| Один hot-лид видят все | Общий заказ, 50 откликов | **Персональный** match по стеку |
| Дороже = «успей» | Аукцион внимания | **Агент** приносит *твои* заказы |
| 🔴 «перегрет» | Конкуренция как продукт | **Совместимость стека** (O82), не очередь |

**Проблема наплыва на hot-лид остаётся** — решать **без** аукциона на карточке:

1. **Развести ленты (уже в каноне):** `final_rank` per user · O30 push только при km ≥ порога · paid instant (O11) — юзеры **не смотрят одну и ту же сортировку**.
2. **O89 + тихий потолок (backend):** после N успешных uniquify на lead — **не** новый mini-LLM, ответ «черновик временно недоступен / возьми другой матч»; **без** счётчика на UI (заказчик не видит «50 откликов RawLead»).
3. **Квота в подписке (Stars):** N черновиков/мес **глобально**, не «цена лида» — fair use, не рынок.
4. **Ingest + match:** больше лидов, меньше «все на один самородок» — O63/O99, не FOMO.

**UI светофора:** только если когда-нибудь вернётся идея — с **@lead-design**; сейчас не в ROADMAP.

**Открытый вопрос владельцу:** что бесит сильнее — **одинаковые отклики на бирже** (O89/judge) или **толпа на один заказ в ленте** (rank/push)?

---

## § O101 — Потолок черновиков на lead (**✅ владелец 2026-06-03**)

**Суть:** на один заказ — **ограниченное число** персональных черновиков (L3). Когда лимит исчерпан — карточка **остаётся в ленте**, кнопка отклика **серая/disabled**. ~~На карточке — строка **«осталось N из 10»**~~ **→ O208-B:** счётчик **не на карточке**; K только в FAQ/pricing. Без аукциона и токенов (≠ O100 ❌).

**Число 10 — старт, не догма:** перед продом прогнать **judge** (синтетика: 1 base → 15–20 L3 с разными `user_id`) → среднее, с какого номера uniqueness/human_tone падают · зафиксировать **K** (может 8, может 12).

| Правило | Простыми словами |
|---------|------------------|
| Что считаем | Только **первый удачный** черновик у юзера на этот заказ. Открыл старый — слот не тратится. |
| Анти-тык | Лимит черновиков **в час на человека** (`DRAFT_HOURLY_LIMIT`) — **owner 2026-06-13: 5/час для всех, вкл. premium** (§ **O208-B**). Слот засчитывается, если есть **нормальный мэтч** по навыкам (km ≥ порога — уточнить в ТЗ, ориентир 30%). |
| Лента | Слотов **0** → заказа **нет в `/lenta/`** для новых. У кого черновик уже есть — видит в **ЛК/inbox**. |
| UI | «Осталось 3 из 10 черновиков» · дизайн позже с @lead-design |
| Ключи OpenRouter | Пачка ключей **не из-за этого**: на заказ макс **1 тяжёлый + K лёгких** L3. Два ключа — для **парсера/L1**, не для кнопки отклика. |

**Этап:** judge-калибровка K → § `CODER_PROMPT` → @coder **после** E2E/regen.

**Gate:** не ломать O72e — judge меряет **base** shared; uniquify — отдельный smoke (5 пар base→rewrite, Sonnet «send не хуже»).

**Handoff:** § **O89** в `CODER_PROMPT.md` · copy → `@lead-product` · UI → `@lead-designer`.

**Старт K=10 (владелец 2026-06-03):** число **10** — рабочая гипотеза до judge; после regen/judge можно сдвинуть (8–12). Не путать с **DRAFT_HOURLY_LIMIT** (anti-тыk на человека).

---

## § O105 — Оплата Premium без эквайринга (**✅ владелец 2026-06-03**)

**Продукт:** **RawLead Premium** — доступ к контуру **O101** (персональный L3, лимит слотов на lead, anti-тык).

**Цена:** **790 ₽/мес** (или эквивалент в USDT/TON по курсу на момент инвойса). Stars **оставляем** (O12/O29) — второй канал, не заменяем.

**Обещание в copy (бот + сайт):**

| Строка | Текст |
|--------|-------|
| Доставка | **&lt; 1 минуты** — paid instant (O11), не anon 15 мин |
| Лимит | **До 10 черновиков на один заказ** — без каннибализма (O101) |
| Уникальность | **ИИ создаёт уникальный черновик** — не бан на бирже, не «как бот» (O89/O72e-10) |

**Flow в @rawlead_bot (канон UX):**

1. Экран выбора: **💳 Банковская карта РФ / СБП** · **🪙 Crypto (USDT / TON)** · (Stars — как сейчас, отдельная ветка).
2. **СБП:** короткое сообщение — «Генерация инвойса для User #[ID]…» · сумма **790 ₽** · реквизиты СБП (Т-Банк, владелец) · кнопка **«Проверить оплату»**.
3. **Crypto:** сумма в USDT (TRC20) и/или TON · адрес кошелька владельца · **«Проверить оплату»**. Кошельки владельца: **Trust** (mobile) — приоритет для TON; MetaMask — опц. для USDT; **v1 = адрес + ручная/полуавто проверка**, не deep-link в кошелёк.
4. После подтверждения — `is_active` + срок подписки (как Stars).

**Техника (волны):**

| Волна | Что | Кто |
|-------|-----|-----|
| **O105-w1** | Тексты бота + кнопки + pending-статус + owner approve в `/ops/` или FLPARSING | @coder |
| **O105-w2** | Crypto: опрос TON API / TronGrid по tx hash или сумме+memo | @coder |
| **O105-w3** | СБП авто-сверка — только с банковским API / ЮKassa; **не сейчас** | backlog O102-pay |

**Не в O105-w1:** подключение MetaMask/Trust in-app (WalletConnect / TON Connect) — **v2**, после первых оплат.

**Copy/UI:** полный проход текстов — `@lead-product` · экраны бота и `/pricing/` — `@lead-designer`.

---

## § O106 — Карточка ленты: меньше шума (**✅ владелец 2026-06-03** · **уточнено O208-B 2026-06-13**)

**Боль:** на карточке **слишком много информации** — перегруз после O94–O97.

**Направление (не код сейчас):** пересборка по эталону `flow.php` + problem-doc O96, но **агрессивнее сжать**:

- **Оставить:** источник · title · бюджет · % совместимости · CTA.
- **Убрать с preview (owner 2026-06-13):** **просмотры** (O25) · **число откликов/слотов** («осталось N из K») — см. § **O208-B**.
- **Убрать/спрятать:** breakdown в collapsed · лишние badge · дубли tool/skill · «качество заказа» (уже out).
- **Раскрытие:** детали (навыки, сложность O97, L3 tray) — **по tap**, не в preview.

**Handoff:** `@lead-designer` wireframe **до** `@coder` · O101 K и hourly — **не на карточке**, только в FAQ/pricing/429 toast.

**Связь:** [`2026-06-02-o96-polish-card-ui.md`](../../problems/2026-06-02-o96-polish-card-ui.md) — baseline, O106 = v2 minimal.

---

## § O208-B — Лимиты · K · карточка · воронка (**owner 2026-06-13 · до Coder**)

**Контекст:** волна 2 O208 — quiz-first. Владелец хочет **зафиксировать продуктовые правила** до кода: анти-спам, judge K, чище карточка, нормальная воронка auth.

### B1 — Hourly cap **5** для всех

| Было | Стало (owner) |
|------|----------------|
| `DRAFT_HOURLY_LIMIT` default 0 (без лимита) · copy «10/час» (O116) | **`5 черновиков/час на человека` — включая premium и trial** |
| Только anti-тык для free? | **Даже premium** — «чтобы придурки не тыкали всё подряд» |

**Техника (Coder, после PM copy freeze):** `DRAFT_HOURLY_LIMIT=5` prod · 429 toast · pricing/FAQ/how **«5 в час»** (не 10). **Не** путать с **K на lead** (O101).

**Warm cap:** `DRAFT_WARM_HOURLY_CAP=30` — отдельный фоновый контур; owner не менял · Coder не трогать без слова.

### B2 — L3 judge → число **K** (когда убирать карточку из ленты)

**Цель:** не гадать K=10 — **прогнать L3 judge** на синтетике (1 shared base → 15–20 персональных L3 с разными `user_id`) и зафиксировать, **с какой генерации** падают uniqueness / human_tone / send_as_is.

| Выход judge | Продуктовое правило |
|-------------|---------------------|
| K финальное (8–12?) | Макс **K** персональных черновиков на один lead (O101) |
| Слоты = 0 | Карточка **не показывается в `/lenta/`** новым · у кого черновик есть — **inbox/ЛК** |

**Кто:** @coder — pilot judge (экономно, как O72e) **до или параллельно** волне 4 L2 · артефакт: `data/preprod_o101_l3_k_judge.json` + одна строка K в `OWNER_INTENT` / `CODER_PROMPT`.

**Не на карточке:** K и «осталось N» — **убрать из preview** (B3); объяснение — FAQ/pricing.

### B3 — Убрать с карточки просмотры и счётчик откликов

**Supersedes частично O25** (синтетические просмотры на preview) и старую строку O101 на карточке.

| Убрать с collapsed/preview | Оставить |
|----------------------------|----------|
| `display_views` · eye-icon · synthetic «N смотрят» | % совместимости · источник · title · бюджет · время |
| «осталось N из K» · synthetic reply count | CTA отклика · glow при генерации (O203) |

**Код сейчас:** `rawlead-feed.js` `viewsHeadHtml` · `syntheticDisplayReplies` · `reply_slots_remaining` в meta.

**Design:** § O208-CARD-MINIMAL в `LEAD_DESIGN_PROMPT` · wireframe до Coder.

### B4 — Воронка auth (**✅ owner 2026-06-14**)

**Supersedes частично:** O107 (кнопка trial) · O174 (1₽ trial) · O116-R1 (free TG без задержки) · O11 (15 мин → **30 мин** для anon/expired).

| Tier | Delay | Drafts | Push | Лента | Прочее |
|------|-------|--------|------|-------|--------|
| **Anon** | **30 мин** | ❌ | ❌ | **flat** — хронология, все источники, **без km-filter** | browse · promo quiz/TG |
| **Trial** (первый TG-login) | **instant** | ✅ | ✅ | **персональная** (km-sort, match) | auto **3d бесплатно** · **5/h** · 1× на `user_id` |
| **Expired-trial / free** | **30 мин** | ❌ | ❌ | **flat** — как anon | inbox сохраняется · quiz учится но **не влияет на rank** |
| **Premium** | **instant** | ✅ | ✅ | **персональная** | **5/h** · 790₽/мес |

**Правила активации trial:**
- **Auto** при **первом успешном TG-login** — не на anon · не явная кнопка
- **Бесплатно** (не 1₽ ЮKassa)
- После 3d → downgrade в expired/free row выше

**Flat feed (anon + expired):** последние заказы по времени · все источники · **без** персонального ранжирования / min_match / km-sort · filter bar скрыт или disabled (PM+Design).

**UX expired-trial (owner ✅ 2026-06-14):** **обязательный баннер** на `/lenta/` и в ЛК — не тихая деградация:
- Copy (черновик PM): **«Пробный период закончился · Лента без фильтров и с задержкой 30 мин · Вернуть персонализацию → Premium 790 ₽»**
- CTA → `/pricing/` или pay flow

**Coder (после PM+Design freeze):** `apply_delay` для anon **и** expired-trial JWT · `plan=trial` auto на first login · flat feed mode flag.

**Handoff:** `@lead-product` copy pack · `@lead-designer` paywall/expired banner wireframe → `@coder`.

---

## § O107 — Trial Premium 3 дня (**✅ владелец 2026-06-03** · **amended O208-B4 2026-06-14**)

**Суть:** новый пользователь получает **3 календарных дня** полного **Premium** — instant · черновики · push · O101 · **5/h**.

**Amended (O208-B4):** активация **auto при первом TG-login** (не кнопка) · **бесплатно** (supersedes O174 1₽) · после trial → **flat feed + 30 мин** (как anon).

**Не путать:** ≠ **3q** «3 матча бесплатно» из vision — **O107 заменяет 3q на запуске** (полный Premium, не лимит матчей).

| Правило | Канон (v1) |
|---------|------------|
| Длительность | **3×24 ч** с момента активации |
| Кто | Любой **новый** TG-аккаунт после `/login` · **1 trial на `user_id` навсегда** |
| Активация | **Явная кнопка** «Попробовать 3 дня бесплатно» — **не** автостарт при регистрации (Lead рекомендация: меньше абьюза) |
| Во время trial | `plan=trial` · `is_active=true` · `active_until=now+3d` · **полный** Premium |
| После окончания | → `free` · лента с **15 мин** задержкой · новые черновики **закрыты** · **inbox сохраняется** (уже созданные черновики не удаляем) |
| Оплата | **Без карты / без Stars** на старте trial · конверсия → `/pay` (O105) |
| Напоминания | За **24 ч** до конца — push/TG: «Trial заканчивается завтра» · в день X — «Trial закончился · Premium 790 ₽» |
| Абьюз | Повторный trial → «Trial уже использован» · мультиаккаунты — **не** блокируем в v1 |

**Copy (черновик → PM):**

- CTA: **«Попробовать 3 дня бесплатно»**
- Badge в ЛК: **«Trial · осталось N дн.»**
- Pricing: **«3 дня Premium бесплатно — один раз на аккаунт»**

**Техника (Coder, после E2E, вместе с O105-w1):**

- Neon: `subscriptions.trial_used_at TIMESTAMPTZ` **или** `plan='trial'` + проверка истории
- API/bot: `POST /v1/subscription/trial-start` · guard «уже был trial»
- Cron/check: при `active_until < now` и `plan=trial` → downgrade free
- UI: trial badge · CTA скрыть если `trial_used`

**Gate:** PM прописать тексты + Design (badge, CTA) · **не** auto-renew (нет эквайринга).

**Открыто на PM (если владелец не сказал иначе):** trial с **первого входа** доступен только в `/cabinet/` или ещё на anon-strip `/lenta/`?

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
2. ~~Ограничения max 12~~ — **снято owner 2026-06-15** (quiz-first, manual picker убран)
3. ~~Telemetry~~ ✅
4. A/B — **отложено** до O93
5. Веса/auto-priorities — после O93

---

## § QUIZ-FIRST-NO-CAP — **owner 2026-06-15**

**Решение:** ручной ввод навыков **нет** (O208) · лимит **12 не держим** — обрезка при import **вредит** профилю.

| Было | Стало |
|------|--------|
| Skill Tree sheet · «Выбрано N / 12» | **Квиз** + retake + behavior weights |
| API/UI reject или trim >12 | **Без cap** на quiz import · `__quiz_niche:*` отдельно |
| PRODUCT_CANON «макс 12» | **Снято** · канон → `PRODUCT_CANON` §4 · `feed-cabinet-mvp` §0.1 |

**Код:** ✅ O230 prod **2026-06-15**.

**Owner 2026-06-15 · inbox delete:** удалил отклик в ЛК → на карточке в ленте **нет** «Отклик ✓» и match без draft-boost → § **O231-INBOX-DELETE-MATCH**.

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

## § O94-w3 — UX лента (feedback владельца 2026-06-02)

| # | Решение |
|---|---------|
| 1 | L3 **под** выбранным L1, без сдвига соседних чипов (wrap column) |
| 2 | L3 плашки **меньше** — явный tier 3 |
| 3 | Sort **только** клик «по дате»/«по совместимости» под заголовком; **убрать** «Дата ▾» сверху |
| 4 | Счётчик: **N заказов · M новых сегодня** |
| 5 | Modal навыков = **как ЛК**; **без** «Ещё навыки»; **«Мои навыки»** из профиля |

**→ @coder** § O94-w3 · deploy **1.15.0** ✅

**Follow-up владельца:** w3 технически OK, но **UX плохой** — L3 «те же плашки», взгляд теряется → **Design O94-w4** (не CSS-hotfix).

---

## § O94-w4 — Design: Skill Tree L3 UX (2026-06-02)

**Запрос владельца:** окно навыков неудобно — при клике всё съезжает, подуровень не отличить от L1.

**Решение Lead:** **@designer** wireframe 2–3 варианта → `feed-cabinet-mvp` § **4.7** → `@coder` § **O94-w4-code**.

**Gate:** Coder **stop** skill-tree UI до approve Design.

**Scope (rev 2026-06-02):** O94-w4 — **единый** Skill Tree sheet (cabinet + lenta ⚙ logged-in). Anon lenta — без sheet (§ O95).

**Lead рекомендует:** sub-tray + ghost L3 + copy «уточнение, необязательно».

---

## § O95 — `/lenta/` два режима (**✅ решение владельца 2026-06-02**)

### 1. Anon (гость)

- Filter bar: **только** **Все / Разработка / Дизайн / Маркетинг / Тексты** — **без** «Навыки · N»
- Лента: фильтр по **category**, без keyword match
- Карточка: **нет** % совместимости · CTA: *«Зарегистрируйтесь, чтобы настроить точный мэтчинг под свой стек и забрать готовый черновик отклика»* → login
- Удалить: guest `localStorage`, modal навыков на ленте

**Зачем:** показать свежие заказы → триггер регистрации.

### 2. Logged-in (Free/Paid TG)

- **Нет** chips категорий на `/lenta/` — лента = **персональная** по `user_tags` (Neon, до 12 из ЛК)
- Match % на карточках · sort по совместимости
- Строка статуса + **«Изменить навыки»** (⚙) → **та же** bottom-sheet Skill Tree v0.5
- **Save sheet = `PUT /v1/me/tags`** · лента ↔ ЛК **один профиль** (настроил на ленте → в ЛК; в ЛК → на ленте)

**Design O94-w4:** L3 tray для **единого** sheet (lenta + cabinet), не «только ЛК».

**Vision:** `@lead-product` — §0 anon без tag-picker; registered = profile-driven feed.

**→ @coder** § **O95** · **→ @designer** § **O94-w4** (общий sheet)

**Owner smoke 2026-06-02 (1.16.0):** hint «Применить»≠«Сохранить» · лимит 12/12 ругается · telethon×2 в tray · ⚙ lenta save не обновляет feed · sort «по дате» dead click без tags · **→ @coder § O95-fix** · тикет `problems/2026-06-02-o95-feed-skills-regression.md`

---

## § O96 — полный copy-pass + tone (**→ @lead-product · 2026-06-02**)

**Решение владельца 2026-06-02:** сначала **Lead Product**, потом **Design**. **Не лезть в docs сразу** — сначала **совет с владельцем**, спор если надо, **только после OK** — результат в канон.

**Tone:** немного **дерзкий**, живой · **подробно** по каждому экрану (anon / login / pay / empty / error).

**Scope Product:** все тексты — /lenta/ · /cabinet/ · /pricing/ · лендинг · header · тексты badge O97 (1–4).

**Scope Design (после OK copy · @lead-designer):** UX всех страниц · карточки легче · **категория на карточке** · skill tree (O98-w) · design tests.

**Статус O96-D:** **✅ Lead Designer ф2 2026-06-02** · `feed-cabinet-mvp` §4.8–4.10 · §7.7.

**Статус O97-code:** **✅ API deploy 2026-06-02**

**Статус O97-bench (владелец 2026-06-02):** judge по **complexity 1–4** (4 = нет норм ТЗ) · gate **≥70% ok** или avg **≥3/4** · force backfill ~80 · **до E2E/vault**.

**Порядок:** **→ @coder § O97-bench** → E2E → vault.

## § O97 — Тег сложности 1–4 (**✅ решение владельца 2026-06-02, апдейт 4-уровневая шкала**)

**Зачем:** фрилансер сразу видит «сожрёт вечер» vs «помойка без ТЗ» — до клика в заказ.

**Архитектура (Lead):** **L1 Judge** (Gemini Flash Lite) — +1 поле в JSON разметки. **Без новых таблиц Neon** — persist в существующий JSON (`ai_reasons` или эквивалент L1 payload). Guardrail O92/O93: **не** трогаем schema/judge-инфру на v1, только промпт + parse + UI.

**Шкала промпта (тех. канон):**

| N | Смысл |
|---|--------|
| 1 | Скрипт · 1 файл · ~1 вечер · видеоурок |
| 2 | Типовой проект · ясное ТЗ · лендинг/бот/WP |
| 3 | Несколько систем / монолит **с нормальным ТЗ** |
| 4 | **Нет нормального ТЗ** · «сделайте красиво» · риск на исполнителе |

**UI-плашки (🟢🟡🟠🔴):** **→ @lead-product** + **→ @designer** · badge **4 = «Без норм ТЗ»**.

**Порядок:** **после O96-copy · до E2E и PRE-PROD AI vault (O21)**. Новые прогоны vault — **только после O97 + bench**.

**Волны:**

| # | Кто | Что |
|---|-----|-----|
| w1 | @lead-product | Copy «что значит N/5 для юзера» · tooltip |
| w2 | @designer | Badge wireframe · feed card § |
| w3 | @coder | L1 prompt · parse · persist · UI · targeted bench |
| w4 | Lead | Gate calibration · потом vault |

**→ @coder** § **O97** (queued) · **→ @lead-product** § **O97-w1** · **→ @designer** § **O97-w2**

---

## § O98-w — Skill Tree UX: переписать фильтр навыков (**→ @designer · queued**)

**Запрос владельца 2026-06-02:** picker навыков (⚙ `/lenta/` + modal `/cabinet/`) **жутко неудобен** — **как лучше, пока не знает**.

**Lead:** не tray-hotfix — **Design-исследование** 2–3 концепта → `feed-cabinet-mvp` § **4.8** → Coder.

**После:** O97-w2 · **до** E2E / vault · Coder не раньше approve макета.

**Симптомы:** tray раздувается · 4 ниши × 12 лимит · tier неочевиден · детали → [`DESIGNER_PROMPT.md`](../design/DESIGNER_PROMPT.md) § O98-w.

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
| ~~P2~~ | ~~**O100 Светофор**~~ | § **O100** | **❌** — не аукцион на лиде |

**Волна 2026-05-28 принята Lead** — детали: [`STATUS.md`](../common/STATUS.md) · [`archive/TASKS_HISTORY.md`](../archive/TASKS_HISTORY.md).

---

## § O116 — UI/UX + copy перед рекламой (**2026-06-04 · владелец**)

**Цель:** polish маркетинга + лента/ЛК/тариф/FAQ/how/contact · **не блокирует** L2 r11 (другие файлы).

**Порядок Lead:** W1–b2 ✅ · **W4 код** ✅ · prod deploy **1.18.14** ⏸ · O116 закрыть после deploy+smoke.

**Ops 2026-06-04:** `deploy-o116-mkt-vps.py` · `scripts/apply_neon_018.py` на VPS.

**Handoff Coder (2026-06-04):** `CODER_PROMPT` § **O116-WP-Z234** · Design `LEAD_DESIGN_PROMPT` § O116-D · PM § O116-COPY.

### Решения владельца (2026-06-04) — **✅ зафиксировано**

| # | Вопрос | Решение |
|---|--------|---------|
| **R1** | Persist сортировки | **B)** `localStorage` + **Neon** `user_feed_prefs` (sync при login, merge с локальным) |
| **R2** | Задержка 15 мин | **Только anon** без JWT. **Любой зарегистрированный** (TG-login, free/trial/expired) — **без задержки** в API и UI. Убрать баннер/strip/FAQ-строки про 15 мин для auth. **Уточнение O11** — см. ниже |
| **R3** | Contact / support | **TG владельцу** (личный чат `TELEGRAM_CHAT_ID`): бот шлёт **«Тикет от пользователя N»** + текст. **Не email.** Ответ пользователю — по-прежнему окно «Поддержка» + admin (Neon threads), красный `!` |

**O11 amend (решение владельца):** две скорости → **anon ~15 мин** · **registered instant** · **premium** = instant + черновики/push/слоты (без изменения paid-gate на draft).

**Код сейчас:** `/v1/feed` снимает delay только при `_user_effective_access` (paid/trial) — **Coder:** при валидном `user_id` → `apply_delay=False` (personal match rank можно оставить только для paid, отдельно от delay).

### W1 — Copy (→ `LEAD_PRODUCT_PROMPT` § O116-COPY)

| # | Поверхность | Было → Стало |
|---|-------------|--------------|
| 1 | Hero | «Меньше вкладок…» — **отступ ниже** (design spacing) |
| 2 | Home flow | **Убрать** 3 карточки под «один поток…» (Не один текст / Не автоспам / До 10 откликов…) |
| 3 | Pricing | Убрать `(~800–1440 ₽)` · убрать «FL.ru PRO — 1 270 ₽… RawLead — подбор…» (везде) |
| 4 | Pricing bullet | «До 10 персональных…» → **«Умный лимит (10 откликов в час) — защита от спам-фильтров бирж»** |
| 5 | Pricing | Убрать «Каждая строка откроет @rawlead_bot…» |
| 6 | Pricing CTA free | «Смотреть ленту» → **«Продолжить с ограничениями (Free) →»** |
| 7 | How | **Добавить** блок «Защита от спама» (текст владельца) |
| 8 | FAQ Q | **Anon:** 15 мин · **зарегистрированный:** без задержки (free) · Premium: черновики/push · лимит 10 / Telegram / trial — формулировки чат 2026-06-04 |
| 9 | Feed slot | «Осталось 10 из 10 ⓘ» → **«написано 10 из 10 ⓘ»** · tooltip: «Только 10 пользователей…» |

### W2 — Design spec (→ `LEAD_DESIGN_PROMPT` § O116-D)

| # | UX | DoD |
|---|-----|-----|
| D1 | **Ticker** header | 3 фразы (факт + агрегатор + Python/FastAPI/…) · цикл **25–30 с** · **pause on hover** · mobile short variant |
| D2 | **Факты ticker** | «Радар онлайн · N лидов…» — **живые** из API/status (не хардкод 800+) |
| D3 | **Feed toolbar** | `Сортировка: Свежие \| Совместимость от: [80% ↓]` — без тяжёлых dropdown |
| D4 | **Persist prefs** | **R1:** localStorage + Neon `user_feed_prefs` · merge on login |
| D5 | **Карточка** | glow при draft → flip back · pulse «идеальный матч» · теги match/gray · `+n` раскрывается на flip |
| D6 | **Бейдж биржи** | выше/левее · спец в кружке · **stack** для смежных |
| D7 | **Free anon** | серая полоска совместимости + 🔒 · CTA «Написать отклик» бледный · shake → «открыть доступ» → `/pricing/` |
| D8 | **Сложность** | только **paid** · только **задняя** сторона карты |
| D9 | **ЛК** | карточки компактнее · **убрать** Пауза/Возобновить/Оплата · premium: «продлить» не trial |
| D10 | **ⓘ icon** | нормальная иконка (не кривой символ) |

### W3 — Coder (→ `CODER_PROMPT` § O116)

| # | Backend / WP | Файлы (ориентир) |
|---|--------------|------------------|
| C1 | **Prefs persist** | **R1:** `rawlead_feed_prefs` localStorage · `PUT/GET /v1/me/feed-prefs` → Neon JSON `{sort,min_match,category}` · on login merge (server wins on conflict или newest ts — Coder) |
| C2 | **Feed API** | `GET /v1/feed` — для **auth** те же query `sort`/`min_match` что anon · specialty sort как у anon |
| C3 | **Toolbar** | заменить toggle на селектор Свежие \| % (default 80, шаги 70/80/90?) |
| C4 | **Delay R2** | `api_server.py` `/v1/feed`: valid JWT → `apply_delay=False` (не только paid). UI: strip/banner `#rl-feed-delay-notice` · anon strip в `page-lenta.php` — **только anon** · cabinet copy без «15 мин» для auth |
| C4b | **Убрать** | «20 заказов под профиль» |
| C5 | **Теги** | match → brand green/yellow · missing profile → muted gray · `+n` on flip |
| C6 | **Views fake** | «отклики» −1 от просмотров · rand 8–10 · не писать реальный draft |
| C7 | **Hourly limit** | `DRAFT_HOURLY_LIMIT=10` prod · UI copy согласован · `draft_limits.py` уже есть |
| C8 | **Pay deeplink** | pricing кнопки → bot tab crypto/sbp/stars (O109 pattern) |
| C9 | **ЛК inbox** | total replies (не page count) · delete sync · **тот же** sort UI что лента |
| C10 | **Cabinet states** | hide trial if premium/active · expired → «возобновить» без 3 дня |

### W4 — Contact + support (**R3 · после W3**)

| # | Что | DoD |
|---|-----|-----|
| I1 | **Inbound** | `/contact/` форма + FAB «Поддержка» → `POST /v1/support/ticket` · Neon thread |
| I2 | **→ владелец TG** | @rawlead_bot → `TELEGRAM_CHAT_ID`: **«Тикет от пользователя {n}»** (@username, user_id, превью текста) · reuse `relay_message_to_owner_chat` / Bot API |
| I3 | **Admin reply** | owner admin panel → ответ в thread → пользователь видит в modal «Поддержка» |
| I4 | **Badge** | красный `!` на FAB/иконке при непрочитанном ответе |

**Не в v1:** email · `mail()` на WP.

---

## § MIMO-AUDIT — MiMo Code pilot (owner 2026-06-12 · уточнено 2026-06-19)

**Что это:** [MiMo Code](https://github.com/XiaomiMiMo/MiMo-Code) — **terminal coding agent** (fork [OpenCode](https://github.com/anomalyco/opencode)), MIT · v0.1.1 · Xiaomi MiMo team · **не просто модель**, а оболочка с памятью, subagents, long-horizon loops.

**Модель:** MiMo-V2.5 (MoE, заявлен **1M tokens** context) · канал **MiMo Auto** — бесплатно **ограниченное время**, без регистрации · трафик через **серверы Xiaomi** (не self-host модели).

**Маркетинг vs факты (Lead):**

| Обещание в постах | Реальность |
|-------------------|------------|
| «Безлимитный контекст / миллионы строк» | в доке **1M tokens** (~сотни K строк, не ∞) |
| «Разносит Claude Code на 3 бенчах» | SWE-bench / Terminal Bench — **свои прогоны Xiaomi** · v0.1 · 499 open issues на GitHub |
| «Полный опенсорс» | **CLI/harness** MIT ✅ · **веса MiMo-V2.5** — отдельно, free channel = облако |
| «Без потерь данных» | persistent memory в агенте — **не** гарантия для prod secrets |

**Зачем нам:** второй проход **полного аудита** (наследник **O38** Gemini 2M) — `src/` parsers · `ai_analyze` L1/L2 · `rawlead-next/` · docs drift · после Next cutover включить nginx/deploy.

**Кто:** **владелец** pilot (отдельный терминал) · **не** замена Cursor/Coder в hot path · findings → `docs/problems/YYYY-MM-DD-mimo-audit.md` → Lead triage → `@coder` / `@mechanic`.

**Когда:** **после O280 cutover** (или параллельно на **копии** репо, если не трогаешь hot Coder) · **не** блокирует M1 ads.

**Безопасность (обязательно):**

- клон/копия репо **без** `.env` / `.env.site` / сессий TG / VPS keys
- **не** MiMo Auto на репо с secrets — или Custom Provider → свой OpenRouter (уже есть)
- итог аудита — markdown в `docs/problems/`, не сырой лог с токенами в git

**Установка (Windows):** `npm install -g @mimo-ai/cli` · [mimo.xiaomi.com/coder](https://mimo.xiaomi.com/coder) · WSL clipboard — см. README.

**Промпт старта (копипаст в MiMo):** «Read `docs/README.md` → `PROJECT_MAP.md` → `ARCHITECTURE.md` → `src/ai_analyze.py` + parsers. Report: AI P0/P1, parser stability, docs drift vs prod, Next `rawlead-next/` risks. Format like `problems/2026-05-29-gemini-full-audit.md`. No code changes.»

**Сравнение с текущим стеком:**

| | Cursor + Coder | Mechanic Gemini 2M | MiMo Code |
|--|----------------|-------------------|-----------|
| Роль | плановые фичи | инциденты | **разовый wide audit** |
| Контекст | чат + rules | ~2M OR | harness + 1M claim |
| Секреты | `.cursorignore` | тикет | **owner: чистая копия** |

---

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

## § O99 — Очеловечить парсер + быстрее на ленту (P0 продукт)

**Боль владельца 2026-06-03:** прокси-каскад не даёт ощущения «премиум мгновенно»; банит быстро; хочется **обойти антибот** без рулетки IP.

**Позиция Lead:** «обойти» = не взлом, а **меньше похоже на бота** + **развязать скорость ленты от L1**.

| # | Решение | DoD |
|---|---------|-----|
| 1 | **FL/Kwork fetch через браузер** (Playwright persistent context или аналог), cookies на слот, jitter 200–800 ms, стабильный UA | 24 ч без `alive=0/4` на primary при нормальных IP |
| 2 | **Быстрый путь (владелец 2026-06-03):** в ленту **только после L1** (`feed_visible=true`) — **без** карточек «только заголовок» (иначе спам). Ускорение = L1 **сразу** на каждый новый FL/Kwork (не ждать конец цикла), приоритет hot над backlog, 3 воркера | p95 feed_lag fl/kwork &lt; 3 мин (O90) |
| 3 | **Опрос secondary** (YouDo/Пчёл) — реже или отдельный пул; **не** 403→бан primary | FL цикл не блокируется |
| 4 | **Бан 403:** 2× подряд на **том же** source перед TTL (уже в бэклоге v2.1) | меньше ложных банов |
| 5 | **Инфра:** 6–8 IP, FL/Kwork только primary; residential опц. | `DEPLOY_VPS.md` |
| 6 | **2-й OpenRouter ключ L1** | ✅ `OPENROUTER_API_KEY_L1_B` на VPS · round-robin воркеры 2/4 → ключ B · `L1_MAX_WORKERS=4` | `l1_pool.py` · `ai_analyze.py` |

**Не в O99:** смена judge/O97 · редизайн ленты · TG (уже event-driven).

### O99-w — второй ключ OpenRouter (владелец 2026-06-03)

**Идея:** ещё один ИИ-поток → очередь L1 не растягивается.

**Факты:** сейчас **3 воркера** (`L1_MAX_WORKERS=3`), **один** `OPENROUTER_API_KEY`. Второй ключ **ускоряет**, если упираемся в **лимит RPM** OpenRouter, а не в fetch/прокси.

**Без кода (сразу):** на VPS `L1_MAX_WORKERS=4` в `.env.site` + рестарт radar — если 429 нет, хватит одного ключа.

**Код (2026-06-03):** `cfg.l1_openrouter_api_key(slot)` — воркеры **1,3** → основной ключ, **2,4** → `OPENROUTER_API_KEY_L1_B`. L2/judge — только основной.

**Не делать:** второй ключ на L2/judge/backfill.

**Очередь:** **E2E** · инфра **#5** (6–8 IP) — ops по необходимости · regen/judge **откликов** — параллельный чат, не ingest.

**Coder:** O99 ingest **✅ 2026-06-03** — см. `STATUS.md`.
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

| 2026-06-04 | **O108 v1.1 B+C** | Лимиты по типу · маркер «файл есть, не прочитан» · красный chip на карточке | **✅ решение владельца** · § O108 · **→ Coder** |
| 2026-06-04 | **TG в PUBLIC_FEED** | 21 канал allowlist + secondary биржи в `/lenta/` | **✅ решение владельца** · VPS `.env.site` |
| 2026-06-04 | **O116 W1 triage** | delay только anon (R1) · FAQ три уровня (R2) · strip + pricing copy (R3) | **→ § O116** · `LEAD_PRODUCT_PROMPT` § O116-COPY |
| 2026-06-04 | **O116 R1–R3 ✅** | R1 принят · R2 принят · R3 обязателен → **→ W2 @lead-designer** | § O116 · `LEAD_PRODUCT_PROMPT` § O116-COPY |

---

## § O108 — TZ из вложений (**→ Coder · v1 + v1.1 B+C**)

**Боль:** на FL/Kwork полное ТЗ часто **только во вложении** — L1/L2 «слепые»; модель пишет «вижу ZIP», хотя файла не читала.

**Решение владельца 2026-06-04:** гибрид **B + C** — умные лимиты + маркер честности + **красный** индикатор на карточке, если ТЗ на странице есть, но текст не извлечён (**причина — вес**).

### v1.1 B — умные лимиты (`.env`)

| Тип | Лимит | Поведение |
|-----|-------|-----------|
| `.docx` `.pdf` `.txt` | **8 MB** (`TZ_ATTACHMENT_MAX_TEXT_MB`) | полный extract |
| `.zip` `.rar` | **2 MB** (`TZ_ATTACHMENT_MAX_ARCHIVE_MB`) | ≤2 MB — extract текстовых внутри; **>**2 MB — **только листинг имён** |

### v1.1 C — маркер честности

```text
[TZ attachment — файл на странице, 52 MB, текст не извлечён из-за размера]
```

**L2:** можно «вижу, что прикрепили архив N MB — ознакомлюсь в диалоге» · **нельзя** описывать содержимое.

**Persist:** `ai_reasons.tz_attachment` → `{status, filename, size_mb, reason}`.

### UI — красный chip (`/lenta/`)

| status | Chip (**#C0392B**, `.rl-feed-card__tz-warn`) |
|--------|-----------------------------------------------|
| `skipped_size` | **ТЗ не прочитано · 52 MB** |
| `skipped_auth` | **ТЗ не прочитано · нужен вход на биржу** |
| `skipped_empty` | **ТЗ не прочитано · файл без текста** |
| `extracted` | chip не показывать (v1.1) |

Под «Суть задания», над черновиком. Полный DoD → `CODER_PROMPT` § O108-BC.

---

## § O109 — Kwork delist + bot deeplink «Лента» (**→ ✅ Coder · 2026-06-04**)

**Боль (владелец 2026-06-03):** бот прислал Match push по Kwork, карточки **нет в `/lenta/`**; кнопка «Лента» открывает общую ленту, а не нужный заказ.

**Корень:** O65 `delist_reason=source_gone` — ложный срабатывание: в `_KWORK_GONE_MARKERS` была подстрока `"404"` (встречается в тексте ТЗ, не только HTTP 404). Push успевал до delist.

**Решение:**

| # | Что | DoD |
|---|-----|-----|
| 1 | **Delist fix** | убрать `"404"` из HTML-маркеров; HTTP 404 status — оставить; grace **6 ч** после `l1_completed_at` перед recheck |
| 2 | **Relist** | `UPDATE` kwork с `delist_reason=source_gone` за 14 дней (скрипт `ops-relist-kwork-vps.py`) |
| 3 | **Bot deeplink** | «Лента» → `https://rawlead.ru/lenta/?lead={id}` |
| 4 | **Feed UX** | parse `?lead=` · fetch card если нет в списке · scroll + expand · pulse `.rl-lead-card--push-focus` |

**Theme:** **1.18.6** · verify lead **#11837** (Kwork 3190279) в feed.

**Процесс:** код сессии до ужесточения Lead rules — retroactive verify; rules A+B+C в `lead-no-code.mdc` / `lead-architect.mdc` / `LEAD.md`.

---

## § O108 (архив spec 2026-06-03)

_Заменено решением v1.1 B+C выше._

**Боль (архив):** listing/body короткий → L1/L2 «слепые», judge FAIL on specificity.

**Идея владельца 2026-06-03:** Playwright на **странице заказа** видит ссылку на файл → скачать → вытащить текст → дописать в контекст перед L1/L2.

| # | Решение | DoD v1 |
|---|---------|--------|
| 1 | **Detect** | на detail-fetch FL/Kwork: `<a href*="download">` / known CDN patterns · whitelist `.docx` `.pdf` `.txt` |
| 2 | **Download** | Playwright → `/tmp/rawlead_attach/{lead_id}/` · max **2 MB** · timeout 30s · cleanup после extract |
| 3 | **Extract** | `python-docx` (docx) · `pypdf` (pdf text-layer) · fallback skip |
| 4 | **Enrich** | append к `body` / `task_text` с маркером `[TZ attachment]` · cap **8k chars** в prompt |
| 5 | **Persist** | опц. `leads.attachment_text` или поле в `ai_reasons` — не дублировать каждый L1 |
| 6 | **Fail-open** | нет файла / auth wall / scan-PDF → ingest как сейчас, **не** блокировать |

**Lead: идея ✅ норм**, с оговорками:

- **v1 без OCR** — сканы в PDF не прочитаем (pypdf пустой) · v2: Tesseract opt-in.
- **Auth:** часть файлов только залогиненному — нужна cookie-сессия browser profile (как O99), не httpx.
- **Когда качать:** только **detail page** (не listing) · только если `len(body) < N` или явная ссылка «скачать ТЗ».
- **Не в v1:** .zip, .rar, exe · malware scan · хранение файлов на диске Neon.
- **Оценка:** ~1 вечер spike + ~1 вечер prod (FL+Kwork) · отдельный § Coder после **O72e vault PASS**.

**Очередь:** после E2E/vault · параллельно не блокирует O101/O105.

---

## § O116 — Pre-ads copy: TWO-SPEEDS update + FAQ (**W1 PM · 2026-06-04**)

**Контекст:** перед soft-ads. Три решения, которые напрямую влияют на конверсию холодного трафика из рекламы.

**Волны:** W1 PM → W2 Design → W3 Coder.

### Решения владельца R1–R3

| # | Решение | Суть | Следствие |
|---|---------|------|-----------|
| **R1** | **Delay только anon** | Задержка 15 мин — **только без TG-входа**. Free TG login = лента **без задержки**, **без кнопки «Написать отклик»** | Новый funnel для рекламы: anon → TG login → Premium; hook «войди — без ожидания» |
| **R2** | **FAQ три уровня** | Flat Q1–Q9 → три группы: «Начало» / «Как работает» / «Premium» + NEW Q10 (объяснение R1) | Навигатор для холодного трафика; на мобайл — аккордеон |
| **R3** | **Strip + pricing copy update** | Anon strip → «⏱ Лента с задержкой · [Войди — сразу →]» · Free strip — убрать label задержки · Pricing Feature 1 → черновики главное (не «без задержки») | Честный UX под R1; value-prop Premium = черновики + push + inbox |

**Принято владельцем 2026-06-04:** R1 ✅ · R2 ✅ · R3 ✅ (обязателен вслед за R1).

**Copy + FAQ spec (полный):** [`LEAD_PRODUCT_PROMPT.md`](../../product/LEAD_PRODUCT_PROMPT.md) § **O116-COPY** (Z1–Z4).

---

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
