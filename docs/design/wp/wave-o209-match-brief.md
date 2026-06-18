# Wave O209 — Match-First Design Brief

**Статус:** ✅ **shipped** theme **1.18.84** · Lead verify+deploy 2026-06-14  
**Создан:** Lead Designer 2026-06-14  
**Источник:** [`LEAD_DESIGN_PROMPT.md`](../../team/design/LEAD_DESIGN_PROMPT.md) § O209-MATCH-EXPERIENCE  
**Канон продукта:** [`OWNER_INTENT.md`](../../team/architect/OWNER_INTENT.md) § O208-B  
**Токены:** [`DESIGN_SYSTEM.md`](../../team/design/DESIGN_SYSTEM.md) · [`REFERENCE.md`](REFERENCE.md) v5  
**Supersedes:** O199-QUIZ-UX · O208-CARD-MINIMAL (оба folded в этот бриф)

---

## Guard (не ломать UI)

| Уровень | Что трогаем |
|---------|------------|
| **P0 FULL REBUILD** | `/quiz/` — PHP template, JS, CSS, copy — всё с нуля |
| **P1 COPY + DELTA** | `/lenta/` · `/cabinet/` · `/` · `/pricing/` · `/faq/` · `/how/` — **только** строки, баннеры, tier strips; структура/grid/nav — **не трогать** |
| Запрещено | Новый hero layout · смена filter bar · cabinet inbox grid · «редизайн ради редизайна» |

---

## Лексикон match-first

| ✅ Использовать | ❌ Не использовать |
|----------------|-------------------|
| **совпадение** · **% совпадения** · **match** | Tinder · тиндер · дейтинг · «как в тиндере» |
| **профиль из квиза** · **система учится** · **лента формируется** | «добавь навыки» · ручной picker в UI |
| **заказы под тебя** · **персональная лента** · **близко по стеку** | «все фрилансеры» · аукцион · «осталось N мест» |
| **Да, близко** / **Не моё** (quiz buttons) | «Взял бы» (старое) |
| **3 дня бесплатно** · **Trial бесплатно** | «1 ₽ / 3 дня» (superseded O208-B4) |
| **5 откликов в час** | «10 в час» (superseded O208-B1) |
| **30 мин задержки** (anon + expired) | «15 мин» (superseded O208-B4) |

---

## Tier Matrix (канон O208-B4, freeze)

| Tier | Задержка | Черновики | Push | Лента | Активация |
|------|----------|-----------|------|-------|-----------|
| **Anon** | 30 мин | ❌ | ❌ | flat (хронология, все источники) | — |
| **Trial** | instant | ✅ 5/ч | ✅ | персональная (km-sort + match) | auto первый TG-login · 3д бесплатно · 1× на `user_id` |
| **Expired-trial** | 30 мин | ❌ | ❌ | flat (как anon) | — |
| **Premium** | instant | ✅ 5/ч | ✅ | персональная | 790 ₽/мес · ЮKassa |

---

## P0 — /quiz/ Full Rebuild

### Аудит текущего состояния

| Элемент | Сейчас | Проблема |
|---------|--------|----------|
| Title H1 | «Настрой ленту под себя» | нет match-месседжа |
| Кнопки | «Взял бы» / «Не моё» | «Взял бы» — разговорное, не match-first |
| Snippet | `hidden` в DOM | суть задания не видна → карточка не информативна |
| Progress | «N из M» | скучно, нет match-нарратива |
| Finale title | «Твой профиль:» | нет эмоции завершения |
| TG CTA | «Войди через Telegram — открой свою ленту» | нет упоминания Trial |
| Skip | «Посмотреть ленту без настройки →» | OK, оставить (релексировать) |

### Новый UX-flow

```
[INTRO] → [CARD × adaptive (min 5, max ~15, PM решает стоп)]
        → [FINALE: профиль + TG CTA] → /lenta/ (trial active)
                                      → /lenta/ (anon, skip)
```

