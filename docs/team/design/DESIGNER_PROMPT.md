# Designer — **→ Now:** § **O215-WP-LIVE-POLISH** — local BrowserSync iteration with owner

**O96-D закрыт у Lead Designer** → **`@coder` § O96-code** · см. [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § O96-D.

**Канон WP:** [`REFERENCE.md`](../../design/wp/REFERENCE.md) v5 · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md)

---

## § O215-WP-LIVE-POLISH — Design polish before Perf (owner 2026-06-14)

**Owner decision:** O209 shipped but **visual polish not done** — do **not** start Perf wave yet. Iterate **locally** via BrowserSync with owner before any deploy.

**Ticket context:** `OWNER_INTENT` § O127 (filters/cards unify) · O209 P1 deltas shipped in **1.18.84** — owner still not fully satisfied.

### Workflow (mandatory)

1. **Owner one-time setup** (see `TASKS.md` § BrowserSync · skill `rawlead-wp-live-dev`)
2. **Designer session:** owner opens `http://localhost:3000/lenta/` (and home/quiz/pricing as needed) · owner points what feels wrong · Designer edits **repo** `wordpress/rawlead-kadence-child/` (`rawlead.css`, templates, partial JS)
3. **Live inject:** BrowserSync reflects CSS without full F5 cycle
4. **When block approved:** bump `RAWLEAD_CHILD_VERSION` in theme · handoff `@coder` or owner runs `deploy-wp-theme-vps.py`

**Do not:** Playwright prod audit for every 2px tweak · deploy after each micro-change · full redesign (O209 guard still applies)

### Priority pages (owner-led — confirm in session)

| P | URL (via localhost:3000) | Typical pain (from owner history) |
|---|---------------------------|-----------------------------------|
| **1** | `/lenta/` | filter bar tier chrome · card readability · match % · spacing |
| **2** | `/` home | hero · tier preview · match copy density |
| **3** | `/quiz/` | flow polish post-O209 rebuild |
| **4** | `/pricing/` · `/cabinet/` | tier chips · trial/expired banners |

### Deliverables

- **Session notes** in reply to owner: what changed + before/after (screenshot paths ok)
- **Files touched** list for Lead verify before deploy
- If scope > 1 day → `@lead-designer` short delta spec in `feed-cabinet-mvp.md` § supplement (owner approval)

### DoD (wave gate)

- Owner says «дизайн ок для prod» on **lenta + home + quiz** minimum
- Then → `@lead-designer` Perf scope · **not before**

**Deploy:** only after owner OK · `@coder` or owner · `deploy-wp-theme-vps.py`

---

## § O98-w — Skill Tree / фильтр навыков: UX с нуля (**queued · после O96-D ф1**)

**Запрос владельца 2026-06-02:** окно выбора навыков (⚙ лента + modal ЛК) **«жутко неудобно»** — решения пока **нет**, нужен **Design-исследование** (2–3 варианта), не CSS-hotfix.

**Контекст prod 1.16.1:** O94-w4 tray + O95-fix (dedupe, scroll) — **технически OK**, владелец **не принимает** UX.

### Симптомы (зафиксировать «было» + скрины prod)

| # | Симптом |
|---|---------|
| 1 | Много выбранных L1 → tray «Уточнение» **раздувается**, теряется обзор |
| 2 | 4 ниши × subheads × 12 лимит — **когнитивная перегрузка** |
| 3 | Непонятно «достаточно L1» vs «надо L3» · save vs отмена |
| 4 | Лента ⚙ и ЛК — один sheet, но **паттерн** всё ещё «форму на 12 полей» |

### Задача Design (solution unknown — **исследование**)

| # | Deliverable |
|---|-------------|
| d1 | **2–3 концепта** (wireframe desktop + mobile 390px): альтернативы tray / wizard / collapsed-by-default / «сначала ниши, потом детали» / … |
| d2 | Сравнительная таблица: скорость выбора · понятность tier · scroll · 12 лимит |
| d3 | **Рекомендация Lead+владелец** — один вариант или гибрид |
| d4 | Спека § **4.8** в `feed-cabinet-mvp.md` → handoff `@coder` |

