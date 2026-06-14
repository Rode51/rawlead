# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-14)

**Стадия:** prod live · **волна 1 ingest/ops ✅** (O212–O214) · **ads ⏸** · **→ волна 3 Perf**

### ✅ Сделано (не возвращать в hot)

| Блок | § / факт |
|------|----------|
| **YouDo+FL ingest** | **O190+O191+O193** subprocess · stable cycles |
| **Pay + pre-launch** | O174 ЮKassa smoke · O185 w1–w3/t5b/t6 |
| **Feed + delist** | O175–O178 · O180–O182b |
| **Ingest + VPS** | O99 · O160 locks · VPS **4 GB** |
| **ИИ quality** | O72e aggregate · O164 L2 grounding |
| **TG handlers** | **O206 t3c** ✅ owner · мгновенно |

### ⏳ До soft ads (порядок owner 2026-06-13)

| Волна | Что | Кто |
|-------|-----|-----|
| **1 · TG** | t2b sync · **O207** funnel proof · O188 join ~127 | @coder |
| **2 · Концепция** | **O208** quiz-first UI/UX · тексты · воронка · убрать ручные навыки | @lead-product → @lead-designer → @coder |
| **3 · Perf** | Оптимизация загрузки `/lenta/` · home · quiz | @lead-designer scope → @coder |
| **4 · L2** | **O200** full regen · **≥70% × 4 категории** | @coder после «да» owner |
| **5 · Pre-ads** | Финальный stress @50 VU · O186 security | owner + @coder |
| **6 · GTM** | ads + portfolio | **последним** ⏸ |

**Не в hot:** join wave можно идти **параллельно** волне 2–3 на VPS.

### ⏸ После ads / фон

| # | Что |
|---|-----|
| **ingest SLA** | Биржи: lag p50 в ops · укоротить цикл где безопасно (FL/Kwork = poll, не push как TG) |
| **O113-seo** | органика |
| **O105-w2** | crypto auto-check |
| **O110** | FL 403 отдельный пул — по триггеру |
| **O92b** | pending_tags review |
| **O82-w3** | embeddings match |

---

## Фазы vision §4 (сжато)

| Фаза | Статус |
|------|--------|
| **0** · dogfood радар | ✅ |
| **E0–E5** · WP site + auth + cabinet | ✅ |
| **3f** · ИИ draft + L2/L3 | ✅ gate passed |
| **Launch** · pay + trial + E2E | **→ сейчас** |
| **GTM** · soft ads | после launch |
| **v1** · multi-user scale · billing polish | backlog |

**Отменено:** mobile app · отдельный маркет-сайт · Freelancehunt

---

## O72e gate (aggregate ✅ · **O200** per-category ⏳)

| Слой | Gate | Факт |
|------|------|------|
| L2 | send ≥70% overall | **71.8%** ✅ |
| L2 | **send ≥70% × 4 cat** | **⏳ O200** · owner gate **70%** (не 60%) |
| L2 | combined ≥4.0 | **4.28** ✅ |
| L1 | usable ≥70% | **83.1%** ✅ |
| L3 | smoke | **92%** ✅ |

Детали: [`OWNER_INTENT.md`](OWNER_INTENT.md) · § **O200** `CODER_PROMPT`

---

## Парсеры (O63)

| source | Статус |
|--------|--------|
| FL · Kwork · TG | ✅ prod |
| FR.ru · FreelanceJob · Пчёл | ✅ secondary VPS |
| YouDo | ⏳ chromium/proxy — не блокер launch |

---

## O207 — TG: доказать воронку + настройка фильтра (owner 2026-06-13)

**Проблема:** непонятно, **есть ли заказы в группах** и **только ли filter/L1** их режет — или listen gap / handler / «не слушаем».

**Принцип:** сначала **измерить правду** (принято → причина отсева → лента), потом **крутить фильтр на данных**, не вслепую.

| Фаза | Что | Артефакт |
|------|-----|----------|
| **A. Truth ladder** | На каждое TG-сообщение: стадия + `skip_reason` (listen / filter / spam / L1 / AI / neon) | лог + Neon агрегаты · `/ops/tg` per-acc **и per-chat** |
| **B. Chat health** | По каждому listen-чату: `msgs_24h` · `last_msg` · breakdown причин | ops таблица «чат молчит vs режем» |
| **C. Sample audit** | N случайных `skip` в сутки — **полный текст** + ссылка; owner размечает «заказ / не заказ» | `data/tg_skip_samples.json` · кнопка в ops «разбор» |
| **D. Filter lab** | Replay размеченного корпуса через `filters.py` / L1 **без деплоя**; diff до/после правки | скрипт + отчёт «+N заказов / +M шума» |
| **E. Golden posts** | Test group + 5–10 эталонных vacancy-постов owner — **must pass** filter→L1 | pytest + smoke чеклист |

**Не делаем в O207:** слепое ужесточение `word_filter` без sample audit · «режем file до 5 чатов» (owner intent: listen = joined).

**Зависимости:** O206 **t3c** (handlers живы) → **t2b** sync → O207 A→E.

**Тикет:** [`problems/2026-06-13-tg-feed-volume.md`](../../problems/2026-06-13-tg-feed-volume.md) · решение owner: [`OWNER_INTENT.md`](OWNER_INTENT.md)

**Coder (когда дойдём):** § **O207** в `CODER_PROMPT` · наследует O206 t4b/t5.

---

## O208 — Концепция quiz-first: UI · copy · воронка (owner 2026-06-13)

**Контекст:** концепция сменилась — пользователь **не выбирает навыки руками**; квиз + лента учат профиль. Старые фильтры/копирайт/экраны — от прошлой модели.

**После волны 1 (TG t2b + O207 базово).**

| Слой | Что | Артефакт |
|------|-----|----------|
| **Product** | Tier/лимиты **✅ freeze** · vision bump после O209 | `LEAD_PRODUCT_PROMPT` § O208-MONETIZATION |
| **Design** | **O209** — полный UX+copy match-first (quiz · lenta · home · pricing · FAQ) | `LEAD_DESIGN_PROMPT` § **O209-MATCH-EXPERIENCE** |
| **Coder** | Убрать manual skills picker · quiz-first only · `DRAFT_HOURLY_LIMIT=5` · card strip · L3 judge→K | § после PM+Design freeze |
| **Не смешивать** | Ingest filter/L1 (O207) ≠ UI «навыки» — разные слои |

**Perf (волна 3):** scope в Design § O199 «Site optimization» → Coder: `/lenta/` P0.

**Зависимости:** O207 A (truth ladder) желательно до тюнинга **ingest** filter · O208 — **продуктовый** слой для пользователя.

---

Coder ТЗ: [`CODER_PROMPT.md`](CODER_PROMPT.md) · решения: [`OWNER_INTENT.md`](OWNER_INTENT.md)

---

_Lead Architect · 2026-06-13 · волны до ads · O208 concept · L2 70%_
