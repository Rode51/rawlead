# 2026-06-12 — TG AuthKeyDuplicated (owner PC login)

**Статус:** ✅ **acc1+acc2+acc3 auth** · ✅ **acc3 monitor ready** (2 чата v2 join) · ⏳ **O188 wave4** owner не давал · v2 join идёт 4/час

---

## Симптом

`radar_site.log` ~14:33–14:41 UTC:

```
тг:монитор ошибка: AuthKeyDuplicatedError('The authorization key (session file) was used under two different IP addresses simultaneously...')
тг:монитор ошибка: OperationalError('database is locked'); переподключение через 30с
```

**Следствие:** TG-лиды с **сгоревшего acc** не идут · монитор крутит reconnect каждые 30с впустую.

---

## Причина (подтверждено owner)

Owner **случайно залогинился тем же acc с ПК**, пока VPS монитор держал ту же `.session`. Telegram **убивает ключ** — нужна **новая сессия на VPS**.

**Правило:** acc1/acc2/acc3 — **только VPS** · **никогда** с ПК / Prime / Telegram app.

---

## Решение (Mechanic 2026-06-12)

### t1 — Identify ✅

| acc | session | статус |
|-----|---------|--------|
| acc1 | `+7XXXXXXXXX1_telethon.session` | ✅ allowlist ok · `тг:монитор:acc1: ready` 15:00:52 UTC |
| acc2 | `+7XXXXXXXXX2_telethon.session` | ✅ allowlist ok · `тг:монитор:acc2: ready` 15:00:53 UTC |
| **acc3** | **`7XXXXXXXXX4_telethon.session`** (+351924778041) | ❌ **`allowlist:acc3:connect:AuthKeyDuplicatedError`** с 14:32 UTC |

Лог: `grep allowlist …14:32` → acc1 ok · acc2 ok · **acc3 AuthKeyDuplicated**.

### t2 — Replace session ⚠️ blocked

1. Backup сгоревшего на VPS: `7XXXXXXXXX4_telethon.session.burned-2026-06-12` (40960 B)
2. Restore с ПК `Desktop\Parser\7XXXXXXXXX4_telethon.session` (36864 B, mtime до инцидента) → **тоже AuthKeyDuplicated** (ключ мёртв глобально у Telegram)
3. **Interim:** `TELETHON_MONITOR_ACCOUNTS=acc1,acc2` в `.env.site` + `.env` на VPS · `systemctl restart rawlead-radar` — acc3 reconnect больше не роняет весь tg_main

### t3 — Owner action (blocker acc3)

Owner path **2026-06-12:** `C:\Users\hramo\Desktop\Parser\7XXXXXXXXX4_telethon.session` — **AuthKeyDuplicated** on VPS (dead).

Owner **2026-06-12 ~15:14:** `C:\Users\hramo\Downloads\7XXXXXXXXX4.json` (547 B) — **JSON only**, no paired `.session` in Downloads · Telethon radar **needs `.session`**, not JSON alone (see `docs/ops/TELEGRAM_LOGIN.md` § «Что лежит у тебя»).

**⚠️ Lead:** Re-uploading Desktop `.session` or JSON-only **will not** fix acc3. Need **untouched `.session` from retriv zip** (same purchase) **never opened on PC**, or **new Session+Json from seller**.

Нужна **свежая Session+Json** продавца для **7XXXXXXXXX4** (+351924778041):

1. Найти **оригинал в архиве покупки (retriv)** — файл, который **никогда** не открывали на ПК после покупки
2. Если в архиве только мёртвый ключ → **перекупить / запросить новую Session+Json у продавца**
3. Импорт в Telethon **только через VPS-прокси** `168.90.199.99` (acc3) · **не** открывать на ПК
4. scp новый `7XXXXXXXXX4_telethon.session` → `/opt/rawlead/data/sessions/` · `chown rawlead:rawlead`
5. Вернуть `TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3` · restart radar · DoD: `тг:монитор:acc3: ready`

**Заметка:** на ПК сегодня появился `7XXXXXXXXX5_tdata.zip` (11:39) — это **acc4**, не acc3; сгорел именно acc3.

### t4 — Owner: **новый acc3** (2026-06-12 ~15:18) ✅ unblock

| | |
|---|---|
| **Файл** | `C:\Users\hramo\Desktop\Parser\239823951_telethon.session` (28672 B) |
| **Старый acc3** | `7XXXXXXXXX4` — **снять**, ключ мёртв |
| **JSON** | нет рядом — для Telethon достаточно `.session` |
| **Owner** | «Новый акк» · к Mechanic **ещё не ходил** |

