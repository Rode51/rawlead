# STATUS

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.12** · [`ROADMAP.md`](../architect/ROADMAP.md)

**Очередь:** [`TASKS.md`](TASKS.md)

> Hot ≤80 строк.

---

## O109 ✅ Lead verify + VPS (2026-06-04)

**Theme:** **1.18.6** · `deploy-o109-bot-deeplink-vps.py` OK · curl `1.18.6`

**Симптом (владелец):** push Match 82% Kwork #3190279 — в `/lenta/` карточки нет; кнопка «Лента» вела в общую ленту.

**Причина:** O65 delist ложный `source_gone` — маркер `"404"` в HTML Kwork; push успел до скрытия.

**Fix (Coder, § O109):** убран `"404"` из `_KWORK_GONE_MARKERS` · grace **6 ч** после L1 · relist **234** kwork · bot «Лента» → `/lenta/?lead={id}` · scroll + pulse `.rl-lead-card--push-focus`.

**Verify:** lead **#11837** в feed API ✅ · `GET /wp-json/rawlead/v1/leads/11837` ✅ · tests **9/9**

**Процесс:** код в сессии до ужесточения `lead-no-code` — приёмка Lead retroactive · rules A+B+C **2026-06-04**

**Owner:** новый push → deep link; старый push — вручную [`/lenta/?lead=11837`](https://rawlead.ru/lenta/?lead=11837)

---

## O108-BC ✅ (2026-06-04)

**Theme:** **1.18.5** · TZ attachments B+C · TG **21** канал в `PUBLIC_FEED_SOURCES` · tests **31/31**

---

## PRE-RELEASE-AUDIT ✅ (2026-06-04)

**Theme:** **1.18.4** · BUG-1…5 + P1 · `/pricing/` · cabinet sub · notif 3 presets

---

## O72e-L2-r7 ✅ pilot PASS (2026-06-04)

**Coder:** `l3_human_style.py` · tests **19/19** · regen #8772,#8752 · pilot r7

| Прогон | combined | send |
|--------|----------|------|
| pilot r7 | **4.30 ✅** | **80% ✅** |

**Full judge 71 ⏸** — решение владельца: когда придёт время (после E2E).

---

## Сейчас (очередь)

| # | Задача | Кто | Статус |
|---|--------|-----|--------|
| **E2E S6** | PRE-PROD smoke + UX walk | **owner** | **→ сейчас** |

**VPS ⏸:** один инстанс ок до юзеров → 2-й worker или апгрейд тарифа.

---

## Архив (детали)

O72e-L2 r3–r5 · O105 WP **1.18.3** · hotfix draft l3 (2026-06-03) · Judge прогоны — [`STATUS_ARCHIVE.md`](../archive/STATUS_ARCHIVE.md)

---

_Lead verify · 2026-06-04 · prod theme **1.18.6**_
