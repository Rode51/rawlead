# Coder — Контур 1 «добить» + ЛК на WP (портфолио)

**Дата:** 2026-05-24 · Lead  
**Контекст:** владелец с **пн** массово откликается; завтра — стабильный радар + **личный кабинет** на WP для портфолио (первый проект).

**Vision:** [`PRODUCT_VISION.md`](PRODUCT_VISION.md) §0c (Контур 1 = owner) · [`TZ_WP.md`](TZ_WP.md)

---

## Цель завтра (MVP приёмки)

### A. Контур 1 — «работает без сюрпризов»

| # | Готово когда |
|---|----------------|
| A1 | Пульт ▶ — 2 процесса, TG зелёная, `tg_smoke.py` ok |
| A2 | VPN выкл — бот отвечает на **ℹ Статус** |
| A3 | Join волна 3 идёт (`tg_join.log`), acc1/2/3 слушают |
| A4 | Карточка в боте: вердict + (если успеешь) **match % / breakdown** — минимум текущий формат не ломать |
| A5 | `AI_ENABLED=1` в `.env` — ИИ на owner-потоке |

**Не блокирует приёмку:** Neon в проде (можно заглушка / следующий спринт).

### B. ЛК на WordPress — **для портфолио** (не полный SaaS)

Страница **`/cabinet`** (или `/account`) в child theme `rawlead-kadence-child`:

| Блок | MVP |
|------|-----|
| Hero | «Личный кабинет RawLead» + подпись «демо / owner» |
| **Мои теги** | UI: 8–12 chip (Python, FastAPI, парсеры…) — сохранение в **user meta WP** или localStorage (без Neon ok) |
| **Лента** | 3–5 **демо-карточек** в стиле REFERENCE (rank %, источник, вердict) + пометка «live data — этап 2» **ИЛИ** read-only JSON из `wordpress/.../demo-leads.json` в репо |
| CTA | Ссылка на Telegram бота / «как подключить» |

**Стиль:** тот же Manrope/Unbounded, что главная — [`REFERENCE.md`](../design/wp/REFERENCE.md).

**Не делать завтра:** WooCommerce, multi-user, Neon API, Habr ingest, оплата.

---

## Файлы (ожидаемо)

| Путь | Действие |
|------|----------|
| `wordpress/rawlead-kadence-child/page-cabinet.php` или template | ЛК layout |
| `wordpress/rawlead-kadence-child/assets/css/rawlead.css` | стили кабинета |
| `wordpress/rawlead-kadence-child/inc/demo-leads.php` или `data/demo-leads.json` | демо-лента |
| `docs/ops/WP_KADENCE_INSTALL.md` | § «Кабинет /cabinet» |
| `docs/PORTFOLIO.md` | 1 абзац: ЛК + скриншот (владелец) |
| `docs/team/STATUS.md` | сдача |

Опционально если успеешь после B:
- `contour=owner` в ingest stub / коммент в `pg_storage.py`
- match breakdown в `telegram_notify.py`

---

## Как проверить

1. `http://radarzakaz.local/cabinet` — светлый ЛК, теги, demo-лента.
2. Пульт ▶ 30 мин — без падений, бот жив.
3. Скрин главной + ЛК — владелец кладёт в портфолио.

---

## Не делать

- `TASKS.md`, `FOR_YOU.md`
- Push GitHub без просьбы владельца
- Контур 2 / `SOURCES_SAAS.md`

---

_Lead · 2026-05-23 · новый чат `@coder`_