**⚠️ Критично:** файл создан на ПК **15:18** — **не** запускать `tg_list_dialogs` / Prime / Telegram на ПК с этой сессией. Первый login — **только VPS** через `TELETHON_PROXY_ACC3` (`168.90.199.99`), иначе снова `AuthKeyDuplicated`.

### t4 — Mechanic swap ✅ (2026-06-12 ~15:21–15:30 UTC)

| Шаг | Result |
|-----|--------|
| stop radar | ✅ |
| backup dead `7XXXXXXXXX4*` | ✅ → `*.burned-2026-06-12-t4` |
| upload `239823951_telethon.session` | ✅ 28672 B · `chown rawlead:rawlead` |
| `TELETHON_SESSION_ACC3` | ✅ `/opt/rawlead/data/sessions/239823951_telethon` (.env + .env.site) |
| `TELETHON_MONITOR_ACCOUNTS` | ✅ `acc1,acc2,acc3` |
| `tg_list_dialogs --account acc3` (VPS) | ✅ `777000 Telegram` |
| `allowlist:acc3:ok` | ✅ **15:27:37** `user_id=8954350656` |
| `AuthKeyDuplicated` after swap | ✅ **none** (last **15:00:11** pre-swap) |
| `тг:монитор:acc3: ready` | ⏳ **нет** — новая сессия **не в чатах** из `telethon_chat_ids_acc3.txt` (12× «пропуск чата» → disconnect); join queue 11/13 `done` для **старого** acc |

**Follow-up (owner / @coder):** re-join acc3 в 12 tier-a чатов + `test_bots` pending → restart radar → `тг:монитор:acc3: ready`. См. § t4 step 8 ниже.

**Mechanic t4 — swap acc3 on VPS** (archive checklist)

1. `systemctl stop rawlead-radar`
2. Backup dead: `7XXXXXXXXX4_telethon.session*` → `*.burned-*` (if still present)
3. scp `239823951_telethon.session` → `/opt/rawlead/data/sessions/` · `chown rawlead:rawlead`
4. VPS `.env.site` + `.env`: `TELETHON_SESSION_ACC3=/opt/rawlead/data/sessions/239823951_telethon` (no `.session` suffix)
5. `TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3` · restart radar
6. Probe: `tg_list_dialogs.py --account acc3` **on VPS only** (proxy acc3)
7. DoD: `allowlist:acc3:ok` · `тг:монитор:acc3: ready` · no `AuthKeyDuplicated` 10 min
8. **Join:** новый номер — чаты acc3 могут быть пусты; сверить `telethon_chat_ids_acc3.txt` / join queue if needed (отдельный шаг owner)

**Files (VPS ops, not git):** session path · `TELETHON_MONITOR_ACCOUNTS` · optional update `docs/ops/TELEGRAM_ACCOUNTS.md` after verify.

---

## Изменённые файлы (VPS ops, не git)

| Что | Где |
|-----|-----|
| `TELETHON_MONITOR_ACCOUNTS=acc1,acc2,acc3` | `/opt/rawlead/.env.site`, `/opt/rawlead/.env` |
| `TELETHON_SESSION_ACC3=…/239823951_telethon` | `/opt/rawlead/.env.site`, `/opt/rawlead/.env` |
| new session | `/opt/rawlead/data/sessions/239823951_telethon.session` |
| backup dead session | `/opt/rawlead/data/sessions/7XXXXXXXXX4_telethon.session.burned-2026-06-12-t4` (+ nested `.burned-2026-06-12`) |
| ops script (local) | `scripts/_tmp_tg_acc3_swap_239823951_vps.py` |
| restart | `systemctl restart rawlead-radar` |

---

## Как проверить

```bash
grep AuthKeyDuplicated /opt/rawlead/data/radar_site.log | tail -1   # до 15:00:11 UTC, после fix — нет новых
grep 'тг:монитор:acc.: ready' /opt/rawlead/data/radar_site.log | tail -4
grep allowlist /opt/rawlead/data/radar_site.log | tail -4            # acc1+acc2 ok, acc3 не в списке
systemctl is-active rawlead-radar                                     # active
```

---

## Задача Mechanic (archive)

### t1 — Identify burned account(s)

```bash
grep AuthKeyDuplicated /opt/rawlead/data/radar_site.log | tail -5
grep 'тг:монитор:' /opt/rawlead/data/radar_site.log | tail -30
# which accN fails before/after error
python scripts/tg_list_dialogs.py --account acc1  # expect fail
python scripts/tg_list_dialogs.py --account acc2
python scripts/tg_list_dialogs.py --account acc3
```

