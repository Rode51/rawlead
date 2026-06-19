# Next auth — bot Start OK but site not logged in

**Date:** 2026-06-19  
**Area:** `rawlead-next` · `auth-context.tsx` · `bot-login.ts`  
**Status:** fixed → deploy prod **2026-06-19** (§ O280-R5)

## Symptoms

- QR modal open on desktop · Start in @rawlead_bot
- Bot confirms (or user believes Start sent)
- Site: modal stuck on «Ожидаем…» **or** closes but header still «Войти» / skeleton

## Root cause (Lead triage)

**Primary:** `AuthProvider` mount effect runs `completeAuthAfterToken()` when old JWT in localStorage. User opens `LoginDialog` → `logout()` + new poll → bot success → `login()`. **Stale bootstrap promise** `.catch()` still runs → `clearToken()` + `anon` → login wiped.

**Secondary:** poll 410 if phone opened `cabinet/?auth=`; silent network retry; strict `assertCompleteProfile` without TG name.

## Fix

`rawlead-next/**` — § **O280-R5**.
