# 2026-06-15 — /lenta/ не грузится (JS syntax error)

**Severity:** P0 prod · feed полностью мёртва  
**Introduced:** theme **1.19.17** · § O247-DRAFT-LIMIT-UX deploy  
**Symptom:** «Показано 0 из 0», кнопка «Показать ещё» из SSR, **нет** XHR к `/feed` или `/me/feed`. Anon + logged-in.

## Root cause

`rawlead-feed.js` **SyntaxError** — лишняя закрывающая `}` после `parseDraftApiError`:

```2422:2426:wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js
    return err;
  }
  }   // ← DELETE this line

  function draftQuotaPayload(data) {
```

`node --check rawlead-feed.js` → `Unexpected token 'function'` at line 2426.

IIFE обрывается → `window.rawleadFeed` есть, но скрипт не выполняется → `resetAndLoad()` never runs.

## API OK

`GET /wp-json/rawlead/v1/feed?limit=3` → items, `today_count=255`. Backend не виноват.

## Fix (Coder)

1. Remove extra `}` line 2424.
2. `node --check wordpress/.../rawlead-feed.js`
3. Bump theme **1.19.18** (`functions.php` + `style.css` header).
4. `python scripts/deploy-wp-theme-vps.py`
5. Smoke: `/lenta/` Network → feed XHR · карточки · `ver=1.19.18`

## Lead verify miss

O247 accept не прогнал syntax-check JS — добавить в DoD Coder § O247 follow-up.
