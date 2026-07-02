# RawLead

RawLead — сервис для поиска и приоритизации фриланс-заказов из нескольких источников с поддержкой ИИ-сценариев.

Прод: [rawlead.ru](https://rawlead.ru)

## Что это

RawLead собирает заказы из FL/Kwork/Telegram, фильтрует шум, рассчитывает релевантность под стек пользователя и ускоряет путь до отклика.

Ключевая ценность:
- одна лента вместо нескольких вкладок с биржами
- процент совместимости по каждому заказу
- прозрачная модель доступа (trial -> feed -> pro)
- быстрый путь к отклику через ИИ-подсказки

## Что реализовано

- мульти-источниковый ingest (web + Telegram)
- backend на FastAPI с логикой подписок и tier-доступа
- frontend на Next.js (`/lenta`, `/pricing`, `/cabinet`)
- paywall и интеграция checkout
- push-уведомления по матчам в Telegram
- deploy-скрипты и smoke-проверки

## Архитектура (верхний уровень)

- **Frontend:** Next.js static export (`rawlead-next/`)
- **Backend:** FastAPI (`src/`)
- **Данные:** Postgres
- **Автоматизация:** Python workers/parsers
- **Инфраструктура:** VPS + systemd + nginx
- **Мессенджинг:** Telegram bot + Telethon accounts

## Основные инженерные направления

- безопасный rollout через feature flags и smoke-first подход
- реализация paywall/tier-логики с обработкой edge cases
- разграничение сценариев для anon и expired-trial
- связка продуктового UX с backend-проверками доступа
- надежный deploy/rollback процесс

## Структура репозитория

- `src/` — backend-логика и доменные сервисы
- `rawlead-next/` — веб-приложение
- `scripts/` — deploy/ops-инструменты
- `tests/` — автоматизированные проверки
- `docs/` — продуктовая и техническая документация

Основные документы:
- индекс docs: [`docs/README.md`](docs/README.md)
- продуктовый вектор: [`docs/team/product/PRODUCT_VISION.md`](docs/team/product/PRODUCT_VISION.md)
- roadmap: [`docs/team/architect/ROADMAP.md`](docs/team/architect/ROADMAP.md)
- текущий срез prod: [`docs/team/common/PROD_FACTS.md`](docs/team/common/PROD_FACTS.md)

## Быстрый старт (локально)

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
```

Frontend:

```powershell
cd rawlead-next
npm install
npm run dev
```

## Примечание

В репозитории есть как продуктовый код, так и внутренние операционные материалы.
Для знакомства с проектом достаточно начать с `src/`, `rawlead-next/`, `tests/` и `docs/README.md`.
