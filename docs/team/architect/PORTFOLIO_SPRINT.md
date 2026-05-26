# Спринт «Портфолио» — 2026-05-25

> **Ворота прод (2026-05-26):** [`PRE_PROD_GATE.md`](PRE_PROD_GATE.md) — портфолио = **рабочий продукт** для чужих; **P5 только после P1 + D1 + P4**.

> **Vision v0.10:** 4 категории Digital — [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §0i. V10/P7 ✅. Ingest массовый — **⏸**. Dogfood — **не ослаблять**.

**Цель:** продукт под **Digital-специалистов**, не «все заказы рунета».

**Neon:** ✅ `DATABASE_URL` на ПК — не блокер.

**Канон ingest:** [`INGEST_SOURCES_PLAN.md`](INGEST_SOURCES_PLAN.md) · JSON 25 источников · сегодня **не** все 25 — только whitelist + 0–2 сайта P1.

---

## Порядок до прода (ворота)

| # | Блок | Кто | Статус |
|---|------|-----|--------|
| **3a** · **V10** · **P7** | W2 + 4 ниши + category API | ✅ 2026-05-26 |
| **P1** | Чистая лента: whitelist FL/Kwork/TG + ingest | @coder + allowlist | **→ старт** |
| **D1** | Чипы Код/Дизайн/Маркетинг/Тексты в `/lenta/` | @lead-designer → @coder | после P1 |
| **P4** | Кабинет + Telegram Login | @coder | после D1 |
| **P5** | Деплой 24/7 | @coder + владелец | только после ворот + «едем на прод» |

## После прода / параллельно (не блокер)

| # | Блок | Кто |
|---|------|-----|
| **0** | Allowlist TG (владелец) | блокер **части** P1 |
| **P2** | Радар 2 мин + прокси | @coder |
| **P3** | UI прочее | @coder |
| **P8** | Дешёвая LLM | @coder |
| **P6** | GitHub без ИИ-следов | @coder |

**Не в этот день (явно):** §3f полный ИИ-агент, WooCommerce, 25 парсеров, Supabase/Celery из PDF.

---

## 0. Владелец (сегодня утром)

| # | Что | Куда |
|---|-----|------|
| 0.1 | **Приёмка W2** (~5 мин): `wp_install_rawlead_theme.py` → `radarzakaz.local` → «W2 принято» или список багов | [`FOR_YOU.md`](../../FOR_YOU.md) |
| 0.2 | **Whitelist TG:** список `@channel` / `t.me/...` «нормальных» чатов | новый файл `docs/ops/TG_PUBLIC_FEED_ALLOWLIST.txt` (по одной ссылке на строку) |
| 0.3 | **Сайты P1** | ✅ канон: [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt) — VC.ru, Freelancehunt, Habr Freelance, Habr Career (+ FL/Kwork) |
| 0.4 | **Прокси для парсера:** 2+ URL (HTTP/SOCKS) для ротации FL/Kwork | `.env` — `FL_PROXY_URLS` / см. § P2 в CODER_PROMPT (Coder заведёт имена) |
| 0.5 | **Хостинг WP** + **VPS** (см. бюджет) | [`DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md) |
| 0.6 | DNS: сайт → WP, `api.` → VPS | там же |

---

## 1. Чистая общая лента (`/lenta/`)

**Правило владельца:** в публичной ленте только:

- `fl` (FL.ru)
- `kwork` (Kwork)
- TG только из **allowlist** владельца (tier A из плана, не старые dogfood-чаты)
- **все 4 сайта P1** из списка PDF: `vc_ru`, `freelancehunt`, `habr_freelance`, `habr_career` — см. [`PUBLIC_FEED_WEB_SOURCES.txt`](../../ops/PUBLIC_FEED_WEB_SOURCES.txt)

**Не показывать:** старые MVP-TG (`Помогатор`, `frilanc`, `workk_on`, …) — см. [`INGEST_SOURCES_PLAN.md`](INGEST_SOURCES_PLAN.md) § TG.

### Coder (§ P1 в [`CODER_PROMPT.md`](CODER_PROMPT.md))

| Задача | Суть |
|--------|------|
| P1.1 | `GET /v1/feed` — фильтр `source IN (...)` из конфига/env |
| P1.2 | Скрипт/миграция: старые лиды с `source` вне whitelist → `is_visible=false` (или не трогать историю, только read-filter) |
| P1.3 | Обновить `TG_JOIN_QUEUE.csv` / мониторинг под allowlist; не слушать мусорные чаты в радаре |
| P1.4 | Опционально: парсер 1–2 сайтов P1 → `POST /v1/internal/leads` |

**Приёмка:** `/lenta/` на Local — нет карточек из старых TG; есть FL/Kwork; после join allowlist — появляются TG с меткой.

---

## 2. Радар: 2 минуты + прокси

| Задача | Суть |
|--------|------|
| P2.1 | `POLL_INTERVAL_MINUTES=2` в `.env`; снять hardcode «минимум 10» в `config.py` (или `MIN_POLL_INTERVAL_MINUTES=2`) |
| P2.2 | Пул прокси для HTTP-парсеров FL/Kwork: round-robin / skip dead; лог смены |
| P2.3 | Предупреждение владельцу: чаще опрос = выше риск rate-limit; прокси обязательны |

Telethon-прокси для acc — отдельно (`TG_PROXY_URL`), не путать с парсером бирж.

---

## 3. UI/UX перед хостом

После P1 на Local — проход по чеклисту:

| # | Проверка |
|---|----------|
| u1 | Лендинг W2: nav, hero, тарифы `#pricing-preview` |
| u2 | `/lenta/`: 2 колонки desktop, «Применить», пустое состояние без «сломано» |
| u3 | Карточка: источник (цветная точка FL/Kwork/TG), нет плейсхолдера «после обогащения» на пустом `ai_reasons` — показать snippet `body` или короткий текст |
| u4 | `/cabinet/`: до и после логина визуально цельно |
| u5 | Mobile 375px — лента и лендинг |

Спека: [`REFERENCE.md`](../../design/wp/REFERENCE.md) §3 · [`feed-cabinet-mvp.md`](../../design/wp/feed-cabinet-mvp.md).

---

## 4. Кабинет + регистрация через Telegram

**Сейчас:** MVP `X-RawLead-User-Id` только owner UUID — чужой пользователь 403.

**Нужно:**

| # | Компонент |
|---|-----------|
| 4.1 | API: `POST /v1/auth/telegram` — проверка `hash` Login Widget, upsert `users`, выдача JWT (или signed session) |
| 4.2 | API: `/v1/me/*` по `Authorization: Bearer` |
| 4.3 | WP: страница входа, Telegram Login Widget, хранение токена, редирект в `/cabinet/` |
| 4.4 | `.env` на API: `TELEGRAM_BOT_TOKEN` для проверки (тот же бот или отдельный — решит Coder) |

Детали: § P4 в [`CODER_PROMPT.md`](CODER_PROMPT.md) · ориентир [`TZ_API.md`](TZ_API.md).

---

## 5. Деплой — **бюджет 24/7 без ПК** (решение владельца)

**Канон:** [`DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md) (~350–800 ₽/мес).

| Шаг | Действие |
|-----|----------|
| 5.1 | Shared WP: child-тема + плагин |
| 5.2 | VPS: **API + радар** (одна машина), systemd, Caddy HTTPS `api.домен` |
| 5.3 | WP → `https://api.домен`, CORS |
| 5.4 | Перенос `.env` + Telethon-сессий на VPS; **выключить** радар на ПК |
| 5.5 | Этапы E1→E2 в DEPLOY_BUDGET |

**Туннель с ПК (вариант A)** — **не используем** (ПК выключен = лента мертва).

---

## 6. GitHub «для заказчиков»

**Не пушить** в публичный `uisness` как есть.

| Вариант | Как |
|---------|-----|
| **A (рекомендуем)** | Новый репо `rawlead-portfolio` — subtree: `wordpress/`, `desktop/` скрины, `README.md` кейса |
| **B** | Ветка `portfolio-public` — без `.cursor/`, без `docs/team/*`, без «vibe/AI agent» в коммитах |

**Убрать из витрины:** `.cursor/rules`, `CODER_PROMPT`, упоминания Cursor/Auto/Lead, «всё сделал ИИ», внутренние `docs/problems`, `.env*`.

**Оставить:** pitch, стек (Python, WP, Tauri, Postgres), 3–5 скринов, ссылка на live site.

Скрипт очистки — § P6 в CODER_PROMPT.

---

## Прод без ПК — простыми словами

Три части, две оплаты:

| Часть | Где | Цена |
|-------|-----|------|
| Сайт (WP) | Shared-хостинг | ~150–350 ₽ |
| API + радар | **Один дешёвый VPS** | ~200–450 ₽ |
| База | Neon | 0 ₽ |

**Важно:** радар (`tg_main`, FL, Kwork) тоже на VPS — иначе с выключенным ПК лиды не приходят.

```
Сайт (хостинг) ──► api.твой-домен.ru (VPS) ──► Neon
                        ▲
                   радар на том же VPS
                        ▼
                   Telegram-бот
```

Подробно: [`DEPLOY_BUDGET.md`](../../ops/DEPLOY_BUDGET.md).

---

## Риски дня

| Риск | Митигация |
|------|-----------|
| TG auth + деплой в один день — много | Сначала P1 лента + UI; auth и хостинг параллельно только если Coder успевает |
| 2 мин опрос — бан FL | прокси-пул, backoff при 429 |
| Скрыть ИИ в git — забыть файл | чеклист P6 + `rg -i cursor` перед push |

---

## Копипаст владельцу → @coder

```
@coder Новый чат — спринт «Портфолио» 2026-05-25.

Читай по порядку:
1. docs/team/architect/PORTFOLIO_SPRINT.md
2. docs/team/architect/CODER_PROMPT.md — § P1…P6 (активно)

Старт с § P1 (whitelist ленты), пока ждём allowlist TG от владельца — можно FL+Kwork only + filter в API.

Neon готов. POLL 2 мин + прокси — § P2. TG Login кабинет — § P4. Деплой — § P5. Публичный git — § P6.

Не делать: §3f ИИ-агент, 25 парсеров, WooCommerce.
```

---

_Lead Architect · 2026-05-25 · владелец: портфолио + чистая лента + TG auth + без ИИ в публичном git_
