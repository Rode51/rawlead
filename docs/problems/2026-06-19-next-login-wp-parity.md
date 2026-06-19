# Next login — WP parity required (R6)

**Date:** 2026-06-19  
**Status:** fixed → deploy prod **2026-06-19** (§ O280-R6)

## Owner

- R5 prod: login still fails after Start in bot
- Missing WP login UX (button → QR desktop / Telegram mobile, Cancel, ghost link)

## Root cause (Lead)

Next reimplemented auth with extra `/me/subscription` await before `login()` and stripped WP UI. WP `pollBotComplete` on 200: `setToken` + `saveUserMeta(data)` + show — immediate.

## Fix

Port `page-cabinet.php` + `rawlead-cabinet.js` poll to `LoginPanel.tsx`. **Styles:** match current Next (globals.css, Hero/pricing CTAs) — **not** WP `rawlead.css`.
