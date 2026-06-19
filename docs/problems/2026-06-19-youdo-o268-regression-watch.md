# YouDo O268 — регрессия watch (1712b loop)

**Дата:** 2026-06-19 ~02:17 UTC (обновлено после hard reset)  
**Статус:** ✅ **O269 deploy 2026-06-19** — watch `sticky_reload` / `warm=1`  
**Родитель:** [`2026-06-19-youdo-o268-breakthrough.md`](2026-06-19-youdo-o268-breakthrough.md)

---

## Решение (Mechanic O269 · 2026-06-19)

**Корень:** O268 `YOUDO_STICKY_AFTER_OK=1` гонял slot1 через **one-shot** `youdo_fetch_worker.py` (ephemeral) до in-memory `_YOUDO_SESSION_LISTING_OK`. Subprocess умирает после fetch → sticky worker **никогда** не держит tab между `fetch_every_n` циклами → в логе `sticky_reload=0`, `warm=1=0` за всю историю.

**Fix:** disk-profile-as-session + worker survival между `fetch_every_n`:

1. **Disk profile gate** — если `data/youdo_{hint}_g2/cookies.sqlite` живой (>512 B), slot1 идёт в **long-lived** `youdo_sticky_worker.py` (не ephemeral one-shot).
2. **Worker survival (O269)** — stderr drain · sticky PID в `cleanup_stale` keep-set · `ping` keepalive на `fetch_every_n` skip · log `sticky_worker_died` при respawn.

Ephemeral-first остаётся только для **пустого/wiped** profile (breakthrough path 10:04).

| Файл | Изменение |
|------|-----------|
| `src/exchange_browser_fetch.py` | `_youdo_disk_profile_has_session()` · gate · keepalive · stderr drain |
| `src/youdo_parser.py` | `youdo_sticky_keepalive_ping()` on skip |
| `scripts/youdo_sticky_worker.py` | `cmd=ping` |
| `tests/test_o268_youdo_recovery.py` | disk session → sticky |

**Как проверить на VPS (после deploy `exchange_browser_fetch.py` + restart radar):**

```bash
python scripts/_probe_youdo_sticky.py
# или:
grep 'sticky_reload' /opt/rawlead/data/radar_site.log | tail -15
grep 'youdo:trace stage=sticky_' /opt/rawlead/data/radar_site.log | grep -c 'warm=1'
```

Ожидание: после 1-го `sticky_goto` (warm=0) и restore golden profile — на **следующем** fetch-цикле (`fetch_every_n=4`) строки `stage=sticky_reload warm=1`.

**Deploy:** Lead — upload `src/exchange_browser_fetch.py` · `systemctl restart rawlead-radar` (или `deploy-o268` upload path).

---

## Симптом (owner)

«Смотри логи, опять антибот после хардресета» — manual hard reset из `/ops/`, через ~30 с снова 1712b.

## Факты VPS (probe 2026-06-19 ~02:17 UTC)

| Метрика | Значение |
|---------|----------|
| **Hard reset сработал** | `restart_source` youdo · `cycle_n` сброшен `213 → 1` (~02:10 UTC) |
| **Ok после reset** | `02:06:13` и `02:10:30` · `outcome=ok parsed=50` · DC `185.147.131.15:8000` |
| **ingest после reset** | `new=29` и `new=7` |
| **Регрессия снова** | `02:11:02 UTC` — через **32 с** после последнего ok · спираль `html_len=1701` |
| **Профиль на диске** | `data/youdo_*` — **пусто** (golden tar **не** восстановлен) |
| **Golden backup** | `backups/youdo_profile_g2_2026-06-19.tar.gz` — **есть** (66 MB) |
| **sticky_goto >100k** | последний `00:45:22` — после reset ok **без** новой sticky в логе |

**Вывод:** hard reset **не бесполезен** — дал 2 успешных цикла. Но без restore golden profile DC быстро снова в ServicePipe shell. Это **шаг 3 playbook**, не повтор hard reset.

### Хронология reset (UTC)

```text
02:05:53  fetch:youdo start (cycle_n=213)
02:06:13  outcome=ok parsed=50          ← ok до/во время reset
02:09:49  sticky_teardown
02:10:14  cycle_n=1                     ← радар после ops restart
02:10:30  outcome=ok parsed=50          ← ok после reset
02:11:02  html_len=1701 antibot_hit=1   ← снова SP (тот же fetch / carousel)
02:11–02:17  непрерывная спираль 1712b
```

---

## Симптом (ранее 01:53)

«YouDo опять упал» — в ленте старые заказы / ops 🔴 antibot.

## Факты VPS (probe 2026-06-19 01:53)

| Метрика | Значение |
|---------|----------|
| Последний **успех** (до reset) | `01:41:32 UTC` · `outcome=ok parsed=50` · DC `185.147.131.15:8000` |
| Последний **ingest 50** | `new=33` (цикл до регрессии) |
| **Регрессия с** | `~01:53 UTC` — спираль `html_len=1701` · `antibot_hit=1` · ServicePipe shell |
| **sticky_goto >100k** | последний в логе `00:45:22` (271KB) — после 01:10/01:41 ok без новой строки sticky в tail |
| **Сейчас** | `youdo:skip fetch_every_n=4` + `ingest done=0` — **норма между циклами**, не путать с полным падением |
| **health:youdo** | может показывать `parsed=50` из **кэша** последнего ok — карточка зелёная при живом antibot |

