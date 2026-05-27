# TASKS (активное)

Архив: [`archive/TASKS_HISTORY.md`](archive/TASKS_HISTORY.md)  
Vision: [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) v0.9 · план Product: [`LEAD_PRODUCT_PROMPT.md`](../product/LEAD_PRODUCT_PROMPT.md)

---

## Владелец — Vision v0.10 (2026-05-26)

| # | Задача | Статус |
|---|--------|--------|
| V0.1 | PM + Product §0i | ✅ |
| V0.2 | Приёмка § P3a / W2 | ✅ 2026-05-26 |
| V0.3 | Приёмка § V10 | ✅ 2026-05-26 |
| V0.4 | § V10.5 + P7 + backfill | ✅ 2026-05-26 |
| — | Хостинг / allowlist TG | ⏳ после V10 |

## Lead → Design / Coder (активно)

| # | § | Статус |
|---|-----|--------|
| **0** | **SITE-BAT-VENV** — дубли system/venv (b4–b10) | ✅ Lead verify 2026-05-27 |
| **0a** | **BOT-NOTIFY-SPLIT** — два бота | ✅ Lead verify 2026-05-27 |
| **0b** | **SQLITE-NEON-SYNC** — resync (s7–s12) | ✅ Lead verify 2026-05-27 (footer `neon_insert: 17`) |
| **0b** | **POST-RESTART-CHECK + WP/TG/PROXY + UX** | → @coder |
| **1** | **NEON-DEDUP-REPLAY** + **LOG-NEON-CYCLE** | ✅ код 2026-05-27 · owner verify ⏳ |
| **2** | **P5-PREP** (CORS, логи воркеров, locks если Linux) | → @coder после п.1 |
| **3** | **FEED-DECOUPLE** (лента = `is_visible`, не `notified_at`) | ✅ код 2026-05-27 · owner verify ⏳ |
| **4** | **SITE-AI-FALLBACK** (не слать “всё” при `ai_unavailable`) | ✅ код 2026-05-27 · owner verify ⏳ |
| **5** | **LOG-NOTIFY-DETAIL** — подробные трейс-логи доставки в TG | → @coder после п.1 |
| 0 | **P1.3d / D1 / P4** | ✅ принято 2026-05-26 |
| 0b | **F-LOCAL** фильтры + ИИ | ✅ принято 2026-05-26 |
| 0c | **S-SPLIT** legacy/site | ✅ код · env владелец 2026-05-27 |
| 0c2 | **S-SPLIT-NEON-DATA** | ✅ код · приёмка ⏳ |
| 0c3 | **F-SITE-FILTERS-0i** + пульт | ✅ код 2026-05-27 · приёмка ⏳ |
| 0d | **S-SPLIT-TG** | ✅ код · Site `TELEGRAM_CHAT_ID` ⏳ владелец |
| 0d2 | **PULT-THEME** | ✅ код · приёмка ⏳ |
| 0e | **F-PROMPT p3** | ✅ код |
| 0f | **P5** деплой | ⏸ после п.1–2 + «едем на прод» |
| — | **@lead-designer** | ⏸ последняя очередь |
| — | Neon `DATABASE_URL` | ✅ |
| — | Аудит Gemini | справочник → [`problems/2026-05-27-preprod-audit-full.md`](../problems/2026-05-27-preprod-audit-full.md) |

→ полный план: [`../architect/PORTFOLIO_SPRINT.md`](../architect/PORTFOLIO_SPRINT.md) · [`../FOR_YOU.md`](../FOR_YOU.md)

---

## Lead Architect

- [x] Принять vision v0.9 · `ROADMAP` · `LEAD_DESIGN_PROMPT` · ревизия docs 2026-05-24
- [x] Уборка docs: `PROJECT_MAP` § агентам, `ARCHITECTURE`/`TZ_API`/`SOURCES_POOLS`, архив SOURCES_SAAS, без дублей в корне `docs/`
- [x] Волна 2: приёмка Lead Design → очередь Product
- [ ] После копирайта Product — `CODER_PROMPT` § волна 2
- [ ] После **3b** — дочистить `NEON_SCHEMA.md` (полная схема users/tags)
- [ ] После MVP — `PORTFOLIO.md` под ставку B