| acc | VPS session file (typical) |
|-----|----------------------------|
| acc1 | `+7XXXXXXXXX1_telethon.session` |
| acc2 | `+7XXXXXXXXX2_telethon.session` |
| acc3 | `7XXXXXXXXX4_telethon.session` |

### t2 — Replace session on VPS only

1. `systemctl stop rawlead-radar`
2. Backup dead: `mv …_telethon.session …_telethon.session.burned-2026-06-12`
3. **Restore fresh session** (pick one):
   - **A:** owner PC backup **до** инцидента (не файл от сегодняшнего входа) → scp to `/opt/rawlead/data/`
   - **B:** seller original Session+Json from owner archive
   - **C:** if A/B dead too → escalate owner (Session+Json без SMS)
4. `chown rawlead:rawlead` · paths match `.env.site` `TELETHON_SESSION_*`
5. `systemctl start rawlead-radar`
6. DoD: `тг:монитор:accN: ready` · **no** AuthKeyDuplicated 10 min · TG leads in Neon

### t3 — Optional hardening

- Document in `FOR_YOU.md`: «не открывать acc на ПК»
- Alert if AuthKeyDuplicated → push @FLPARSINGBOT once

---

## Owner (done / pending)

- ✅ Вышел с ПК · обещал не логиниться снова
- ✅ Новый acc3: `239823951_telethon.session` — Mechanic залил на VPS (**не открывать на ПК**)
- ⏳ **Join acc3:** новый номер не в 12 чатах — нужен re-join (queue / owner smoke `test_bots` pending)

---

## Verify (Lead 2026-06-12 ~15:08 UTC)

| Check | Result |
|-------|--------|
| Last `AuthKeyDuplicated` | **15:00:11** — before restart; **no new** after |
| `тг:монитор:acc1: ready` | **15:00:52** ✅ |
| `тг:монитор:acc2: ready` | **15:00:53** ✅ |
| `тг:монитор:acc3: ready` | **нет** (acc3 disabled) |
| `TELETHON_MONITOR_ACCOUNTS` | `acc1,acc2` |
| `allowlist` after fix | acc1 ok · acc2 ok · acc3 not polled |
| `здравье:ок` / `тг:пульс` | **15:02–15:06** — monitor alive |

**DoD acc1+acc2:** ✅ · **DoD acc3 session:** ✅ · **DoD acc3 monitor:** ⏳ join 12 чатов

## Verify (Lead 2026-06-12 ~15:42 UTC)

| Check | Result |
|-------|--------|
| `239823951_telethon.session` on VPS | ✅ 28672 B |
| `TELETHON_SESSION_ACC3` | ✅ `/opt/rawlead/data/sessions/239823951_telethon` |
| `TELETHON_MONITOR_ACCOUNTS` | ✅ `acc1,acc2,acc3` |
| `allowlist:acc3:ok` | ✅ **15:29:52** `user_id=8954350656` |
| `AuthKeyDuplicated` after swap | ✅ **none** (last **15:00:11** pre-swap) |
| `тг:монитор:acc3: ready` | ❌ **нет** — 12× «пропуск чата» → «ни один чат из списка не найден» |
| acc1+acc2 | ✅ `ready` **15:30:16** |

**Lead verdict:** swap **принят** · acc3 **живой**, но **не слушает** — новый номер не в чатах · **→ join queue acc3**

## Verify (Lead 2026-06-12 ~16:30 UTC)

| Check | Result |
|-------|--------|
| `тг:монитор:acc3: ready` | ✅ **15:56:36** · `чатов=1` → **2** после join |
| `telethon_chat_ids_acc3.txt` | **2** ids: normrabota, designhunters (+ join in progress) |
| `tg_join.log` | ✅ `join:ok acc3` **15:53** normrabota · **16:10** designhunters |
| `AuthKeyDuplicated` after swap | ✅ **none** (last **15:00:11**) |
| acc3 `OperationalError locked` | ⚠️ **16:20–16:26** intermittent (session contention) |
| **O188 v3 queue** | ❌ **not deployed** — VPS still `TG_JOIN_QUEUE_v2.csv` · **4/h** not 10/h |
| `тг:join:` in `radar_site.log` | ❌ not yet (O188 t3 pending) |

**Lead verdict:** Mechanic t4 **✅** · acc3 listen **partial** (v2 backlog join auto) · **O188 → owner handoff @coder**