**Паттерн:** 4–6 ч стабильно (O268) → сессия/Camoufox ловит **1712b** → carousel крутится без `sticky_goto` 270k → ingest 0 на fetch-циклах.

---

## Паттерны в логе (что смотреть)

| Паттерн | Значение | Действие |
|---------|----------|----------|
| `sticky_goto html_len=27xxxx` | ✅ пробили SPA | ничего |
| `fetch:youdo outcome=ok parsed=50` | ✅ listing | ничего |
| `youdo:ingest done=50 new=N` | ✅ в БД | ничего |
| `html_len=1701` + `antibot_hit=1` | 🔴 ServicePipe shell | см. playbook ниже |
| `youdo:skip fetch_every_n` | ⏸ каждый 4-й цикл | **не паниковать** |
| `Connection closed` / `html_len=0` | 🔴 worker crash | hard reset |
| `dc_alive=0/4` | 🔴 все DC в бане | ops «Сбросить баны YouDo» |
| нет `outcome=ok` **>45 мин** | 🔴 stuck | hard reset → restore profile |

**Эталон ok-строки:** golden doc § «Эталонная строка лога».

---

## Playbook владельца (без кода)

### 1. Быстрая проверка (2 мин)

На VPS или через Lead:

```bash
grep 'fetch:youdo outcome=ok' /opt/rawlead/data/radar_site.log | tail -3
grep 'youdo:ingest done=50' /opt/rawlead/data/radar_site.log | tail -3
tail -30 /opt/rawlead/data/radar_site.log | grep -i youdo
```

Локально: `python scripts/_probe_youdo_now.py`

### 2. Если 1712b >30 мин подряд

1. **`/ops/`** → Ctrl+Shift+R (свежий JS) → **Hard reset YouDo** (не «restart radar» вслепую).
2. Подождать **1 полный fetch-цикл** (~15 мин, `fetch_every_n=4`).
3. Снова grep: ждём `sticky_goto html_len>100000` или `outcome=ok`.
4. **Если ok был, но через 1–2 мин снова 1712b** — hard reset уже отработал; сразу **шаг 3** (restore golden tar). Повторный reset не поможет.

### 3. Если hard reset не помог (2 цикла **или** ok→1712b за минуту)

**Restore golden profile** (не rm вручную):

```bash
cd /opt/rawlead/data
sha256sum backups/youdo_profile_g2_2026-06-19.tar.gz
# bd854d5cad868637973cf616e6ecd637153de34bb6cdf2e1e34078064022ef68
sudo -u rawlead tar -xzf backups/youdo_profile_g2_2026-06-19.tar.gz
systemctl restart rawlead-radar
```

### 4. Что записать в чат (для @mechanic)

Скопируй **одним блоком**:

- время последнего `outcome=ok` (UTC)
- 5–10 строк tail с `html_len=` / `antibot`
- был ли hard reset из ops (да/нет)
- `ls -la data/youdo_185.147.131.15:8000_g2/cookies.sqlite` (размер/дата)
- скрин `/ops/` воронка YouDo

### 5. **Не делать** без Mechanic

- `rm -rf data/youdo_*`
- менять `YOUDO_PROFILE_GENERATION`
- включать RU burst «чтобы пробить» (дорого, не стратегия)
- деплой нового YouDo-кода «на всякий случай» без тикета

### 6. Почему auto hard reset **не сработал** (O268)

**Hard reset есть** (`youdo_hard_reset`, ops, `YOUDO_HARD_RESET_FAILS=1` на VPS). Но **O268** специально **отключил** auto hard reset на **первый** soft ServicePipe fail:

```text
hard_reset_eligible = streak >= 1
  AND NOT (sticky_warm AND streak == 1)
  AND NOT (streak == 1 AND soft_sp_fail)   # ← 1712b попадает сюда
```

При `YOUDO_SOFT_SERVICEPIPE_BAN=1` первый 1712b в цикле → **cooldown 30 мин**, не teardown. Carousel внутри одного fetch крутит antibot много раз, но **streak часто остаётся 1** → hard reset не вызывается (проверено: в логе **нет** `hard_reset` после 2026-06-18 13:45, хотя 1712b шёл 2026-06-19 01:53+).

**Ручной** hard reset из `/ops/` или restore golden profile — по-прежнему рабочий путь.

**→ O269:** пересмотреть policy — например hard reset после N×1712b в одном fetch или при `sticky_warm` + нет `html_len>100k` 45 мин.

---

## Стабилизация (→ @mechanic O269)

| Идея | Зачем |
|------|--------|
| Auto **profile restore** из tar после N×1712b без sticky ok | не ждать ручного restore |
| **Cooldown** carousel: не крутить 4 слота подряд на poisoned cookies | меньше SP lock |
| **Sticky TTL** жёстче: `YOUDO_STICKY_MAX_AGE_SEC` + force ephemeral после 1712b | свежий профиль без wipe |
| **Alert** в ops: «нет outcome=ok 45m» | owner видит до ленты |
| Сохранять **debug HTML** 1712b раз в сутки для diff | понимать смену SP |

---

## Probe scripts (repo)

- `scripts/_probe_youdo_moment.py` — ingest + tail
- `scripts/_probe_youdo_now.py` — sticky + env + profile

---

_Lead Architect · 2026-06-19_