**Не в scope:** anon bar (O95) · API tags · новые теги каталога · O97 badge сложности (отдельно § O97-w2).

**Порядок:** **после** § **O97-w2** (badge) · **до** E2E / vault · Coder **не раньше** approve макета.

**Gate:** владелец не знает «как правильно» — Design **обязан** предложить, не уточнять у владельца готовый макет.

---

## § O94-w4 — Skill Tree: L3 без потери взгляда (P0 · 2026-06-02 · ✅ сдано)

**Запрос владельца:** окно навыков неудобно — клик по L1 → «всё съезжает», под ним **такие же** чипы → непонятно tier 2 vs tier 3.

**Scope:** L3 tray + визуальная иерархия · **единый Skill Tree sheet** — `/cabinet/` modal **и** `/lenta/` «Изменить навыки» (logged-in) · mobile 390px.

**Anon `/lenta/`:** sheet **нет** (§ **O95**) — Design рисует entry logged-in + cabinet.

**Не в scope:** O95 anon shell, API, новые теги.

### Проблемы (зафиксировать в wireframe «было»)

| # | Симптом |
|---|---------|
| 1 | L3 = те же `.rl-skill-chip` (border, fill) — не читается «подуровень» |
| 2 | Рост колонки L1 сдвигает соседей при wrap / длинных subhead-рядах |
| 3 | Нет copy «это уточнение, необязательно» |
| 4 | Несколько L1 с L3 — хаос при 2+ выбранных |

### Deliverables Design

| # | Артефакт | Статус |
|---|----------|--------|
| d1 | **2–3 варианта** L3 UX (wireframe desktop + mobile) | ✅ 2026-06-02 |
| d2 | **Выбор владельца** — **A+B** | ✅ 2026-06-02 |
| d3 | Спека [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) § **4.7** | ✅ 2026-06-02 |
| d4 | Handoff `@coder` § **O94-w4-code** ниже | ✅ 2026-06-02 |

### d1 — Wireframes (2026-06-02)

#### «До» (O94-w3) — фиксируем проблему

```
ПО ЗАДАЧЕ:   [✓ Telegram-боты ▾] [WordPress] [Парсинг] [API] [ИИ]
               └ [aiogram] [Telethon]  ← те же рамки/fill ← #1; L1-строка выросла ← #2
ПО ТЕХНОЛОГИИ: [✓ Python ▾] [✓ JavaScript ▾]
               └ [Django] [FastAPI]    └ [React]  ← хаос 2 раскрытых ← #4
```

#### Вариант A — Sub-tray (L1-строка FIXED)

```
ПО ЗАДАЧЕ:   [✓ Telegram-боты ▾] [WordPress] [Парсинг] [API] [ИИ]  ← не растёт
             ┌─ Уточнение (необязательно) ──────────────────────┐
             │  [aiogram] [Telethon]                            │  ← L3 в tray
             └──────────────────────────────────────────────────┘
ПО ТЕХНОЛОГИИ: [✓ Python ▾] [JavaScript]
             ┌─ Уточнение (необязательно) ──────────────────────┐
             │  [Django] [FastAPI]                              │
             └──────────────────────────────────────────────────┘
```
Mobile: tray full-width внутри `.rl-niche-root__body` · grid shift = 0

#### Вариант B — Ghost L3 + label (indent, другой стиль)

```
ПО ЗАДАЧЕ:   [✓ Telegram-боты ▾] [WordPress] [Парсинг] [API] [ИИ]
  Уточнение:  [○ aiogram] [○ Telethon]   ← ghost: bg #F0F0EC, 1px #D4D4D4, 12px/400
ПО ТЕХНОЛОГИИ: [✓ Python ▾] [✓ JavaScript ▾]
  Уточнение:  [○ Django] [● FastAPI] [○ React]  ← ● selected: bg #FEF9C3, 12px/600
```
Grid shift остаётся (−) · tier читается (✓) · mobile indent 12px

