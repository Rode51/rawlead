# /cabinet/ — Telegram Login не завершает вход (локалка)

**Статус:** ✅ принято владельцем 2026-05-27 (fallback login)  
**Дата:** 2026-05-27  
**Приоритет:** P0 (блокер PRE-LAUNCH / P4)

## Симптом (факт)

- На `http://127.0.0.1:10007/cabinet/` вместо кнопки Telegram в блоке логина виден серый/битый placeholder.
- Пользователь не может войти в кабинет: token не сохраняется, экран логина не переключается на app.

## Что проверено

- `/cabinet/` отдается `200`, JS подключен, `rawleadCabinet` в странице есть.
- `tgBotUsername` в странице = `rawlead_bot`.
- BotFather `/setdomain` для `rawlead_bot` на `127.0.0.1` выполнен.
- Прямой OAuth URL открывается и авторизация проходит.
- В API виден `POST /v1/auth/telegram` (на невалидных попытках `401`), профильная env-загрузка для API переключена на `.env.site`.

## Текущее понимание причины

Ломается встроенный Telegram Login iframe/script в контексте WP-страницы (`/cabinet/`) — browser privacy / third-party cookies / anti-tracker path.  
Внешний OAuth URL живой, backend `/v1/auth/telegram` работает.

## Уже сделано

- Дефолт login bot для кабинета: `rawlead_bot`.
- Добавлены подсказки/диагностика в UI кабинета.
- API переведен на профильную env-загрузку (`.env.site`) для login token.
- **Coder:** fallback UI + popup/deep-link (`rawlead-cabinet.js`, `functions.php`); `FOR_YOU.md` / `RUN.md` § `RAWLEAD_TG_LOGIN_FALLBACK_URL`.

## Требование владельца

Снять блокер входа в кабинет на локалке/предпроде: должен быть рабочий путь логина даже при падении Telegram Widget.

## Задачи @coder

| # | Готово когда |
|---|--------------|
| cbl-1 | Добавлен fallback вход **без iframe Telegram Widget** (одноразовый код через бота / deep-link flow) |
| cbl-2 | Fallback сохраняет `access_token` в `localStorage` и переключает gate → app |
| cbl-3 | Если widget не загрузился за N секунд: явный UI state + кнопка fallback |
| cbl-4 | Логи/ошибки в UI понятные: где отвал (widget load / auth verify / token save) |
| cbl-5 | `RUN.md`/`FOR_YOU.md`: короткая инструкция «как войти в /cabinet/ локально, если widget пустой» |

## Приёмка

1. На `127.0.0.1:10007/cabinet/` при пустом widget пользователь нажимает fallback и завершает вход.
2. После входа `GET /v1/me/feed` и `/v1/me/tags` идут `200`; кабинет показывает данные.
3. Повторное открытие `/cabinet/` — app открывается без повторного логина (token сохранён).
