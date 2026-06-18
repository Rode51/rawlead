# Push TG — crash on every lead (UUID subscript)

**Date:** 2026-06-15  
**Severity:** P0 — match push fully down on prod  
**Symptom:** Monica (and all users) meet push gates but receive **zero** pushes; `match_push_log` empty.

## Evidence

**Monica Neon (tg 8688264540):**
- `plan=agent`, `is_active=true`, `active_until` 2026-07-15
- `tg_chat_id=8688264540`, `push_enabled=true`, `push_min_match=60`
- **27** `user_tags`
- **`match_push_log` count = 0**

**VPS `radar_site.log` (repeat on every visible L1 lead):**
```
push:match:err lead=21767:'UUID' object is not subscriptable
```

## Root cause (Lead read-only)

`push_match_for_lead()` in `src/match_push.py` uses `user_id[:8]` in log/err strings.  
`psycopg` returns `user_id` as **`uuid.UUID`**, not `str` → exception aborts push for the lead.

Likely lines: ~1288, ~1299 (and same pattern elsewhere in file ~678, ~723, …).

## Fix (→ @coder § O250)

1. `str(user_id)[:8]` (or small helper) everywhere in `match_push.py`.
2. pytest: `push_match_for_lead` with mocked cursor returning `uuid.UUID` user_id → assert send + log, no crash.
3. Deploy API (`rawlead-api` + radar restart) · smoke: new `push:match:user=` line in log, Monica gets push on next ≥60% lead.

## Not the cause

- Empty tags / missing trial / push toggle — **ruled out** for Monica.
- `MATCH_PUSH` env — enabled on VPS.

## Follow-up (P0 → O250b)

Push uses **`keyword_match`** · feed uses **`compatibility_match`**. Monica @80%: leads 26785/26784 show feed **100/93** but push km **12/8** → silent skip. Fix: align push formula with feed.

## Follow-up (P0 → O250c, owner 2026-06-15 evening)

**Symptom:** still no push for Monica + owner on fresh cards (TG 100%, Kwork ~80% on `/lenta/`).

**State:**
- `match_push_log` **0** (push never succeeded on prod).
- O250 UUID fix deployed · recent L1 cycles **no** new UUID errors.
- **O250b not confirmed on VPS** — push may still use old `keyword_match` → skip despite feed %.

**Owner decision:** **no backfill** — old cards stay without push; only **new** L1 leads after O250b deploy.

**Owner first:** `scripts/deploy-o250b-vps.py` → wait for next lead ≥ threshold · `@coder` § **O250c** only if forward still fails.