#### Вариант A+B — рекомендован Lead ⭐

```
ПО ЗАДАЧЕ:   [✓ Telegram-боты ▾] [WordPress] [Парсинг] [API] [ИИ]  ← FIXED
             ┌─ Уточнение (необязательно) ──────────────────────┐
             │  [○ aiogram] [○ Telethon]  ← ghost в tray        │
             └──────────────────────────────────────────────────┘
ПО ТЕХНОЛОГИИ: [✓ Python ▾] [JavaScript]
             ┌─ Уточнение (необязательно) ──────────────────────┐
             │  [○ Django] [● FastAPI]    ← selected L3         │
             └──────────────────────────────────────────────────┘
```
Mobile: tray full-width · cabinet = lenta (один компонент) · AC-D1–D4 ✓

---

### Варианты — сводка

| ID | Идея | Решает #1 | Решает #2 | Решает #3 | Решает #4 |
|----|------|:---------:|:---------:|:---------:|:---------:|
| **A** | Sub-tray full-width | — | ✓ | ✓ (label) | ✓ (C-паттерн) |
| **B** | Ghost chips + label | ✓ | — | ✓ | — |
| **A+B** ⭐ | Tray + ghost | ✓ | ✓ | ✓ | ✓ |

**d2 ✅ Владелец 2026-06-02: A+B** — tray + ghost chips

### Acceptance Design (AC-D-w4)

- AC-D1: wireframe «до/после» с JS+Python на одной строке — ✅ выше
- AC-D2: явное отличие L1 vs L3 (не только font-size −2px) — ✅ ghost vs filled
- AC-D3: copy optional refinement (1 строка) — ✅ «Уточнение (необязательно)»
- AC-D4: **единый sheet** cabinet + lenta «Изменить навыки» (anon lenta — без sheet)

**Gate:** §4.7 ✅ → **O94-w4-code** ниже · shell anon/logged-in → **O95**

---

## § O94-w4-code → @coder (P0 · Design ✅ · 2026-06-02)

**Основание:** Design A+B принят · спека [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) § **4.7**

### Файлы

```
wordpress/rawlead-kadence-child/assets/css/rawlead.css        ← .rl-l3-tray + .rl-skill-chip--l3
wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js  ← tray logic cabinet
wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js     ← tray logic lenta
```

### Что сделать

| # | Задача |
|---|--------|
| 1 | **CSS** `.rl-l3-tray` / `.rl-l3-tray__label` / `.rl-l3-tray__group` — по §4.7 токенам |
| 2 | **CSS** `.rl-skill-chip--l3` обновить: 28px / 12px / ghost `#F0F0EC` / checked `#FEF9C3` |
| 3 | **JS** L1 `.is-selected` → tray `is-visible` под subhead-блоком; L1 deselected → hidden (L3 state persist) |
| 4 | **JS** 2+ L1 в subhead → один tray, chips с мини-лейблами («Python:» / «JavaScript:») |
| 5 | Один переиспользуемый tray-модуль: cabinet + lenta |

### Acceptance (из §4.7)

- AC-O94-1: L1-строка не растёт ← **главный фикс**
- AC-O94-2: L3 ghost 28px vs L1 filled 36px
- AC-O94-3: copy «Уточнение (необязательно)»
- AC-O94-4: один компонент cabinet = lenta
- AC-O94-5: 2 L1 → один tray, мини-лейблы
- AC-O94-6: `tags[]` payload без изменений
- AC-O94-7: mobile full-width tray

---

## § O93-w1 — 3-level Skill Tree (архив handoff)

**Owner: PM вариант B** — «По задаче» + «По технологии»; **Python и JavaScript** Tier A (не option «Гибрид»).

### Продуктовая модель (wireframe)

**Разработка:**

| Subhead | Chips | Поведение |
|---------|-------|-----------|
| **По задаче** | Telegram-боты, WordPress, Парсинг, API, ИИ | L1; клик = match достаточен |
| **По технологии** | **Python**, **JavaScript** | для дженералистов |
| **L3 под chip** | aiogram, Telethon / Django, FastAPI / React | collapsed; необязательно |

