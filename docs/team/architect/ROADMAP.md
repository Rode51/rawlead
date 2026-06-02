# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-01 → 02)

| # | Что | Статус |
|---|-----|--------|
| **O72e L2** | send/combined on full | **✅** |
| **O72e L1** | category/tags | **✅ O72e-9 PASS** (02.06, `075032Z`) |
| **O90+O91** | ingest lag + watchdog | **✅ done** |
| **O89** | uniquify | **✅ done** |
| **O92** | Skill Tree interim в ЛК | **deploy** `1.11.30` · **не финал** |
| **O93** | Skill Tree PM вариант B + match expand | **✅ deploy** `1.12.0` |
| **O93-w2** | авто-L3 + лента modal | **✅ код** · deploy **w2b** |
| **O94-v0.5** | PM research | **✅ approve** |
| **O94-code** | v0.5 в код + UI 4 ниши | **✅ deploy 1.14.0** |
| **O94-L1** | AI.md + targeted bench | **→ @coder** |
| **E2E UX** | Playwright + владелец | **после w2b** |
| **O92b** | pending_tags review | **⏸** |
| **Реклама** | soft-launch | **⏸** |

**Порядок:** **w2b deploy → O94-code → O94-L1 bench → E2E → O92b → GTM**.

---

## O72e — prompt quality gate (активно)

| Слой | Gate |
|------|------|
| **L2** | combined ≥4.0 · send ≥50% |
| **L1** | usable ≥70% |
| **Инструменты** | `$0` bench 5/5 · full на свежих лидах |

Coder: [`CODER_PROMPT.md`](CODER_PROMPT.md) § O90/O91 · Owner: [`FOR_YOU.md`](../../FOR_YOU.md) § «Твои шаги».

_(O72 auto-metrics — ✅ архив, см. STATUS_ARCHIVE.)_

---

## O89 — reply uniquify (следом)

**Решение владельца:** один **pro**-каркас при ingest · **flash-lite** rephrase **per user** на «Написать отклик» · copy «уникальный отклик».

Детали: [`OWNER_INTENT.md`](OWNER_INTENT.md) § O89.

---

## O92 — Skill Tree в профиле (после O89)

**Идея владельца:** вместо плоского списка навыков в ЛК — 4 корневые ниши (dev/design/marketing/text) с раскрывающимися ветками и чекбоксами canonical-tag.

**V1 guardrail:** UI/UX-only. Payload в API тот же (`["tag_a","tag_b"]`), **L1/LLM/prompts/Neon schema не меняем**.

**Цель:** повысить полноту и точность заполнения профиля без регресса качества matching.

## O92b — Semi-auto рост каталога навыков (после O92)

**Факт:** в Neon уже есть `public.pending_tags` (candidate queue от L1 unknown tags, `seen_count` + `first_seen_at`).

**Принцип:** только semi-auto. Автоматически собирать кандидатов можно, автоматически писать в canonical-tag каталог — нельзя.

**Поток:** `pending_tags` → ranking/cleanup → owner review → ручное approve в каталог → rollout + smoke.

---

## O63 — парсеры

| source | Статус |
|--------|--------|
| FL · Kwork · TG | ✅ prod |
| YouDo · Freelance.ru | ✅ w1 |
| FreelanceJob · Пчёл | ✅ w2 |

---

## O82 — Match UX v2

| Волна | Статус |
|-------|--------|
| w1 · w2 | **✅** deploy VPS |
| w3 embeddings | backlog |

---

## Фазы (vision §4)

| Фаза | Статус |
|------|--------|
| 0 · 0b · 3b–3d · E0–E5 · P5 E2 | ✅ |
| **3f** ИИ draft + tools | **→ O72e gate** |
| 3g–3h Auth + Stars | ✅ база · polish по мере GTM |
| 4 O73 analytics | backlog |
| 5 P-PORTFOLIO · 5b GTM | после gate |

Coder ТЗ: [`CODER_PROMPT.md`](CODER_PROMPT.md) · решения: [`OWNER_INTENT.md`](OWNER_INTENT.md).

---

## Отменено

Freelancehunt · ставка A «только портфолио» · цена «от 300 ₽» · 25 источников сразу.

---

_Lead Architect · 2026-06-02_
