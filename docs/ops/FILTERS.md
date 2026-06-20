# Фильтры слов — индекс (Site vs Legacy)

**Код читает не этот файл**, а профильный канон:

| Профиль | `RADAR_PROFILE` | Файл (канон) | Кто правит |
|---------|-----------------|--------------|------------|
| **Site** (prod VPS, `/lenta/`) | `site` | [`FILTERS_SITE.md`](FILTERS_SITE.md) | Product + Coder при SITE-тюнинге |
| **Legacy** (dogfood @FLPARSINGBOT) | `legacy` | [`FILTERS_LEGACY.md`](FILTERS_LEGACY.md) | **заморожен** — не менять без задачи владельца |

`src/filters.py` → `FILTERS_MD_PATH` из `src/config.py` · тесты: `tests/test_l1_dual_api_key.py` (site path).

**Решение владельца O9:** Site и Legacy — **разные файлы** ([`OWNER_INTENT.md`](../team/architect/OWNER_INTENT.md)).

---

## Как пользоваться

1. Определи профиль: Site = rawlead.ru + Neon ingest · Legacy = consumer из Neon → FLPARSING.
2. Правь **только** свой файл (`FILTERS_SITE` или `FILTERS_LEGACY`).
3. Сохрани → перезапуск радара (`systemctl` на VPS или `main.py` локально).
4. `.env`: `FILTER_WIDE=1` (рекомендуется) — в ИИ всё, кроме явного **стопа**.

---

## Связанные docs

| Тема | Файл |
|------|------|
| URL бирж | [`SOURCES_POOLS.md`](SOURCES_POOLS.md) |
| ИИ-профиль | [`PROFILE.md`](PROFILE.md) |
| Deep Research (стоп-списки) | [`../team/archive/FILTERS_DEEP_RESEARCH_2026.md`](../team/archive/FILTERS_DEEP_RESEARCH_2026.md) |
| Vision §0i категории | [`../team/product/PRODUCT_VISION.md`](../team/product/PRODUCT_VISION.md) |
| Лог радара | [`RADAR_LOG.md`](RADAR_LOG.md) |

---

## Уровни (кратко)

| Уровень | Где |
|---------|-----|
| 1 — URL лент FL | `.env` → `FL_PROJECTS_URL` |
| 2 — слова берём/стоп | **FILTERS_SITE** или **FILTERS_LEGACY** |
| 3 — `MIN_BUDGET_RUB` | `.env` (после MVP) |
| 4 — ИИ verdict | `PROFILE.md` + L1 pipeline |

```
Листинг → dedup → FILTER_WIDE + стоп/берём → L1 → лента/TG
```

---

_Lead · 2026-06-20 · audit A2: индекс вместо третьей копии списков_