**Anti-pattern:** одна полка · aiogram рядом с «Telegram-боты» · только Python без JavaScript (это «Гибрид», не B).

### Пример dev

```
Разработка ▾
  По задаче
  [✓ Telegram-боты] [ WordPress ] [ Парсинг ] [ API ] [ ИИ ]
  └─ Telegram-боты ▾ → [ aiogram ] [ Telethon ]

  По технологии
  [✓ Python ] [ JavaScript ]
  └─ Python ▾ → [ Django ] [ FastAPI ]
  └─ JavaScript ▾ → [ React ]
```

### Surfaces — один паттерн

| Surface | Контейнер | Отличие |
|---------|-----------|---------|
| `/cabinet/` | sheet (как O92 interim) | save → профиль |
| `/lenta/` | panel «Навыки ▾» / mobile bottom sheet | «Применить» → сортировка ленты |

Reuse: NEO-BRUTALIST · `.rl-skill-tree-*` где можно · max 12 · hint 6–8 · telemetry events.

### Состояния (AC для design)

| # | Состояние |
|---|-----------|
| D1 | L1 only selected — valid save, microcopy «Направления выбраны — этого достаточно» |
| D2 | L1 chip selected + tap ▾ → L3 row visible под chip; L3 unchecked OK |
| D3 | L1 deselected — L3 row скрыт (selections persist в payload при повторном раскрытии) |
| D4 | max 12 (суммарно L1+L3) — block new chips |
| D5 | Loading / error / success — как O92 §4.5 |
| D6 | Mobile 95vh sheet, sticky «Сохранить» / «Применить» |

### Wireframes — 4 фрейма

#### Frame 1 — /cabinet/ desktop (≥768px)

```
┌─ Навыки ──────────────────────── [Выбрано 2 / 12] [✕] ─┐
│  max-width: 480px · border: 2px solid #0A0A0A            │
│  shadow: 6px 6px 0 #0A0A0A                               │
│                                                          │
│  [▸ Дизайн]                      ← niche collapsed       │
│  [▸ Маркетинг]                   ← niche collapsed       │
│  [▸ Тексты]                      ← niche collapsed       │
│  [▾ Разработка]                  ← niche expanded        │
│  ┌──────────────────────────────────────────────────┐    │
│  │  ПО ЗАДАЧЕ                                       │    │  ← subhead
│  │  [✓ Telegram-боты ▾] [WordPress] [Парсинг]       │    │  ← L1 chips
│  │  [API] [ИИ]                                      │    │
│  │    └ [aiogram] [Telethon]  ← L3, indent 16px     │    │  ← под раскрытым chip
│  │                                                  │    │
│  │  ПО ТЕХНОЛОГИИ                                   │    │  ← subhead
│  │  [✓ Python ▾] [JavaScript]                       │    │  ← оба Tier A
│  │    └ [Django] [FastAPI]    ← L3, indent 16px     │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ⚡ Направления выбраны — этого достаточно               │  ← D1 microcopy, bg #FEF9C3
│                                                          │
│  [Сохранить навыки →]                  Сбросить всё      │
└──────────────────────────────────────────────────────────┘
```

#### Frame 2 — /cabinet/ mobile (<768px)

