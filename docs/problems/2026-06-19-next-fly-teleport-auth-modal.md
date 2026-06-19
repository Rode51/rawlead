# Next — fly teleport on scroll + QR login stuck + modal UX

**Date:** 2026-06-19  
**Area:** `rawlead-next` · `/` FlowSection · auth `/cabinet/`  
**Status:** fixed → deploy prod **2026-06-19** (§ O280-R4)

## Symptoms (owner, post-R3 deploy)

1. **Landing fly:** without scroll — animation OK. **During scroll mid-flight — card teleports** to slot (no spring).
2. **QR login:** scan QR → Start in @rawlead_bot → **page does nothing** (cabinet does not open, no login in header).
3. **UX request:** login in **modal overlay** on current page, not redirect to `/cabinet/`.

## Root cause (Lead triage)

| Issue | Cause |
|-------|--------|
| Teleport on scroll | R3 `FlowSection`: `scroll`/`resize` listener calls `snapFlyingToSlot()` — instant place card, cancels fly |
| Lenis amplifies | `SmoothScroll` emits scroll during wheel — triggers snap even on small scroll |
| QR silent fail | Poll may get JWT but `completeAuthAfterToken()` via `/me` fails; errors not always surfaced in UI. WP uses `bot-complete` body for `saveUserMeta` immediately |
| Modal vs page | R3 routed `/lenta/` login to `/cabinet/`; `LoginModal` has no QR image |

## Fix

`rawlead-next/**` — see `CODER_PROMPT` § **O280-R4**.
