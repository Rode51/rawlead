# RawLead — инвентарь страниц и экранов (prod WP)

**Домен:** `https://rawlead.ru` · **тема:** `rawlead-kadence-child` **`1.19.20`** (asset `ver=` на `/lenta/`, 2026-06-19)  
**Цель Next:** пакет `rawlead-next/` · **не путать** с `portfolio/` (`https://rode51.ru` — личный сайт Rode51).

**Prod verify:** Playwright smoke **2026-06-19** (desktop 1280px, гость) + сверка с `wordpress/rawlead-kadence-child/`.

Легенда доступа: **Гость** · **Auth** (JWT в `localStorage` `rawlead_access_token`) · **Premium** (`effective_access` из subscription).

---

## Prod snapshot (как на сайте сейчас)

| Факт | Значение на prod |
|------|------------------|
| Hero H1 `/` | **«Заказы под твой стек. Без мусора.»** (не «Лиды без шума») |
| Hero CTA | **«Смотреть ленту →»** · **«Настроить ленту →»** (`/quiz/`) |
| Announcement | **«Радар онлайн · N лидов в неделю»** → CTA «Смотреть ленту →» |
| Nav (marketing) | Лента · Тарифы · Как устроено · Войти |
| `/lenta/` H1 | **«Лента заказов»** |
| Load more | **«Показать ещё»** (не infinite scroll) |
| Anon strip | **«Заказы с задержкой 30 мин.»** · **«Войди через TG — 3 дня Premium бесплатно»** |
| Filter bar cats | Все · Разработка · Дизайн · Маркетинг · Тексты |
| Filter «Навыки» | **скрыт для auth** (`display:none` O199) · у гостя кнопка **locked** · mobile — sheet **«Фильтр»** |
| Skill-tree modal | **в HTML**, `hidden` · **не primary UX** — профиль через **квиз** |
| Quiz кнопки | **«Мимо»** · **«Берем»** (не «Да, близко» / «Не моё») |
| Quiz intro H1 | **«Ответь на карточки — лента найдёт твои заказы»** |
| `/pricing/` | H1 **«Тарифы»** · **790 ₽/мес** · trial **3 дня** auto |
| `/cabinet/` gate | H1 **«Кабинет»** · lead **«Лента уже подбирает совпадения… черновики»** · **«Войти через Telegram»** · QR/poll |

**Next (O280):** портировать **поведение** и API; визуал — не в этом файле.

---

## Сводка MVP (gate до рекламы)

| Приоритет | URL | MVP |
|-----------|-----|-----|
| P0 | `/lenta/` | ✅ |
| P0 | Экран карточки заказа (expand / `?lead=`) | ✅ |
| P0 | Квиз (overlay + `/quiz/`) | ✅ |
| P0 | `/cabinet/` + login | ✅ |
| P1 | `/pricing/` | ✅ |
| P1 | `/` home | ✅ упрощённо |
| P2 | `/how/`, `/faq/`, `/contact/` | контент можно 1:1 позже |
| — | `/ops/` | **не переносим** (FastAPI) |
| — | `/portfolio/` | **не этот пакет** |

---

## 1. Главная `/`

**Шаблон:** `front-page.php` · секции: hero → flow → manifest → features → pricing-preview.

| Блок | Содержимое | Кто видит |
|------|------------|-----------|
| Announcement bar | «Радар онлайн · N лидов в неделю» → «Смотреть ленту →» | все |
| Header | Лого · Лента · Тарифы · Как устроено · Войти | все |
| Hero (жёлтый full viewport) | H1 **«Заказы под твой стек. Без мусора.»** · подзаголовок про ИИ/черновики · CTA **«Смотреть ленту →»** / **«Настроить ленту →»** | все |
| Live preview | 3 карточки из API (последние лиды) | все |
| Flow | 5 шагов «как работает» | все |
| Manifest / Features | ценность продукта | все |
| Pricing preview | тизер тарифа → `/pricing/` | все |
| Footer | ссылки · контакты | все |

**API:** `GET /v1/feed` (preview, anon) · `GET /v1/public/site-stats` (ticker).  
**JS:** `rawlead-scroll.js`, `rawlead-ticker.js`, `rawlead-flow.js`.