**Адаптивный стоп (Product PM gate):** дизайн поддерживает плавный финал в любой момент после мин-порога. Кнопка «Достаточно → Смотреть ленту» появляется после 5 карточек (`.rl-quiz__early-cta`, hidden → visible при N ≥ 5).

---

### Экраны — мобайл-первый (390 px)

#### SCREEN 0 — Intro

```
┌──────────────────────────────────┐
│  ┌────────────────────────────┐  │
│  │  [RAWLEAD wordmark]        │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │                            │  │
│  │  Покажи, что берёшь —      │  │  ← H1  Manrope 28/700
│  │  лента настроится сама     │  │
│  │                            │  │
│  └────────────────────────────┘  │
│                                  │
│  Не надо вводить навыки.         │  ← sub  Manrope 16/400
│  Отвечай на карточки — RawLead   │
│  найдёт совпадения под тебя.     │
│                                  │
│  ┌────────────────────────────┐  │
│  │    Начать  →               │  │  ← btn--primary full-width 48dp
│  └────────────────────────────┘  │
│                                  │
│  Смотреть ленту без настройки →  │  ← rl-link-muted
└──────────────────────────────────┘
```

**CSS tokens:** фон `#FACC15` (жёлтый, как hero) · H1 `#0A0A0A` · граница `border: 3px solid #0A0A0A` на карточке (NEO-BRUTALIST)

---

#### SCREEN 1-N — Card

```
┌──────────────────────────────────┐
│  Профиль формируется…    [███░░] │  ← progress bar: старт 10%, линейный fill
│                                  │
│  ┌────────────────────────────┐  │
│  │  [source badge]  [бюджет]  │  │  ← source chip · бюджет bold
│  │                            │  │
│  │  Название заказа           │  │  ← H2  Manrope 18/700  2 строки max
│  │                            │  │
│  │  Короткое описание сути    │  │  ← excerpt  Manrope 14/400  3 строки
│  │  задания — 2–4 предложения │  │    overflow ellipsis
│  │                            │  │
│  │  [тег] [тег] [тег]         │  │  ← .rl-chips  компакт
│  └────────────────────────────┘  │
│                                  │
│  ┌──────────┐  ┌──────────────┐  │
│  │  Не моё  │  │  Да, близко  │  │  ← 48dp height  равная ширина
│  │  (ghost) │  │  (primary)   │  │    gap: 12px
│  └──────────┘  └──────────────┘  │
│                                  │
│  (N ≥ 5) Хватит → смотреть ленту │  ← .rl-quiz__early-cta  rl-link-muted
└──────────────────────────────────┘
```

**Микро-анимация карточки (button-triggered directional exit, НЕ swipe-drag):**

| Кнопка | Exit карточки | Enter новой |
|--------|---------------|-------------|
| «Да, близко» | `translateX(+120%) rotate(4deg)` + `opacity 0` · 180ms ease-out | `translateY(20px) opacity 0` → `translateY(0) opacity 1` · 150ms ease-in · delay 160ms |
| «Не моё» | `translateX(-120%) rotate(-4deg)` + `opacity 0` · 180ms ease-out | то же |

Принципы:
- Только `transform` + `opacity` (NEO-motion rule)
- Без drag-жеста, без цветного overlay, без физики пружины — **не Tinder affordance**
- Новая карточка **всегда** поднимается снизу (не приходит со стороны)
- Кнопки блокируются (`pointer-events: none`) на время exit-анимации (180ms) — защита от двойного клика
- JS: `card.classList.add('is-exit-right')` / `'is-exit-left'` → по окончании анимации — удалить, показать следующую

```css
.rl-quiz-card.is-exit-right {
  transform: translateX(120%) rotate(4deg);
  opacity: 0;
  transition: transform 180ms ease-out, opacity 180ms ease-out;
}
.rl-quiz-card.is-exit-left {
  transform: translateX(-120%) rotate(-4deg);
  opacity: 0;
  transition: transform 180ms ease-out, opacity 180ms ease-out;
}
.rl-quiz-card.is-enter {
  transform: translateY(20px);
  opacity: 0;
  transition: transform 150ms ease-in, opacity 150ms ease-in;
}
.rl-quiz-card.is-enter.is-visible {
  transform: translateY(0);
  opacity: 1;
}
```

