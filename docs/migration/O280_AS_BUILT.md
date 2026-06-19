# O280 — as-built (Claude Code verify)

**Verify:** Lead Architect · **2026-06-19** (сессия 5 · full UI + build)  
**Пакет:** `rawlead-next/` · **Prod WP:** theme 1.19.20 (ещё на rawlead.ru)  
**Build:** `npm run build` ✅ · static `out/` — `/`, `/lenta/`, `/cabinet/`, `/pricing/`, `/faq/`, `/how/`, `/contact/`

---

## Вердикт

| Фаза | Статус | Комментарий |
|------|--------|-------------|
| **0** scaffold + API | **✅** | `lib/api.ts`, `types.ts`, smoke `/lenta/` |
| **1** home + full lenta | **✅ 2026-06-19** | Hero · LivePreview · Flow · Features · PricingPreview · FilterBar · FeedCard · MatchBar · LoginModal · QuizOverlay · AnonStrip |
| **1b** lenta polish | **✅ 2026-06-19** | FilterSheet mobile · source filter · skeleton fix · auth timeout |
| **2** cabinet + draft | **✅ 2026-06-19** | anon gate · inbox · copy/delete · subscription (parity fix § handoff) |
| **3** marketing + cutover | **🟡 UI ✅** | `/pricing/` `/faq/` `/how/` `/contact/` · deploy/nginx **pending** |
| **Gate ads** | **🔴** | **O280-E2E-NEXT** green · cutover · Metrika phase 3 |

**Итог:** весь UI MVP в Next ✅ · **следующий шаг** — Playwright n1–n24 (каждая кнопка) → nginx cutover.

---

## Verify checklist (Lead 2026-06-19)

| Проверка | Результат |
|----------|-----------|
| `npm run build` | ✅ 8 routes (+ `/pricing/` `/faq/` `/how/` `/contact/`) |
| Только `rawlead-next/**` | ✅ (read wordpress/docs) |
| Hero H1 prod | ✅ «Заказы под твой стек. Без мусора.» |
| Lenta H1 | ✅ «Лента заказов» |
| Quiz кнопки | ✅ «Мимо» / «Берем» |
| Quiz intro | ✅ «Ответь на карточки — лента найдёт твои заказы» |
| Anon strip | ✅ «Заказы с задержкой 30 мин.» |
| Filter cats | ✅ Все · Разработка · Дизайн · Маркетинг · Тексты |
| Load more | ✅ «Показать ещё» |
| O272 event | ✅ `rawlead-tags-imported` в QuizOverlay |
| JWT rotation | ✅ `X-Rawlead-Access-Token` в `api.ts` |
| API smoke (server) | ✅ `GET /v1/feed` · `GET /v1/public/site-stats` |
| CORS localhost:3001 | ❌ preflight без ACAO — dev показывает mock cards |

---

## Что в repo (файлы)

### App routes

| Route | Файл | Статус |
|-------|------|--------|
| `/` | `app/page.tsx` | ✅ home |
| `/lenta/` | `app/lenta/page.tsx` | ✅ phase 1 |
| `/cabinet/` | `app/cabinet/page.tsx` | ✅ Phase 2 |
| `/pricing/` | `app/pricing/page.tsx` | ✅ |
| `/faq/` | `app/faq/page.tsx` | ✅ |
| `/how/` | `app/how/page.tsx` | ✅ |
| `/contact/` | `app/contact/page.tsx` | ✅ |
| `/quiz/` | — | overlay через `/lenta/#quiz` |

### `lib/`

| Файл | Содержание |
|------|------------|
| `api.ts` | `feedApi`, `authApi`, `meApi`, `quizApi` · JWT rotation · BASE `api.rawlead.ru/v1` |
| `types.ts` | `LeadItem`, `FeedResponse`, auth, draft, subscription, quiz |
| `auth-context.tsx` | `AuthProvider` · `useAuth` · feedTier · hasUserSkills |
| `utils.ts` | `timeAgo` · `SOURCE_LABEL/COLOR` · `NICHE_ICON` · `DIFFICULTY_BADGES` |

### Components

| Папка | Файлы |
|-------|-------|
| `/` | `Providers.tsx` — AuthProvider + SmoothScroll |
| `layout/` | `Header` · `Footer` · `AnnouncementBar` |
| `home/` | `Hero`, `LivePreview`, `FlowSection`, `Features`, `PricingPreview` (+ `HowItWorks`, `Manifest` — не в `page.tsx`) |
| `ui/` | `Button`, `ScrollReveal`, `SmoothScroll` |
| `feed/` | `FeedCard` · `MatchBar` · `FilterBar` · `FilterSheet` · `FilterDropdown` · `AnonStrip` · `LoginModal` · `QuizOverlay` |
| `cabinet/` | `InboxCard` |