---

## 2. Лента `/lenta/`

**Шаблон:** `page-lenta.php` · **главный продуктовый экран.**

| Зона | Содержимое | Гость | Auth | Premium / Trial |
|------|------------|-------|------|-----------------|
| Header (минимальный) | Лого · Войти / @user | ✅ | ✅ | ✅ |
| Filter bar | Категории Все/Разработка/Дизайн/Маркетинг/Тексты · **Навыки ▾** (только гость desktop, locked) · **Сортировка** (locked гостю) · mobile: **«Фильтр»** sheet | ✅ | ✅ skills hidden | ✅ |
| Заголовок | «Лента заказов» · счётчик «N за 7 дней» | ✅ | ✅ | ✅ |
| Сетка карточек | title, source, budget, match bar, hot badge | ✅ delay 30m | ✅ instant | ✅ + % match |
| Match bar | % совместимости | скрыт / locked / blur по tier | quiz lock → overlay | полный % |
| Load more | **«Показать ещё»** · offset pagination | ✅ | ✅ | ✅ |
| Quiz overlay | `#rl-feed-quiz-overlay` · CTA «Настроить ленту →» | `#quiz` / promo | import → API | retake |
| FAB «?» | report bug (owner) | owner | owner | owner |

**Поведение гостя:** лента видна с **задержкой 30 мин** (`feed_delayed: true` в API).  
**Поведение auth:** JWT → без задержки; при наличии `user_tags` — персональная сортировка / match sort.

**API:** `GET /v1/feed` · `GET /v1/me/feed` (legacy, редко) · `GET /v1/me/tags` · `GET /v1/skills/catalog` · `GET/PUT /v1/me/feed-prefs` · draft endpoints на карточке.

**Deprecated (не строить в Next):** ручной Skill Tree как primary UX. На WP 1.19.20 modal **в DOM**, но **скрыт для auth**; кнопка «Навыки» в filter bar **не показывается** залогиненным (CSS O199). Канон профиля — **квиз** (`feed-cabinet-mvp.md` §0.1).

---

## 3. Карточка заказа (экран внутри ленты)

**Отдельного URL нет** (кроме deep link).

| Вход | Поведение |
|------|-----------|
| Клик по карточке | expand in-place: L1 summary, body, tools, TZ attachment |
| `/lenta/?lead={id}` | scroll + open lead |
| `/lenta/#quiz` | открыть квиз overlay |

| Элемент expanded | Гость | Auth free | Trial/Premium |
|------------------|-------|-----------|---------------|
| Полный текст / summary | частично | ✅ | ✅ |
| Ссылка на биржу | ✅ | ✅ | ✅ |
| Match % детально | lock | quiz / tier | ✅ |
| «Написать отклик» → draft | ❌ | trial/premium | ✅ |
| Warm draft on expand | — | premium | ✅ |

**API:** `GET /v1/leads/{id}` · `POST/GET /v1/me/leads/{id}/draft` · `POST .../draft/warm` · `GET /v1/me/draft/quota`.

---

## 4. Квиз

| Место | URL / UI |
|-------|----------|
| Standalone | `/quiz/` (`page-quiz.php`) |
| Overlay | `/lenta/` modal `#rl-feed-quiz-overlay` |
| Retake | кабинет · кнопка «Пройти тест заново» |

| Шаг | UX (prod 1.19.20) |
|-----|---------------------|
| Intro | H1 «Ответь на карточки — лента найдёт твои заказы» · CTA «Настроить ленту →» |
| Карточки | **«Мимо»** / **«Берем»** · блок «Суть задания» |
| Финиш | profile → `POST /v1/me/tags/import` |
| После import | event `rawlead-tags-imported` + `rawlead_user_tags_rev` (O272) |

**Auth:** import требует JWT; до логина — профиль в `localStorage`, sync после входа.

**API:** `GET /v1/quiz/start` · `POST /v1/quiz/next` · `POST /v1/me/tags/import`.

---

## 5. Кабинет `/cabinet/`

**Шаблон:** `page-cabinet.php` · **inbox откликов**, не дубликат ленты.