```
      ──────── ← handle 40×4px, bg #D4D4D4
┌────────────────────────────────────────┐
│  Навыки                     [✕]        │
│  Выбрано 2 / 12                        │
├────────────────────────────────────────┤ scroll
│  [▸ Дизайн]                            │
│  [▸ Маркетинг]                         │
│  [▸ Тексты]                            │
│  [▾ Разработка]                        │
│  ┌──────────────────────────────────┐  │
│  │  ПО ЗАДАЧЕ                       │  │  ← subhead
│  │  [✓ Telegram-боты ▾] [WordPress] │  │  ← L1, wrap
│  │  [Парсинг] [API] [ИИ]            │  │
│  │    └ [aiogram] [Telethon]        │  │  ← L3, indent 12px
│  │                                  │  │
│  │  ПО ТЕХНОЛОГИИ                   │  │  ← subhead
│  │  [✓ Python ▾] [JavaScript]       │  │  ← оба Tier A
│  │    └ [Django] [FastAPI]          │  │  ← L3, indent 12px
│  └──────────────────────────────────┘  │
│  ⚡ Направления выбраны — достаточно   │  ← D1, bg #FEF9C3 12px
├────────────────────────────────────────┤ sticky
│  [Сохранить навыки →]   full-width     │  52px
└────────────────────────────────────────┘
overlay rgba(0,0,0,0.5) → tap закрывает
```

#### Frame 3 — /lenta/ desktop (≥768px)

Тот же Skill Tree — в panel «Навыки ▾», кнопка «Применить» вместо «Сохранить»:

```
┌──────────────────────────────────────────────────────────┐
│ [Все] [Разработка] [Дизайн] [Маркетинг] [Тексты]         │ ← filter bar
│                                 [Навыки ▾] [Сорт ▾]      │
└──────────────────────────────────────────────────────────┘
                 ↓ клик [Навыки ▾]
┌─ Навыки ──────────────────── [Выбрано 2] [✕] ──┐
│  max-width: 420px · NEO border/shadow            │
│  [▸ Дизайн]                                     │
│  [▸ Маркетинг]                                  │
│  [▸ Тексты]                                     │
│  [▾ Разработка]                                 │
│  ┌────────────────────────────────────────────┐  │
│  │  ПО ЗАДАЧЕ                                 │  │
│  │  [✓ Telegram-боты ▾] [WordPress]           │  │
│  │  [Парсинг] [API] [ИИ]                      │  │
│  │    └ [aiogram] [Telethon]   ← L3           │  │
│  │                                            │  │
│  │  ПО ТЕХНОЛОГИИ                             │  │
│  │  [✓ Python ▾] [JavaScript]                 │  │
│  │    └ [Django] [FastAPI]     ← L3           │  │
│  └────────────────────────────────────────────┘  │
│  [Применить →]            Сбросить               │  ← «Применить» (сортировка)
└──────────────────────────────────────────────────┘
```

#### Frame 4 — /lenta/ mobile (<768px)

Unified [Фильтры ▾] sheet (95vh) — Skill Tree внутри блока НАВЫКИ:

```
      ────────  ← handle
┌────────────────────────────────────────┐
│  Фильтры                      [✕]      │
├────────────────────────────────────────┤
│  СПЕЦИАЛИЗАЦИЯ                         │
│  [Все ✓] [Разработка] [Дизайн]         │
│  [Маркетинг] [Тексты]                  │
│  ──────────────────────────────────    │
│  НАВЫКИ                                │
│  [▸ Дизайн]                            │
│  [▸ Маркетинг]                         │
│  [▸ Тексты]                            │
│  [▾ Разработка]                        │
│  ┌──────────────────────────────────┐  │
│  │  ПО ЗАДАЧЕ                       │  │
│  │  [✓ Telegram-боты ▾] [WordPress] │  │
│  │  [Парсинг] [API] [ИИ]            │  │
│  │    └ [aiogram] [Telethon] ← L3   │  │
│  │  ПО ТЕХНОЛОГИИ                   │  │
│  │  [✓ Python ▾] [JavaScript]       │  │
│  │    └ [Django] [FastAPI]   ← L3   │  │
│  └──────────────────────────────────┘  │
│  ──────────────────────────────────    │
│  СОРТИРОВКА                            │
│  (●) Новые  ( ) По совместимости       │
├────────────────────────────────────────┤ sticky
│  [Применить →]     full-width 52px     │
└────────────────────────────────────────┘
overlay rgba(0,0,0,0.5) → tap закрывает
```

**Одинаково на обоих surfaces:** структура ниш, L1/L3 поведение, счётчик, лимит.  
**Разница:** /cabinet/ → «Сохранить» → профиль; /lenta/ → «Применить» → сортировка.

