# 2026-06-13 — spam 422 · TG test group silent · ops logs/restart

**Symptoms (owner):**
- `POST …/tg-spam` → **422** (Network)
- Test group `https://t.me/+Z7HcnIAdSw9kY2U6` — message sent, no feed, accs «молчат»
- `/ops/` logs empty · `Radar: перезапуск` no visible effect
- Funnel all red · cycle 24+ min

---

## spam 422 — root cause (Lead verify)

`rawlead-api.php` spam proxy:

```php
rawlead_api_post('/v1/admin/leads/' . $id . '/tg-spam', [], $headers);
```

PHP `wp_json_encode([])` → body **`[]`** (JSON array).  
FastAPI `TgSpamPayload` expects **object** → **422 Unprocessable Entity**.

**Fix:** pass `(object)[]` or `'{}'` · same for `/hide` if broken · pytest proxy.

---

## TG test group

- Link in `TG_PUBLIC_FEED_ALLOWLIST.txt` + join queue `5177575757`
- acc1 file includes id (deploy 13.06)
- Silence + no feed may be: **radar cycle stuck** (24m) · handler not firing · L1 drop · chat_id mismatch (`5177575757` vs `-100…`)

**VPS checks (Mechanic/Coder):**
```bash
grep -E 'тг:пульс|тг:монитор|5177575757|test_bots|NewMessage' /opt/rawlead/data/radar_site.log | tail -40
systemctl status rawlead-radar
```

---

## ops — ✅ fixed t7 (Lead deploy 2026-06-13)

**Was:** auth `GET /ops/` **~14.6s** (SSR `fetch_dashboard`).

**Now:** `data=None` shell · prod auth **0.02s** · `ops-pult.js` 200.

**Owner smoke:** `/ops/` opens fast · logs Live · buttons work · banner → «Выполняем…».

---

## TG test group — ✅ fixed t6 (Lead deploy 2026-06-13)

**Was:** peer `-5177575757` vs message `-1005177575757` — silent drop.

**Now:** `_message_chat_listened` + `_chat_id_keys` in `tg_monitor.py` · radar restarted.

**Owner smoke:** send msg in test group → grep `тг:сообщ` + chat `5177575757` in log.

---

## Owner action now (updated 2026-06-13)

1. `/ops/` — **работает** после hard refresh ✅
2. «Проверить ссылки» — **504** → t10 (delist в HTTP >120s)
3. Логи — **каша** → t11 (`ops-pult.js` newline) + t12 (убрать ids dump)
4. Test group — post **текстом** · acc1 слушает · acc3 нет в file · последний `тг:сообщ` 10.06

---

## delist 504 — root cause (Lead verify)

`POST /ops/control` target=delist action=run → `_run_delist_batch_ops()` sync · limit=15 URL checks · nginx 120s timeout.

Scheduled delist OK: stats «13.06.2026 13:27 — 46/1».

---

## ops log «каша» — root cause

`ops-pult.js:154` — `line + "\\n"` (literal backslash-n) + inline spans in `<pre>`.

Server also dumps `ids=[…32 chats…]` at `тг:монитор:старт` (`tg_monitor.py:560`).

---

## TG test group — VPS facts (13.06)

- acc1: 32 peers incl. `-5177575757` ✅
- acc3: `telethon_chat_ids_acc3.txt` **нет** `5177575757` · `пропуск чата`
- `тг:сообщ …5177575757` last: **2026-06-10** — today's post **not in log**
- t6 chat_id match deployed — likely silent drop (no text) or acc3 gap

---

## Deploy 2026-06-13 (Lead)

**t10+t11+t13** on VPS via `deploy-o205-ops-spam-vps.py` · api+radar active.

**Owner smoke:** Ctrl+Shift+R `/ops/` · delist no 504 · logs построчно · test group → `тг:сообщ` or `тг:пропуск`.

---

## Queue

- **✅** t10 delist async · t11 log UI · t13 `тг:пропуск` — deployed
- **@coder:** t12 no `ids=[` startup · probe `str(path)` · t8 dashboard · t3 smoke
