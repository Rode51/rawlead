# Портфолио — цели (Rode51 / labs)

**Статус:** 2026-06-18 · **P1 v1 desktop ✅** · **prod:** `https://rawlead.ru/portfolio/` (временно)

---

## Зачем сайт

| | |
|---|---|
| **Кто смотрит** | Клиент с FL.ru / биржи · **desktop = главное впечатление** · mobile — не ломается |
| **За 10 секунд (desktop)** | «Премиальный prod dev · можно писать» |
| **Запомнить** | Бренд **Rode51** · не RawLead как продукт |
| **Действие** | Telegram **@rcnn43** · [FL профиль](https://www.fl.ru/users/KhramovskikhN/portfolio/) |

**Домен (цель):** `labs.rawlead.ru` · static site · отдельно от prod rawlead.ru.

**Не цель:** копия rawlead.ru · не agency-лендинг «AI slop».

---

## Роли

| Роль | Делает |
|------|--------|
| **`@lead-portfolio`** | Refs, mood, промпты EN, приёмка по скринам · **0 кода** |
| **Claude Code** | `portfolio/` Next.js · `.claude/skills/` |
| **Владелец** | Taste, терминал Claude, 10‑sec test **1440px** (+ mobile sanity) |
| **`@lead-architect`** | Deploy labs (по «задеплой») |

Регламент: [`LEAD_PORTFOLIO.md`](LEAD_PORTFOLIO.md) · план: [`LEAD_PORTFOLIO_PROMPT.md`](LEAD_PORTFOLIO_PROMPT.md) · промпты Claude: [`CLAUDE_CODE_HANDOFF.md`](CLAUDE_CODE_HANDOFF.md)

---

## Главный кейс на сайте

**RawLead** — реальный prod (радар, AI, TG, WP). Факты: [`../common/PORTFOLIO.md`](../common/PORTFOLIO.md) (не UI).

**Crystal Debt** — второй кейс · MVP paused · без третьего проекта.

---

## Референсы

Живая таблица: [`../../design/portfolio/README.md`](../../design/portfolio/README.md) — заполняется **с нуля** (owner + Lead Portfolio).

**❌ Superseded:** P288 · terracotta · spiral · PNG в `refs/` — не использовать в промптах.

---

## Claude Code на ПК

[`FOR_YOU.md`](../../FOR_YOU.md) § Claude Code · relay `127.0.0.1:18777`.

```text
@lead-portfolio
Правила: .cursor/rules/lead-portfolio.mdc
План: docs/team/portfolio/LEAD_PORTFOLIO_PROMPT.md
```
