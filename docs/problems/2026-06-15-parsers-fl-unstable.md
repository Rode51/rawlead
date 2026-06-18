# Парсеры «все упали» — triage 2026-06-15

**Owner:** «опять все парсеры упали»  
**Lead triage:** VPS log + Neon read-only · ~12:00 MSK

---

## Короткий ответ

**Не все.** Радар **active**. Сломан по сути **FL** (нестабильно `parsed=0`). **Kwork/YouDo/TG/secondary** качают; в ленте «тишина» из‑за **fresh=0** (дубли) + **FL мёртв** + плохие L1-карточки (YouDo физуслуги).

| Source | VPS сейчас | Neon 24h | Суть |
|--------|------------|----------|------|
| **FL** | 🔴 `parsed=0` ↔ 30 · `pool_exhausted alive=0/25` | last **2026-06-14 16:46 UTC** | Прокси-пул сжигается · O222 не задеплоен |
| **Kwork** | 🟡 `parsed=36 fresh=0 pages=3` | last **03:28 UTC** | Парсер OK · **нет новых** на 3 страницах |
| **YouDo** | 🟢 `parsed=50 fresh=50 new=3` | last **03:28 UTC** | Listing OK · **detail stub** ~1700b → L1 галлюцинации |
| **TG** | 🟢 acc1–3 connected | активен | Много `skip:dup_content` |
| **freelance_ru/job/pchyol** | 🟢 health ok | есть вставки | filter skip часть |

---

## FL — корень (recurring)

См. [`2026-06-15-fl-parsed-zero-pool-exhausted.md`](2026-06-15-fl-parsed-zero-pool-exhausted.md).

1. 25 residential + 4 DC → antibot → ban TTL 1h → **`alive=0/25`** → `parsed=0`.
2. Краткие окна DC `alive=4/4` → `parsed=30` но **`fresh=0`**.
3. **Fix в коде:** § **O222-FL-HARD-RESET** (`CODER_PROMPT`) — stop cascade on first ban.

**Ops (Lead 2026-06-15):** `scripts/clear-vps-proxy-bans.py` + restart radar ✅ → после ~2 мин **`listing:fl parsed=30`** (11:58 MSK). Без **O222** снова сгорит через 1–2 ч.

---

## Kwork — не «упал», а «нет новых»

`parsed=36 pages=3` каждый цикл. Новые заказы на Kwork **ниже rank-36** или режутся **word filter** → `fresh=0`.

Follow-up: § O213 уже в prod; owner проверить `KWORK_PROJECTS_URL` в `.env`.

---

## YouDo — ingest есть, качество L1 плохое

Пример: [t14857148](https://youdo.com/t14857148) — перевозка гидробортом → L1 выдал WordPress+API → «ИДЕАЛЬНО ✦».

**Fix:** § **O223-YOUDO-L1-GUARD** (`CODER_PROMPT`).

---

## Verify done

- [ ] `listing:fl parsed>=25` 3 цикла подряд после clear bans
- [ ] Neon: новый `source=fl` за 2h
- [ ] `/ops/` FL не 🔴 pool_exhausted
- [ ] O222 deploy → no cascade

---

_Lead triage 2026-06-15_
