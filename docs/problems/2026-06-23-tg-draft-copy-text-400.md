# TG draft sendMessage 400 — copy_text format

**Дата:** 2026-06-23  
**Симптом:** кнопка «Отклик» в @rawlead_bot — черновик не приходит в TG (генерация идёт).  
**Статус:** root cause ✅ · hotfix ✅ deploy 2026-06-23

## Prod evidence

```
tg:draft:callback lead=25282 tg=1342741103
tg:draft:sendMessage fail chat=1342741103: {"ok":false,"error_code":400,
  "description":"Bad Request: can't parse inline keyboard button: Field \"copy_text\" must be of type Object"}
tg:draft:ok user=... lead=25282   # draft generated, message NOT delivered
```

Лента `/v1/me/leads/.../draft` работает — сломан только **отправка в TG** после TG-DRAFT-BUTTONS deploy.

## Root cause

`src/match_push.py` `_draft_result_keyboard`:

```python
{"text": "Скопировать текст", "copy_text": copy_text}  # WRONG — string
```

Telegram Bot API 7.x: `copy_text` = **CopyTextButton object** `{"text": "..."}`, max **256** chars (не 4000).

## Fix (P0)

1. `copy_text`: `{"text": copy_payload}` где `copy_payload` обрезан до 256.
2. Тесты `test_o265`: assert `copy_btn["copy_text"] == {"text": "..."}`.
3. Deploy `match_push.py` + restart `rawlead-api` `rawlead-bot-poll`.

## Rollback (если hotfix задержится)

Убрать `reply_markup` из `_send_tg_draft_result` — отклики снова придут без кнопок.
