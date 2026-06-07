# Схема работы в Cursor (экономия токенов)

## Главное правило

**Всё важное — в файлах `docs/`, не в чате.**  
Чат = короткая команда. Длинные обсуждения — **Gemini в браузере**, итог 5–10 строк → Lead кладёт в `docs/`.

**Навигация для всех AI:** [`docs/README.md`](../README.md) → [`team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md) → файл роли.  
**Промпт задачи** — только в `CODER_PROMPT.md` / `DESIGNER_PROMPT.md`; в **новый чат** — **один** `@coder` / `@designer` / … (пути в `.cursor/rules/<роль>.mdc` § «Включение»).  
**Git commit/push** — только **Lead Architect** (по вашей просьбе на push).

---

## Кому писать

| Вопрос / задача | Куда | Первое сообщение |
|-----------------|------|------------------|
| Что делать **тебе** | **`docs/FOR_YOU.md`** | без чата |
| **Продукт:** vision, контуры, метрики | **Lead Product** `@lead-product` | **`PRODUCT_VISION.md`** · инициатива: `LEAD_PRODUCT_PROMPT.md` |
| **Roadmap, TASKS, приоритеты в работу** | **Lead Architect** `@lead-architect` | **`ROADMAP.md`** ← из vision |
| **Дизайн:** стратегия UI, система, план | **Lead Designer** `@lead-designer` | [`LEAD_DESIGN.md`](team/design/LEAD_DESIGN.md) · план: `LEAD_DESIGN_PROMPT.md` |
| **Инженерия:** docs, Coder, приёмка | **Lead Architect** `@lead-architect` | `lead-architect.mdc` · `CODER_PROMPT.md` |
| **Дизайн UI** (исполнение) | **Designer** (новый чат) | `@designer` (или `@.cursor/rules/designer.mdc`) |
| **Фича / код** | **Coder** (новый чат) | `@coder` (или `@.cursor/rules/coder.mdc`) |
| **Поломка / регресс** | **Mechanic** `@mechanic` | `@mechanic` + `@docs/problems/…` · модель **Gemini 2.5 (2M)** |
| Brainstorm / черновик | **Gemini** (браузер) → итог → Lead | — |
| **Плановая фича** | **Coder** `@coder` | `@coder` · `CODER_PROMPT.md` |

### Правила Cursor — не путать

Карта всех AI: **[`docs/team/common/PROJECT_MAP.md`](team/common/PROJECT_MAP.md)** · детали: `ARCHITECTURE.md`, `CODE_STRUCTURE.md`.

Карта всех `.mdc`: **`.cursor/rules/README.md`**.

| Тип | Файлы |
|-----|--------|
| **Always** | `economy.mdc`, `lead-no-code.mdc` |
| **Роль (@ в чате)** | `lead-architect`, `lead-product`, `lead-designer`, `coder`, `mechanic`, `designer`, `owner` |
| **Гард по путям** | `code-guard.mdc` — когда открыт код |

**Apply Intelligently** в UI = Agent сам решает по `description`; для ролей надёжнее **`@coder`** / **`@lead-architect`** в первом сообщении, а не полагаться на «умное» подключение.

Роли: **`.cursor/rules/`** · масштаб: **[`SCALE.md`](SCALE.md)** · бэкап: **[`../ops/BACKUP.md`](../ops/BACKUP.md)**

**Не пиши Coder** «объясни весь проект» — он читает `CODER_PROMPT.md` / `TZ.md` сам.

**Lead никогда не кодит** — отдельный чат `@lead-architect`; любая правка `src/` → новый чат `@coder`. Правила: `lead-no-code.mdc`.

---

## Harness O119 — гибрид без ECC

**Оркестратор отдельно не нужен:** triage, очередь и handoff — это **Lead Architect** (`STATUS`, `TASKS`, `CODER_PROMPT`, `problems/`). Роль не дублируем.

**Что добавилось:** 4 project-skills в `.cursor/skills/rawlead-*` — короткие сценарии (поиск до кода, инцидент, VPS, WP live dev). Agent включает skill **когда задача подходит**, не грузит всё в каждый чат.

| Skill | Зачем |
|-------|--------|
| `rawlead-search-first` | grep/read до правок — меньше регрессов и токенов |
| `rawlead-incident` | «всё сломалось» → тикет → Mechanic |
| `rawlead-vps-probe` | proxy, systemd, `probe_all_proxies.py` |
| `rawlead-wp-live-dev` | Local + BrowserSync (O118) |

**Что не меняется:**

- `@coder` / `@mechanic` / `@lead-designer` — как раньше
- `economy.mdc` — hot STATUS/TASKS
- Lead **не кодит** · commit — Lead по просьбе
- Новые `.md` в docs — только с твоим «да»

**Запрещено:** `./install.ps1 --profile full` из [ECC](https://github.com/affaan-m/ecc) — конфликт rules и раздувание контекста.

**Тебе по ходу:** когда Lead вводит новый skill или меняет harness — объяснит в чате одним абзацем «новое правило».

---

## Отдельный чат на роль

Стартовые фразы — в **`.cursor/rules/*.mdc`**.

| Роль | Когда | Чат |
|------|-------|-----|
| **Lead Product** | стратегия, roadmap | `@lead-product` |
| **Lead Designer** | план UI, design system | `@lead-designer` |
| **Lead Architect** | инженерия, Coder-промпт | `@lead-architect` |
| **Designer** | есть `DESIGNER_PROMPT.md` | `@designer` |
| **Coder** | есть `CODER_PROMPT.md` | `@coder` |
| **Mechanic** | тикет `docs/problems/` · **Gemini 2.5** | `@mechanic` + тикет |

**Lead-* не кодят.** Внедрение — ты + Coder/Designer по их PROMPT-файлам.

**Coder vs Mechanic:** поломка «сейчас» → Mechanic (тикет). Задача в `CODER_PROMPT` → Coder. Не оба на одном §. Канон: [`team/architect/LEAD.md`](../architect/LEAD.md) § «Coder vs Mechanic».

**После Mechanic:** Lead — тикет «решено», при необходимости `FOR_YOU` / `CODER_PROMPT`.

---

## Цикл одной фичи

Полный регламент и чеклисты: **[`SCALE.md`](SCALE.md)** (таблица шагов 1–6, Lead, владелец, бэкап).

---

## Как экономить токены (чеклист)

| Делай | Не делай |
|-------|----------|
| Первое сообщение: `@coder` (пути в `coder.mdc`) | Копировать весь TZ в чат |
| Одна задача = **новый** Coder-чат | Переиспользовать старый Coder-чат |
| Одна поломка = один чат Mechanic + один файл `docs/problems/` | Дебаг всего MVP в чате Lead |
| «Смотри CODER_PROMPT.md» | «Сделай всё из TZ» |
| Ошибка: последние 15 строк консоли | Скрин + простыня переписки |
| Правки FILTERS/PROFILE — файл на диске | «Запомни 20 слов навсегда» |
| Lead / Coder / Mechanic: **Agent** | Ask для правок кода |
| Модель **Auto** на всё подряд (есть отдельная квота **Auto+Composer**) | Max без причины |
| Итог сессии в `STATUS.md` | «Напомни что мы делали вчера» в новом чате |
| Факты только из файлов repo | AI «помнит» то, чего нет в docs |

**Gemini (браузер):** черновики, «5 вариантов», обучение → итог в Lead.  
**Cursor Lead:** зафиксировать решение в `docs/`.  
**Cursor Coder:** фичи по `CODER_PROMPT.md` (узкое чтение).  
**Cursor Mechanic + Gemini 2.5 (2M):** починка по `docs/problems/*.md`; при жёстком баге — весь проект в контексте.

---

## Файлы — шпаргалка

Иерархия документов: **[`SCALE.md`](SCALE.md)** § «Документы». Правила ролей: **`.cursor/rules/*.mdc`**.

---

## Один раз в Cursor

1. **Open Folder** → repo
2. **Settings → Rules** → Project Rules включены
3. Закладки чатов: **Lead PM**, **Lead Design**, **Lead Arch**, **Coder**, **Designer**, **Mechanic**
4. **MCP (опционально):** [`MCP_POOL.md`](MCP_POOL.md)

**Новый проект с той же командой:** [`templates/cursor-team-kit/README.md`](templates/cursor-team-kit/README.md) · `bootstrap.ps1`

---

## Старт агента (все роли)

| Шаг | Файл |
|-----|------|
| 1 | [`README.md`](../README.md) |
| 2 | [`PROJECT_MAP.md`](PROJECT_MAP.md) — § «Агентам» |
| 3 | Промпт роли — см. [`.cursor/rules/README.md`](../../.cursor/rules/README.md) § «Старт по роли» |

Правила Cursor: **всегда** `economy.mdc` + `lead-no-code.mdc`; роль — **`@coder`** / **`@lead-architect`** и т.д. в первом сообщении.

---

## MCP — когда агенту нужен интернет / браузер

| Задача | Сервер (см. `MCP_POOL.md`) |
|--------|----------------------------|
| Поиск в сети, свежие факты | Perplexity |
| Скрап страницы в markdown | Firecrawl |
| Автотест UI, клики | Playwright |
| Картинка / видео workflow | Glif |
| Ваш открытый Chrome + логин | Chrome (`claude --chrome` в Claude Code) |

Если tools MCP в чате **нет** — агент должен попросить владельца включить сервер, а не «притворяться», что сходил на сайт.

---

## Квоты Cursor Pro (два счётчика)

В **Usage** два отдельных прогресса (не «Auto бесплатный навсегда»):

| Счётчик | Что ест | Перелив |
|---------|---------|---------|
| **Auto + Composer** | Режим **Auto**, Composer | сверх лимита → **API-квота** или on-demand |
| **API** | Встроенные модели (Sonnet…), ~**$20** в плане | on-demand |

**Вывод:** длинный **Lead на Auto** всё равно **тратит подписку** (сначала Auto+Composer %, потом API). **Lead на свой API at-cost** (Google **или** OpenRouter) — не копит счётчики Cursor, если в чате выбрана **именно** эта модель, не Auto.

**Только OpenRouter (нет Google key):** Lead → **Agent** + OR Flash; Coder → **Auto** + Agent; при `Tool ''` на Lead — резерв Agent **Auto**.

---

## OpenRouter в Cursor (BYOK) — модели по ролям

**Зачем:** вынести часть запросов на **свой API** (Google BYOK и т.д.), чтобы не съедать квоты Cursor. **Lead** — основной кандидат (длинный чат, много docs).

### Один раз в Cursor Settings → Models

| Шаг | Значение |
|-----|----------|
| OpenAI API Key | Включить · ключ **OpenRouter** (`sk-or-…`) |
| Override OpenAI Base URL | `https://openrouter.ai/api/v1` |
| Verify | Нажать **Verify** у OpenAI key |
| + Add model | Каждый ID из таблицы ниже — **отдельной строкой**, Enter |

На [openrouter.ai/models](https://openrouter.ai/models) фильтр **tools** — иначе Agent в Cursor может не работать.

### Что добавить (+ Add model) — копипаст ID

| Имя в UI (как назовёте) | Model ID | Когда |
|-------------------------|----------|--------|
| OR Flash daily | `google/gemini-2.5-flash` | **Coder / Designer** — основной день |
| OR DeepSeek cheap | `deepseek/deepseek-chat-v3-0324` | мелкие правки, черновой код |
| OR Haiku fast | `anthropic/claude-3.5-haiku` | короткие задачи, docs-правки |
| OR Sonnet release | `anthropic/claude-sonnet-4` | **перед релизом**, узкие правки (вместо встроенной Sonnet) |
| OR Sonnet cheap | `anthropic/claude-sonnet-4:floor` | то же, дешевле, медленнее |
| OR Gemini Pro | `google/gemini-2.5-pro` | **только @mechanic** + тикет |
| OR Sonnet fast | `anthropic/claude-sonnet-4:nitro` | если `:floor` тормозит на дедлайне |

Если Cursor пишет «model not found» — скопируйте ID с карточки модели на OpenRouter (кнопка clipboard), не с памяти.

### Какой чат — какая модель

| Чат | Модель в селекторе | Платит |
|-----|-------------------|--------|
| **Lead Architect** (один долгий) | **Agent** + **OR** `google/gemini-2.5-flash` · резерв **Auto** | OR → OpenRouter · Auto → **Auto+Composer** |
| **Coder** (новый на задачу) | `google/gemini-2.5-flash` или DeepSeek | OpenRouter |
| **Designer** | Flash | OpenRouter |
| **Mechanic** | `google/gemini-2.5-pro` | OpenRouter |
| Узкая правка перед релизом | `anthropic/claude-sonnet-4:floor` | OpenRouter · **не** встроенная Sonnet |

**Не трогать встроенную Sonnet/Max** в селекторе — они едят **пул Pro**. Перед релизом — OR Sonnet из таблицы.

**Tab** (автодополнение) всегда на Cursor — OR на это не влияет.

### Лимит OpenRouter

В [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits) — потолок **$30–50/мес**, алерт 80%. Смотреть расход: Activity → фильтр по model id.

### Если Agent падает на OR-модели

1. Verify key ещё раз  
2. Base URL именно с `/v1`  
3. Взять другую модель с **tools** (Flash / Sonnet)  
4. Chat иногда стабильнее Agent на BYOK — для плана достаточно, для кода — Agent + Flash

### Ошибка `Tool '' not found in provided tools` (Request ID в попапе)

**Смысл:** Agent отправил вызов инструмента с **пустым именем** — Google / Bedrock / Anthropic отклоняют запрос. В metadata часто **`is_byok: false`** → запрос идёт **через бэкенд Cursor**, а не на ваш OpenRouter.

**Частые причины:**

| # | Причина | Что сделать |
|---|---------|-------------|
| 1 | **Agent + OpenRouter** — у Cursor ограниченная поддержка; Agent часто **не** ходит на Override URL | См. обходы ниже |
| 2 | Включены **MCP** (Playwright, Firecrawl, Neon…) + Agent | **Settings → Tools & MCP** — выключить все → **новый чат** → тест. Потом включать по одному |
| 3 | Выбрана **встроенная** Sonnet/Gemini, не OR-модель из списка | В селекторе — только добавленные `google/gemini-2.5-flash` и т.д. |
| 4 | Режим **Agent** при BYOK | Попробовать **Ask** на той же OR-модели (без полного Agent) |

**Рабочая схема для uisness (2026-06):**

| Роль | Режим Cursor | Модель | Платит |
|------|--------------|--------|--------|
| Lead | **Agent** | **OR** `google/gemini-2.5-flash` | OpenRouter |
| Coder — обычный день | **Agent** | **Auto** | Auto+Composer (MCP) |
| Coder — перед релиз | **Agent** | **Anthropic BYOK** Sonnet (ключ Anthropic, не OR) **или** встроенная Sonnet (пул Pro) | API / Pro |
| Coder — эксперимент OR | **Ask** (не Agent) | OR Flash | OpenRouter |
| Mechanic | Agent | **Google BYOK** Gemini 2.5 **или** OR Gemini Pro | API / OR |
| L1/L2/regen в Python | — | OpenRouter в `.env` | OR (как сейчас) |

**OpenRouter + Agent** на Coder — ненадёжно (держать **Auto**). На **Lead** OR+Agent пробовать Flash; скрипты — OR в `.env`.

**Быстрый тест после ошибки:** MCP off → новый чат → модель **Auto** → Agent → «прочитай STATUS.md». Ок → включать MCP по одному. Не ок → **Help → HTTP Compatibility Mode → HTTP/1.1**, перезапуск Cursor.

### Anthropic BYOK + MCP — часто ломается (2026-06)

**Симптом:** только Claude (свой ключ Anthropic или OR→Claude): `Tool '' not found` / `missing field type` в Agent **с включённым MCP**. GPT / Gemini / **Auto** при тех же MCP обычно ок.

**MCP отключать надолго не нужно.** Сначала **настройки**, не серверы:

| Проверка | Действие |
|----------|----------|
| Конфликт ключей | **Либо** Anthropic BYOK, **либо** OpenRouter (Override URL). Не оба сразу. Для Anthropic: Override OpenAI Base URL = **Off**, OpenAI key (OR) = **Off** |
| Релиз без Anthropic API | **Встроенная** Sonnet (пул Pro) + MCP on — не свой ключ Anthropic |
| Дешёвый API + MCP | **Google BYOK** → Gemini 2.5 Flash/Pro (официальный слот Google в Models) |
| Прокси в Cursor | `settings.json` → `http.proxy` может ронять **только** Anthropic API — тест: временно proxy off, новый чат, Sonnet BYOK |
| MCP «залип» | Settings → Tools & MCP: toggle **off/on** всех → **новый** чат (не старый тред) |

**Рабочий стек с MCP (uisness):**

| Роль | Модель | MCP |
|------|--------|-----|
| Lead | **OR Flash** (Agent) | MCP по задаче; OR падает → Agent **Auto** |
| Coder день | **Auto** | Playwright / Firecrawl / Neon по нужде |
| Coder релиз | **встроенная Sonnet** (не Anthropic BYOK) | да |
| Альтернатива Sonnet | **Google BYOK** `gemini-2.5-pro` | да |
| Mechanic | Google BYOK Gemini 2.5 Pro | по тикету |
| Скрипты L1/L2 | OpenRouter в `.env` | — |

Anthropic ключ в Cursor — **отложить**, пока Agent+Claude+MCP не починят в вашей версии; OR→Claude в Agent — та же история.

### Только OpenRouter (нет Google AI Studio)

| Шаг | Settings → Models |
|-----|-------------------|
| 1 | **OpenAI API Key** On → ключ `sk-or-…` |
| 2 | **Override Base URL** → `https://openrouter.ai/api/v1` |
| 3 | **Anthropic / Google** BYOK в Cursor — **Off** (конфликт) |
| 4 | **+ Add model:** `google/gemini-2.5-flash`, `anthropic/claude-3.5-haiku`, `deepseek/deepseek-chat-v3-0324` |
| 5 | Лимит на [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits) |

| Роль | Режим | Модель |
|------|-------|--------|
| **Lead** | **Agent** (следит за `docs/`, TASKS, PROMPT) | `google/gemini-2.5-flash` |
| **Lead MCP** | только по задаче (Neon/Firecrawl…), не держать Playwright «всегда» | — |
| **Lead резерв** | Agent | **Auto**, если OR даёт `Tool ''` |
| **Coder** | Agent + MCP | **Auto** |
| **Релиз** | Agent | **встроенная Sonnet**, не OR Claude |

**Не на Lead OR:** `claude-sonnet-*`. **Ask** — только если Agent временно сломан; для Lead по регламенту нужен **Agent**.

**Экономия без Ask:** черновики в **Gemini в браузере** → 5–10 строк в чат Lead → один Agent-ход правит файлы (меньше OR-токенов).