**Прогресс-бар:** `width` начинает с `10%` (первая карточка), затем линейно по `(current_idx / total_expected) * 100%`. После early-stop — плавно до 100%. Без indeterminate-режима.

---

#### SCREEN N+1 — Finale (Profile)

```
┌──────────────────────────────────┐
│                                  │
│  ✓ Готово. Вот что мы узнали:    │  ← H2  Manrope 22/700
│                                  │
│  ┌────────────────────────────┐  │
│  │  💻 Разработка   ████████  │  │  ← category bar (% из сессии)
│  │  🎨 Дизайн       ████      │  │    Manrope 14/600
│  │  📣 Маркетинг    ██        │  │    фон bar `#FACC15`
│  │  ✍️ Тексты       ░         │  │
│  └────────────────────────────┘  │
│                                  │
│  Лента уже настраивается.        │  ← Manrope 15/400
│  Войди — сохраним профиль и      │
│  откроем персональную ленту.     │
│                                  │
│  ┌────────────────────────────┐  │
│  │  [TG widget / войти]       │  │  ← TG Login Widget
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │  3 дня Premium бесплатно   │  │  ← trial promo chip
│  │  — автоматически при входе │  │    фон `#FACC15`, border 2px
│  └────────────────────────────┘  │
│                                  │
│  Смотреть без входа →            │  ← rl-link-muted → /lenta/ anon
└──────────────────────────────────┘
```

**Trial promo chip** (`.rl-quiz__trial-promo`): только на finale, только если `plan = anon` (JS проверяет localStorage токен). Если уже авторизован — скрыть чип, показать «Открыть ленту →».

---

#### SCREEN — Error / Loading

```
Loading: spinner (16px) + «Загружаем карточки…» — центр экрана, без hero-bg

Error: «Не удалось загрузить — попробуй ещё раз» + [Попробовать] btn--ghost
       + «Смотреть ленту без настройки →»
