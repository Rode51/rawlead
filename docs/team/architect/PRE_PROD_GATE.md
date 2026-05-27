# Ворота перед продом (владелец 2026-05-26)

**Решение:** портфолио = **рабочий продукт**, куда заходят люди и получают пользу — не «лендинг со скриншотами».

**Прод (§ P5)** — **только после** блоков ниже **и** § **F-LOCAL** (фильтры + ИИ на локале). Хостинг можно купить заранее, трафик — нет.

---

## Блокер ленты (2026-05-27) — до «едем на прод»

| # | Блок | Кто | Готово когда |
|---|------|-----|--------------|
| **N** | **NEON-DEDUP-REPLAY** — dup не обрывает L1; зомби в Neon догоняются | @coder | Neon: новые/обновлённые строки с L1; `/lenta/` не пустая при Site ▶; см. [`CODER_PROMPT.md`](CODER_PROMPT.md) § NEON-DEDUP-REPLAY |
| **F** | **FEED-DECOUPLE** — `/v1/feed` не зависит от `notified_at` | @coder | `/lenta/` показывает `is_visible=true` даже при `notified_at IS NULL` |
| **A** | **SITE-AI-FALLBACK** — site-бот не спамит при `ai_unavailable` | @coder | при сбое L1 в логах есть счётчик, но TG без мусора |
| **O** | **Site-бот** — `TELEGRAM_CHAT_ID` в `.env.site` = чат, куда писал @rawlead_bot | владелец | Нет `chat not found` в `radar_site.log` |

Промпт Coder: § **NEON-DEDUP-REPLAY** · § **LOG-NEON-CYCLE** · затем § **P5-PREP**.

---

## Обязательно до P5 (код)

### F-LOCAL — фильтры Python + экономия ИИ (владелец 2026-05-26)

| # | Блок | Кто | Готово когда |
|---|------|-----|--------------|
| **0** | **F-LOCAL** Стоп-слова, V10.1, дешёвая LLM, dogfood | @coder + владелец | Локально: в бот — релевантные «Брать»; в логе P1.4 — понятные `filter`/`МИМО`/`dup` |
| — | Lead Designer (концепция) | @lead-designer | **Последняя очередь** — правки визуала после F-LOCAL |

Промпт: [`CODER_PROMPT.md`](CODER_PROMPT.md) § **F-LOCAL**

---

## Обязательно до P5 (продукт)

| # | Блок | Кто | Готово когда |
|---|------|-----|--------------|
| **1** | **P1** Чистая публичная лента + ingest | @coder + allowlist TG | ✅ код · env: 3 биржи |
| **2** | **D1** Чипы категорий в `/lenta/` | **@designer** → @coder | ✅ 2026-05-26 |
| **3** | **P4** Кабинет + вход через Telegram | @coder | ✅ код 2026-05-26 · владелец: SQL + wp-config |

**После:** § P5 деплой 24/7 · опц. P6 публичный GitHub без ИИ-следов.

---

## Не блокирует прод (после запуска)

| Задача | Когда |
|--------|--------|
| § 3f ИИ-агент (черновик отклика) | после первых юзеров |
| § P8 дешёвая LLM | по ROI |
| 25 источников ingest | волнами |
| WooCommerce / биллинг | после P4 |

---

## С тебя (владелец)

| # | Действие | Блокер |
|---|----------|--------|
| 1 | Заполнить [`TG_PUBLIC_FEED_ALLOWLIST.txt`](../../ops/TG_PUBLIC_FEED_ALLOWLIST.txt) | P1 |
| 2 | ~~Сайты P1~~ — **зафиксированы** в [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) | — |
| 3 | Приёмка P1 → D1 → P4 на Local | каждый блок |
| 4 | **«едем на прод»** | старт P5 |
| 5 | Beget/Timeweb + VPS — можно купить заранее | P5 |

---

## Порядок Coder

```
P1 → D1 → P4 → F-LOCAL → S-SPLIT* → NEON-DEDUP-REPLAY → LOG-NEON-CYCLE → P5-PREP → P5 (деплой)
```

Промпт: [`CODER_PROMPT.md`](CODER_PROMPT.md) · Design: [`LEAD_DESIGN_PROMPT.md`](../design/LEAD_DESIGN_PROMPT.md) § D1

---

_Lead Architect · 2026-05-26_
