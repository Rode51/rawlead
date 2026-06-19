# Next login — modal vs QR, ghost «Telegram» user

**Date:** 2026-06-19  
**Area:** `rawlead-next` auth · `/lenta/` · `/cabinet/`  
**Status:** partial fix R3 · **open R4** (QR stuck + modal + fly teleport)

## Symptoms (owner)

1. «Войти» on `/lenta/` opens modal «Открыть Telegram», not QR (expected like cabinet).
2. After flow: header shows **TELEGRAM** + letter **T**, no `@username`, no TG photo.
3. Feed cards still show **«Войди и увидишь»** while header shows logged-in + «Выйти».
4. Cabinet: «В системе: Telegram», Premium «Нет доступа».
5. Landing «Один поток»: during card fly animation, **scrolling** moves the flying card with the viewport / overlaps slot (duplicate card on slot).

## Root cause (Lead triage)

| Issue | Cause |
|-------|--------|
| **`access_token` = `undefined`** | Poll `GET /auth/bot-complete` on **401** (bot not confirmed yet): `apiFetch` does not throw → `setToken(res.access_token)` stores literal `"undefined"` · poll **stops** on first attempt. WP checks `res.ok && access_token`. |
| Fly + scroll | `FlyingOverlay` uses `position: fixed` + viewport `getBoundingClientRect()` — on scroll, slots move in document, overlay stays viewport-fixed → desync / overlap |
| No QR on lenta | `LoginModal` auto-starts bot poll; QR only on `/cabinet/page.tsx` |
| «TELEGRAM» label | `displayHandle()` fallback when `/me` has empty `username` and `first_name` |
| «Войди и увидишь» when logged in | `MatchBar.tsx` treats `free` tier same as `anon` (WP does not) |
| Possible stale JWT | New login does not `clearToken()` before `botSession()` |

## Workaround (owner)

1. «Выйти» or clear site data: `rawlead_access_token`, `rawlead_user_meta`.
2. Open **https://rawlead.ru/cabinet/** directly.
3. Scan QR · confirm **Start** in @rawlead_bot.
4. Expect `@username` in header after reload.

## Fix

`rawlead-next/**` only — see `CODER_PROMPT` § **O280-R3**.