```

---

#### Desktop (≥ 768px)

Карточка центрируется: `max-width: 560px; margin: 0 auto`. Кнопки — `min-width: 160px`. Intro — полноэкранный `min-height: 100svh`, H1 `40px`. Finale — две колонки не нужны, вертикальный блок достаточен.

---

### Copy Strings для PHP (старое → новое)

| ID строки / контекст | Старая строка | Новая строка |
|----------------------|---------------|--------------|
| `quiz.php` H1 | `Настрой ленту под себя` | `Покажи, что берёшь — лента настроится сама` |
| intro sub (новый) | — | `Не надо вводить навыки. Отвечай на карточки — RawLead найдёт совпадения под тебя.` |
| intro CTA (новый) | — | `Начать  →` |
| quiz loading | `Загружаем карточки…` | `Загружаем карточки…` *(без изменений)* |
| btn like | `Взял бы` | `Да, близко` |
| btn nope | `Не моё` | `Не моё` *(без изменений)* |
| progress (JS строка) | `N из M` (формат) | `Профиль формируется…` (без счётчика) |
| early-cta (новый) | — | `Хватит → смотреть ленту` |
| result title | `Твой профиль:` | `Готово. Вот что мы узнали:` |
| result sub (новый) | — | `Лента уже настраивается. Войди — сохраним профиль и откроем персональную ленту.` |
| TG CTA lead | `Войди через Telegram — открой свою ленту` | `Войди через Telegram — 3 дня Premium бесплатно` |
| trial promo chip (новый) | — | `3 дня Premium бесплатно — автоматически при входе` |
| retry btn | `Пройти снова` | `Начать заново` |
| skip lenta (play area) | — | `Смотреть без настройки →` |
| skip lenta (result) | `Посмотреть ленту без настройки →` | `Смотреть без входа →` |

---

### CSS Classes (новая схема для Coder)

| Класс | Применение |
|-------|-----------|
| `.rl-quiz` | корневой wrapper (без изменений — JS-хук) |
| `.rl-quiz__intro` | **новый** экран-intro (скрыт после старта) |
| `.rl-quiz__play` | play area (без изменений) |
| `.rl-quiz__result` | финал (без изменений) |
| `.rl-quiz__early-cta` | **новый** «хватит → смотреть» (hidden до N≥5) |
| `.rl-quiz__trial-promo` | **новый** чип trial на финале |
| `.rl-quiz-card__excerpt` | **новый** (был `__snippet hidden`) — показывать открыто |
| `.rl-quiz__progress-fill` | без изменений |
| `.rl-quiz__category-bars` | **новый** контейнер category bars на финале |
| `.rl-quiz__category-bar` | **новый** строка category (emoji + label + bar) |

**Не переименовывать:** `.rl-quiz`, `.rl-quiz-card` (JS-хуки на `id=rl-quiz-*`).

---

## P1 — Copy + Delta по URL

> Формат: Файл | Класс/ID | Старая строка → Новая строка

---

### /lenta/ — `page-lenta.php` + `rawlead-feed.js`

#### Lenta head

| Класс/ID | Старое | Новое |
|----------|--------|-------|
| `.rl-feed-head__title` | `Лента заказов` | `Лента заказов` *(без изм.)* |
| — | — | `% совпадения` на карточке — **усилить визуально** (см. REFERENCE.md § Match label режим A) |

#### Anon strip (`.rl-feed-anon-strip` — если существует или новый)

| Элемент | Старое | Новое |
|---------|--------|-------|
| Текст задержки | `15 мин задержки` | `Заказы с задержкой 30 мин` |
| CTA hook | `Войди →` | `Войди через TG — 3 дня Premium бесплатно` |
| Link | → `/cabinet/` | → `/quiz/` (quiz-first) |

#### Quiz promo block (`#rl-feed-quiz-promo`) — **upgrade от text-link к banner-card**

Текущее поведение: `ensureAnonQuizPromo()` вставляет text-node. Новое:

```
┌──────────────────────────────────┐
│  ✦ Персональная лента за 2 мин  │  ← H3  Manrope 15/700
│  Ответь на карточки — ИИ         │
│  подберёт заказы под твой стек   │  ← sub  14/400
│  [  Настроить ленту  →  ]        │  ← btn--primary compact → /quiz/
└──────────────────────────────────┘
```

**CSS:** `.rl-feed-quiz-promo` · border `3px solid #0A0A0A` · bg `#FACC15` · box-shadow `4px 4px 0 #0A0A0A` · NEO-BRUTALIST. Вставляется после 3-й карточки в anon-режиме (как сейчас).

#### Expired-trial banner (`#rl-feed-expired-banner`) — **новый обязательный элемент**

Отображается: `plan = expired_trial` (JS проверяет JWT/localStorage). Dismissible — **нет** (owner: не тихая деградация).

```
┌──────────────────────────────────┐
│  ⚠ Пробный период закончился    │  ← Manrope 14/700  icon ⚠
│  Лента без фильтров и с          │
│  задержкой 30 мин.               │  ← 14/400
│  [  Вернуть персонализацию  →  ] │  ← btn--primary → /pricing/
│  Premium · 790 ₽/мес             │  ← 12/400 muted
└──────────────────────────────────┘
```

