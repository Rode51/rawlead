# 2026-06-13 — TG в ленте ~15 за 3 недели (owner)

**Owner:** «за 3 недели всего 15 сообщений с TG в ленте — не может такого быть».

**Lead VPS verify (radar_site.log):**

| Метрика | Значение |
|---------|----------|
| `тг:сообщ` июнь 2026 | **548** (радар **принимает**) |
| `visible=1` в логе (всё время) | **36** |
| `visible=1` июнь | **23** |
| `skip:ai` (в т.ч. МИМО) | **198** |
| `pipeline:skip filter` | **348** |
| Listen сейчас (acc1+2+3) | **32+25+7 = 64** чата |
| Join queue `done` (owner intent) | **~127** — разрыв file↔listen |

**Вывод:** проблема **не** «ничего не слушаем». Воронка: **много сообщений → L1/AI/filter режет → в `/lenta/` почти ничего**.

**Побочный:** t13 `тг:пропуск reason=не_слушаем` на **все** чаты вне listen → лог врёт («всё мимо»).

---

## Гипотезы (приоритет)

1. **Listen gap** — вступили 127, слушаем 64; acc2/3 не в test group file; чужие `не_слушаем` ≠ «не работает».
2. **L1/AI слишком жёсткий для TG** — `skip:ai:МИМО` доминирует; vacancy-like посты owner не проходят.
3. **acc1 test group** — пост виден acc2 `не_слушаем`, acc1 молчит (отдельный баг).
4. **Ops UX** — нет сводки «принято / в ленту / отфильтровано» по acc.

---

## Deploy 2026-06-13 (Lead) — O206 ✅

`deploy-o206-tg-funnel-vps.py` · radar restart · audits on VPS.

**VPS facts:**
- acc1 queue **72 done** · file **32** — gap 40 chat_ids
- funnel 7d: **282** → **54** visible (19%) · filter &gt; AI
- t1: interest-set logging live

**Owner smoke:** ✅ test group — **мгновенно** (owner принял 2026-06-13).

---

## acc1 handler deaf — t3b fix (Lead verify 23:06)

**Before (22:49):** msg=70 → only acc2 `не_слушаем`, acc1 silent.

**After t3b deploy:**
- `handler_ok` acc1 peers=32 test_group_peer=1
- `sync ok` · `membership_ok=True`
- `test_group join_ok` 23:05 (re-join path fired)
- acc1 handler alive: `тг:пропуск` other chats 23:00

## t3c — fix ✅ (Lead verify 23:28)

**Deploy:** `deploy-o206-t3c-watchdog-vps.py` · restart 23:26:43

- `_client_connected` sync (no await)
- `_reconnect_session` per-acc (no mass disconnect)
- Pulse 23:28:46: **connected=1** acc1/2/3
- **No** reconnect death loop after deploy
- acc3 handlers live 23:27+

**Open:** t2b sync · O207

**Owner 2026-06-13:** принял · приходит **мгновенно**.

---

## Queue

- **✅** O206 t3c
- **→** t2b sync · owner smoke · **O207** plan

---

## План O207 — доказать воронку + filter lab

**Owner:** «надо проверять, есть ли заказы в группах; точно ли только filter; настраивать filter по-другому».

### Вопросы, на которые отвечаем

| # | Вопрос | Как |
|---|--------|-----|
| 1 | Группа **молчит** или мы **не слушаем**? | per-chat `last_msg` · join=listen audit |
| 2 | Сообщения **приходят**, но **не в ленту**? | truth ladder: received → skip_reason → visible |
| 3 | Отсев **только filter/L1** или ещё spam/AI? | breakdown по стадиям · не один агрегат |
| 4 | Filter **слишком жёсткий** на реальных заказах? | sample audit owner + replay lab |

### Фазы (см. `ROADMAP` § O207)

- **A** truth ladder + Neon
- **B** chat health в ops
- **C** sample skip audit (owner labels)
- **D** filter lab replay
- **E** golden posts test group

**Порядок:** t3c → t2b → O207 A→E · **не** ужесточать filter до sample audit.

---

## Owner labeling (O207-t4)

1. Coder на VPS/local: `python scripts/tg_history_sample.py --account acc1 --max-chats 15 --per-chat 10` → `data/tg_history_sample.json`
2. Скопировать в `data/tg_history_sample_labeled.json` и у каждой строки в `rows[]` проставить `"owner_label": "vacancy"` | `"noise"` | `"unsure"` (или `null`).
3. Прогнать offline: `python scripts/tg_filter_replay.py --in data/tg_history_sample_labeled.json` → `data/tg_filter_replay.json` + summary в консоли.
4. Сверить: где `owner_label=vacancy`, но `stage=filter|spam` — кандидаты на смягчение filter/L1 (**отдельная задача O207b**, не менять filter в O207).
5. Baseline из лога: `python scripts/tg_funnel_audit.py --log data/radar_site.log` → `days_7` / `days_30` в JSON + `data/tg_funnel_audit_human.md`.
