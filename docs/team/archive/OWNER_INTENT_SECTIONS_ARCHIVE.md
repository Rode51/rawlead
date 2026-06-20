# OWNER_INTENT — § детали (архив)

Перенесено из hot `OWNER_INTENT.md` 2026-06-20 (audit A5). Канон решений — таблица § «Решения (обязательные)» в hot.

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


---

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