### Компонентные спеки: subhead · L1 · L3 chip

| Элемент | Размер | Цвет / вес | Прочее |
|---------|--------|------------|--------|
| **Subhead** («ПО ЗАДАЧЕ» / «ПО ТЕХНОЛОГИИ») | Manrope 11px/600 | `#525252` UPPERCASE | margin: 8px 0 4px; letter-spacing 0.5px |
| **L1 chip** (Telegram-боты, Python…) | min-height 36px · padding 6px 12px | как O92 chip-states | border-radius 2px; **L1 крупнее L3** |
| **L1 chip с ▾** | то же + суффикс «▾» при unchecked / «✓ … ▾» при checked | checked: bg `#FACC15`, border `2px solid #0A0A0A` | ▾ только у chips с дочерними L3 |
| **L3 chip** (aiogram, Django, React…) | min-height 28px · padding 4px 10px | unchecked: bg `#F0F0EC`, border `1px solid #D4D4D4`, text `12px/400 #525252`; checked: bg `#FEF9C3`, border `1.5px solid #0A0A0A`, text `12px/600 #0A0A0A` | indent 16px desktop / 12px mobile; border-radius 2px |
| **L3 row** | flex-wrap, gap 6px | — | padding-top 6px; скрыт пока L1 не expanded |

**L3 visibility:** L3 row появляется только когда L1 chip `is-selected` + повторный tap/click (▾ → раскрыть). Снятие L1 → L3 row скрывается, выбранные L3 теги сохраняются в состоянии. Отмена L1 НЕ сбрасывает L3 — только прячет.

**Max-count:** лимит 12 суммарно по L1+L3; disabled-правило из O92 §4.5 AC-4 применяется ко всем уровням.

**Нише Дизайн / Маркетинг / Тексты:** subheads «По задаче» / «По технологии» — **не добавлять**; они остаются flat (как O92). Только «Разработка» получает 2-subhead структуру.

### Deliverable

1. Wireframes desktop + mobile: **cabinet + lenta** (можно 2 frame на surface)
2. Точечное обновление [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) — новая § **4.6 O93** (AC + wireframe), **не** переписывать §4.5 O92 interim
3. Компонентные specs: L1 chip vs L2 chip vs L3 chip (размер/weight/border — L1 крупнее)

**Guardrail:** L1 prompt / API payload shape (`tags[]`) — без новых полей в wireframe.

---

## § O92-w1 — Skill Tree interim (архив handoff)

**Основание:** `feed-cabinet-mvp.md` §4.5 AC-1–AC-12 · O92 **✅ v1 deploy 1.11.30**  
**Файлы:**

```
wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js   ← Skill Tree sheet logic
wordpress/rawlead-kadence-child/assets/css/rawlead.css          ← .rl-skill-tree-* классы
wordpress/rawlead-kadence-child/page-cabinet.php                ← markup sheet
```

### Desktop (≥768px) — выпадающая панель

```
┌─ Навыки ─────────────────────── [Выбрано 3 / 12] [✕] ──┐
│                                                         │
│  ┌─ Разработка ▸ ────────────────────────────────────┐  │  ← collapsed
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Дизайн ▾ ────────────────────────────────────────┐  │  ← expanded
│  │  [✓ Figma] [✓ UI/UX дизайн] [Веб-дизайн]          │  │
│  │  [Лендинг] [Мобайл] [Баннеры] [Фирм. стиль]       │  │
│  │  [Презентации] [Логотипы]                          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Маркетинг ▸ ─────────────────────────────────────┐  │
│  └───────────────────────────────────────────────────┘  │
│  ┌─ Тексты ▸ ────────────────────────────────────────┐  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  [Сохранить навыки →]               Сбросить всё        │
└─────────────────────────────────────────────────────────┘
max-width: 480px · border: 2px solid #0A0A0A
shadow: 6px 6px 0 #0A0A0A · bg #FFFFFF
```

