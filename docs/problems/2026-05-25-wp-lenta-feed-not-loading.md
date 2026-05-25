# WP `/lenta/` — лента не грузится

**Дата:** 2026-05-25  
**Статус:** ✅ отбой владелец — лента грузится (uvicorn + тема)  
**Владелец:** лента не работает после §3g; просит разбор WordPress

---

## Симптом

1. `http://radarzakaz.local/lenta/` — плашка **«Не удалось загрузить ленту. Попробовать снова»** (иногда).
2. Или пустые скелетоны + **«Пока нет навыков в ленте — дождитесь заказов из бота»**.
3. В **Telegram бот заказы приходят** — радар живой.

Скрин у владельца: ошибка загрузки + блок навыков пустой.

---

## Архитектура (для Mechanic)

```
Браузер → WP REST wp-json/rawlead/v1/feed
        → PHP rawlead-api.php → GET http://127.0.0.1:18766/v1/feed
        → Neon (notified_at IS NOT NULL)
```

**Не путать:** `/feed/` в WP = RSS WordPress. Лента продукта: **`/lenta/`** (slug `lenta`, `page-lenta.php`).

---

## Уже сделано (Coder §3g, commit `54ba7d5`)

| Что | Где |
|-----|-----|
| REST прокси feed/tags/skills | `wordpress/rawlead-kadence-child/inc/rawlead-api.php` |
| UI ленты | `page-lenta.php`, `assets/js/rawlead-feed.js` |
| Только лиды из бота | `src/api_server.py` — `notified_at IS NOT NULL` |
| Меню «Кабинет» | `template-parts/rawlead/header.php` |

Тикет RSS: [`2026-05-25-wp-feed-slug-rss-conflict.md`](2026-05-25-wp-feed-slug-rss-conflict.md)

---

## Гипотезы (проверить по порядку)

### H1 — API не запущен (частая)

- Симптом: **«Не удалось загрузить ленту»** (HTTP 500 от WP REST).
- Проверка: `GET http://127.0.0.1:18766/health` → 200.
- WP: `wp_remote_get` к `RAWLEAD_API_URL` (default `http://127.0.0.1:18766`).

### H2 — Тема на Local устарела

- Симптом: нет блока «Навыки», старый JS.
- Fix: из корня репо `python scripts/wp_install_rawlead_theme.py` (Local **Start**).

### H3 — Плагин / страницы

- Нужны страницы slug **`lenta`**, **`cabinet`** (publish).
- Плагин `rawlead-landing` v0.3 — при активации создаёт страницы; можно `scripts/wp_skeleton_setup.py`.
- Постоянные ссылки: Настройки → сохранить.

### H4 — Пул ленты пустой (не баг WP)

- API §3g: только `notified_at IS NOT NULL`.
- Старые лиды в Neon без `notified_at` → **0 карточек**, не ошибка сети.
- SQL (Neon): см. `docs/ops/RUN.md` §5 — backfill / hide junk.

### H5 — WP REST / nonce / CORS

- `rawlead-feed.js` → `fetch(restFeed)` same-origin.
- Проверить в DevTools Network: `wp-json/rawlead/v1/feed` — код, body (`detail`).

### H6 — `skills/catalog` 404

- Если uvicorn **старый** процесс (до §3g) — 404 на catalog; feed должен грузиться отдельно (JS fallback).
- Перезапуск: `uvicorn src.api_server:app --port 18766` из корня, **новое** окно после git pull.

---

## Чеклист Mechanic (выполнить и записать в § Решение)

- [ ] Local `radarzakaz` **Start**, тема **RawLead Kadence Child** активна
- [ ] `wp_install_rawlead_theme.py` — тема свежая из репо
- [ ] Страницы `lenta`, `cabinet` есть (`wp post list` или админка)
- [ ] `GET /wp-json/rawlead/v1/feed?limit=2` — 200 + JSON `items` (не 500)
- [ ] `GET /wp-json/rawlead/v1/skills/catalog` — 200 (при запущенном uvicorn)
- [ ] `uvicorn` + `GET /v1/health` — version `0.3g` или новее
- [ ] DevTools: какой URL падает, текст `detail`
- [ ] Neon: `SELECT count(*) FROM leads WHERE notified_at IS NOT NULL AND is_visible` — >0?

---

## Файлы

| Путь |
|------|
| `wordpress/rawlead-kadence-child/inc/rawlead-api.php` |
| `wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js` |
| `wordpress/rawlead-kadence-child/page-lenta.php` |
| `scripts/wp_install_rawlead_theme.py` |
| `docs/ops/RUN.md` §5 |
| `docs/ops/WP_KADENCE_INSTALL.md` |

## Не трогать без согласования Lead

- Смена логики «только из бота» (§3g) — продуктовое решение
- Новые фичи (3f)

---

## Решение

**2026-05-25:** владелец — лента работает. Причина типичная: API (`uvicorn`) не был запущен или тема Local устарела. Mechanic не требуется.

---

_Mechanic · тикет от Lead Architect · 2026-05-25_
