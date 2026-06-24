# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md)

---

## Сейчас (2026-06-22)

**Стадия:** prod **Next** на `rawlead.ru` · API+радар+бот на VPS · **M1 реклама запущена** · первые посетители **~23.06**

### 🔴 M1 hot — реклама live

| # | Что | Почему | Статус |
|---|-----|--------|--------|
| **YOUDO-IMAP-ONLY** | Заказы **только из почты** · listing/antibot **выкл** · **last N + PG dedup** | Реклама · письма не доходят до ленты | **→ § CODER_PROMPT** P0 |
| **QUIZ-REDESIGN** | Переделать квиз | После стабильного YouDo | **P1 queued** |

**Для посетителя сейчас:** FL · Kwork · TG — **норм** · YouDo — **чиним IMAP** (не браузер).

### ~~YOUDO-DETAIL / listing~~ — ⏸ 2026-06-23

Решение owner: browser listing/click **не развиваем** · IMAP-only.

**Канон проблемы:** [`2026-06-16-youdo-antibot-browser.md`](../../problems/2026-06-16-youdo-antibot-browser.md) · O262g detail ServicePipe · golden baseline O268.

### ✅ Закрыто до M1

| Блок | Факт |
|------|------|
| **O280** WP → Next cutover | ✅ **2026-06-19** · nginx → `/var/www/rawlead.ru` (static export) |
| **O218 / PRE-ADS** | G0–G10 ✅ · stress 50 VU · security hotfix |
| **O200 L2/L3** | judge PASS · draft quality gate |
| **O271** | БД на VPS Postgres |
| **rode51.ru** | portfolio P2 live |

WP тема в repo — **legacy**, не на корне домена. Rollback: `/var/www/rawlead.ru-wp`.

### → Сейчас (owner)

**M1 wave 1** — реклама **запущена** · TG посевы · воронка `@rawlead_bot` · [`M1_SEEDING_CHECKLIST.md`](../marketing/M1_SEEDING_CHECKLIST.md)

**Smoke перед трафиком:** `/lenta/` FL+Kwork карточки + черновик · YouDo — карточки есть, ТЗ короткое (см. YOUDO-DETAIL).

### После wave 1 / фон (@coder)

| # | Что |
|---|-----|
| **YOUDO-IMAP-ONLY** | P0 · почта · **last N + PG dedup** · listing off |
| **QUIZ-REDESIGN** | P1 · после YouDo ✅ · product+design → coder |
| CSP/HSTS nginx | MiMo backlog |
| JWT httpOnly | XSS hardening |
| DB pool + feed COUNT | нагрузка >50 VU |
| O284 billing confirm | return URL cabinet |
| O207 TG funnel metrics | не блокер посевов |

### ⏸ Позже

ingest SLA · O73 heatmap · O92b pending_tags · api_server split (A13)

---

## Фазы vision §4 (сжато)

| Фаза | Статус |
|------|------|
| **0** · dogfood радар | ✅ |
| **E0–E5** · site + auth + cabinet | ✅ (Next) |
| **3f** · ИИ draft + L2/L3 | ✅ |
| **Launch** · trial + pay + pre-ads gate | ✅ gate |
| **GTM** · M1 посевы | **→ сейчас** |
| **v1** · scale + billing polish | backlog |

**Отменено:** mobile app · отдельный маркет-сайт · Freelancehunt

---

## O200 gate (reference)

L2 judge send **82.5%** · combined **4.25** · L3 uniq **3.04** · артефакт `data/preprod_o200_judge_human.md`

## Парсеры

FL · Kwork · TG · FR · FreelanceJob · Пчёл — ✅ prod · full TZ via HTTP detail.

**YouDo** — listing ✅ camoufox · **detail `/t{id}` ❌ ServicePipe** → snippet-only в ленте до § **YOUDO-DETAIL-BREAKTHROUGH** · код `fetch_youdo_detail_snapshot` есть, пробой антибота — нет.

---

Детали O207/O208 и старые волны → [`ROADMAP` archive](../archive/) · [`OWNER_INTENT.md`](OWNER_INTENT.md)