**CSS:** `.rl-feed-expired-banner` · border `3px solid #0A0A0A` · bg `#FEF9C3` (светло-жёлтый, не #FACC15) · mb `16px` · top ленты перед первой карточкой.

#### Feed card (`.rl-lead-card`) — card minimal delta (O208-B3)

| Убрать | Класс/JS переменная | Действие |
|--------|---------------------|----------|
| Просмотры (eye icon + «N смотрят») | `.rl-feed-card__views` · `viewsHeadHtml` (JS) | `display: none` → Coder убирает из PHP + JS |
| Счётчик откликов/слотов («осталось N из K») | `reply_slots_remaining` в meta · `syntheticDisplayReplies` | убрать из PHP render + JS |
| «N фрилансеров» / конкуренция | любые строки с числом конкурентов | убрать |

| Оставить | Примечание |
|----------|-----------|
| % совпадения (`.rl-match-bar`) | **усилить**: font-weight 700 · color `#0A0A0A` · label «Совпадение» |
| Источник · title · excerpt · бюджет · время | без изменений |
| CTA отклика | без изменений |
| Glow при генерации (O203) | оставить |

#### Flat feed state (anon + expired)

Filter bar: скрыт или disabled (`.rl-filter-bar` → `hidden` / `aria-disabled`). Empty state:
- Старое: «Добавь навыки → умная лента» (если есть) → **убрать**
- Новое: `«Лента показывает последние заказы · Персонализация — после входа»`

---

### /cabinet/ — `page-cabinet.php`

| Класс/ID | Старое | Новое |
|----------|--------|-------|
| `.rl-cabinet-login__lead` | `Настроишь навыки — лента покажет заказы под твой стек. Черновик отклика — за один клик.` | `Лента уже подбирает совпадения. Войди — посмотришь свой профиль и черновики.` |
| `.rl-cabinet-sub__price` | `790 ₽/мес · trial 1 ₽ / 3 дня` | `790 ₽/мес · первые 3 дня бесплатно` |
| `.rl-cabinet-sub__trial` btn label | `Попробовать Premium →` (если есть) | `Активировать Trial бесплатно →` |
| `.rl-cabinet-head__lead` | `Отклики с ленты — здесь.` | `Отклики с ленты — здесь.` *(без изм.)* |
| empty state | `Добавь навыки — покажем заказы под твой стек.` | `Лента автоматически подбирает заказы под профиль из квиза. [Пройти квиз →]` |

**Убрать из UI кабинета (ручной skills picker):**
- Любой `<input>` / `<textarea>` для ввода навыков вручную
- Кнопка «Сохранить навыки →» (`#rl-feed-skills-apply`)
- Раздел «Навыки» как отдельный textarea — **скрыть** (CSS `display: none` или Coder убирает PHP)

**Trial badge (новый):** когда `plan = trial` — в хедере кабинета показывать:
```
┌─────────────────────────────┐
│  ✓ Trial Premium · N дн.   │  ← `.rl-trial-badge`  bg #FACC15  Manrope 12/700
└─────────────────────────────┘
```

**Expired banner в кабинете:** аналогично ленте — `.rl-cabinet-expired-banner`, то же copy что в lenta.

---

### / (home) — `hero.php` · `marketing.php` · `audience.php`

#### Hero copy

| ID | Старое | Новое |
|----|--------|-------|
| `#rl-hero-title` H1 | `Заказы под твой стек. Без мусора.` | **Оставить** (сильный, match-compatible) |
| hero sub | `ИИ находит заказы под твой стек и пишет черновик отклика — свой у каждого. Не шаблон с полки, не копипаст. Отправляешь ты — своими словами.` | Добавить в конец: `· % совпадения на каждой карточке.` |
| primary CTA | (текущий текст/href) | Href → `/quiz/` · label `Настроить ленту →` |
| secondary CTA | (текущий) | `Смотреть заказы →` → `/lenta/` |

#### Announcement bar

| Строка | Старое | Новое |
|--------|--------|-------|
| `.rl-announcement__text-full` | `Агрегатор фриланс-бирж RawLead — все заказы на удалёнку в одном месте ·` | `RawLead — заказы под твой стек с % совпадения · FL · Kwork · TG ·` |

#### Audience block (`audience.php`)

| Элемент | Старое | Новое |
|---------|--------|-------|
| dev text | `…заказы точно по твоим навыкам, без шума.` | `…% совпадения на каждой карточке, без шума.` |
| copy text | `…только заказы под твой профиль.` | без изменений |

#### Live preview (`live-preview.php`)

| Строка | Старое | Новое |
|--------|--------|-------|
| label | `Последние заказы из ленты` | `Последние заказы · с % совпадения после квиза` |

---

### /pricing/ — `pricing-card.php` · `marketing.php`

| Элемент | Старое | Новое |
|---------|--------|-------|
| trial price line | `trial 1 ₽ / 3 дня` | `первые 3 дня — бесплатно` |
| trial footer note | `Оплата картой или СБП через ЮKassa. Trial — 1 ₽ / 3 дня, далее 790 ₽/мес.` | `Первые 3 дня — бесплатно (1× на аккаунт TG). Далее 790 ₽/мес, отмена в любой момент. Оплата картой или СБП через ЮKassa.` |
| feature «без задержки» | `Лента без задержки и push — заказы появляются сразу при match` | `Персональная лента с % совпадения · push при матче · без задержки` |
| feature (новый) | — | `5 откликов в час · черновик под твой стек` |
| `marketing.php` free tier | (если есть «15 мин задержки») | `30 мин задержки · лента без персонализации` |
| `marketing.php` main copy | `790 ₽ / мес … Premium … от 790 ₽/мес` | Оставить цену · заменить trial copy |

**Tier table (новый блок на pricing):**

```
┌──────────────────────────────────────────────────────────────┐
│          Anon          │       Trial (3 дня)  │   Premium    │
│  30 мин · flat лента   │  instant · персон.   │  instant ·   │
│  без черновиков        │  5/ч · push          │  5/ч · push  │
│                        │  бесплатно           │  790 ₽/мес   │
└──────────────────────────────────────────────────────────────┘
```

CSS-компонент: `.rl-tier-table` — три колонки, NEO-BRUTALIST border, trial-колонка bg `#FACC15`.

---

### /faq/ — `marketing.php` (FAQ блоки)

| Вопрос/ответ | Старое | Новое |
|--------------|--------|-------|
| Задержка (анон) | «15 мин» | **«30 мин»** |
| Trial копирайт | «1 ₽ / 3 дня Premium один раз после входа» | **«бесплатно · 3 дня Premium автоматически при первом входе через TG»** |
| Hourly cap | «умный лимит 10 откликов в час» | **«5 откликов в час (включая Premium)»** |
| «Зачем Premium, если лента и так…?» | «После входа через Telegram — лента сразу. Это бесплатно. Premium даёт…» | **Переписать:** «После первого входа — 3 дня Trial бесплатно: персональная лента, черновики, push. После Trial — лента с задержкой 30 мин и без персонализации. Premium возвращает всё это за 790 ₽/мес.» |
| «Добавь свои навыки» | «Добавь навыки — ИИ найдёт подходящие заказы» | **«Пройди квиз — ИИ узнает твой профиль и найдёт совпадения»** |
| Откликов в час | «10 откликов в час» | **«5 откликов в час»** |

**Новый FAQ-вопрос (добавить):**
> **Что такое % совпадения?**  
> «Это насколько заказ подходит под твой профиль из квиза. 90%+ — отлично совпадает. Алгоритм учитывает категорию, навыки и тип задачи. Не рейтинг среди других фрилансеров — только твой личный match.»

---

### /how/ — (если есть страница)

| Строка | Изменение |
|--------|-----------|
| «15 мин» упоминания | → «30 мин» |
| «добавь навыки» → ручной picker | → «пройди квиз» |
| Trial «1 ₽» | → «бесплатно» |

---

## Paywall States — Wireframes

### Expired-trial banner (lenta + cabinet)

```
┌──────────────────────────────────────────────────────┐
│  ⚠  Пробный период закончился                       │
│     Лента без фильтров и с задержкой 30 мин.         │
│     [ Вернуть персонализацию → ]   Premium · 790 ₽  │
└──────────────────────────────────────────────────────┘
```
CSS: `.rl-expired-banner` · bg `#FEF9C3` · border `3px solid #0A0A0A` · box-shadow `4px 4px 0 #0A0A0A` · padding `16px` · dismissible = **false**

### Trial badge (cabinet header)

```
[ ✓ Trial Premium · 2 дн. ]
```
CSS: `.rl-trial-badge` · display `inline-flex` · bg `#FACC15` · border `2px solid #0A0A0A` · Manrope 12/700 · padding `4px 10px`

### Anon strip (lenta top)

```
┌──────────────────────────────────────────────────────┐
│  Заказы с задержкой 30 мин. Войди через TG —         │
│  3 дня Premium бесплатно  [ Войти ]                  │
└──────────────────────────────────────────────────────┘
```
CSS: `.rl-feed-anon-strip` · bg `#0A0A0A` · color `#FACC15` · Manrope 13/600

### Premium CTA disabled state (hourly 5/ч исчерпан)

Кнопка отклика: `disabled` + tooltip/title = `«Лимит 5 откликов/час исчерпан · обновится через N мин»` · opacity `0.5` · cursor `not-allowed`

---

## Handoff Checklist

### Lead Designer → @designer

- [x] Ревью wireframes quiz (Screens 0, 1-N, finale) — **выполнено @designer 2026-06-14**
- [x] Уточнить mobile-кнопки: «Да, близко» — иконка ✓ нужна или текст достаточен? → **текст достаточен**
- [x] Category bars finale — **рендерить все 4, скрывать нулевые через `data-pct=0` CSS**
- [x] Trial promo chip: animate? → **статик** (bg #FACC15 + NEO-shadow достаточно)

### Designer decisions (финал, принято владельцем)

| Элемент | Решение |
|---------|---------|
| Кнопка «Начать →» | `48dp` (было 52px) — унифицировано со стандартом |
| Кнопка «Да, близко» | Только текст, без иконки ✓ |
| Progress bar | Старт `10%`, linear fill по `current_idx / total_expected` |
| Trial promo chip | Статик; `bg #FACC15`, `border 2px solid #0A0A0A`, `shadow 4px 4px 0 #0A0A0A` |
| Category bars | Все 4 рендерятся; `[data-pct="0"]` → `display:none` |
| Анимация карточки | **Directional exit:** «Да» → вправо `rotate(4deg)`, «Нет» → влево `rotate(-4deg)`; новая карточка — снизу. НЕ swipe-drag. CSS: `.is-exit-right` / `.is-exit-left` / `.is-enter` |

### @designer → @lead-architect → @coder

**Файлы Coder (P0 /quiz/):**
```
wordpress/rawlead-kadence-child/page-quiz.php
wordpress/rawlead-kadence-child/template-parts/rawlead/quiz.php
wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js
wordpress/rawlead-kadence-child/assets/css/rawlead.css  § quiz
```

**Файлы Coder (P1 deltas):**
```
wordpress/rawlead-kadence-child/inc/marketing.php       ← FAQ + pricing copy
wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-card.php
wordpress/rawlead-kadence-child/template-parts/rawlead/hero.php
wordpress/rawlead-kadence-child/template-parts/rawlead/live-preview.php
wordpress/rawlead-kadence-child/template-parts/rawlead/audience.php
wordpress/rawlead-kadence-child/page-lenta.php          ← anon strip, expired banner
wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js   ← quiz promo upgrade, expired banner, rm views
wordpress/rawlead-kadence-child/page-cabinet.php        ← trial badge, expired banner, rm skills input
wordpress/rawlead-kadence-child/assets/css/rawlead.css  § tier strips, expired, quiz-promo
```

**Не трогать Coder:** `src/` · `scripts/` · API · `REFERENCE.md` baseline структура

---

_Lead Designer · NEO-BRUTALIST · 2026-06-14 · O209 match-first_