### Mobile (<768px) — bottom sheet 95vh

```
      ──────── ← handle 40px×4px, bg #D4D4D4
┌────────────────────────────────────────┐
│  Навыки                     [✕]        │
│  Выбрано 3 / 12                        │
├────────────────────────────────────────┤ scroll
│  ┌─ Разработка ▸ ──────────────────┐   │
│  └─────────────────────────────────┘   │
│  ┌─ Дизайн ▾ ──────────────────────┐   │
│  │  [✓ Figma] [✓ UI/UX дизайн]     │   │
│  │  [Веб-дизайн] [Лендинг]         │   │
│  │  [Мобайл] [Баннеры]             │   │
│  └─────────────────────────────────┘   │
│  ┌─ Маркетинг ▸ ──────────────────┐   │
│  └─────────────────────────────────┘   │
│  ┌─ Тексты ▸ ──────────────────────┐   │
│  └─────────────────────────────────┘   │
├────────────────────────────────────────┤ sticky
│  [Сохранить навыки →]   full-width     │ 52px
└────────────────────────────────────────┘
overlay rgba(0,0,0,0.5) → tap закрывает
```

### Компонент: root niche block

| Состояние | Вид |
|-----------|-----|
| Collapsed | bg `#F5F5F0`, border `2px solid #0A0A0A`, shadow `2px 2px 0 #0A0A0A`, `min-height: 44px`; `▸` |
| Expanded | bg `#FFFFFF`, border `2px solid #0A0A0A`, shadow `4px 4px 0 #0A0A0A`; `▾`; padding-bottom `12px` |
| Hover | `translate(-1px,-1px)` + shadow `4px 4px 0 #0A0A0A`, 120ms |

Заголовок ниши: Manrope 14px/700 `#0A0A0A`. **Несколько ниш открываются одновременно** (не аккордеон, AC-3).

### Компонент: chip навыка (checkbox-chip)

| Состояние | CSS |
|-----------|-----|
| Unchecked | bg `#F5F5F0`, border `1.5px solid #D4D4D4`, text `#525252 14px/400` |
| Checked | bg `#FACC15`, border `2px solid #0A0A0A`, text `#0A0A0A 14px/700`, shadow `2px 2px 0 #0A0A0A` |
| Disabled (13-й) | bg `#F5F5F0`, border `1.5px solid #D4D4D4`, text `#A3A3A3`, opacity `0.55`, cursor `not-allowed` |
| Focus | outline `2px solid #0A0A0A`, offset `2px` |

`min-height: 36px` · `padding: 6px 12px` · `border-radius: 2px`

### Счётчик, hint, лимит

| N выбрано | UI |
|-----------|-----|
| 0 | «Выбрано 0 / 12» — Manrope 13px/600 `#525252` в шапке sheet |
| 1–6 | «Выбрано N / 12» — `#0A0A0A` |
| **7–11** | + hint-баннер: `⚡ Рекомендуем 6–8 ключевых — так совместимость точнее` · bg `#FEF9C3`, border-left `3px solid #FACC15`, pad `8px 12px`, 13px/400 `#525252` · **не блокирует выбор** |
| **12** | + limit-msg: `Максимум 12 навыков — сними лишние, чтобы добавить новые` · bg `#FEE2E2`, border-left `3px solid #DC2626`, 13px/400 `#DC2626` · все незвыбранные → disabled |

### Кнопка «Сохранить»

| Состояние | Вид |
|-----------|-----|
| N=0 | ghost: bg `#F5F5F0`, text `#A3A3A3`, border `2px solid #D4D4D4`, `not-allowed` |
| N≥1 idle | NEO primary: bg `#0A0A0A`, text `#FACC15`, border `2px solid #0A0A0A`, shadow `4px 4px 0 rgba(0,0,0,0.3)` |
| Loading | spinner 20px + «Сохраняем…», disabled |
| Success | bg `#16A34A`, text `#FFFFFF`, «Навыки сохранены ✓» → sheet закрывается 1.5с |
| Error | кнопка активна; inline: «Ошибка — попробуй снова» `#DC2626` под кнопкой; sheet не закрывается |

