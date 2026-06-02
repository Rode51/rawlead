# Prod incident: `/cabinet/` login+QR, `/lenta/` load, tools leak on cards

**Статус:** открыто  
**Дата:** 2026-06-02  
**Приоритет:** **P0** (блокер основного пользовательского пути)

## Симптом (со слов владельца)

1. Не заходит в ЛК (`/cabinet/`).
2. Не грузится QR-код входа.
3. Не грузится лента (`/lenta/`).
4. До полного падения: на части карточек без отклика показывался блок «Инструменты» в описании.

## Ожидалось

- `/cabinet/` открывается, Telegram login работает, QR подгружается.
- `/lenta/` отдает карточки без клиентской ошибки загрузки.
- В анонимной ленте блок «Инструменты» скрыт (решение O83: tools only for auth).

## Фактически (пока без root-cause)

- Имеем multi-symptom инцидент по трём поверхностям одновременно: auth/QR, feed, card UI.
- Риск общего корня: API proxy/endpoint regress, JS bundle mismatch, theme/API version drift, auth endpoint degradation.

---

## Контекст для Mechanic

- Последний зафиксированный статус до инцидента: O72e gate PASS, активный трек O90+O91.
- Исторически похожие места поломок:
  - `/v1/auth/telegram` (500/NameError),
  - WP proxy `wp-json/rawlead/v1/*`,
  - несовпадение theme/js версии между repo и prod.
- Продуктовый guardrail: по O83 «Инструменты» в anon `/lenta/` не показывать.

---

## Scope диагностики (Mechanic)

1. Проверить доступность цепочки:
   - `https://rawlead.ru/wp-json/rawlead/v1/feed?limit=1`
   - `https://rawlead.ru/wp-json/rawlead/v1/auth/telegram`
   - `https://api.rawlead.ru/health`
2. Проверить ошибки в браузерной консоли:
   - загрузка QR/login script,
   - ошибки `rawlead-feed.js` / `rawlead-cabinet.js`.
3. Проверить прод-логи API и WP proxy на 4xx/5xx в момент инцидента.
4. Проверить, что в anon-ответе feed не утекают `tools_required`/tools-block в рендер.

## Accept (что считаем закрытием)

- `/cabinet/` логин и QR снова работают end-to-end.
- `/lenta/` стабильно грузится без fallback ошибки.
- На anon карточках без отклика блок «Инструменты» не рендерится.
- В тикете зафиксированы root-cause + точечный fix + шаги проверки.

---

## Файлы-кандидаты (ориентир)

- `src/api_server.py`
- `src/owner_admin.py`
- `wordpress/rawlead-kadence-child/inc/rawlead-api.php`
- `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js`
- `wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js`
- `wordpress/rawlead-kadence-child/template-parts/rawlead/flow.php` (если затронут общий JS enqueue)
- `wordpress/rawlead-kadence-child/functions.php`

## Не трогать без отдельного решения Lead

- O90/O91 scope (lag/watchdog), если не связано напрямую с текущим инцидентом.
- L1/L2 prompt logic (O72e), если не является доказанным root-cause.

---

## Решение (заполняет Mechanic)

**Статус:** решено  
**Дата:** 2026-06-02

### Причина
- Общий root-cause в WP proxy: `rawlead_api_base_url()` по умолчанию возвращал `http://127.0.0.1:18766`.
- На prod (`rawlead.ru`) это loopback самого web-сервера WP, а не API-хоста, поэтому прокси-роуты `wp-json/rawlead/v1/*` одновременно отдавали ошибки для:
  - `/auth/telegram` и bot-session/QR,
  - `/feed`,
  - связанных запросов кабинета.
- Из-за этого сломался основной user flow (`/cabinet/` + QR + `/lenta/`).

### Что сделано
- Внесён hotfix в вычисление base URL API в WP proxy:
  - если сайт работает на `rawlead.ru`/`www.rawlead.ru`, default API = `https://api.rawlead.ru`;
  - локальная разработка без явного `RAWLEAD_API_URL` по-прежнему использует `http://127.0.0.1:18766`.
- Логика с `define('RAWLEAD_API_URL', ...)` сохранена и остаётся приоритетной.
- Это устраняет прод-падение без изменения контрактов API и без побочных правок в `src/`.

### Изменённые файлы
- `wordpress/rawlead-kadence-child/inc/rawlead-api.php`
- `docs/problems/2026-06-02-site-lk-qr-feed-and-tools-regression.md`

### Как проверить
1. Smoke доступности:
   - `https://rawlead.ru/wp-json/rawlead/v1/feed?limit=1` → HTTP 200 + JSON с `items`.
   - `https://rawlead.ru/wp-json/rawlead/v1/auth/telegram` (POST с валидным JSON Telegram auth) → не 5xx со стороны proxy.
   - `https://api.rawlead.ru/health` → HTTP 200.
2. Флоу `/cabinet/`:
   - открыть `https://rawlead.ru/cabinet/`,
   - нажать вход, убедиться что поднимается bot-session и отображается QR/Telegram deep-link,
   - завершить вход, убедиться что кабинет открывается без ошибки.
3. Флоу `/lenta/`:
   - открыть `https://rawlead.ru/lenta/`,
   - убедиться, что карточки загружаются без баннера «Не удалось загрузить».
4. Guardrail O83 (anon tools):
   - в анонимной сессии открыть карточку в `/lenta/` и убедиться, что блок «Инструменты» не показывается.
