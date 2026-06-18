# 2026-06-14 — /lenta/ и /cabinet/ не грузятся (JS SyntaxError)

**Severity:** P0 · prod  
**Reported:** owner 2026-06-14 (во время O220-L1-PROMPT-R2)  
**Lead verify:** 2026-06-14

## Symptom

- `/lenta/` — «Показано 0 из 0», карточек нет, квиз «Загружаем карточки…»
- `/cabinet/` — зависает на логине / «Ждём подтверждение в Telegram…» (если был QR-poll)
- Anon и logged-in одинаково

## Not the cause

| Check | Result |
|-------|--------|
| HTTP `/lenta/`, `/cabinet/` | 200 |
| `GET /wp-json/rawlead/v1/feed?limit=3` | 200, items OK |
| `GET /wp-json/rawlead/v1/me/feed` (valid JWT) | 200, 20 items |
| `rawlead-api` | active |

**Backend OK — чисто фронт.**

## Root cause

**SyntaxError** в O220 `renderMatchBreakdown` — строка HTML не закрыта одинарной кавычкой JS.

```javascript
// BROKEN (missing closing ' at EOL)
'" aria-label="Что значит совместимость">?</button></div>"

// FIX
'" aria-label="Что значит совместимость">?</button></div>"'
```

| File | Line |
|------|------|
| `wordpress/.../assets/js/rawlead-feed.js` | **2011** |
| `wordpress/.../assets/js/rawlead-cabinet.js` | **4175** |

Verify:

```bash
node --check wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js
node --check wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js
```

Browser не выполняет файл целиком → нет `Promise.all` init → нет fetch ленты; cabinet.js тоже мёртв.

## Fix (@coder P0)

1. Add trailing `'` on both lines above.
2. `node --check` both files green.
3. Bump `RAWLEAD_CHILD_VERSION` in `functions.php`.
4. Deploy theme to prod (rsync / existing deploy script).
5. Smoke: incognito `/lenta/` — карточки; login — `/cabinet/` boot.

## After hotfix

Resume § **O220-L1-PROMPT-R2** (radar `ai_analyze.py` only — unrelated).