---

## Волна 2 — лендинг UX + тексты (**→ @coder**)

**Порядок:** Design ✅ · Product ✅ · Architect ✅ · **Coder**

| Шаг | Кто | Статус |
|-----|-----|--------|
| 0–2 | Владелец · Lead Design · Lead Product | ✅ 2026-05-25 |
| 3 | **@lead-architect** → `CODER_PROMPT` § W2 | ✅ |
| 4 | **@coder** § W2 | ✅ Coder 2026-05-25 · приёмка владельцем ⏳ |
| 4b | **@coder** § 3h | ✅ |
| 4c | **@coder** § 3i | ✅ |
| 4d | **@coder** § 3j | ✅ Lead задеплоил тему 2026-05-25 |
| 5 | Ingest 25 источников (PDF) | 📋 [`docs/archive/INGEST_SOURCES_SNG_25.json`](../archive/INGEST_SOURCES_SNG_25.json) · очередь P1 сайты → Coder 3i |

### Бриф владельца (2026-05-25)

- **«Смотреть тарифы»** — не на `/pricing`, а **автоскролл** к блоку тарифов внизу главной (`#тариф` / `pricing-preview`).
- **Навигация:** возможно убрать пункт **«Главная»** (логотип RawLead → home).
- **Главная:** возможно явная кнопка **«Лента»** → `/lenta/` — решение Design.
- **§ 3h** (карточки ленты = как на главной, multi-навыки) — **после** волны 2 или параллельно после Design OK.

---

## Lead → Coder

**Ворота прод:** [`PRE_PROD_GATE.md`](../architect/PRE_PROD_GATE.md) · **Промпт:** [`CODER_PROMPT.md`](../architect/CODER_PROMPT.md) — **P1 → D1 → P4 → P5**

| # | Трек | Статус |
|---|------|--------|
| … | § W2 · V10 · P7 | ✅ |
| **P1** | Whitelist + парсеры + **P1.4 логи** | **→ @coder** (P1.4 после 3c) |
| **D1** | Чипы category в `/lenta/` | **→ @lead-designer**, потом @coder |
| **P4** | TG Login кабинет | после D1 |
| **P5** | Деплой | после ворот + «едем на прод» |
| **P2** · **P3** · **P8** | прокси / UI / LLM | не блокер прода |
| **P6** | Публичный git | после прода |
| … | 3f ИИ-агент | после P |

---

## Lead → Designer

**Промпт:** [`LEAD_DESIGN_PROMPT.md`](LEAD_DESIGN_PROMPT.md) → [`DESIGNER_PROMPT.md`](DESIGNER_PROMPT.md)

| # | Трек | Статус |
|---|------|--------|
| 1 | Концепция `/feed` + `/cabinet` | ✅ Lead Designer 2026-05-25 |
| 2 | Handoff лендинг + пульт | ✅ Designer → [`DESIGN_BRIEF.md`](design/DESIGN_BRIEF.md) §195 |
| 3 | § W в коде | ✅ Lead 2026-05-25 |
| 4 | **3d** `/lenta` + каркас `/cabinet` | ✅ |
| 5 | **3e** ЛК | ✅ принято владельцем 2026-05-25 |
| 6 | **§ 3g** лента | ✅ commit `54ba7d5` |
| 7 | Лента WP load | ✅ отбой |
| 8 | **Волна 2** UX | ✅ Lead Designer · `REFERENCE` §3 |
| 9 | **Волна 2** копирайт | ✅ Lead Product |
| 10 | **§ W2** в коде | ✅ |
| 11 | **§ 3h** в коде | ✅ |
| 12 | **§ D1** чипы category в `/lenta/` | **→ @lead-designer** (перед продом) |

---

## Отложено (после MVP)

- `/uslugi`, FL витрина, Habr-кейс, биллинг, multi-user, TG Login
- WooCommerce · VK/Avito ingest
- **3i** парсеры сайтов-агрегаторов · **3j** площадки напрямую · **3k** скрыть TG raw из `/lenta/` — `PRODUCT_VISION.md` §0h v2