| Состояние | UI | Кто |
|-----------|-----|-----|
| Gate | «Войти через Telegram» · QR / deep link bot | гость |
| App (hidden до JWT) | подписка · уведомления · inbox откликов | auth |

| Секция | Содержимое (prod 2026-06-19) |
|--------|------------------------------|
| User bar | avatar · @username · logout · hint @rawlead_bot |
| Subscription | **RawLead Premium** · trial **авто при 1-м входе TG** (O219) · **без** кнопки «Активировать Trial» у нового юзера · 790 ₽/мес · pay CTA после trial |
| Notifications | push threshold 60/80/100% · toggle (при `effective_access`) |
| Inbox list | карточки · accordion черновик · Копировать · Удалить · load more |
| **Навыки** | **не показываем** (O219: CSS+JS скрывают chips и заголовок «Твои навыки») |
| Retake quiz | кнопка «Пройти тест заново» → `/lenta/#quiz` (без списка тегов) |
| Empty states | нет квиза → квиз · нет откликов → лента · post-trial без access → pricing |

**API:** auth bot flow · `GET /v1/me` · `GET /v1/me/replies` · `DELETE /v1/me/replies/{id}` · draft · subscription · notification-settings.

### Next `rawlead-next` vs prod (2026-06-19)

| | Prod WP | Next local |
|--|---------|------------|
| Anon lead | «…профиль и **черновики**» | «…**сохранять отклики**» ❌ |
| Login | QR + poll (desktop/mobile) | deep link only ❌ |
| User bar | avatar · logout | нет ❌ |
| Sub title | **RawLead Premium** | «ИИ-агент» ❌ |
| Уведомления | 60/80/100% + toggle | ✅ при trial/paid |
| Skills | **скрыты** (O219) | ❌ показывает chips |
| Trial CTA | **auto**, без кнопки у нового | ❌ «Активировать Trial» |
| Inbox | load more | ✅ |
| Dev `?dev=*` | — | ❌ **не prod** |

**Канон для Claude:** [`O280_AS_BUILT.md`](O280_AS_BUILT.md) § Prod parity.

---

## 6. Тарифы `/pricing/`

**Шаблон:** `page-pricing.php` · одна карточка Premium.

| Элемент | Содержимое |
|---------|------------|
| Hero | «Тарифы» · 3 дня trial при входе |
| Card | 790 ₽/мес · фичи · CTA checkout |
| Checkout | YooKassa → redirect / bot confirm |

**API:** `GET /v1/me/subscription` · `POST /v1/me/subscription/checkout` · `POST /v1/me/subscription/confirm`.

---

## 7. Маркетинговые inner pages

| URL | Slug | Контент | MVP |
|-----|------|---------|-----|
| `/how/` | how | 5 шагов + CTA кабинет | P2 |
| `/faq/` | faq | 3 группы accordion | P2 |
| `/contact/` | contact | Telegram @rcnn43 | P2 |

Контент канон: `wordpress/.../inc/marketing.php` → `rawlead_inner_page_html()`.

---

## 8. Глобальные UI (все product pages)

| Компонент | Страницы |
|-----------|----------|
| Header sticky | все |
| Footer | все кроме минимального feed header |
| Metrika | prod goals (`rawlead-metrika.js`) |
| Pageview beacon | `POST /v1/admin/pageview` `{path, visitor_id}` |

---

## 9. Вне scope `rawlead-next/`

| URL | Почему |
|-----|--------|
| `api.rawlead.ru/ops/` | ops пульт на FastAPI |
| `rode51.ru` | статика Rode51 (`portfolio/`) — отдельный домен, не rawlead-next |
| WP `/wp-admin/` | убирается после cutover |

---

## Checklist «страница готова»

- [ ] Header/nav соответствует типу страницы (marketing vs product minimal)
- [ ] Гость vs auth состояния без «мигания» (см. `rl-cabinet-auth-pending`)
- [ ] Mobile 390px — thumb zone ≥ 44px (`feed-cabinet-mvp` §0)
- [ ] Quiz-first — нет ручного skill picker

_Источник: WP templates + Playwright prod 2026-06-19 · theme 1.19.20 · Lead Architect_