### Config

- `next.config.mjs` — `output: 'export'`, `trailingSlash: true` ✅
- `package.json` — Next **14.2.29**, framer-motion, lenis
- `dev` port **3001**

---

## Prod parity — Lead verify 2026-06-19

**Источник:** `curl https://rawlead.ru/*` · `page-*.php` · theme **`ver=1.19.20`** · `scripts/_probe_prod_ui.py`

### `/` home — ✅ близко к prod

| Элемент | Prod (WP) | Next `rawlead-next` |
|---------|-----------|---------------------|
| H1 | «Заказы под твой стек. Без мусора.» | ✅ `Hero.tsx` |
| CTA | «Смотреть ленту» · «Настроить ленту» | ✅ `/lenta/` · квиз через `/lenta/#quiz` (не `/quiz/` route) |
| Nav | Лента · Тарифы · Как устроено | ✅ Header |
| Pricing teaser | RawLead Premium 790 ₽ · 3 дня | ✅ `PricingPreview` |
| Metrika / pageview | `rawlead-metrika.js` | ❌ phase 3 |

### `/lenta/` — ✅ близко к prod

| Элемент | Prod | Next |
|---------|------|------|
| H1 | «Лента заказов» | ✅ |
| Anon strip | задержка 30 мин + TG trial hint | ✅ `AnonStrip` |
| Filter cats | 5 chips | ✅ |
| Mobile filter | sheet «Фильтр» + биржи | ✅ `FilterSheet` (7 sources) |
| Sort | Новые / По совместимости | ✅ |
| Load more | «Показать ещё» + счётчик | ✅ |
| Quiz | overlay «Мимо» / «Берем» | ✅ `QuizOverlay` |
| Link cabinet | «Кабинет →» над H1 | ❌ нет bar |
| Skill-tree modal | в DOM, hidden | ❌ не нужен (quiz-first) |

### `/cabinet/` — 🟡 MVP в Next · **prod parity gaps**

**Reference (истина):** `page-cabinet.php` · `rawlead-cabinet.js` · `rawlead.css` (O219) · `api_server._try_auto_start_trial_on_login`

**⚠️ Не смотреть на `?dev=free` / `?dev=paid`** — это **фейковые моки** для localhost; **не соответствуют prod** (навыки, «Бесплатно», кнопка Trial).

#### Prod-канон кабинета (2026-06-19 · owner confirm)

| Тема | **Как на prod сейчас** |
|------|------------------------|
| **Тариф «Free»** | **Нет отдельного free-тарифа в UI** для нового юзера. Первый вход TG → API **сам** стартует Trial 3 дня (`O219 r6`). |
| **Кнопка «Активировать Trial»** | **Не показываем** новым — trial уже включён. Кнопка в PHP/JS только если `status=free && !trial_used` (редкий legacy). |
| **Навыки / chips** | **Не показываем** (O219 quiz-first): CSS `display:none` на «Твои навыки» + `renderTags()` всегда `hidden`. Профиль = квиз в фоне. |
| **«Пройти тест заново»** | Кнопка **есть** под inbox (не chips) · ведёт на `/lenta/#quiz`. |
| **Подписка H2** | **«RawLead Premium»** (не «ИИ-агент», не «RawLead Free»). |
| **Цена** | «790 ₽/мес · первые 3 дня бесплатно» — **скрыта**, когда trial/premium активен. |
| **Badge** | Trial: `Trial · N дн.` или `✓ Trial Premium · N дн.` · Active: `✅ Premium активен до …` |
| **После trial без оплаты** | Expired + CTA «Подключить Premium» / баннер · лента с задержкой — **не** маркетинговый «Free». |
| **Уведомления** | Секция видна при `effective_access` (trial считается): пороги 60/80/100% · toggle Push. |
| **Inbox** | «Мои отклики» · subtitle · accordion черновик · load more. |

#### STATE 1 — Anon (гость)

| Элемент | **Prod** | **Next** |
|---------|----------|----------|
| H1 | «Кабинет» | ✅ |
| Lead | «…профиль и **черновики**» | ✅ (auth path) |
| Login | TG + QR/poll | ✅ (auth path) |
| `?dev=*` | — | ❌ **убрать/переписать** — вводит в заблуждение |

#### STATE 2 — Auth (после JWT, **реальный** flow)

**Порядок секций prod:**

