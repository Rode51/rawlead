# Приёмка prod — O60 (2026-05-30)

**Статус:** **✅ закрыт** (Lead verify 2026-05-30) · **→ O37-UX**
**Источник:** владелец при приёмке O59

## Симптомы

| # | Проблема |
|---|----------|
| 1 | «Отклик ✓» виден **без регистрации** (shared `reply_draft` в публичной ленте) |
| 2 | Draft fail → retries → **лимит 10/час** · владелец: **лимит убрать** |
| 3 | Счётчик «60 заказов · **по совместимости**» при другом sort/filter |
| 4 | Главная «Последние заказы» — **статичные** demo (O55), не обновляются |
| 5 | Лента давно без новых · **FL.ru 0** в radar log |

## VPS snapshot (Lead)

- `rawlead-radar` active · FL **0** downloaded/cycle · Kwork dup/filter · `neon_insert: 0`
- Последний lead в API feed: ~`2026-05-30T00:41 UTC`

## Fix

→ [`CODER_PROMPT.md`](../team/architect/CODER_PROMPT.md) § **O60**

## Root-cause O60e (Coder 2026-05-30)

| | |
|--|--|
| **Симптом** | `FL.ru скачано 0` при active radar |
| **Корень** | сбой **page-2+** листинга (часто **мертвый FL_PROXY**) → весь `fetch_listing_projects` падал → 0 карточек за цикл |
| **Fix** | `fl_parser.py`: partial OK — при ошибке стр. ≥2 отдаём карточки со стр. 1; `main.py`: `fetch_error` в строку лога |
| **→ Lead ops** | VPS: проверить `FL_PROXY_URL` / `FL_PROXY_URLS` или убрать для direct; `DRAFT_HOURLY_LIMIT=0` в `.env.site` |