### Collapsed skills-strip (after save)

- Чипы с `[×]` немедленно после `200 OK` (без reload)
- Порядок: Dev → Design → Marketing → Text
- **Empty (0 навыков):** `[+ Добавь навыки для совместимости →]` — ghost link, `min-height: 44px`; hint под строкой: «Лента покажет совместимость» Manrope 12px `#525252`
- **Saved flash:** outline `2px solid #16A34A` на collapsed row на 2с
- **Skeleton (initial load):** 3 placeholder-chip — bg `#F5F5F0`, pulse, `60–100px × 30px`, `border-radius: 2px`

### CSS-классы

```css
.rl-skill-tree            /* sheet/panel container */
.rl-skill-tree__header    /* sticky: title + counter + close */
.rl-skill-tree__counter   /* "Выбрано N / 12" */
.rl-skill-tree__hint      /* hint banner (N≥7), bg #FEF9C3 */
.rl-skill-tree__limit-msg /* limit message (N=12), bg #FEE2E2 */
.rl-skill-tree__body      /* scrollable body */
.rl-skill-tree__footer    /* sticky footer */
.rl-niche-root            /* collapsible niche container */
.rl-niche-root__header    /* clickable header, min-height 44px */
.rl-niche-root--expanded  /* modifier */
.rl-niche-root__chips     /* flex-wrap chip group, gap 8px */
.rl-skill-chip            /* checkbox-chip */
.rl-skill-chip.is-selected /* bg #FACC15 */
.rl-skill-chip.is-disabled /* opacity 0.55, not-allowed */
```

### Telemetry (AC-9, try/catch — не блокирует UX)

```js
// skill_select / skill_unselect: { niche: 'design', tag: 'figma' }
// skills_save:                   { selected_count: 5, niche_mix: ['design', 'dev'] }
```

### Acceptance checklist

- [ ] 4 root ниши видны всегда; клик → expand chips; повторный → collapse; ≥1 ниш открыты одновременно
- [ ] Chip: tap → is-selected (yellow); повторный → снять; counter обновляется синхронно
- [ ] Hint ≥7 появляется; исчезает при ≤6; лимит N=12 → disabled + msg
- [ ] [Сохранить]: N=0 → disabled; loading → success/close → strip обновляется; error → sheet не закрывается
- [ ] Mobile sheet 95vh; scroll внутри; sticky footer 52px; overlay tap = закрыть
- [ ] Desktop panel max-width 480px; NEO shadow/border
- [ ] Collapsed strip: empty state, saved flash, skeleton
- [ ] Telemetry try/catch
- [ ] Tokens: `REFERENCE §2` · `DESIGN_SYSTEM § WP NEO-BRUTALIST`

---

## § O82-w1b — Match v2 (**→ @coder**, P0 · после **D-O82b**)

**Lead brief:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § **D-O82b**

| ID | Что сделать |
|----|-------------|
| r1 | Убрать чипы «Брать ✓» / «Сомнительно» с карточки ленты |
| r2 | Label + bar = **только «Совместимость»** (`keyword_match`), не «Качество заказа» |
| r3 | CTA «Добавь навыки…» = **`!isLoggedIn() && !hasUserSkills()`** только |
| r4 | Breakdown = совпадение стека (по макету D-O82b), без `ai_score` в UI |
| r5 | Обновить U11 в `ux_audit.py` |

---

## Закрыто (индекс)

| Волна | Статус |
|-------|--------|
| WAVE-UX-MOBILE | ✅ |
| WAVE-2-CSS · O41 | ✅ |
| O82-w1 match breakdown | ✅ 2026-06-01 → [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) § D-O82 |

Детали → [`archive/DESIGNER_PROMPT_ARCHIVE.md`](../archive/DESIGNER_PROMPT_ARCHIVE.md)

---

_Lead Designer · hot · 2026-06-02 · O92 Skill Tree handoff_
