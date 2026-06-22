# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md)

---

## Сейчас (2026-06-22)

**Стадия:** prod **Next** на `rawlead.ru` · API+радар+бот на VPS · **M1 реклама запущена** · первые посетители **~23.06**

### 🔴 M1 hot — риск для новых юзеров

| # | Что | Почему срочно | Статус |
|---|-----|---------------|--------|
| **YOUDO-DETAIL** | Пробой **detail-fetch** YouDo (`/t{id}`) — полное ТЗ, не snippet | ServicePipe блокирует detail на VPS · L1/черновики YouDo слабее FL/Kwork · в ленте 4219 лидов с body 60–100 chars | **→ @coder P0** |
| **mitigation** | Snippet-режим в ленте | `YOUDO_DETAIL_MIN_CHARS=0` · restore 4219 visible | ✅ 2026-06-22 |

**Для посетителя сейчас:** FL · Kwork · TG — **норм** (полное ТЗ) · YouDo — **есть в ленте**, но описание короткое · фильтры — ✅ после hotfix 22.06.

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
| **YOUDO-DETAIL** | § `CODER_PROMPT` · detail breakthrough ServicePipe |
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
