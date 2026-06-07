# Для тебя

## Сейчас — E2E → vault (ingest O99 ✅ на VPS)

| Шаг | Что |
|-----|-----|
| 1 | **O97 + O99 ingest** ✅ — API/radar на VPS, browser FL/Kwork, hot L1 |
| 2 | **E2E** — Playwright + твой smoke на rawlead.ru |
| 3 | **Отклики (L2)** — отдельный чат: regen/judge, **не трогай** пока идёт `regen_shared_reply_drafts.py` |

**Прокси v2 + O99 browser** — на VPS. При `pool_exhausted` — `scripts/clear-vps-proxy-bans.py`, не путать с regen откликов.

**Runbook 2026-06-03** (L1 хвост · TG acc2 · YouDo): [`problems/2026-06-03-ingest-l1-tg-youdo.md`](problems/2026-06-03-ingest-l1-tg-youdo.md).

---

## L1 и очередь без разбора

| Что | Действие |
|-----|----------|
| Свежие без L1 (48 ч) | На VPS: `L1_BACKLOG_DRAIN=1` в `.env.site` — пачка L1 каждый цикл |
| Старый хвост (лишний OpenRouter) | `scripts/clear_l1_backlog.py --profile site --by-age --days-old 2 --apply` (сначала `--dry-run`) |
| Проверка | `/status` → «Без L1 (48 ч)»; лог `конвейер:L1=` |

---

## TG acc2 и join

- **Слушает** только чаты из `data/telethon_chat_ids_acc2.txt` (после join).
- **Волна v2:** 6 чатов в [`docs/ops/TG_JOIN_QUEUE_v2.csv`](docs/ops/TG_JOIN_QUEUE_v2.csv) — join ~15 мин между чатами.
- **`TG_JOIN_IN_TG_MAIN=1`** обязателен на VPS (иначе join не крутится в radar).
- Старые ~25 чатов из `TG_JOIN_QUEUE.csv` — отдельно: `tg_sync_chat_ids.py --account acc2`.

---

## YouDo / O63 secondary (2026-06-03)

| source | Статус |
|--------|--------|
| **Freelance.ru** | ✅ **25 новых** на VPS после O63-FIX deploy — идут в L1 |
| **FreelanceJob** | ✅ 40 скачано · filter 6 — ожидаемо, см. `FILTERS_SITE.md` |
| **YouDo** | ✅ **node-proxy RU** (3 слота) · smoke **50 задач** · radar 24/7 · фикс: Chrome UA + antibot `noscript` + ephemeral browser |
| **Пчёл** | парсер ок · на листинге часто 0 новых (floor/dup) |

Deploy: `scripts/deploy-youdo-browser-vps.py` · диагностика: `scripts/_diag_secondary_logs_vps.py` → `data/_diag_secondary_logs.txt`.

---

## Gate (простыми словами)

- **Complexity L1:** 1 вечер · 2 проект · 3 система · **4 без норм ТЗ**
- **Judge:** насколько L1 угадал — **≥70% ok** или avg **≥3** из 4
- **L1 usable:** как O72e — **≥70%**

---

---

## Два бота (не путать)

| Бот | Зачем | Что приходит в ЛС |
|-----|--------|-------------------|
| **@FLPARSINGBOT** | Админ / dogfood | Карточки бирж под твои фильтры; **прокси** (бан, переключение, «осталось N/M»); `/status` с биржами и Neon consumer |
| **@rawlead_bot** | Продукт | Match подписчикам; **не** служебные алерты парсера |

**Прокси:** пуши только в чат **@FLPARSINGBOT** (не @rawlead_bot). Если видишь «FLPARSING · прокси» в чате RawLead — на VPS в `.env.legacy` был чужой токен; код теперь проверяет getMe. Проверка: `python scripts/verify-vps-bot-identity.py` → legacy=@FLPARSINGBOT, site=@rawlead_bot.

**TG Bot API failover (O120):** пул из `TG_PROXY_URL` + `TELETHON_PROXY_ACC1/2/3` (или явный `TG_PROXY_URLS`). При смерти слота бот сам переключается — **не нужно** править `.env`. В @FLPARSINGBOT придёт **`FLPARSING · TG Bot API прокси`**: какой слот забанен, причина (таймаут/прокси), на какой переключились, «свободно N из M». Опц. `TG_PROXY_DIRECT=1` — последний fallback direct с VPS. Состояние: `data/tg_proxy_pool.json`.

**Проверка:** `/status` в @FLPARSINGBOT → блоки FL (primary) и secondary.

## Биржи: датчики O104 ✅ на VPS

| Куда | Что |
|------|-----|
| **@FLPARSINGBOT** `/status` | 🟢🟡🔴 по каждой бирже + причина |
| **@FLPARSINGBOT** push | `🔴 YouDo · …` — max раз в 30 мин |
| **`/ops/`** | «Биржи и скорость» · lag минуты |
| **`radar_site.log`** | `health:youdo status=ok` |

**Regen/judge в консоли не ломает:** O104 на VPS (SQLite + log); regen/judge — Neon `reply_draft`, отдельный процесс.

## O99 ingest — **включено на VPS** (2026-06-03)

1. **FL/Kwork** — браузерный fetch + fallback httpx (`EXCHANGE_LISTING_BROWSER=1`).
2. **Лента** — только после L1; hot drain после FL/Kwork, до secondary.
3. **Secondary** — каждый 2-й цикл; свои прокси, не банят primary.
4. **L1:** 4 воркера, два OpenRouter-ключа (см. `.env.site`).
5. **Отдельно:** regen **текстов отклика** (`regen_shared_reply_drafts.py`) — **не** ingest; идёт в другом чате.

Канон: [`KAK_ETO_RABOTAET.md`](KAK_ETO_RABOTAET.md) · [`STATUS.md`](team/common/STATUS.md).

---

_Lead · 2026-06-03_
