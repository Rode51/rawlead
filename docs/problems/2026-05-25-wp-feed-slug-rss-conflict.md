# WP: slug `feed` → RSS вместо ленты

**Дата:** 2026-05-25  
**Статус:** ✅ исправлено (slug `lenta`, `page-lenta.php`)

## Симптом

`http://radarzakaz.local/feed/` — XML RSS («Hello world!»), нет карточек заказов.

## Причина

WordPress резервирует URL `/feed/` под ленту записей. Страницы со slug `feed` не создаются (получается `feed-2`). Меню вело на `/feed/` → RSS.

## Решение

- Страница ленты: slug **`lenta`**, шаблон `page-lenta.php`
- Плагин `rawlead-landing`: создаёт `lenta` + `cabinet` при активации
- Доки: `RUN.md`, `FOR_YOU.md`

## Проверка

`http://radarzakaz.local/lenta/` + uvicorn :18766 → блок «Лента заказов», карточки из API.