1. User bar — avatar · «В системе: @name» · bot hint · Выйти  
2. **RawLead Premium** — badge trial/active · detail · pay CTA **только** если нет access / expired  
3. **Уведомления** — при trial/premium  
4. **Мои отклики** — **без** блока навыков/chips · retake quiz опционально · inbox · load more  

| Секция | **Prod** | **Next сейчас** | Fix |
|--------|----------|-----------------|-----|
| Skills chips | **скрыты** | показывает tags + «Твои навыки» | ❌ **убрать** |
| Trial CTA | **auto**, кнопки нет у нового | «Активировать Trial» | ❌ |
| Badge «Бесплатно» | **нет** у нового юзера | есть в dev mock | ❌ |
| Subscription | см. таблицу выше | частично ок в auth path | 🟡 wiring API |
| Уведомления | ✅ | ✅ при isPaid | 🟡 |
| Inbox | ✅ | ✅ | 🟡 pagination ok |
| Skill-tree modal | в DOM, hidden | не строить | ✅ |

**Dev shortcuts:** `?dev=free|paid` — **deprecated для дизайна**; parity только через реальный JWT или обновлённые моки под trial-by-default.

### `/pricing/` — ❌ только на prod

| Элемент | Prod | Next |
|---------|------|------|
| H1 | «Тарифы» | 404 |
| Lead | «Пробуй 3 дня бесплатно — автоматически при первом входе.» | — |
| Card | **RawLead Premium** · 790 ₽/мес · bullets · **«Оформить Premium →»** (YooKassa) | — |
| Legal | trial 1× per TG · no autodebit | — |

**Reference:** `page-pricing.php` · `template-parts/rawlead/pricing-card.php` · `rawlead-pricing.js`

---

## Сверка строк (кратко)

| Элемент | Prod | Next | Match |
|---------|------|------|-------|
| Hero H1 | «Заказы под твой стек. Без мусора.» | Hero | ✅ |
| `/lenta/` H1 | «Лента заказов» | lenta | ✅ |
| Mobile filter | sheet «Фильтр» | FilterSheet | ✅ |
| Cabinet anon lead | «…профиль и черновики» | «…сохранять отклики» | ❌ |
| Cabinet sub title | RawLead Premium | ИИ-агент | ❌ |
| Cabinet notif | есть | нет | ❌ |
| `/pricing/` | есть | 404 | ❌ |

---

## Build (Lead verify 2026-06-19)

```
Route (app)              Size     First Load JS
/                        45.7 kB  142 kB
/lenta                   12.6 kB  109 kB
/cabinet                  7.6 kB  104 kB
```

`out/` — `/`, `/lenta/`, `/cabinet/` static HTML.

---

## Gaps (очередь Claude)

### P0 — cabinet parity (до cutover)

- Anon lead copy + **QR / poll login** как `page-cabinet.php`
- **User bar** (avatar · logout · @rawlead_bot hint)
- Subscription block: **«RawLead Premium»** + trial line prod
- Inbox header subtitle + skills **inline** (не 3 отдельные карточки)

### P0 — phase 3 `/pricing/`

- `page-pricing.php` + `pricing-card.php` + checkout JS parity

### P1

- Cabinet **Уведомления** (push threshold API)
- Inbox **load more** + empty states как WP
- `/lenta/` link «Кабинет →» bar
- Metrika · pageview beacon

### @coder (infra)

- `RADAR_CORS_ORIGINS` + `http://localhost:3001`
- `deploy-web-rawlead-vps.py` + nginx cutover

### Known dev behavior

`lenta/page.tsx` при **любом** fetch error подставляет `MOCK_LEADS` — UI виден без API, но маскирует реальные ошибки. На cutover с CORS ок — не проблема.

---

## Owner smoke (локально)

```bash
cd rawlead-next
npm run dev   # :3001
```

1. `/` — hero, live preview (API или пусто), flow, pricing teaser  
2. `/lenta/` — mock-карточки если CORS · иначе живой feed  
3. Квиз — `/lenta/#quiz` или «Настроить ленту» (если ссылка на `/quiz/` — 404, используй hash)  
4. «Тарифы» / «Кабинет» / «Войти» — лента ok · pricing/cabinet **404 пока завтра**

---

## Handoff Claude — cabinet parity + pricing

```text
O280: cabinet prod parity + /pricing/ (phase 3).
Read FIRST: docs/migration/O280_AS_BUILT.md § Prod parity.
Reference: page-cabinet.php · rawlead-cabinet.js · page-pricing.php.
Do NOT rebuild home or lenta.
```

---

_Обновлять после каждой сессии Claude · sync `rawlead-next/CLAUDE.md` § As-built_
