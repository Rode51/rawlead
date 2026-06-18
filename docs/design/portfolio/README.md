# Портфолио — референс-сайты

**Статус:** 2026-06-18 · **refs + P1 as-built** · polish P2.

**Правило:** реф = **mood**, не pixel-perfect копия · 3–5 сайтов max.

| Сайт | URL | Что брать (ощущение) |
|------|-----|----------------------|
| Gustaf Furusten | https://gustaffurusten.se/ | Кинетическая типографика при загрузке · split-letter анимация · монospace + condensed sans mix · счётчики-числа как декор |
| Shoya Kajita | https://shoya-kajita.com/ | Терминальный loading screen как UI · code-aesthetic · «система запускается» как нарратив |
| Sirnik | https://www.sirnik.co/ | Структура кейс-грида · «structure and emotion» rhythm · логика case layout |
| Daniel Sun | https://danielsun.space/ | Личный тон solo dev · work grid с hover · честная история без agency-пафоса |
| We Are Yellow (Awwwards) | https://www.awwwards.com/sites/we-are-yellow-1 | Смелость с цветом · один сильный акцент · не бояться большого цветового пятна |

---

## Как заполнять

1. Владелец кидает 5–10 ссылок (Awwwards, личные, studios).
2. `@lead-portfolio` отбирает 3–5 + одна строка «что брать» на каждый.
3. Owner sign-off «refs ok» → Claude Code может `uipro --design-system --persist`.

---

## ❌ Superseded (не в промптах Claude Code)

| Что | Почему |
|-----|--------|
| Obys/Cappen/Gustaf **старая** таблица | owner 2026-06-18: новый mood |
| `refs/*.png` (spiral, terracotta, …) | P288 legacy · цепляет старые промпты |

Цели сайта: [`../../team/portfolio/README.md`](../../team/portfolio/README.md).
