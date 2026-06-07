# Lead Designer — активный план

**Обновлено:** 2026-06-07 · **Регламент:** [`LEAD_DESIGN.md`](LEAD_DESIGN.md) — **кто какой файл читает**

| | |
|--|--|
| **→ Сейчас** | — (idle) |
| **O127-D** | ✅ Filter Bar v2 + Lead Card v3 · **2026-06-07** → **@coder O127-WP** |
| **O121-D** | ✅ wireframes `/ops/` прокси + IA · **2026-06-05** → **@lead-architect** → Coder **O121-w1** |
| **O116-D** | ✅ Lead Design 2026-06-04 |
| **PRE-RELEASE-AUDIT** | ✅ Coder **1.18.4** · Lead verify ✅ |
| **D-O81** | **✅ Design 2026-06-01** (канвас v9 · спека § O81-w1) |
| **D-O82b** | Match v2 breakdown — **⏸** |
| **D-O40** | **✅ Lead verify 2026-05-30** |
| **O96-D ф2** | **✅ спеки сданы 2026-06-02** → @lead-architect → @coder |
| **O105-D** | **✅ Lead verify 2026-06-03 · → @coder** (CODER_PROMPT § O105-WP · O106) |
| **Vision** | [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** |

**Gate:** O127-D → O127-WP → owner BrowserSync → E2E/stress → ads.

---

## § O127-D — Финальный UI unify: Filter Bar + Lead Card (**✅ Lead Design 2026-06-07 · → Coder O127-WP**)

**Запрос владельца:** функции ок, **вид не устраивает** — фильтры anon/free/premium выглядят по-разному; карточки не доведены; mobile 390px. Не ребренд NEO.

**Канон продукта:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § O127 · очередь [`TASKS.md`](../common/TASKS.md) шаг **9b**.

**Детальная спека (Coder-handoff):** [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) **§9 O127**.

---

### Решения (канон, не менять без нового слова владельца)

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | Три layout фильтра → один? | **Один chrome** — одна высота, один border. Правые кнопки присутствуют у всех тиров: у anon — locked-состояние (muted), у auth — active. |
| Q2 | Locked кнопки у anon — скрыть или muted? | **Muted + клик** → inline hint под баром «Войди чтобы настраивать» + ссылка `/cabinet/`. Не скрывать — chrome должен быть одинаковым. |
| Q3 | Sorting для Free vs Premium | **Free:** Свежие / По совм. (без min%). **Premium:** + выбор мин.% (60/70/80/90). Один компонент, разные опции по tier. |
| Q4 | Одна карточка для /lenta/ + /cabinet/? | **Да** — `.rl-lead-card` единый. Tier-rows `[data-tier]` + CSS управляют видимостью match row (auth only) и slot row (paid only). |
| Q5 | CTA на карточке — сколько? | **Ровно один** на карточку. Anon → ghost CTA /cabinet/. Free → locked CTA (inline upsell). Premium/lenta → primary CTA. Cabinet → accordion черновик. |
| Q6 | «Брать»/«Сомнительно» чипы | **Убраны** (O82/O96 — уже решено). Проверить что не рендерятся нигде. |
| Q7 | Mobile thumb-zone CTA | **min-height 48px** для CTA на карточке. Filter bar кнопки — 44px. |

---

### О127-А — Filter Bar System: capability matrix

| Capability | Anon | Free TG | Premium |
|-----------|------|---------|---------| 
| Категории (chips) | ✅ | ✅ | ✅ |
| [Навыки ▾] | 🔒 muted | ✅ (badge если есть) | ✅ (число badge) |
| [Сортировка ▾] | 🔒 muted | ✅ Свежие/По совм. | ✅ + мин. % |
| Match bar на карточке | ❌ | ✅ | ✅ |
| CTA «Написать отклик» | ghost → /cabinet/ | 🔒 muted → upsell | ✅ primary |
| Slot line «Осталось N» | ❌ | ❌ | ✅ |
| Сложность (expanded) | ❌ | ❌ | ✅ |

**Chrome (одинаковый):** height 52px desktop / 48px mobile · bg `#FFFFFF` · border-bottom `2px solid #0A0A0A` · sticky под header.

**Locked кнопки (anon):** bg `#F5F5F0` · border `2px solid #D4D4D4` · text `#A3A3A3` · cursor pointer.  
**Клик на locked** → inline hint под баром (full-width, `position:absolute; top:100%`): «Войди чтобы настраивать подбор по навыкам → [Войти в кабинет]». Закрывается по tap outside / 4с.

---

### O127-B — Lead Card v3: F-pattern + thumb-zone

**F-pattern (читает сверху вниз, слева→право на первых строках):**

```
① HEAD:  [niche icon] [●Source] [ИДЕАЛЬНО✦/badge]        👁N · Xмин
② TITLE: Заголовок заказа (2 строки)
③ BUDGET: N ₽
④ MATCH ROW (auth only): ▓▓▓▓▓▓░  N%  Совместимость
⑤ SLOT ROW (paid only):  Осталось N из 10 ⓘ  (muted)
⑥ TAGS:  [tag1] [tag2]  +3→
⑦ CTA:   [один primary action — 48px min-height]
```

**Expanded (tap):**
```
Суть: (L1 summary)
Сложность: 🟡 Проект  (paid only)
Совпало: N из M тегов
[Читать на бирже ↗]
[черновик accordion — только cabinet/paid]
```

---

### DoD Design O127-D

- [x] Capability matrix Filter Bar (Q1–Q3) зафиксирована
- [x] Unified chrome spec (52/48px, locked state) в feed-cabinet-mvp.md §9
- [x] Lead Card v3 (F-pattern, один CTA, tier rows) в feed-cabinet-mvp.md §9
- [x] Mobile 390px thumb-zone (48px CTA, 44px filter buttons) — в §9
- [x] Heuristic pass (F-pattern, one primary CTA) — задокументирован
- [x] Handoff → @lead-architect одной строкой

---

### Handoff → @lead-architect

> **O127-D готово → Coder O127-WP:** единый filter bar chrome (locked для anon, active для auth) + Lead Card v3 (data-tier rows, один CTA, 48px mobile) · детальная спека: `feed-cabinet-mvp.md` §9 · деплой одной волной.

---

## § O121-D — `/ops/` админка: прокси + IA (**✅ Lead Design 2026-06-05 · → Coder O121-w1**)

**Решение владельца:** админка **до рекламы** · каждый день ломается FL/прокси — без панели владелец не чинит сам · **не Tauri**, только web `/ops/`.

**Канон продукта:** [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § O121 · очередь [`TASKS.md`](../common/TASKS.md) шаг **6**.

**Scope этой волны (Design):** wireframes + CSS-спека **только** для расширения `/ops/` — секция **«Прокси»**, навигация по блокам, mobile 390px. **Не** публичный сайт, **не** NEO-brutalist лендинг.

**Coder после spec:** § **O121-w1** в [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md).

---

### Контекст — что уже есть на `/ops/` (не ломать)

Тёмная ops-тема (`owner_admin.py`): `#0f1419` bg · карточки `#1a2332` · статусы 🟢🟡🔴.

| Секция (сверху вниз) | Статус |
|----------------------|--------|
| Сводка (сайт · radar · feed · bots · problems 24h) | ✅ |
| **Боты** — @rawlead_bot · @FLPARSINGBOT · restart | ✅ O121-w0b/c |
| **Биржи и скорость** — FL · Kwork · задержка ленты | ✅ read |
| **Управление** — radar pause/restart · site · delist | ✅ |
| Последние заказы · посещения · поддержка | ✅ |

**Добавить:** секция **«Прокси»** — **между** «Биржи» и «Управление».

---

### Решения (канон, не менять без нового слова владельца)

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | Стиль `/ops/` | **Оставить тёмный ops-UI** — не переносить NEO-brutalist с лендинга |
| Q2 | Layout | **Одна длинная страница** + якоря/mini-nav (как сейчас), не отдельный SPA |
| Q3 | Пароли прокси | **Никогда plaintext** — только mask `{scheme}://{user}:***@{host}:{port}` (как `probe_all_proxies.mask()`) |
| Q4 | Группы слотов | **3 группы:** TG Bot API · Telethon acc1–3 · Биржи (FL / Kwork / pool) |
| Q5 | Действия w1 | **Проверить** (probe) · **Переключить** (manual active) · **Сбросить бан** — в w2, в wireframe заложить место |
| Q6 | Auto-failover | **Read-only badge** в w1: «Авто: вкл/выкл» · toggle — w2 |
| Q7 | Mobile | **Обязательно 390px** — владелец чинит с телефона; таблица → **карточки-строки** |
| Q8 | Ошибки действий | Тот же паттерн что «Боты»: строка статуса под кнопками + текст ошибки (не alert) |
| Q9 | TG acc / Neon ingest | **Не в этой волне** — placeholder-секция «Скоро» или якорь без wireframe |
| Q10 | Mini-nav по секциям | **Да** — sticky chips под header; на mobile горизонтальный scroll; **в той же волне w1**, что и секция «Прокси» |

---

### IA — порядок секций (финал)

```
[Header] Пульт RawLead · статус строка

[Mini-nav sticky] → #ops-summary · #ops-bots · #ops-exchanges · #ops-proxies · #ops-controls · #ops-leads
  └ mobile: overflow-x scroll · chips не переносятся

1. #ops-summary   Сводка (cards grid)              — KEEP + id
2. #ops-bots      Боты                             — KEEP + id
3. #ops-exchanges Биржи и скорость                 — KEEP + id
4. #ops-proxies   Прокси                    ← NEW § O121-D
5. #ops-controls  Управление (radar · delist · …)  — KEEP + id
6. #ops-leads     Последние заказы                 — KEEP + id
7. Посещения · Поддержка                           — KEEP (без chip — редко нужны)
```

**Mini-nav (Q10 = да):** только `/ops/` · muted chips · active = `border-color: var(--ok)` + dot `var(--ok)` · tap → `scrollIntoView({ behavior: 'smooth', block: 'start' })` · **не** менять порядок существующих секций.

---

### O121-P0 — Mini-nav (desktop + mobile)

```
┌─ sticky под «Пульт RawLead» ────────────────────────────────────────┐
│ [ Сводка ] [ Боты ] [ Биржи ] [ Прокси ● ] [ Управление ] [ Лиды ] │
└─────────────────────────────────────────────────────────────────────┘
  ● = текущая секция в viewport (IntersectionObserver) или last tap

Mobile 390px — тот же ряд, overflow-x: auto, padding .5rem 0:
  Сводка · Боты · Биржи · Прокси · Управление · Лиды
  (tap target chip ≥ 36px height · padding .35rem .6rem)
```

**Не в nav:** Посещения · Поддержка — длинный хвост, владелец до них скроллит.

---

### O121-P1 — Desktop wireframe: секция «Прокси» (1440)

```
<section id="ops-proxies">
  <h3>Прокси</h3>
  <p class="sub">Слоты VPS · без паролей · переключение без SSH</p>

  ┌─ Toolbar ─────────────────────────────────────────────────────────┐
  │  [ Проверить все ]     Авто-переключение: ● Вкл   (read w1)      │
  │  Active TG: слот 2 · 45.152.x.x:8080 (masked)                    │
  └──────────────────────────────────────────────────────────────────┘

  ── TG Bot API ─────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────────────┐
  │ Слот │ Адрес (mask)      │ Статус │ Бан до    │ Действия        │
  ├──────┼───────────────────┼────────┼───────────┼─────────────────┤
  │  1   │ user:***@45…:8080 │ 🟢     │ —         │ [Проверить] [→] │
  │  2 ● │ user:***@91…:8080 │ 🟢 ACTIVE │ —       │ [Проверить]     │
  │  3   │ user:***@12…:8080 │ 🔴     │ 6ч · probe│ [Проверить] [→] │
  └──────────────────────────────────────────────────────────────────┘
  ● = active row highlight: border-left 3px var(--ok) · bg #1e2a22

  ── Telethon (парсинг TG) ──────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────────────┐
  │ acc1 │ … │ 🟡 │ strikes 2/3 │ [Проверить] [→]                    │
  │ acc2 │ … │ 🟢 ACTIVE │ —   │ [Проверить]                        │
  │ acc3 │ … │ 🟢 │ —         │ [Проверить] [→]                    │
  └──────────────────────────────────────────────────────────────────┘

  ── Биржи (FL / Kwork / pool) ──────────────────────────────────────
  ┌──────────────────────────────────────────────────────────────────┐
  │ FL pool │ slot 1 │ … │ 🟢 │ [Проверить]                        │
  │ Kwork   │ slot 1 │ … │ 🟡 │ HTTP 403 · [Проверить] [→]         │
  │ Общий   │ slot 2 │ … │ 🟢 ACTIVE │ [Проверить]                │
  └──────────────────────────────────────────────────────────────────┘

  <p class="sub ctl-hint">Последняя проверка: 2 мин назад · probe: Telegram + FL + Kwork</p>
  <div id="rl-ops-proxy-status" class="ctl-status"><span class="dot"></span><span>Ожидание</span></div>
</section>
```

**Probe раскрыт (пример строки 3, см. O121-P3):**

```
│  3   │ http://user:***@12…:8080 │ 🔴 │ до 18:00 │ [Проверить] [→] │
  └─ .ops-proxy-probe (под tr / внутри card на mobile)
       TCP api.telegram.org      🟢 120 ms
       HTTPS api.telegram.org    🟢 340 ms
       HTTPS www.fl.ru           🔴 timeout
```

**Колонки таблицы (минимум):**

| Колонка | Содержание |
|---------|------------|
| Слот / acc | `слот 1` · `acc2` · `FL pool` |
| Адрес | masked URL only |
| Статус | 🟢 ok · 🟡 degraded · 🔴 banned/down |
| Бан / причина | «до 14:30» · `probe_fail` → human: «HTTPS probe fail» |
| Действия | `[Проверить]` · `[→ Активировать]` (не «Switch» по-английски) |

**Кнопка `[→]`:** secondary `.btn` · не primary — опасное действие только по явному клику.

---

### O121-P2 — Mobile 390px: прокси-карточки

Таблица **не** горизонтальный скролл — **stack карточек**:

```
┌─────────────────────────────────────┐
│ TG Bot API · слот 2        ● ACTIVE │
│ user:***@91.152.x.x:8080            │
│ 🟢 Работает                         │
│ [ Проверить ]  [ Сделать активным ] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ TG Bot API · слот 1                 │
│ 🔴 Забанен до 18:00                 │
│ probe_fail                          │
│ [ Проверить ]  [ Сделать активным ] │
└─────────────────────────────────────┘
```

- Кнопки **full-width** на mobile, min-height **44px**
- Группа = muted label над карточками: `TG BOT API` · `TELETHON` · `БИРЖИ`
- Toolbar «Проверить все» — sticky **под** header ops или первым элементом секции

---

### O121-P3 — Probe result (inline, не modal)

После «Проверить» — **раскрытие под строкой** (accordion 1 уровень):

```
  TCP api.telegram.org     🟢 120ms
  HTTPS api.telegram.org   🟢 340ms
  HTTPS fl.ru/projects     🔴 timeout
```

Цвета: ok `var(--ok)` · fail `var(--bad)` · muted latency.

**Не:** отдельное модальное окно · не toast без деталей.

---

### O121-P4 — Состояния и copy (RU, для владельца)

| Статус | Текст в UI |
|--------|------------|
| active | «Сейчас используется» |
| banned | «Забанен до {time}» |
| probe_ok | «Проверка ок» |
| probe_fail | «Не отвечает — {причина}» |
| switching | «Переключаем…» (кнопки disabled) |
| auto_on | «Авто-переключение: вкл» |
| auto_off | «Авто-переключение: выкл — только вручную» |

Голос: **коротко, без жаргона** — владелец не devops. «Слот», не «endpoint».

---

### O121-P5 — CSS delta (ops-тема, не лендинг)

Добавить к существующим классам `owner_admin.py`:

```css
.ops-proxy-toolbar { display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin-bottom:.75rem }
.ops-proxy-group { margin:1rem 0 }
.ops-proxy-group__title { font-size:.75rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:.5rem 0 }
.ops-proxy-table { width:100%; font-size:.82rem }
.ops-proxy-table tr.is-active { border-left:3px solid var(--ok); background:#1a2820 }
.ops-proxy-card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:.85rem; margin-bottom:.5rem }
.ops-proxy-card.is-active { border-color:var(--ok) }
.ops-proxy-probe { font-size:.78rem; color:var(--muted); padding:.35rem 0 .35rem .5rem; border-left:2px solid var(--line) }
.ops-mini-nav { display:flex; gap:.35rem; overflow-x:auto; padding:.5rem 0; margin-bottom:.75rem }
.ops-mini-nav a { font-size:.75rem; padding:.35rem .6rem; border-radius:6px; border:1px solid var(--line); color:var(--muted); white-space:nowrap }
.ops-mini-nav a.is-active { color:var(--txt); border-color:var(--ok) }
.ops-mini-nav a.is-active::before { content:''; display:inline-block; width:.4rem; height:.4rem; border-radius:50%; background:var(--ok); margin-right:.25rem }
@media (min-width:768px) { .ops-proxy-card { display:none } }
@media (max-width:767px) { .ops-proxy-table { display:none } }
```

**HTML-вставка (между «Биржи» и «Управление»):**

```html
<nav class="ops-mini-nav" aria-label="Разделы пульта">…chips…</nav>
<!-- существующие section: добавить id="ops-summary" | ops-bots | ops-exchanges | ops-controls | ops-leads -->

<section id="ops-proxies">
  <h3>Прокси</h3>
  <p class="sub">Слоты VPS · без паролей · переключение без SSH</p>
  <div class="ops-proxy-toolbar">…</div>
  <div class="ops-proxy-group" data-group="tg-bot">…table desktop / cards mobile…</div>
  <div class="ops-proxy-group" data-group="telethon">…</div>
  <div class="ops-proxy-group" data-group="exchanges">…</div>
  <p class="sub ctl-hint" id="rl-ops-proxy-hint">Последняя проверка: —</p>
  <div id="rl-ops-proxy-status" class="ctl-status">…</div>
</section>
```

**Probe targets по группе (для inline-результата):**

| Группа | HTTPS checks |
|--------|----------------|
| TG Bot API | `api.telegram.org` |
| Telethon accN | `api.telegram.org` (тот же probe, другой слот) |
| Биржи FL | `www.fl.ru` |
| Биржи Kwork | `kwork.ru` |
| Общий pool | FL + Kwork (как `probe_all_proxies.py`) |

**w2 placeholder в toolbar:** кнопка «Сбросить бан» — **disabled** в w1 · `title="Скоро"` · не прятать (владелец видит roadmap).

**Файлы Coder:** `src/owner_admin.py` · `tg_proxy_pool.py` · `exchange_proxy.py` · `scripts/probe_all_proxies.py` (reuse mask/probe) · API `GET /ops/proxies` · `POST /ops/control` (`proxy-probe` · `proxy-switch` · имена — по бэку).

---

### Не в scope O121-D (w1)

| Исключено | Когда |
|-----------|-------|
| CRUD новых URL прокси | O121-w4 |
| TG acc join / список чатов | O121-w3 |
| Neon ingest dashboard | O121-w3 |
| История переключений (timeline) | w2+ |
| Публичный URL без auth | никогда |

---

### DoD Design O121-D

- [x] Wireframe desktop **O121-P1** + mobile **O121-P2** зафиксированы в этом файле
- [x] IA + **O121-P0** mini-nav — **да**, section ids + sticky chips
- [x] Probe inline **O121-P3** — accordion под строкой, не modal
- [x] CSS delta **O121-P5** — классы названы
- [x] Mask credentials — Q3 · формат `probe_all_proxies.mask()`
- [x] Handoff `@lead-architect` — см. ниже

---

### Handoff → @lead-architect

> **O121-D готово → Coder O121-w1:** `/ops/` секция `#ops-proxies` между «Биржи» и «Управление» · mini-nav **O121-P0** · 3 группы слотов · mask · probe inline · mobile cards · `ctl-status` как у ботов.

---

## § O116-D — TWO-SPEEDS update: anon strip + FAQ 3 групп + pricing F1 (**W2 @lead-designer · 2026-06-04**)

**PM approve:** [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § O116-COPY — R1+R2+R3 ✅ владелец 2026-06-04.

**Scope:** Z2 (anon strip hook → TG login) · Z3 (pricing F1/F2 swap) · Z4 (FAQ accordion 3 групп)

---

### Решения (канон, не менять без нового слова владельца)

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | Free TG login strip — показывать или скрыть? | **Показывать upsell:** «✅ Лента без задержки · [Черновики — Premium →]» → `/pricing/` |
| Q2 | FAQ group header стиль | **Manrope 700 · bg `#F3F3EF` · border-bottom `1px solid #E4E4E7`** · padding 16px 20px · весь header кликабельный |
| Q3 | FAQ: открытая по умолчанию группа | **«Начало»** — desktop + mobile. Остальные closed. |
| Q4 | FAQ Q10 позиция | **Последний в группе «Premium»** (после Q9) |

---

### Z2 — `/lenta/` strip: три состояния (замена O105-Z5)

| Состояние пользователя | Текст strip | CTA target |
|------------------------|-------------|------------|
| **Anon** (нет TG-входа) | `⏱ Лента с задержкой 15 мин · [Войди — сразу →]` | `/cabinet/` (TG login) |
| **Free** (TG вход, нет Premium) | `✅ Лента без задержки · [Черновики — Premium →]` | `/pricing/` |
| **Paid** (Premium активен) | strip скрыт | — |

**CSS delta:**
- Anon strip: структура без изменений · только copy + ссылка `/cabinet/` вместо `/pricing/`
- Free strip (NEW · класс `.rl-feed-strip--free`): `background: #F0FDF4` · «✅» цвет `#15803D` · текст остальной — `var(--rl-text-primary)` · inline link `font-weight: 700`
- Mobile 390px: обе версии — одна строка, помещаются без wrap

**Файлы Coder:**
- `template-parts/rawlead/feed-strip.php` (или аналог) — conditional по `$user_state` (anon / free / paid)
- `rawlead.css` — `.rl-feed-strip--free`

---

### Z3 — `/pricing/` + `#pricing-preview`: bullets F1/F2 swap

| Позиция | Было (O105, live) | Стало (O116-Z3) |
|---------|-------------------|-----------------|
| **Feature 1** | «Лента без задержки — заказы под твой стек сразу» | **«Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам»** |
| **Feature 2** | «Уникальный черновик отклика — ИИ пишет под тебя, не копирует с соседа» | **«Лента без задержки и push — заказы появляются сразу при match»** |
| Feature 3–5 | KEEP | KEEP |

**Применяется:** `/pricing/` (D3) · `#pricing-preview` на главной (D2).

**Не менять:** заголовок карточки · цена · payment block · CTA · compare line.

**Файлы Coder:** `pricing-card.php` · `pricing-preview.php`

---

### Z4 — `/faq/` accordion 3 уровня

**Структура (порядок показа по PM-канону):**

```
▼ Начало                          ← GROUP 1, OPEN by default · bg #F3F3EF
  │  Q6  Как начать?
  │  Q1  Это автоспам?
  └  Q4  Нужен TG?

▶ Как работает                    ← GROUP 2, closed
  │  Q2  Нетехнические специалисты?
  │  Q3  Источники
  │  Q5  Не получу бан?
  └  Q8  Почему лимит 10 откликов?

▶ Premium                         ← GROUP 3, closed
  │  Q7  Сервис платный?
  │  Q9  Есть trial?
  └  Q10 Зачем Premium, если лента без задержки? ← NEW
```

**Спека group header:**
```css
.rl-faq-group__header {
  font-family: var(--rl-font); font-weight: 700; font-size: 16px;
  background: #F3F3EF;
  border: 2px solid #0A0A0A;
  padding: 16px 20px;
  cursor: pointer;
  display: flex; justify-content: space-between; align-items: center;
  min-height: 44px; /* tap target */
}
.rl-faq-group__header::after { content: '▶'; transition: transform 200ms ease-out; }
.rl-faq-group.is-open .rl-faq-group__header::after { transform: rotate(90deg); }
```

**Sub-accordion:** текущий стиль FAQ-аккордеона без изменений — просто вложен под group header.

**Default JS state:** group `data-index="0"` (Начало) → `is-open` класс при init; остальные — закрыты.

**Mobile 390px:** аналогичное поведение; весь group header — tap zone 44px.

**Q10 copy (R1 принят):**
- **Q:** «Зачем Premium, если лента и так без задержки после входа?»
- **A:** «После входа через Telegram — лента сразу. Это бесплатно. Premium даёт: уникальный черновик отклика под твой профиль · push в Telegram при матче · inbox с черновиками · до 10 слотов на горячий заказ.»

**Файлы Coder:** `page-faq.php` (перегруппировать Q + добавить Q10) · `rawlead.css` (`.rl-faq-group`) · `rawlead-feed.js` или отдельный `rawlead-faq.js` (group toggle)

---

### Найденные ошибки дизайна (Design Audit O116)

| # | Поверхность | Проблема | Fix |
|---|-------------|----------|-----|
| **E1** | D3 + D2 wireframe (этот файл § O105-D) | Feature 1 буллет устарел — «Лента без задержки» (O116-Z3 принят, порядок поменялся) | → **обновлено в D3 ниже** |
| **E2** | `/lenta/` strip — Free TG login | Нет дизайн-спеки для нового состояния (3-й state, O116-Z1) | → **закрыт выше в Z2** |
| **E3** | `/faq/` | Q10 не существует в спеке; 3-групп accordion — новый компонент без CSS-спеки | → **закрыт выше в Z4** |
| **E4** | `§ TWO-SPEEDS-UI` (архив этого файла) | Старая спека strip ссылается anon → `/pricing/`; теперь anon → `/cabinet/` | → архивная секция, Coder ориентируется на **O116-D Z2** |
| **E5** | BUG-4 риск регрессии | PRE-RELEASE-AUDIT BUG-4 фикс (paid → скрыть trial CTA) теперь требует 4-й логики: free-TG-login ≠ paid; убедиться что free strip не показывается premium-пользователям | → Coder проверяет в smoke |

---

### DoD Design O116

- [ ] Z2: `/lenta/` strip — 3 состояния spec передана Coder · free strip `.rl-feed-strip--free`
- [ ] Z3: `/pricing/` + `#pricing-preview` — F1/F2 swap · copy строго из O116-Z3 (PM approve)
- [ ] Z4: `/faq/` — 3 групп + Q10 · group header spec · default open «Начало»
- [ ] Нет O100-механик (аукцион, FOMO) в copy
- [ ] BUG-4 регрессия-проверка: premium-пользователь не видит free-strip и не видит trial CTA
- [ ] Handoff `@lead-architect` одной строкой в чат

---

## § PRE-RELEASE-AUDIT — UX/UI аудит перед релизом (**→ @lead-architect 2026-06-04**)

**Источник:** Playwright-обход rawlead.ru · desktop 1440 + mobile 390 · анон + залогиненный.

**Handoff:** ✅ Lead Architect → `CODER_PROMPT` § PRE-RELEASE-AUDIT (2026-06-04).

---

### P0 — Блокеры релиза (5 багов)

| # | Файл | Симптом | Fix |
|---|------|---------|-----|
| **BUG-1** | `template-parts/rawlead/pricing.php` + `rawlead.css` | `/pricing/` — страница пустая. Контент в DOM (карточка, буллеты, оплата, CTA) есть, но не рендерится визуально. Пустой белый прямоугольник между hero и footer | Найти CSS-правило скрывающее `.rl-pricing-*` или WP-article контейнер (`display:none` / `height:0` / `visibility:hidden` / `opacity:0`) · убрать |
| **BUG-2** | `rawlead.css` | Иконки ниши (`</>` · `Aa` · `◎` · `✦`) **присутствуют** на preview-карточках главной и в анимации flow-секции, но **отсутствуют** на реальных карточках `/lenta/` · Класс `.rl-feed-card__niche-icon` или аналог не добавляется в PHP-шаблоне карточки ленты | Добавить иконку ниши в `template-parts/rawlead/feed-card.php` в head-строку, рядом с source-бейджем · CSS уже есть |
| **BUG-3** | `rawlead.css` или `how.php` | На `/how/` текст шагов (шаги 2–3) покрашен в синий/оранжевый — цвет ссылок. Это обычный `<p>`, не `<a>`, но стиль наследует `a { color }` | Добавить явный `color: var(--rl-text-primary)` на `.rl-how-step p` / `.rl-how-steps__body` |
| **BUG-4** | `rawlead-cabinet.js` или `cabinet.php` | Блок подписки в ЛК: у пользователя с активным PREMIUM отображается кнопка **«Попробовать 3 дня бесплатно»** — логика состояний не учитывает уже активный статус | Если `is_active === true` — скрыть trial CTA; показывать только статус + «Пауза» / «Оплата» |
| **BUG-5** | `rawlead.css` | Буллеты в тарифной карточке (на главной `#pricing-preview` и на `/pricing/`) покрашены в синий (`:link` / `a li` стиль) | Добавить `.rl-pricing-card li { color: var(--rl-text-primary); }` |

---

### P1 — UX-улучшения (одна волна с P0)

#### P1-A · Поведенческая психология: объяснение лимита откликов

**Проблема:** Пользователь видит «Осталось 10 из 10 ⓘ» и не понимает зачем это. Лимит воспринимается как ограничение, а не как защита.

**Решение — добавить подпись под slot line на карточке:**

```
Осталось 10 из 10  ⓘ
(muted 11px, под slot-line):  «Разные тексты — не шаблон → нет бана на бирже»
```

Только для залогиненных пользователей. Цвет: `var(--rl-text-muted)` · 11px · одна строка.

**Файл:** `template-parts/rawlead/feed-card.php` + `rawlead.css` · класс `.rl-slot-hint`

---

#### P1-B · Hero главной на mobile: hint о контенте ниже

**Проблема:** На mobile (390px) hero занимает весь экран. Пользователь не знает что скроллить.

**Решение:** Уменьшить min-height hero с `100vh` до `88vh` — нижняя часть следующей секции (live feed) будет «подглядывать» на ~60px. Без дополнительных элементов.

**Файл:** `rawlead.css` · `.rl-hero` `min-height`

---

#### P1-C · ЛК: упорядочить action-ссылки подписки

**Проблема:** «Подключить Premium →», «Пауза», «Возобновить», «Оплата» стоят друг под другом как plain text. Нет иерархии — непонятно что важнее.

**Решение — по состоянию:**

| Состояние | Primary (кнопка) | Secondary (muted link) |
|-----------|-----------------|------------------------|
| Free | «Попробовать 3 дня →» | «Подключить Premium →» |
| Trial active | «Оплатить 790 ₽ →» | «Пауза» |
| Paid active | — | «Пауза» · «Оплата» |

Убрать «Возобновить» из default-вида — показывать только если подписка на паузе.

**Файл:** `rawlead-cabinet.js` + CSS · блок `.rl-premium-block__actions`

---

#### P1-D · ЛК: компактные уведомления

**Проблема:** 8 кнопок % (30%–100%) занимают слишком много места на mobile.

**Решение:** Оставить 5 значимых порогов + текстовые метки:

```
[ 30% · Все ]  [ 60% · Средний ]  [ 80% · Хороший ✓ ]  [ 90% ]  [ 100% · Только идеальные ]
```

Или упростить до 3: «Все подходящие (60%+)» · «Хорошие (80%+)» · «Только идеальные (100%)»

**Файл:** `cabinet.php` + `rawlead-cabinet.js`

---

#### P1-E · Footer: заменить личный хэндл

**Проблема:** В footer — «Telegram @rcnn43» (личный хэндл владельца).

**Решение:** Заменить на «Telegram @rawlead_bot» → `https://t.me/rawlead_bot`

**Файл:** `footer.php` или WP-настройки footer

---

#### P1-F · Hero mobile: скрыть preview-карточки

**Проблема:** Preview-карточки (FL.ru, Kwork, ИДЕАЛЬНО ✦) на hero позиционированы абсолютно вправо и уходят за экран на mobile — обрезаются или создают горизонтальный скролл.

**Решение:** `@media (max-width: 767px) { .rl-hero__preview { display: none; } }` — скрыть на mobile, они и так не видны.

**Файл:** `rawlead.css`

---

### Copy: что добавить на главной (P1-G)

**Проблема (поведенческая психология):** Новый пользователь видит Hero → читает subtext → не понимает ценность лимита откликов → уходит на /pricing/ (которая сломана — BUG-1) → bounce.

**После фикса BUG-1 — усилить trust strip на главной:**

Текущий trust strip (есть): `[ Не один текст на всех ]  [ Не автоспам ]  [ Не бан за шаблон ]`

Добавить 4-й chip или заменить один:

```
[ До 10 откликов на заказ — не шаблон, не бан ]
```

**Файл:** `template-parts/rawlead/features.php` · секция trust strip · класс `.rl-trust-strip`

---

### DoD (приёмка Coder)

- [ ] `/pricing/` — карточка и весь контент видны на desktop 1440 и mobile 390
- [ ] `/lenta/` — иконка ниши отображается на каждой карточке
- [ ] `/how/` — текст шагов чёрный, не синий
- [ ] ЛК — PREMIUM-пользователь не видит trial CTA
- [ ] Буллеты тарифа — чёрный текст, не синий
- [ ] Hero mobile — нет горизонтального скролла от preview-карточек
- [ ] Footer — @rawlead_bot
- [ ] ЛК slot-hint строка под «Осталось N из N»
- [ ] Playwright smoke: `/pricing/` · `/lenta/` · `/cabinet/` · `/` — визуально ОК

---

## § O105-D — Premium · карточка · pricing (**✅ ф1 2026-06-03 · → @lead-architect**)

**PM approve:** [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § O105-COPY (Z1–Z8) · PM-аудит prod Playwright · таблица D1–D7 в § O105-Z7.

**Фаза 1:** ✅ владелец 2026-06-03 — wireframes D1–D4·D6·D7 согласованы в чате.  
**Фаза 2:** ✅ спеки зафиксированы · **Lead verify 2026-06-03** · → @coder [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § O105-WP · O106 · O105-w1.

### Решения (канон, не менять без нового слова владельца)

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | Payment rows → действие | Deep-link `@rawlead_bot /pay` напрямую |
| Q2 | Slot line позиция + цвет N=1 | Над CTA · muted · N=1 → amber (#F59E0B) |
| Q3 | Trust strip формат | 3 chip desktop · 1 строка mobile |
| Q4 | Feature 5 «Лимит в час» на mobile | Footnote muted 11px — не буллет |
| Q5 | Trial CTA placement (O107-open) | Только `/cabinet/` free (Вариант A) |

### DoD Design

- [x] Wireframes D1–D4 + D6 + D7 зафиксированы
- [x] Mobile 390 для D3 + D4
- [x] Copy только из O105-Z1–Z6 (PM approve)
- [x] Handoff `@lead-architect` одной строкой в чат

---

### Deliverables

#### D3 — `/pricing/` (P0) · desktop 1440 + mobile 390

**Структура страницы (сверху вниз):**

```
[YELLOW HERO] Тарифы · «Один тариф. Всё включено.»

[CARD — border 2px #0A0A0A · shadow 4px 4px #0A0A0A]
  title:    RawLead Premium  (Manrope 700)
  price:    790 ₽ / мес  (Manrope 800 · 42px desktop / 36px mobile)
  secondary: «или 300 ⭐ Stars (~400–720 ₽)»  (muted 14px)
  ─────────
  bullets (Z3 · O116 · порядок обновлён):
    • Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам  ← F1 NEW
    • Лента без задержки и push — заказы появляются сразу при match          ← F2 NEW
    • Пуш в Telegram — только при хорошем совпадении
    • До 10 персональных откликов на заказ — без толпы одинаковых ботов
    ⁵ Лимит в час — защита от случайных кликов (anti-тык)
      └ desktop: 5-й буллет muted · mobile: footnote 11px под списком
  ─────────
  [NEW BLOCK] «Способы оплаты»  (Manrope 700 · 16px)
  ┌────────────────────────────────────────────────────┐
  │  💳  Банковская карта РФ / СБП — 790 ₽        ›  │  → deep-link @rawlead_bot /pay
  ├────────────────────────────────────────────────────┤
  │  🪙  Crypto — USDT (TRC20) или TON             ›  │  → deep-link @rawlead_bot /pay
  ├────────────────────────────────────────────────────┤
  │  ⭐  Telegram Stars — 300 ⭐ / мес              ›  │  → deep-link @rawlead_bot /pay
  └────────────────────────────────────────────────────┘
  note (muted 12px): «СБП и crypto — в @rawlead_bot /pay. Stars — там же или кнопка в кабинете.»
  ─────────
  [CTA — primary · full-width] «Подключить Premium →»  → /cabinet/ или deep-link бота
  [secondary link] «Смотреть ленту →»
  [compare · muted 12px] «FL.ru PRO — 1 270 ₽ только за доступ к откликам.
                           RawLead — подбор + уникальный черновик + push.»
```

**Mobile 390px отличия:**
- Цена: 36px
- Буллет 5 → footnote muted 11px под списком (не в списке)
- Payment rows: label сокращённый «💳 Карта / СБП — 790 ₽»
- CTA: full-width 52px height

#### D2 — `#pricing-preview` на лендинге `/` (P0)

Урезанная версия D3 — только карточка без HERO. Позиция: под trust strip, перед footer.

```
[CARD] RawLead Premium · 790 ₽/мес · или 300 ⭐ (muted)
  3 буллета (1–3, без 4 и 5) — порядок O116-Z3:
    • Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам
    • Лента без задержки и push — заказы появляются сразу при match
    • Пуш в Telegram — только при хорошем совпадении
  [CTA] «Подключить Premium →»
  [link] «Подробнее о тарифе →» → /pricing/
  compare FL.ru (muted · 1 строка)
```

#### D4 — Карточка `/lenta/` collapsed (P0) · O106 + O101

**Prod now (лишнее в collapsed):** Навыки N% · Сложность · все теги · «AI адаптирует...»

**Новый collapsed (≤ 7 строк контента):**

```
┌──────────────────────────────────────────────────────────┐
│  ● FL.ru   [ИДЕАЛЬНО ✦]                      👁 37      │  head
├──────────────────────────────────────────────────────────┤
│  Название заказа — max 2 lines                           │  title
│  Бюджет: 4 200 ₽                                        │  budget
├──────────────────────────────────────────────────────────┤
│  Совместимость 87%  ████████░░                           │  match bar
├──────────────────────────────────────────────────────────┤
│  Осталось 7 из 10  ⓘ         (muted 11px · над CTA)     │  NEW slot line
│  ──────────────────────── N=1 → amber #F59E0B ──────────  │
├──────────────────────────────────────────────────────────┤
│  [python]  [django]  +3 →     (max 2 chip · остальные →) │  tags truncated
├──────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐   │
│  │              Написать отклик →                    │   │  CTA
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
        tap card / ∨ → expanded: Сложность · все теги · Навыки% · breakdown
```

**Slot line состояния:**

| N | Текст | Цвет |
|---|-------|------|
| 10…2 | «Осталось N из 10» | muted (#71717A) |
| 1 | «Последний черновик на этот заказ» | amber (#F59E0B) |
| 0 | карточка не отображается | — (backend) |

**Убирается из collapsed → в expanded:** Навыки N% · Сложность · теги полностью · breakdown.

**Сохраняется:** «AI адаптирует формулировку под тебя» — копим по Z4: «ИИ напишет формулировку под тебя — не как у остальных» (под CTA, muted 12px, только paid).

**Mobile 390px:** slot line — та же строка, чипов max 1 + «+N →».

#### D1 — Лендинг `/` · Feature 3 + Trust strip (P1)

**Feature 3 (замена):**

```
┌──────────────────────────────────────────────────────┐
│  03                                                  │
│  Уникальный отклик                                   │  ← NEW title (Z1)
│                                                      │
│  Каждый получает свою формулировку — ИИ адаптирует   │
│  текст под тебя. На бирже не выглядишь как бот —    │
│  не один шаблон на всех. Пишешь и отправляешь        │
│  сам — мы не спамим за тебя.                         │
└──────────────────────────────────────────────────────┘
```

**Hero sub (замена):**
> «ИИ находит заказы под твой стек и пишет черновик отклика — свой у каждого. Не шаблон с полки, не копипаст. Отправляешь ты — своими словами.»

**Trust strip (NEW · под блоком 3 features · над `#pricing-preview`):**

```
DESKTOP — 3 chip в ряд:
[ Не один текст на всех ]  [ Не автоспам ]  [ Не бан за шаблон ]
  border 2px #0A0A0A · bg #FAFAF8 · Manrope 700 · 13px · padding 8px 16px

MOBILE 390px — 1 строка:
  «Свой черновик у каждого»  (centered · muted bg #F3F3EF · 14px · padding 12px)
```

#### D6 — Bot `/pay` · 4 экрана (P1)

**Экран 1 — Выбор способа:**
```
RawLead Premium — ИИ-агент на месяц

📥 Лента без задержки — заказы сразу
✍️ Уникальный черновик под твой профиль
🔒 До 10 откликов — без каннибализма

790 ₽ / мес

[ 💳 Банковская карта РФ / СБП ]
[ 🪙 Crypto (USDT / TON)        ]
[ ⭐ Telegram Stars (300 ⭐)     ]
[ ← Назад                       ]
```

**Экран 2a — СБП:**
```
Инвойс для User #{user_id}
Сумма к оплате: 790 ₽

Реквизиты (СБП):
+7XXXXXXXXXX · Т-Банк · Никита

После перевода нажми «Проверить оплату» — сверим автоматически.

[ ✅ Проверить оплату ]   [ Отмена ]

pending:  «Ищем перевод… Обычно до 2 минут.»
fail:     «Платёж пока не видим. Проверь сумму и реквизиты или напиши в поддержку.»
success:  «✅ Premium активен до {date}. Лента без задержки — заходи на /lenta/»
```

**Экран 2b — Crypto:**
```
Инвойс User #{user_id}
790 ₽ ≈ {usdt_amount} USDT (TRC20) · или {ton_amount} TON

USDT (TRC20): {wallet_usdt}
TON: {wallet_ton}
В комментарии к переводу: RL{user_id}

[ ✅ Проверить оплату ]
[ 📋 Скопировать адрес USDT ]
[ 📋 Скопировать адрес TON  ]

v1 note: «Оплата через MetaMask — скопируй адрес вручную. Авто-открытие — позже.»
```

**Экран 2c — Stars:** KEEP текущий Stars-flow (O29) без изменений.

#### D7 — `/cabinet/` блок подписки (P1) · O107 Trial

**Free state (NEW):**
```
┌──────────────────────────────────────────────────────┐
│  RawLead Premium                                     │
│  790 ₽/мес · или 300 ⭐ Stars   (muted 14px)        │
│                                                      │
│  [ Попробовать 3 дня бесплатно ]  ← primary CTA     │
│  [ Подключить Premium →        ]  ← secondary ghost  │
└──────────────────────────────────────────────────────┘
```

**Trial active state:**
```
┌──────────────────────────────────────────────────────┐
│  RawLead Premium        [Trial · N дн. осталось]    │
│  Premium активен до {date}                          │
│  [ Оплатить 790 ₽ → ]    [ Пауза ]                  │
└──────────────────────────────────────────────────────┘
```

**Paid active (обновить copy):**
```
┌──────────────────────────────────────────────────────┐
│  RawLead Premium                       [PREMIUM]    │
│  ✅ Premium активен до {date}                       │
│  [ Пауза ]   [ Оплата ]                             │
└──────────────────────────────────────────────────────┘
```

---

## § O96-D — UX pass всех страниц (**✅ ф2 2026-06-02 · → @coder**)

**Владелец 2026-06-02:** задача **Lead Designer**, не `@designer`. Фаза 1 — **совет с владельцем**, без новых docs.

### Контекст

| # | Артефакт |
|---|----------|
| 1 | Copy-канон **O96-Z1–Z13** — [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § O96 |
| 2 | Playwright prod — [`data/o96_design_survey.md`](../../data/o96_design_survey.md) · скрины `data/o96_design_survey/` |
| 3 | Перезапуск: `.venv\Scripts\python.exe scripts\preprod_playwright\o96_design_survey.py` |

### Scope (владелец)

| # | Задача |
|---|--------|
| d1 | Все страницы desktop 1440 + mobile 390 |
| d2 | **Карточка** — меньше «навалено» · **категория/ниша** на карточке |
| d3 | **O97-w2** — badge сложности (copy O96-Z11, концепт 2) |
| d4 | **O98-w** — Skill Tree 2–3 концепта (после OK карточки) |
| d5 | Design tests / чеклист flows |

### Фаза 1 (**✅ 2026-06-02** · владелец принял)

| Решение | Принято |
|---------|---------|
| Anon CTA — убрать с карточки → один strip над лентой | ✅ |
| Ниша — только иконка (`</>` · `✦` · `◎` · `Aa`) рядом с source, без текста | ✅ |
| O97 badge — только для залогиненных, под breakdown row | ✅ |
| Skill Tree — полный Z4 (§4.5–4.7 + copy §4.10) | ✅ |
| Mobile filter bar — category chips в этот pass | ✅ |
| Карточка единая: лента = кабинет = главная (структура залогиненного) | ✅ |
| Главная flow/live preview — mock данные остаются, структура карточки обновляется | ✅ |
| Анимация главной — не трогать (работает корректно) | ✅ |

### Фаза 2 (**✅ спеки 2026-06-02** · → @lead-architect → @coder)

Спеки написаны в `feed-cabinet-mvp.md`:
- **§4.8** — Новая карточка (иконка ниши + убрать anon CTA + O97 badge)
- **§4.9** — Anon strip
- **§4.10** — Skill Tree Z4 copy-канон
- **§7.7** — Mobile filter bar: category chips

---

## § D-O81 — Лендинг: «Один поток вместо десяти вкладок» (**✅ Design 2026-06-01 · → @coder § O81-w1**)

**Владелец 2026-06-01:** посадочная **непонятна** · блок `flow.php` — сейчас **демо-карточка заказа**, не объясняет продукт.

**Суть продукта (copy):** FL · Kwork · TG · **+ скоро** YouDo · Freelance.ru · FreelanceJob · Пчёл.нет — **один поток**, ИИ фильтр + отклик.

| # | Задача Design | Статус |
|---|---------------|--------|
| d1 | **Заменить** demo `rl-lead-card` в секции flow — анимированная иллюстрация «N вкладок → 1 лента RawLead» | ✅ |
| d2 | Chip-иконки источников (нейтрально, textual + dot) | ✅ |
| d3 | Связка с hero: продукт понятен за 10 сек | ✅ |
| d4 | REFERENCE §3.3 · NEO tokens · mobile 390px | ✅ |
| d5 | Handoff `@coder` § **O81-w1** | ✅ |

**Прототип:** `canvases/d081-flow-section.canvas.tsx` (v9 · принят владельцем 2026-06-01)

**Handoff → Coder: § O81-w1 ниже**

---

## § O81-w1 — Coder: анимация flow-секции на лендинге

**Основание:** § D-O81 Design принят · канвас v9 · владелец «принимаю»  
**Приоритет:** P1  
**Файлы для изменения:**

```
wordpress/rawlead-kadence-child/template-parts/rawlead/flow.php    ← заменить demo-карточку
wordpress/rawlead-kadence-child/assets/css/rawlead.css              ← новые @keyframes + классы
wordpress/rawlead-kadence-child/assets/js/rawlead-flow.js           ← новый файл (animation controller)
wordpress/rawlead-kadence-child/functions.php                       ← enqueue rawlead-flow.js
```

### Визуальная концепция

Биржи (5 chip) **поочерёдно** влетают в логотип с разных сторон → каждый удар **раздувает** логотип (+5% scale) → после всех ударов логотип **заряжается** (~630 мс: дрожит + жёлтое свечение) → **выстреливает 3 карточки** поочерёдно (stagger 380ms), на каждый выстрел — **отдача** (kick-back scale) + логотип постепенно сдувается обратно до 1.0 → **логотип остаётся**.

**Анимация запускается один раз** — через IntersectionObserver при входе секции в viewport (threshold 0.35). Авто-повтор на сайте **не используется**.

### HTML-структура секции

```html
<section class="rl-flow-anim" aria-label="Как работает RawLead">
  <div class="rl-container rl-flow-anim__inner">

    <!-- Левая часть: логотип — 3 слоя анимации -->
    <div class="rl-flow-anim__logo-wrap" id="rl-flow-logo">
      <!-- Слой 1: накопительный scale (JS управляет через style.transform) -->
      <div class="rl-flow-logo__scale">
        <!-- Слой 2: impact shake при поглощении чипа (JS добавляет/убирает is-impact) -->
        <div class="rl-flow-logo__shake">
          <!-- Слой 3: зарядка (.is-charging) или отдача (.is-recoil) -->
          <div class="rl-flow-logo__reaction">
            <a href="/" class="rl-logo rl-flow-anim__logo">
              <span class="rl-logo__icon"><?php echo file_get_contents(RAWLEAD_CHILD_DIR.'/assets/images/wave2-mark-radar-v1.svg'); ?></span>
              <span class="rl-logo__text-block">
                <span class="rl-logo__name">RawLead</span>
                <span class="rl-logo__by">by Rode51</span>
              </span>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Чипы источников (абсолютные, позиционируются JS) -->
    <div class="rl-flow-anim__chips" aria-hidden="true">
      <div class="rl-flow-chip" data-source="fl"           data-dx="-440" data-dy="5"    data-ms="0"  >
        <span class="rl-flow-chip__dot" style="background:#00A65A"></span>FL.ru
      </div>
      <div class="rl-flow-chip" data-source="kwork"        data-dx="465"  data-dy="-55"  data-ms="200">
        <span class="rl-flow-chip__dot" style="background:#EA580C"></span>Kwork
      </div>
      <div class="rl-flow-chip" data-source="tg"           data-dx="15"   data-dy="-292" data-ms="400">
        <span class="rl-flow-chip__dot" style="background:#0088CC"></span>Telegram
      </div>
      <div class="rl-flow-chip" data-source="youdo"        data-dx="-385" data-dy="228"  data-ms="600">
        <span class="rl-flow-chip__dot" style="background:#2563EB"></span>YouDo
      </div>
      <div class="rl-flow-chip" data-source="freelance_ru" data-dx="455"  data-dy="215"  data-ms="800">
        <span class="rl-flow-chip__dot" style="background:#7C3AED"></span>Freelance.ru
      </div>
    </div>

    <!-- Ripple-вспышки (по одной на чип, JS создаёт динамически) -->

    <!-- Правая часть: выходные карточки -->
    <div class="rl-flow-anim__cards" aria-hidden="true">
      <!-- 3 карточки rl-lead-card — точно по спеке /lenta/ -->
      <!-- см. структуру ниже -->
    </div>

  </div>
</section>
```

### CSS-классы и анимации

```css
/* Idle: radar пульсирует до запуска */
@keyframes rl-flow-idle {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.48; }
}

/* ──────────────────────────────────────────────────────────────────────────
   ЛОГОТИП — 3 независимых слоя, каждый на своём div.

   СЛОЙ 1 (data-layer="scale") — накапливает mass:
     scale управляется JS через element.style.transform = scale(N).
     Каждое изменение CSS transition 260ms cubic-bezier(0.17,0,0,1.30)
     (slight overshoot → пружинный «хлопок» вверх при поглощении чипа,
      и «недолёт» вниз при выстреле — ощущается как kick).

   СЛОЙ 2 (data-layer="shake") — удар при попадании чипа:
     JS добавляет/убирает класс .is-impact для каждого попадания.

   СЛОЙ 3 (data-layer="reaction") — заряд или отдача:
     .is-charging — до выстрела (вибрация + жёлтое свечение).
     .is-recoil  — при каждом выстреле (gun kick).
   ────────────────────────────────────────────────────────────────────────── */

/* Слой 2: удар при поглощении чипа */
@keyframes rl-flow-impact {
  0%   { transform: translate(0,0) scale(1.00); }
  16%  { transform: translate(-3px,-2px) scale(1.09); }
  38%  { transform: translate(2px, 1px) scale(0.94); }
  62%  { transform: translate(-1px, 2px) scale(1.03); }
  85%  { transform: translate(1px,-1px) scale(0.99); }
  100% { transform: translate(0,0) scale(1.00); }
}
.rl-flow-logo__shake.is-impact {
  animation: rl-flow-impact 300ms cubic-bezier(0.36,0.07,0.19,0.97) forwards;
}

/* Слой 3A: зарядка (~630ms между последним чипом и первым выстрелом) */
@keyframes rl-flow-charging {
  0%   { transform: translate(0,0);       filter: drop-shadow(0 0 3px rgba(250,204,21,0.70)); }
  25%  { transform: translate(-2px, 1px); filter: drop-shadow(0 0 8px rgba(250,204,21,1.00)); }
  50%  { transform: translate(2px,-1px);  filter: drop-shadow(0 0 5px rgba(250,204,21,0.85)); }
  75%  { transform: translate(-1px, 2px); filter: drop-shadow(0 0 10px rgba(250,204,21,1.00)); }
  100% { transform: translate(0,0);       filter: drop-shadow(0 0 3px rgba(250,204,21,0.70)); }
}
.rl-flow-logo__reaction.is-charging {
  animation: rl-flow-charging 140ms ease-in-out infinite;
}

/* Слой 3B: отдача при каждом выстреле карточкой */
@keyframes rl-flow-recoil {
  0%   { transform: translate(0,0) scale(1.00); }
  14%  { transform: translate(5px, 2px) scale(0.88); }
  32%  { transform: translate(-3px,-1px) scale(1.05); }
  56%  { transform: translate(1px, 1px) scale(0.98); }
  80%  { transform: translate(-1px, 0) scale(1.01); }
  100% { transform: translate(0,0) scale(1.00); }
}
.rl-flow-logo__reaction.is-recoil {
  animation: rl-flow-recoil 370ms cubic-bezier(0.36,0.07,0.19,0.97) forwards;
}

/* Ripple-вспышка на лого при поглощении чипа */
@keyframes rl-flow-ripple {
  0%   { transform: scale(0.12); opacity: 1.00; }
  60%  { transform: scale(2.20); opacity: 0.45; }
  100% { transform: scale(3.90); opacity: 0;    }
}

.rl-flow-anim__logo-wrap {
  transform-origin: center center;
}
/* Слой 1: scale задаётся JS */
.rl-flow-logo__scale {
  transition: transform 260ms cubic-bezier(0.17,0,0,1.30);
  transform-origin: center center;
}
.rl-flow-anim__logo-wrap .rl-logo__icon svg.is-idle {
  animation: rl-flow-idle 2.8s ease-in-out infinite;
}

/* Чип */
.rl-flow-chip {
  position: absolute;
  display: inline-flex; align-items: center; gap: 7px;
  padding: 7px 13px;
  background: #fff;
  border: 2px solid #0A0A0A;
  border-radius: 2px;
  font-family: var(--rl-font); font-size: 13px; font-weight: 700;
  white-space: nowrap;
  /* box-shadow задаётся инлайн через JS (цвет источника) */
  transform-origin: center center; /* JS repositions element so center = logo center */
  /* Начальное состояние: translate(dx, dy) scale(1) — задаётся JS */
}
.rl-flow-chip__dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}

/* Ripple */
.rl-flow-ripple {
  position: absolute;
  width: 40px; height: 40px;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0;
  /* border-color задаётся JS; left/top = logo_cx-20, logo_cy-20 */
}
.rl-flow-ripple.is-running {
  animation: rl-flow-ripple 450ms ease-out forwards;
}

/* Карточки */
.rl-flow-anim__card {
  /* стандартный rl-lead-card */
  background: #fff;
  border-radius: 4px;
  border: none;
  box-shadow: 4px 4px 0 #0A0A0A;
  padding: 20px 24px;
  /* Начало: translate(flyDx, flyDy) scale(0) */
  /* В конце: translate(0,0) scale(1) · transition 520ms cubic-bezier(0.15,0,0,1.12) */
}
.rl-flow-anim__card--perfect {
  border: 2px solid #FACC15;
  box-shadow: 4px 4px 0 #FACC15;
}
```

### JS: `rawlead-flow.js`

**Ответственность:** IntersectionObserver → **однократный** запуск (unobserve после старта) · session guard · 3-слойная физика логотипа · prefersReducedMotion bypass

```js
// Псевдокод логики — полную реализацию Coder пишет сам по этой спеке

var CHIPS = [
  { id:'fl',           color:'#00A65A', dx:-440, dy:5,    ms:0,   rot:'5deg'  },
  { id:'kwork',        color:'#EA580C', dx:465,  dy:-55,  ms:210, rot:'-8deg' },
  { id:'tg',           color:'#0088CC', dx:15,   dy:-292, ms:420, rot:'3deg'  },
  { id:'youdo',        color:'#2563EB', dx:-385, dy:228,  ms:630, rot:'-5deg' },
  { id:'freelance_ru', color:'#7C3AED', dx:455,  dy:215,  ms:840, rot:'7deg'  },
];

var CARDS = [
  { src:'FL.ru',  color:'#00A65A', title:'Telegram-бот для автоматизации заявок', budget:'Бюджет: 25 000 ₽', match:87, perfect:true,  flyDelay:0   },
  { src:'Kwork',  color:'#EA580C', title:'Парсер маркетплейсов на Python',         budget:'Бюджет: 15 000 ₽', match:73, perfect:false, flyDelay:380 },
  { src:'TG',     color:'#0088CC', title:'Лендинг для SaaS-продукта на WP',        budget:'Бюджет: 40 000 ₽', match:61, perfect:false, flyDelay:760 },
];

// Геометрия: LOGO_CX / LOGO_CY = getBoundingClientRect() логотипа (center)
// Chip wrapper: position absolute; left = LOGO_CX-65; top = LOGO_CY-19; w=130; h=38
// Chip начальный state: CSS custom props --dx, --dy, --rot, --ms → @keyframes rl-flow-chip-fly
// Impact момент = 75% от 920ms полёта = 690ms после старта чипа → t = 100 + chip.ms + 690

// === LOGO SCALE (слой 1) ===
// logoScale = 1 + min(impactCount, 5) * 0.052  — растёт при поглощении
//           - min(recoilCount,  3) * 0.088  — сдувается при выстреле
// logoScaleEl.style.transform = `scale(${logoScale})`  ← transition 260ms обработает плавно

// === Timeline (все t от старта IntersectionObserver callback) ===
//   t=100:    фаза 1 — запустить чипы (@keyframes rl-flow-chip-fly с CSS vars)
//
//   t=790:    chip[0] impact → impactCount++ → logoScale → убрать/добавить is-impact на .shake
//   t=1000:   chip[1] impact → то же
//   t=1210:   chip[2] impact → то же
//   t=1420:   chip[3] impact → то же
//   t=1630:   chip[4] impact → то же (logoScale достиг 1.26)
//
//   t=1640:   CHARGING — добавить .is-charging на .reaction
//             Лого вибрирует + жёлтое свечение (~630ms, до выстрела)
//
//   t=2270:   ВЫСТРЕЛ — убрать .is-charging
//             фаза 2: card[0] fly-out
//             recoilCount=1 → logoScale=1.173 → добавить .is-recoil (JS убирает после 370ms)
//   t=2650:   card[1] fly-out
//             recoilCount=2 → logoScale=1.085 → новый .is-recoil
//   t=3030:   card[2] fly-out
//             recoilCount=3 → logoScale≈1.000 → новый .is-recoil
//
//   t=3250:   фаза 3 — бары fill 0→N% (transition 640ms ease-out)
//
//   !! АВТОПОВТОР НА САЙТЕ НЕ ИСПОЛЬЗУЕТСЯ !!
//   IntersectionObserver делает unobserve() после первого запуска.

// === prefersReducedMotion ===
// if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
//   показать финальное состояние сразу (no animation), logoScale=1, bars filled
// }

// === Запуск ===
var io = new IntersectionObserver(function(entries) {
  entries.forEach(function(entry) {
    if (entry.isIntersecting) {
      io.unobserve(entry.target);  // однократно
      startFlowAnimation();
    }
  });
}, { threshold: 0.35 });
io.observe(document.querySelector('.rl-flow-anim'));
```

### Карточка `/lenta/` — точная структура

```html
<article class="rl-lead-card rl-flow-anim__card [rl-flow-anim__card--perfect]">
  <div class="rl-feed-card__head">
    <div class="rl-feed-card__head-start">
      <span class="rl-feed-card__source rl-feed-card__source--[fl|kwork|tg]">
        FL.ru <!-- dot задаётся CSS ::before -->
      </span>
      <!-- только для perfect: -->
      <span class="rl-badge rl-badge--perfect">ИДЕАЛЬНО ✦</span>
    </div>
  </div>
  <h3 class="rl-lead-card__title">Telegram-бот для автоматизации заявок</h3>
  <p class="rl-lead-card__budget">Бюджет: 25 000 ₽</p>
  <div class="rl-match">
    <div class="rl-match__label"><span>Совместимость 87%</span></div>
    <div class="rl-match__bar">
      <span class="rl-match__fill" style="--match-value:0%"></span>
      <!-- JS: --match-value: 0% → 87% при phase=3 (transition width 640ms ease-out) -->
    </div>
  </div>
</article>
```

### Тайминги (итог)

| Событие | Время от replay() |
|---------|-------------------|
| Idle-пульс SVG | немедленно (phase=0) |
| Чип 1 (FL.ru) | 100ms |
| Чип 2 (Kwork) | 300ms |
| Чип 3 (Telegram) | 500ms |
| Чип 4 (YouDo) | 700ms |
| Чип 5 (Freelance.ru) | 900ms |
| Последний чип поглощён | ~1600ms |
| Лого пик взрыва | ~1750ms |
| Карточка 1 (FL.ru) | 1700ms |
| Карточка 2 (Kwork) | 2080ms |
| Карточка 3 (TG) | 2460ms |
| Бары заполняются | 2620ms |
| Авто-повтор | 6620ms |

### Acceptance checklist (Coder)

- [ ] Секция запускается через IntersectionObserver (threshold 0.35)
- [ ] `prefers-reduced-motion`: финальное состояние без анимации, немедленно
- [ ] Mobile 390px: logo area height 152px · **карточки вылетают из логотипа** (fly-out, как desktop) · **не** просто fade/slide-up
- [ ] Логотип остаётся видимым после взрыва (opacity:1 всегда)
- [ ] Карточки: точная структура rl-lead-card как в `/lenta/` (source dot, budget, match bar)
- [ ] Ripple-вспышки: цвет источника, 5 штук, синхронизированы с chip.ms+680
- [ ] Session guard: повторный вход в viewport не стекует таймеры
- [ ] Нет console.error в DevTools

---

## § D-O82 — Match breakdown на карточке (**✅ Lead Design 2026-06-01 · → @coder § O82-w1**)

**Владелец 2026-06-01:** «Совместимость N%» **не moat** — нужна **прозрачность** как в [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §5.

| # | Задача | Статус |
|---|--------|--------|
| d1 | Полоска + 1 строка breakdown (не три одинаковые полоски) | ✅ |
| d2 | Zero state: нет навыков → «Качество заказа» + CTA «Добавь навыки →»; НЕ «0%» | ✅ |
| d3 | Microcopy: tooltip «Качество × 60% + Навыки × 40%» | ✅ |
| d4 | Mobile 390px: «ИДЕАЛЬНО ✦» в match row (заменяет AI-чип), не в meta-строке | ✅ |
| d5 | Handoff `@coder` § **O82-w1** · `REFERENCE.md` §4 + `feed-cabinet-mvp.md` §3.1 | ✅ |

**Спека:** [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §3.1 · [`REFERENCE.md`](../../design/wp/REFERENCE.md) §4  
**Handoff:** [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § **O82-w1**  
**Accept:** владелец 3 карточки — «понятно, не обман» · Coder acceptance checklist в § O82-w1.

---

## § D-O82b — Match карточка v2 (**⏸ после D-O81** · владелец 2026-06-01)

**Gate:** Designer **сначала** закрывает **§ D-O81** · **не** начинать D-O82b, пока владелец не скажет «D-O81 готово» или Lead не снимет gate.

**Кontекст:** O82-w1 Coder **не нравится владельцу** · ушли от идеи «Брать/Сомнительно» на карточке — у каждого свои навыки и своё видение.

**Продукт (канон владельца):**

| Было (w1) | Стало (w1b) |
|-----------|-------------|
| «Качество заказа» + `ai_score` на полоске | **Только «Совместимость»** = насколько **стек/навыки человека** подходят к заказу (`keyword_match`) |
| Чип «Брать ✓» / «Сомнительно» в match row | **Убрать** с публичной карточки (verdict — внутренний L1, не UI ленты) |
| «Добавь навыки…» при любых пустых навыках | **Только:** anon **и** навыки в фильтре **не выбраны** · если фильтр/навыки уже стоят — **не** показывать |
| Breakdown «Качество: N · Навыки: M%» | Breakdown **про совпадение:** напр. «Совпало N из M навыков заказа» или список совпавших тегов (Design решает) |

**Задачи Design:**

| # | Задача |
|---|--------|
| b1 | Перерисовать match-row **без** AI-verdict chip · визуально проще (owner: «карточки не нравятся») |
| b2 | Режим **anon, 0 навыков:** CTA «Добавь навыки…» → sheet «Навыки» · **без** % или нейтральная подсказка |
| b3 | Режим **навыки выбраны** (guest или ЛК): **% совместимости** + breakdown совпадений · **без** «Качество заказа» |
| b4 | `ai_score` / `final_rank` — **не** показывать пользователю на карточке (можно оставить sort=match на бэке) |
| b5 | Handoff `@coder` § **O82-w1b** · правки `REFERENCE.md` §4 · `feed-cabinet-mvp.md` §3.1 |

**Не в scope:** менять L1 verdict в боте · убирать `ai_score` из Neon.

---

**Вход:** `data/preprod_ux_audit_human.md` + JSON + скрины `data/preprod_ux_audit/`.

**Задача Lead Designer:** разложить LLM + robot findings на **P0 / P1 / P2** · записать сюда таблицу · handoff `@coder` § **WAVE-UX-FIX**.

| P | Критерий | Пример |
|---|----------|--------|
| **P0** | Нельзя пользоваться на 390px: не жмётся, не закрывается, 5xx, CTA мёртвый | sheet без tap-outside |
| **P1** | Работает, но бесит: мелкий tap, перекрытие, непонятно куда жать | sticky «Применить» под fold |
| **P2** | Косметика · после S6 | отступы, типографика |

**Шаблон (O37c прогон 2026-05-30):**

| ID | Finding | P | Fix hint |
|----|---------|---|----------|
| **W1** | U3/U8 mobile: `#rl-feed-sheet` не открывается (hidden) | **P0** | `rawlead-feed.js` — openBtn/sidebar/sheetBody; CSS `[hidden]` |
| **W2** | U4 mobile+desktop: tap outside не сворачивает карточку | **P0** | `rawlead-feed.js` click overlay / document |
| **W3** | U7 mobile+desktop: modal навыков ЛК — overlay не закрывает | **P0** | `rawlead-cabinet.js` + overlay handler |
| **W4** | U10 ERR_ABORTED feed/subscription | **P2** | ложный critical скрипта (U2/U5 OK) — игнор `net::ERR_ABORTED` в audit |

**LLM rating:** 1/5 · совпадает с владельцем («моб кривой»).

---

## § D-O40 — Mobile rebuild feed + ЛК (**→ @lead-designer · владелец 2026-05-30**)

**Решение владельца:** не точечные патчи — **полная пересборка mobile** (390×844).

**Тикет:** [`problems/2026-05-30-mobile-ux-owner-review.md`](../../problems/2026-05-30-mobile-ux-owner-review.md)

| ID | Finding | P | Design direction |
|----|---------|---|------------------|
| **M1** | Карточки не влезают (feed + ЛК) | **P0** | Ширина/padding как **hero live preview** на главной · `box-sizing` · без horizontal overflow |
| **M2** | Header пересекается с category bar | **P0** | Mobile header: **burger** · скрыть desktop nav links · sticky stack без overlap |
| **M3** | Фильтры неудобные | **P0** | **Один bottom sheet** «Фильтры»: категории + навыки + сортировка + [Применить] — см. `feed-cabinet-mvp.md` §7.2 |
| **M4** | Tap-outside, modal ЛК | **P0** | Overlay закрывает · карточка collapse · канон §7 |
| **M5** | Audit W1 sheet не открывается | **P0** | JS `#rl-feed-filters-open` → `#rl-feed-sheet` |

**Deliverable Design:** ✅ **Lead verify 2026-05-30** — `feed-cabinet-mvp.md` §7.6 · `DESIGNER_PROMPT.md` § WAVE-UX-MOBILE (M1–M5 + m1–m11).

**→ @coder** § **WAVE-UX-MOBILE** · desktop **не трогать** (≥768px).

---

## § D-O39 — Design canon sync (**✅ закрыт 2026-05-29**)

**Решение владельца:** дизайн **принимаем как на prod** (v1.10.9) · **не менять UI** · только docs.

| # | Статус |
|---|--------|
| d1 | **`feed-cabinet-mvp.md` §2–3** — Lead sync под NEO/prod |
| d2 | **`REFERENCE.md` §1, §4** — карточка: shadow-only + perfect-match жёлтый |
| d3 | `wave-2-css-brief.md` — канон = REFERENCE (без правок кода) |

**→ @lead-designer не нужен** для D-O39.

---

## § WAVE-4-UX-FIX — согласовано владельцем 2026-05-29 (**backlog после O59**)

**Статус:** ✅ согласовано · → @coder через Lead Architect
**Дата:** 2026-05-29
**Бриф для Coder:** `DESIGNER_PROMPT.md` § WAVE-4-UX-FIX

### Контекст (ЦА и голос)

**Аудитория:** фрилансеры 25–35, микс (dev-heavy → 60–65% мужчины, но дизайн/тексты/маркетинг — значимая женская доля). Работают в Telegram и с телефона. Ценят конкретику, не любят корпоративщину. Сленг понимают, но не обязателен.

**Стиль текста:** «Лиды без шума» — коротко, прямо, с характером. Никаких «пожалуйста» и «уважаемый(ая)».

**Правило рода:** `ты` остаётся. **Запрещены** глаголы прошедшего времени с родовым согласованием: `вошёл/вошла`, `нажал/нажала`, `добавил/добавила` → заменяем на нейтральные конструкции (инфинитивы, существительные, настоящее время).

### Решения (не менять без нового слова владельца)

| # | Проблема | Решение |
|---|---------|---------|
| V1 | Карточки ЛК — тонкие строки, не карточки | Полная карточка = та же структура что в ленте + черновик ИИ + `[✕ Удалить]` |
| V2 | «Загрузить ещё» висит даже когда всё загружено | Кнопка скрыта если `shown >= total` |
| V3 | «Загружаем ещё заказы...» висит всегда | Spinner/текст — только в состоянии loading (после клика, до ответа API) |
| V4 | /lenta/ header без полной навигации | Добавить `Тарифы · Как устроено` на все страницы (кроме `/cabinet/` — там уже есть) |
| V5 | Нет кнопки поддержки | FAB bottom-right на всех страницах → открывает inline chat-модалку (UI: textarea + кнопка «Отправить»; backend — placeholder, задача Coder отдельно) |
| V6 | Тексты — мужской род / нейтральные | Полный список замен в `DESIGNER_PROMPT.md` § WAVE-4-COPY |
| V7 | Мало интерактива | Skeleton-loading при первой загрузке; press-анимация кнопок; stagger для новых карточек после «Загрузить ещё» |

### Конвейер

| Этап | Кто | Статус |
|------|-----|--------|
| Решения + бриф | @lead-designer | ✅ 2026-05-29 |
| Спека в DESIGNER_PROMPT | @lead-designer | ✅ 2026-05-29 |
| CODER_PROMPT + deploy | @lead-architect → @coder | **✅ prod 2026-05-29** |

---

## § DESIGN-WAVE-3 / O41 — Gumroad hero (**✅ prod 2026-05-29 · АРХИВ**)

**Дата:** 2026-05-29  
**Статус:** ✅ **Lead Designer — docs сданы** · → @lead-architect → @coder

**Факт:** владелец видит Wave 2 на prod и говорит «это не тотальная пересборка». Цель: **gumroad.com** — максимально приблизиться к этому уровню качества.

**Конкретные проблемы (скрин 2026-05-29):**

| # | Проблема | Что сделать |
|---|---------|------------|
| 1 | **Белая карточка на жёлтом** hero-фоне | → добавить order: 2px solid #0A0A0A + ox-shadow: 4px 4px 0 #0A0A0A или убрать из hero вовсе |
| 2 | **H1 не обновлён** — «Заказы под твой стек» вместо «Лиды без шума» | выяснить: не применено в Coder или нет в REFERENCE — в любом случае зафиксировать |
| 3 | **Secondary CTA** («Вход в ЛК» / «Тарифы ↓») выглядят слабо | специфицировать стиль: ghost-кнопка с order: 2px solid #0A0A0A или простой link-underline |
| 4 | **Общее** — косметика поверх старого, не пересборка | описать, что конкретно отличает RawLead от Gumroad-уровня |

**Решения зафиксированы (2026-05-29):**

| # | Проблема | Решение Lead |
|---|---------|-------------|
| 1 | **Белая карточка на жёлтом** | Hero = только текст+CTA. Live Preview = отдельная белая секция ниже с `border-top: 4px solid #0A0A0A`. Карточки: `border: 2px solid #0A0A0A` + `box-shadow: 4px 4px 0 #0A0A0A` |
| 2 | **H1 не обновлён** | Канон = «Лиды без шума». Если иное — баг Coder. @coder: проверить `hero.php` |
| 3 | **Secondary CTA слабая** | neo-brutalist secondary: `bg transparent` + `border: 2px solid #0A0A0A`; hover: `bg #0A0A0A` + `color #FACC15` |
| 4 | **Общее** | Gumroad-принцип: каждая секция делает ОДНО. Hero = H1+sub+CTA. Preview = отдельный белый блок |

**Документы обновлены (2026-05-29):**

| Файл | Что изменено |
|------|-------------|
| [`REFERENCE.md`](../../design/wp/REFERENCE.md) **§3.2** | Hero = pure text zone. Live Preview = отдельная секция. Secondary CTA spec |
| [`wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) **§ w3-delta-O41** | CSS delta: hero split, secondary CTA, H1 verify, breathing room |
| [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) **§ O41-WAVE3** | Handoff @coder: файлы, задачи O41-1–5, приёмка |

**Конвейер O41:**

| Этап | Кто | Статус |
|------|-----|--------|
| 1 — Анализ + решения | @lead-designer | ✅ 2026-05-29 |
| 2 — REFERENCE §3.2 + wave-2-css-brief delta | @lead-designer | ✅ 2026-05-29 |
| 3 — § O41-WAVE3 в DESIGNER_PROMPT | @lead-designer | ✅ 2026-05-29 |
| 4 — Тема + deploy | @coder + Lead ops | **✅ WAVE-4 prod 2026-05-29** |

## § DESIGN-WAVE-2 — полный план (зафиксировано 2026-05-29)

**Решение владельца:** полное переосмысление UI/UX — не патч поверх Wave 1.
**Источники инспирации:** [gumroad.com](https://gumroad.com) · [feastables.com](https://feastables.com) · [99percentoffsale.com](https://www.99percentoffsale.com) · [retroui.dev](https://retroui.dev)

### Конвейер

| Этап | Кто | Выход | Статус |
|------|-----|-------|--------|
| 1 | `@lead-designer` | Все решения + Recraft концепты | ✅ этот файл |
| 2 | `@lead-designer` | `REFERENCE.md` v5 · `DESIGN_SYSTEM.md` обновление | → после Designer |
| 3 | `@designer` | CSS-спека → [`wave-2-css-brief.md`](../../design/wp/wave-2-css-brief.md) | ✅ 2026-05-29 |
| 4 | `@lead-designer` | ревью brief + REFERENCE v5 | ✅ 2026-05-29 |
| 5 | `@coder` | theme + deploy | **✅** v1.9.0 prod 2026-05-29 |

---

### Решения владельца (финал, не менять без нового слова)

| # | Параметр | Решение |
|---|----------|---------|
| W1 | **Стиль** | NEO-BRUTALIST остаётся (жёлтый hero, чёрные рамки, плоские тени, Manrope) — оживляем анимациями, не меняем язык |
| W2 | **Анимации scroll** | Театральные — элементы «влетают» при входе в viewport (stagger, slide-in с разных направлений, 300–400ms ease-out) |
| W3 | **Анимации hover/click** | Тактильные — быстрые (80–120ms), физичные (shadow растёт, кнопка «нажимается», карточка сдвигается) |
| W4 | **100% совпадение** | Карточка «взрывается»: пульс-кольцо при появлении + жёлтый glow + бейдж «Идеально ✦» |
| W5 | **Match-бар** | Анимированное заполнение при входе в viewport (0% → N%, 600ms ease-out) |
| W6 | **Пагинация** | Кнопка «Загрузить ещё →» вместо infinite scroll |
| W7 | **Баланс** | 50/50 удовольствие / инструмент |
| W8 | **«by Rode51»** | Footer: `RawLead · by Rode51` (muted, 12px) · Header: рядом с лого `by Rode51` (11px, 40% opacity) |
| W9 | **Марка** | Radar-сигнал (3 дуги из угла) — для favicon/TG-аватара · текстовый лого «RawLead» Manrope 900 остаётся |
| W10 | **Иконки категорий** | `</>` dev · `✦` design · мегафон marketing · `Aa` text — единый stroke 2px |
| W11 | **Hero-фон** | Геометрические чёрные фигуры по краям/углам hero-секции — не перекрывают текст |
| W12 | **Карточка лида** | Заголовок + источник badge + бюджет + match-бар (animated) + % совпадения + eye+число просмотров + чипы «Брать»/«Сомнительно» |
| W13 | **Старый дизайн** | Кубики FL/Kwork/TG, белые мягкие карточки — удалить полностью |
| W14 | **Ценник** | **300 ⭐ Telegram Stars / мес** (не 590 ₽) — везде на сайте |
| W15 | **Announcement bar** | Чёрная полоска над шапкой: «Радар онлайн · 800+ лидов в неделю [Смотреть ленту →]» · bg `#0A0A0A` · 38px · Manrope 600 · CTA жёлтый — только лендинг |
| W16 | **Навигация** | `[◎ RawLead by Rode51]  Лента · Тарифы · Как устроено  [Войти →]` · убрать «Контакты» из primary nav · items Manrope 700 13px uppercase letter-spacing 0.08em · active: underline 2px solid #0A0A0A · «Войти →» вместо «Войти в кабинет» |
| W17 | **`/pricing/`** | Полноценная страница: H1 на жёлтом + таблица 2 колонки (Бесплатно vs ИИ-агент: Скорость / Отклики / Push TG / Цена 300 ⭐) + CTA `[Подключить — 300 ⭐ →]` |
| W18 | **`/how/`** | 3 горизонтальных шага вместо 4 карточек 2×2: «Биржи в потоке / ИИ убирает мусор / Ты видишь первым» — одна строка под каждым, без абстракций |
| W19 | **`/contact/`** | Убрать форму CF7; только `[Написать в Telegram →]` + email строчкой muted |

---

### Recraft-ассеты (концепты сгенерированы 2026-05-29)

| Файл | Описание | Статус |
|------|----------|--------|
| `docs/design/assets/rawlead-mark-concept.png` | Radar-марка (3 дуги) — концепт | ✅ |
| `docs/design/assets/rawlead-hero-bg-concept.png` | Hero geo-паттерн чёрный/жёлтый — концепт | ✅ |
| `docs/design/assets/rawlead-category-icons-concept.png` | 4 иконки категорий в сетке — концепт | ✅ |

**Production SVG** — генерить в [recraft.ai](https://recraft.ai) по промптам:

```
Марка (favicon):
"Bold geometric radar signal mark, 3 concentric quarter-circle arcs from bottom-left corner,
flat black vector, SVG, no text, favicon-safe, neo-brutalist"
style: Vector art, model: recraftv3

Hero decoration:
"Neo-brutalist abstract geometry, bold black diagonal lines and rectangles scattered
on transparent/yellow background, flat vector SVG, no gradients, high contrast"
style: Vector art, model: recraftv3

Иконки (по одной):
"Minimal flat icon: [code brackets </> / four-pointed star / megaphone / letters Aa],
black 2px stroke, white fill, consistent with icon set, SVG"
style: Icon, model: recraftv2
```

---

### Анимации — спека (для DESIGNER_PROMPT и Coder)

#### Scroll-театральные (IntersectionObserver, unobserve after first trigger)

```css
/* Карточка — влетает снизу */
.rl-card { opacity: 0; transform: translateY(24px); }
.rl-card.is-visible {
  opacity: 1; transform: none;
  transition: opacity 320ms ease-out, transform 320ms ease-out;
}
/* Stagger: n-я карточка задерживается на n*60ms (max 5-я = 300ms) */
.rl-card:nth-child(2) { transition-delay: 60ms; }
.rl-card:nth-child(3) { transition-delay: 120ms; }
.rl-card:nth-child(4) { transition-delay: 180ms; }
.rl-card:nth-child(5) { transition-delay: 240ms; }

/* Секции лендинга — влетают с небольшим сдвигом */
.rl-section-reveal { opacity: 0; transform: translateY(16px); }
.rl-section-reveal.is-visible { opacity: 1; transform: none;
  transition: opacity 400ms ease-out, transform 400ms ease-out; }
```

#### Hover/click тактильные

```css
/* Карточка hover: тень растёт + сдвиг */
.rl-lead-card { transition: transform 120ms ease-out, box-shadow 120ms ease-out; }
.rl-lead-card:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 #0A0A0A; }

/* Кнопка press: micro-scale */
.rl-btn:active { transform: scale(0.96); transition: transform 60ms ease-out; }

/* Match-bar fill (scroll-trigger) */
.rl-match__fill { width: 0; transition: width 600ms ease-out; }
.rl-card.is-visible .rl-match__fill { width: var(--match-value); }
```

#### 100% match — «взрыв»

```css
.rl-lead-card--perfect {
  border-color: #FACC15;
  box-shadow: 4px 4px 0 #FACC15, 0 0 0 0 rgba(250,204,21,0.4);
}
.rl-lead-card--perfect.is-visible {
  animation: rl-perfect-pulse 600ms ease-out forwards;
}
@keyframes rl-perfect-pulse {
  0%   { box-shadow: 4px 4px 0 #FACC15, 0 0 0 0 rgba(250,204,21,0.6); }
  50%  { box-shadow: 4px 4px 0 #FACC15, 0 0 0 16px rgba(250,204,21,0.2); }
  100% { box-shadow: 4px 4px 0 #FACC15, 0 0 0 24px rgba(250,204,21,0); }
}
.rl-badge--perfect {
  background: #FACC15; color: #0A0A0A;
  border: 2px solid #0A0A0A;
  font-weight: 800; font-size: 11px;
  padding: 2px 8px; letter-spacing: 0.05em;
}
```

---

### Страницы — что изменится (delta от Wave 1)

| Поверхность | Что меняется |
|-------------|-------------|
| **Лендинг hero** | Geo-паттерн по краям (декоративный) · марка рядом с лого · `by Rode51` в header + footer |
| **`/lenta/`** | Карточки с scroll-stagger · match-бар animated · 100%-взрыв · кнопка «Загрузить ещё» вместо scroll · иконки категорий |
| **`/cabinet/`** | Те же анимации · inbox с тактильными hover |
| **Все страницы** | Секции влетают при скролле · hover везде тактильный |
| **Удалить** | Кубики-иллюстрация источников · «кубики собираются» анимация · белые мягкие карточки (если остались) |
| **Шапка (все страницы)** | Announcement bar (лендинг) · новые nav items W16 · «Войти →» |
| **`/pricing/`** | Полная страница W17 · ценник 300 ⭐ |
| **`/how/`** | 3 шага W18 вместо 4 карточек |
| **`/contact/`** | Убрать форму W19 · только TG |

---

### Пагинация — спека

```html
<!-- Вместо infinite scroll: -->
<div class="rl-feed-pagination">
  <button class="rl-btn rl-btn--load-more">
    Загрузить ещё <span class="rl-btn__arrow">→</span>
  </button>
  <span class="rl-feed-pagination__count">Показано 20 из 87</span>
</div>
```

```css
.rl-feed-pagination { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 32px 0; }
.rl-btn--load-more { min-width: 200px; }
.rl-feed-pagination__count { font-size: 13px; color: var(--rl-text-muted); }
```

---

### Handoff → @designer

**Задача:** CSS Wave 2 по спеке выше.
**Файл промпта:** [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § WAVE-2-CSS
**Ассеты:** `docs/design/assets/` (концепты) + Recraft SVG-промпты выше
**После:** Lead Designer ревью → brief → Lead Architect → CODER_PROMPT

---

## § DESIGN-WAVE-1 — **✅ docs сдано 2026-05-29**

**Prod:** v1.7.24 · функции приняты (O20).

| Приоритет | Задача | Файл |
|-----------|--------|------|
| **1** | NEO-BRUTALIST CSS — `rawlead.css` | [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § NEO-BRUTALIST |
| **2** | Inbox UI `/cabinet/` (не match-лента) | § **CABINET-INBOX-UI** ниже |
| **3** | Mobile-first лента + filter bar | § структура `/lenta/` ниже |
| **4** | TWO-SPEEDS UI-спека (strip, pricing) | § **TWO-SPEEDS-UI** · copy от PM |
| **5** | **C1** mobile UX polish | [`OWNER_INTENT.md`](../architect/OWNER_INTENT.md) § **C1** |

**Не в этой волне:** O11 в коде (3r) · P4b per-user draft.

**Handoff Coder:** после CSS + PM copy → Lead пишет § **PRE-LAUNCH-UX** в `CODER_PROMPT.md`.

## § NEO-BRUTALIST — финальный стиль (2026-05-28) — **✅ docs сдано**

**Выбор владельца:** Style 13 из сессии перебора стилей (2026-05-28).
**Все предыдущие решения по стилю (REFERENCE v2/v3, REVOLUTION, editorial, Unbounded, Indigo) — отменены.**

> **Актуальный канон:** [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) § NEO-BRUTALIST · [`../../design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v4 · [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) § NEO-BRUTALIST CSS

### Что меняется (REVOLUTION → NEO-BRUTALIST)

| Параметр | Было | Стало |
|----------|------|-------|
| Атмосфера | Холодный editorial B2B (Linear/Notion) | **«Рабочий инструмент»** — тёплый, прямой, для реального человека |
| Аудитория | SaaS-пользователь | Фрилансер 25–35, работает в Telegram и на телефоне |
| Фон | `#FFFFFF` холодный | **`#FAFAF8`** тёплый белый |
| Акцент | `#0A0A0A` чёрный CTA | **`#4F46E5` Indigo** — один акцент, тёплый, не «стартап синий» |
| Шрифт | Unbounded (агрессивный) + Manrope | **Только Manrope** — чистый, читаемый |
| Карточки | Жёсткая рамка `#E8E8EC` | **Мягкая тень + radius 20px** — как мессенджер-карточка |
| Mobile | Responsive к desktop | **Mobile-first** — большие зоны касания, thumb-zone |
| Навигация | Top header | **Top header** — остаётся (решение владельца) |

### Новые токены (обновить `DESIGN_SYSTEM.md` + `REFERENCE.md`)

| Token | Значение |
|-------|----------|
| `color/bg/page` | `#FAFAF8` |
| `color/bg/section` | `#F3F3EF` |
| `color/bg/inverse` | `#1A1A2E` (тёплый тёмный, не холодный `#0A0A0A`) |
| `color/cta/primary` | `#4F46E5` |
| `color/cta/primary-text` | `#FFFFFF` |
| `color/cta/primary-hover` | `#4338CA` |
| `color/text/primary` | `#18181B` |
| `color/text/body` | `#3F3F46` |
| `color/text/muted` | `#71717A` |
| `color/border` | `#E4E4E7` |
| `color/match/bar` | `#4F46E5` (один акцент) |
| `font/display` | **Manrope** 800 |
| `font/body` | **Manrope** 400–600 |
| `radius/card` | `20px` |
| `shadow/card` | `0 2px 12px rgba(0,0,0,0.07)` |
| `shadow/card-hover` | `0 8px 28px rgba(0,0,0,0.12)` |

### Структура страниц — НОВАЯ

#### 1. Лендинг `/` — продуктовый (не маркетинговый)

Фрилансер не читает features — он смотрит «а что там за заказы». Поэтому:

```
Header (sticky)
  Logo RawLead | Лента · Тарифы · Контакты | [Войти в кабинет]

Hero (viewport height mobile)
  H1: «Лиды без шума»
  Подзаголовок: «Биржи и Telegram — в одной ленте. ИИ убирает мусор до тебя.»
  CTA: [Смотреть ленту →]  (indigo pill, большой)
  
Live Preview Feed (3–4 реальных карточки из /v1/feed)
  — карточки в новом стиле, не интерактивные
  — подпись: «Последние заказы из ленты»
  — [Открыть все →] → /lenta/

Блок «Как это работает» (3 пункта, без нумерации 01-02-03)
  Биржи в одном потоке | ИИ убирает шум | Ты откликаешься сам

Один тариф — карточка ИИ-агент
  [Узнать первым →] → /contact

Footer (тёмный `#1A1A2E`)
  RawLead | Лента · Тарифы · FAQ · Контакты | Telegram
```

**Убрать:** манифест-полоса (слишком театрально), кубики-анимация источников (время не окупается), блок «Для кого» 4 карточки (заменяет live feed).

---

## § CABINET-INBOX-UI — inbox вместо ленты (**O23**)

**Канон:** Product §0j/0k · Coder § **CABINET-INBOX-O23**.

| Поверхность | Было | Стало |
|-------------|------|-------|
| **`/lenta/`** | все видят одинаково | paid: кнопка «Написать отклик»; anon strip про 15 мин |
| **`/cabinet/`** | match-лента + фильтры | **«Мои отклики»** — компактный список; **удалить**; профиль/навыки/подписка сверху |
| **Empty ЛК** | «нет match» | «Напишите отклик на ленте» |

Фильтры sort/min_match (O22) — **на `/lenta/`**, не в sidebar ЛК.

### Три состояния /cabinet/

| Состояние | UI |
|-----------|-----|
| **Anon** | редирект → TG Login (кастомная кнопка, без iframe) |
| **Free** (TG login, не paid) | навыки-чипы (collapsed) + upsell подписки + inbox locked |
| **Paid** (`is_active`) | навыки-чипы (collapsed) + статус подписки + inbox откликов |

**Inbox карточка (paid):** та же карточка что в ленте + черновик + удалить.

Структура (сверху вниз):
```
[Source badge] [Бюджет]  [ИДЕАЛЬНО ✦ — если 100%]   [✕ Удалить]
Заголовок заказа
Match-bar [N%]   👁 N просмотров
[Брать] [Сомнительно]
──────────────────────────
Черновик ИИ ▾              ← всегда раскрыт на desktop; collapsed на mobile
«Текст черновика...»
[Скопировать]
```

Состояния черновика:
- **Есть** — блок «Черновик ИИ» + текст + `[Скопировать]`
- **Нет** — строка «Черновик не сгенерирован · [Написать на ленте →]» (muted)

- `[✕ Удалить]` — top-right угол карточки; удаляет только из ЛК, не отзыв с платформы
- Статус: только дата отклика (нет «просмотрен заказчиком»)
- Empty paid: «Напишите первый отклик на ленте →»
- Empty free: «Доступно с подпиской · 300 ⭐»

---

## § C1-MOBILE-UX — Mobile UX пересбор (**2026-05-29**) ✅ согласовано

**Решение владельца:** 2026-05-28 · волна C E-polish  
**Scope:** WP-сайт на телефоне (390×844) · не Tauri-пульт, не радар  
**Канон:** NEO-BRUTALIST токены + acceptance-слой thumb-zone/sheets/viewport

### Принципы

- Все зоны касания ≥ 44px
- Sticky header 48px + sticky filter bar 44px
- Bottom sheets вместо dropdown на mobile
- Full-width CTA pill 52px
- TG Login: кастомная кнопка deep link, без iframe Telegram

### /lenta/ mobile

| Элемент | Решение |
|---------|---------|
| Filter bar | 1 sticky row: горизонтальный скролл категорий + [Навыки▾] [Сорт▾] справа |
| Навыки sheet | Full-sheet 95vh: табы категорий → чипы → sticky [Применить →] 52px |
| Сортировка sheet | Half-sheet 40vh: 2 варианта |
| TWO-SPEEDS strip | 1 строка под filter bar, не sticky: «⏱ Обновляется раз в 15 мин · Подробнее →» |
| Карточки | 1 col, padding 16px, touch target ≥ 44px |

### /cabinet/ mobile

| Элемент | Решение |
|---------|---------|
| Навыки | Collapsed 1 строка чипов, tap → sheet |
| Stack | навыки → подписка → inbox |
| TG Login | Кастомная кнопка full-width indigo pill 52px; deep link в TG |

### Лендинг + how/pricing/faq mobile

| Элемент | Решение |
|---------|---------|
| Hero H1 | 32px/800, padding-top 24px |
| Hero gap | 32px между sub и CTA |
| CTA primary | full-width pill 52px |
| CTA secondary | border pill 48px, full-width, стек под primary |
| Live preview | 2 карточки (не 3–4) |
| Горизонтальный скролл | убрать везде — 1 колонка |

**Handoff Coder:** TG Login deep link + sheet JS → Lead Architect после CSS.

---

## § TWO-SPEEDS-UI — две скорости (**O11+O23**)


**Не в CSS-спринте NEO сейчас** — заложить в макет/REFERENCE; Coder подключит после фазы **3r**.

| Поверхность | UI-элемент | Спека |
|-------------|------------|--------|
| **`/lenta/`** | Info-strip `.rl-feed-delay-notice` | Под `rl-feed-head__count`, muted 13–14px, ссылка на `/pricing/` |
| **`/lenta/`** | (опц.) иконка часов на карточке | Только если O11 в коде и лид «задержанный» — не обязательно в MVP copy |
| **`/pricing/`** | Таблица сравнения | 2 колонки: «Бесплатно» / «ИИ-агент» — строка **Скорость** |
| **`/how/`**, **`/faq/`** | Текстовый блок / accordion | см. TWO-SPEEDS-COPY |
| **`/cabinet/`** | В блоке подписки | Upsell: «Без задержки» рядом со Stars |

**Mobile:** strip не sticky — одна строка + «Подробнее → pricing».

---

#### 2. Лента `/lenta/` — mobile-first

```
Header (sticky, тонкий)
  RawLead | [Войти в кабинет]

Filter Bar (горизонтальная, sticky под header)
  [Все] [Разработка] [Дизайн] [Маркетинг] [Тексты]  ← горизонтальный скролл на mobile
  [Навыки ▾]  ← dropdown/sheet с чипами из каталога
  [Сортировка ▾]  ← Новые / По совместимости

Feed (карточки)
  — новый стиль: тень, radius 20px, без жёсткой рамки
  — mobile: 1 колонка, full width с padding
  — desktop: 2 колонки max-width 900px по центру
  — infinite scroll

Report bug (FAB внизу справа или footer-ссылка)
```

#### 3. Кабинет `/cabinet/` — тот же стиль, + match

```
Header (sticky)
  RawLead | [Профиль / теги]

Мои навыки (chips, редактируемые, sticky под header)
  [python] [figma] [seo] [+Добавить] ← из каталога

Filter Bar (та же что на /lenta/)

Feed (с match %)
  — карточки идентичны /lenta/ + match-bar indigo
```

#### 4. /how и /faq — оставить отдельными, пересобрать стиль

```
/how — 4 шага (не 5), без timeline-вертикали:
  Карточки 2×2 desktop, 1 col mobile
  Каждая: иконка + заголовок + 2 строки

/faq — аккордеон, тот же тёплый фон
  Убрать «закрытое тестирование», «ранний доступ»
```

### Компоненты — новые

| Компонент | Описание |
|-----------|----------|
| **Кнопка primary** | `#4F46E5` fill, белый текст, radius 999px, hover `#4338CA` |
| **Кнопка secondary** | border `#4F46E5`, текст `#4F46E5`, прозрачный фон |
| **Кнопка ghost** | только текст + → , без рамки |
| **Карточка лида** | shadow `0 2px 12px rgba(0,0,0,0.07)`, radius 20px, hover shadow ↑ + translateY(-2px) |
| **Чип категории** | active: `#4F46E5` fill, inactive: `#F3F3EF` + border `#E4E4E7` |
| **Чип навыка** | active: indigo-100 `#EEF2FF` + indigo text, inactive: серый |
| **Match-bar** | `#4F46E5`, height 4px, radius 2px |
| **Иконки категорий** | line-иконки 20px: `</>` dev · `✦` design · `◎` marketing · `Aa` text |
| **Source badge** | FL зелёный · Kwork оранжевый · TG синий — без изменений |
| **Report bug FAB** | `?` круглая кнопка, bottom-right, `#4F46E5` ghost |

### Голос (из Product-канона)

- Активный залог: «ИИ убрал мусор», не «заказы были отфильтрованы»
- Без восклицательных знаков
- Кнопки = конкретное действие: «Смотреть ленту», «Войти в кабинет»
- Mobile: короткие метки — «Дизайн» не «Дизайн & Видео»
- Пустые состояния: человечные — «Пока нет заказов по этим навыкам — попробуй шире»

### Что сдать Lead Designer

| # | Артефакт | Куда |
|---|----------|------|
| 1 | Обновлённый `DESIGN_SYSTEM.md` — новые токены | `docs/team/design/DESIGN_SYSTEM.md` |
| 2 | Новый `REFERENCE.md` — страницы, компоненты, голос | `docs/design/wp/REFERENCE.md` |
| 3 | Обновлённый `feed-cabinet-mvp.md` — новая структура + компоненты | `docs/design/wp/feed-cabinet-mvp.md` |
| 4 | Handoff → `@designer` (DESIGNER_PROMPT) — CSS-задачи | `docs/team/design/DESIGNER_PROMPT.md` |

**Согласовать с владельцем перед передачей @designer:** финальный вид карточки лида (mockup или описание достаточно), навигация header (список пунктов).

---

---

## Что согласовано (2026-05-25)

Полный диалог: [Lead Designer UI/UX Vision Session](../../../.cursor/projects/c-Users-hramo-uisness)

| Решение | Зафиксировано |
|---------|--------------|
| Карточка лида: раскрывающаяся плашка (вариант C) | ✅ |
| Анимации: «Живой» стиль (stagger, lift, bar, press, cubes) | ✅ |
| Кубики источников: собираются из горизонтали в вертикаль при скролле | ✅ |
| FL.ru цвет: `#00A65A` зелёный | ✅ |
| TG цвет: `#0088CC` официальный | ✅ |
| Навигация: добавить «Лента» → `/feed` | ✅ |
| `/feed` фильтры: sticky sidebar desktop + bottom sheet mobile | ✅ |
| `/feed` scroll: infinite scroll | ✅ |
| `/cabinet` теги: редактируемые чипы прямо на странице | ✅ |
| `/cabinet` ощущение: отдельная «продуктовая» страница (не копия feed) | ✅ |
| Лендинг тарифы: 1 карточка ИИ-агент 300–990 ₽/мес | ✅ |
| Пульт: пульсация лампы ok в running-режиме | ✅ |
| Пульт: структурированный статус в вкладке «Статус» (задача Coder) | ✅ |

---

## § D1 — Чипы категорий в `/lenta/` (**→ перед продом**)

**Триггер:** владелец 2026-05-26 — прод только с рабочим продуктом. API `?category=` есть, UI нет.

**Исполнитель:** **`@designer`** — ✅ **сдано 2026-05-26** ([`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) §2.2–2.3).

| # | Задача | Статус |
|---|--------|--------|
| 1 | §2.2 блок **«Категория»** — 4 ниши §0i + «Все» | ✅ |
| 2 | Active chip `#0A0A0A` | ✅ |
| 3 | Mobile bottom sheet | ✅ |
| 4 | Handoff → `@coder` § D1 | ✅ |

Канон названий: [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §0i.

---

## Документы (все готовы)

| Файл | Что |
|------|-----|
| [`docs/design/wp/REFERENCE.md`](../../design/wp/REFERENCE.md) v2 | Лендинг + анимации (§6) + обновлённые токены |
| [`docs/design/wp/feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md) | **Полная спека** `/feed` + `/cabinet` + пульт |
| [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) | Токены v2 (источники + motion-токены) |
| [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md) | Задача для Designer (CSS + pricing + nav + лампа) |

---

## Волна 2 — ✅ согласовано владельцем 2026-05-25

| # | Решение | Зафиксировано |
|---|---------|--------------|
| W2.1 | «Смотреть тарифы» → якорь `#pricing-preview`, не `/pricing` | ✅ `REFERENCE` §3.2, §3.7 |
| W2.2 | «Главная» убрана из nav; логотип RawLead → `/` | ✅ `REFERENCE` §3.1 |
| W2.3 | Hero primary: «Смотреть ленту» → `/lenta/`; secondary: «Смотреть тарифы ↓» → `#pricing-preview` | ✅ `REFERENCE` §3.2 |
| W2.4 | § 3h карточки ленты — после волны 2 | ⏸ |

→ UX волны 2 **закрыт** (достаточно `REFERENCE` §3). **@designer** для волны 2 **не нужен** — волна 1 сдана. Дальше: **@lead-product** (тексты) → **@coder** (nav/hero/якорь в PHP).

---

## Следующие шаги (волна 1 — закрыта)

| Кто | Что | Когда |
|-----|-----|-------|
| **@designer** | Handoff → `DESIGN_BRIEF` §195 | ✅ 2026-05-25 |
| **@coder** | § W · 3d · 3e · 3g | ✅ |

---

## § PRE-LAUNCH-UX v2 — финальный слой перед продом (**→ @lead-designer**, 2026-05-27)

**Когда:** после § PRE-LAUNCH A–D (@coder) и **после** deep research навыков/инструментов ([`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § SKILLS-TOOLS-RESEARCH).  
**Порядок:** Design (спор с владельцем) → **@lead-product** (тексты) → **@coder** (вёрстка).

**Регламент владельца:** Lead Designer **может и должен спорить**, пока не найдём решение, которое владелец считает идеальным по UX — не «сдать быстрее».

### Бриф владельца (факты)

| # | Задача | Направление (не финал — обсудить) |
|---|--------|-----------------------------------|
| ux1 | **Контакты** | Убрать приглашение на «ранний доступ» |
| ux2 | **Фильтры `/lenta/`** | Сейчас неудобно: специализацию трудно найти; от неё зависят навыки; навыки не в «маленьком окошке» |
| ux3 | **Плашка фильтров** | Предложение владельца: **горизонтальная плашка сверху** (специализация → навыки), быстро и интуитивно |
| ux4 | **«Лента заказов»** | Заголовок и блоки **зажаты** верхней плашкой; дать **больше воздуха** (отступы, иерархия) |
| ux5 | **Сообщить об ошибке** | Пользователь может отправить репорт (что сломалось / скрин / URL) — UX + куда ведёт CTA |
| ux6 | **Мобилка** | Полноценная адаптация (не только bottom sheet «как есть») |

### Что сдать Design

| # | Артефакт |
|---|----------|
| 1 | Wireframe/desktop + mobile: **верхняя** filter-bar (category multi → skills), сравнение с текущим sidebar |
| 2 | Типографика/отступы: hero «Лента заказов» + подзаголовки — «воздух» |
| 3 | Паттерн **Report bug** (footer? FAB? modal?) + поля формы |
| 4 | Контакты **без** closed beta / «заявка» / «ранний доступ» (решение владельца 2026-05-27) — CTA: лента, кабинет, связь |
| 5 | Handoff в `feed-cabinet-mvp.md` или addendum + список для @lead-product (подписи, empty states, ошибки)

**Не в scope Design:** реализация API feedback (Coder после макета); биллинг.

→ Coder: [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) § PRE-LAUNCH-UX · Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md) § PRE-LAUNCH-UX copy.

---

## Scope (итог)

| В scope ✅ | Вне scope ❌ |
|-----------|------------|
| WP лендинг: анимации, цвета, pricing 1-тариф, nav «Лента» | `/uslugi`, FL.ru тексты, Habr-статья |
| WP `/feed`: карточка, фильтры, sidebar, infinite scroll, состояния | Mobile app, отдельный сайт |
| WP `/cabinet`: теги-чипы, match, AI-агент кнопка (disabled до 3f) | Coder-часть PHP (это CODER_PROMPT) |
| Пульт: пульс лампы ok | Новый функционал пульта |
| **P-PORTFOLIO** (личное на VPS) | **📋 после O76** — см. § D-P-PORTFOLIO |

---

## § D-P-PORTFOLIO — личное портфолио исполнителя (**📋 после O76**)

**Владелец 2026-05-31:** тот же VPS · **интерактивно и стильно** — ссылка заказчикам и в FL · **параллельно** soft ads RawLead.

**Не путать с RawLead DS:** отдельная визуальная система «я как разработчик», не копия `/lenta/`.

| # | Deliverable |
|---|-------------|
| d1 | One-pager IA: hero · 4–5 кейсов · контакты/CTA · mobile-first |
| d2 | Интерактив: scroll-reveal · карточки проектов · hover/expand · опц. мини-демо iframe |
| d3 | Кейсы: RawLead · **Crystal Debt** (`crystal-debt-core`) · **Михалыч** (`Miha`) · чат-бот WIP — скрины от владельца |
| d4 | Handoff `@designer` → assets + CSS brief → `@coder` § `CODER_PROMPT` **P-PORTFOLIO** |

**Accept:** владелец готов вставить **одну URL** в FL без стыда.

**Концепция v4 (владелец):** стиль + wow · брутализм `labs.rawlead.ru` · RE-motion · ИИ для **заказчика** = **шоу внедрения**, не форма с 3 буллетами. _(v1–v3 заменены)_

**Запрет:** МИМО/БРАТЬ по тексту заказчика · скучный чат «обо мне» · стена текста.

### ИИ-блок — выбрать 1 главный + 1 запасной (Design → владелец)

| ID | Название | Опыт | LLM |
|----|----------|------|-----|
| **A ★** | **«До / После ИИ»** | Fullwidth **scrub-slider**: слева хаос заявок (brutalist inbox), справа — те же карточки с тегами, автоответом, алертом. Подпись: «Так встраивается слой ИИ». Без ввода текста. | Опц. только на CTA «Сгенерировать под вашу нишу» |
| **B ★** | **«Выбери боль»** | Чипы-жёлтые: `Теряем заявки` `Долгий ответ` `Excel-ад` `Хаос в TG` → **explode** в изометрическую схему-«завод» (CSS): вход → блок **ИИ** → выходы (бот / CRM / отчёт). Клик по блоку — 1 строка + иконка. | После выбора 2+ чипов — 1 запрос «план внедрения» |
| **C** | **«Собери модуль»** | Drag brutalist-плиток `Chat` `OCR` `Parser` `Push` на сетку 3×3 → анимация «деплой лог» в terminal · финал: fake blueprint PNG + «стек под ключ» | Финальный абзац по составу плиток |
| **D** | **«Командная строка»** | Поле ввода стилизовано под CLI: гость печатает `магазин` / `клиника` → не оценка, а **посимвольный** brutalist-log «подключаю модуль…» → 3 строки **пользы для бизнеса** | Да, короткий промпт «integration advisor» |

**Рекомендация Lead:** **A + B** на одной странице: A = мгновенный wow без LLM; B = интерактив + опциональный LLM. C/D — если владелец хочет «игру».

| Слой | Содержание |
|------|------------|
| **База** | `labs.rawlead.ru`: фото, hero, marquee, RawLead **PRODUCTION** (кейс навыка, не ИИ-блок) |
| **Motion** | RE: covers `01/04` · scroll-snap · pin ИИ-сцены · stagger · grid-bg |
| **Кейсы** | RawLead live · CD fake journal · Михалыч character board |
| **Техника** | Ключи server-only · rate limit · mobile: A = swipe вместо scrub |

**Accept Design:** заказчик за 10 с **увидел движение/схему**, не прочитал резюме · владелец: «стильно слать в FL».

Референсы: `labs.rawlead.ru` · [richardekwonye.com](https://www.richardekwonye.com/) · CD journal UI.

---

_Lead Designer · 2026-05-25 · после сдачи Designer — архив в `team/archive/TASKS_HISTORY.md`_
