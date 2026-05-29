# /cabinet/ — TG login 500 Internal Server Error

**Статус:** ⏸ → @coder hotfix  
**Дата:** 2026-05-29  
**Приоритет:** **P0** (блокер входа)

## Симптом

- https://rawlead.ru/cabinet/ — виджет TG грузится, после «Log in as …» → **«Не удалось войти: Internal Server Error»**
- Fallback OAuth — та же ошибка после возврата

## Факт Lead verify (2026-05-29)

```text
POST https://api.rawlead.ru/v1/auth/telegram  → 500 Internal Server Error
POST https://rawlead.ru/wp-json/rawlead/v1/auth/telegram → 500 (proxy)
GET  https://api.rawlead.ru/health → 200 OK
GET  https://rawlead.ru/wp-json/rawlead/v1/feed?limit=1 → 200 OK
```

**Вывод:** API жив, feed работает — **ломается только** `/v1/auth/telegram`.

## Корень (код)

`src/api_server.py` вызывает `verify_telegram_login()` и `login_bot_token()` **без import** из `telegram_login.py` → `NameError` → FastAPI **500**.

## Fix @coder

```python
from src.telegram_login import login_bot_token, verify_telegram_login
```

+ smoke: invalid hash → **401**, не 500 · restart `rawlead-api` на VPS.

## Не путать

- BotFather `/setdomain` — нужен для **виджета**, но здесь виджет **уже работает**
- Theme v1.8.2 / loginUrl — **OK** на prod
