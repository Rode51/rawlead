# Ingest — 25 источников (PDF владельца → RawLead)

**Канон JSON:** [`../archive/INGEST_SOURCES_SNG_25.json`](../archive/INGEST_SOURCES_SNG_25.json)  
**Vision:** [`../product/PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) §0h  
**Не делаем из PDF:** миграция на Supabase, Celery/Redis воркеры, pgvector на MVP, ScraperAPI для FL без бюджета/ROI.

---

## Сверка с RawLead

| PDF предлагает | RawLead сейчас | Решение |
|----------------|----------------|---------|
| FastAPI + Supabase + микросервисы | Python радар + **Neon** + `api_server` | **Оставляем Neon**, ingest через `POST /v1/internal/leads` |
| 25 парсеров сразу | FL + Kwork + 5 «мусорных» TG чатов | **Волнами**, не 25 за раз |
| Telethon на все TG | acc1–3, join-лимиты | **Замена** чатов, не +18 каналов в один день |
| SHA-256 + pgvector dedup | `content_hash` в Neon | **Хватает** strict hash; semantic — потом |
| Scraping API для FL | Свой парсер FL | **Не платим API**, пока свой работает |

---

## Слой A — сайты (публичная лента, приоритет)

| P | Источник | Почему |
|---|----------|--------|
| **P1** | VC.ru `/jobs` (API JSON) | Стабильно, не HTML |
| **P1** | Freelancehunt | Хорошая вёрстка |
| **P1** | Habr Freelance + Habr Career | ИТ + общие, теги в карточке |
| **P2** | Freelance.ru | Средняя защита |
| ✅ | FL.ru, Kwork | Уже в радаре |

---

## Слой C — TG из PDF (не слой A)

Текущие чаты (`Помогатор`, `frilanc`, `workk_on`, …) — **мусор для продукта** → **не расширять**, со временем **вывести из `/lenta/`** (3k).

**Замена очередью join** (по 2–3 канала/неделю, см. `TG_JOIN_SCHEDULE.md`):

| Tier | Каналы | Роль |
|------|--------|------|
| **TG-A** | @distantsiya, @gogetajob, @dh_jobs, @design_jobs, @textodrom, @smmleads, @digitalbroccoli | Премодерация, все ниши |
| **TG-B** | @python_jobs, @javascript_jobs, @qa_jobs, @findervc | Нишевые / объём |
| **TG-low** | @workzavr, @ish_designer | Много шума — только dogfood, не в ленту |

---

## Очередь Coder (3i)

1. Парсер **VC.ru API** → Neon `source=vc_ru`
2. **Freelancehunt** HTML
3. **Habr Freelance** (tasks)
4. Обновить `TG_JOIN_QUEUE.csv` — tier A, не трогать старые MVP-чаты в прод-ленте

---

_Lead Architect · 2026-05-25 · из PDF владельца_
