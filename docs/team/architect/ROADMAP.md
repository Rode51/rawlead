# Дорожная карта

**Vision:** [`PRODUCT_VISION.md`](../product/PRODUCT_VISION.md) **v0.11**

**Снимок:** [`STATUS.md`](../common/STATUS.md) · **очередь:** [`TASKS.md`](../common/TASKS.md) · **реклама:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md)

---

## Сейчас (2026-06-03)

| # | Что | Статус |
|---|-----|--------|
| **O63-FIX** | YouDo · FR.ru · job · Пчёл | **✅** FR **25/cycle** · YouDo ⏳ Playwright VPS |
| **O72e-10** | L1/L2/L3 premium prompts | **→ @coder** |
| **O72e L1** | category/tags | **✅ O72e-9 PASS** (02.06, `075032Z`) |
| **O90+O91** | ingest lag + watchdog | **✅ done** |
| **O89** | uniquify | **✅ done** |
| **O92** | Skill Tree interim в ЛК | **deploy** `1.11.30` · **не финал** |
| **O93** | Skill Tree PM вариант B + match expand | **✅ deploy** `1.12.0` |
| **O93-w2** | авто-L3 + лента modal | **✅ код** · deploy **w2b** |
| **O94-v0.5** | PM research | **✅ approve** |
| **O94-code** | v0.5 в код + UI 4 ниши | **✅ deploy 1.14.0** |
| **O94-L1** | AI.md + bench | **→ O97-bench** |
| **O94-w3** | UX лента: L3 stable, sort, today | **✅ deploy 1.15.0** |
| **O94-w4** | Design L3 tray · единый sheet | **✅** §4.7 |
| **O94-w4-code** | L3 tray в коде | **✅ deploy 1.16.0** |
| **O95** | `/lenta/` anon=ниши · logged-in=профиль+⚙ | **✅ 1.16.0** · **fix → 1.16.1** |
| **O95-fix** | ⚙ save · sort · copy · tray | **✅ 1.16.4** · owner smoke OK |
| **O96-copy** | Copy + UI O96-D | **✅ prod 1.17.2** |
| **O97** | Тег сложности 1–4 · L1 Judge | **✅ bench** · **deploy** |
| **O99** | Human fetch FL/Kwork + fast Neon path | **✅ VPS 2026-06-03** · [`OWNER_INTENT`](OWNER_INTENT.md) § O99 |
| **O98-w** | Skill Tree UX (2–3 концепта) | **⏸** Z4 copy в O96-D |
| **E2E UX** | Playwright + владелец | **4/5** · FR.ru ingest ✅ |
| **PRE-PROD AI vault** | O21 · один прогон | **после E2E** |
| **O92b** | pending_tags review | **⏸** |
| **Реклама** | soft-launch | **⏸** |

**Порядок до релиза:** **O97-bench → E2E → PRE-PROD AI vault → GTM**.  
**Gate vault:** новые прогоны **ИИ-vault** — **только после O97 + bench**.

**Параллельно judge (docs only):** copy-pack · O106-design · § O105 spec — см. [`TASKS.md`](../common/TASKS.md).

**Следующая волна после E2E:** **O101** (K=10 + anti-тыk) → **O105-w1** (790₽ СБП/crypto) → **O106-code** (карточка minimal).

---

## O97 — Тег сложности 1–4 (**до AI vault**)

**Решение владельца 2026-06-02:** L1 Judge (Flash Lite) → поле **`complexity` 1–4** в JSON разметки · **4 = нет норм ТЗ**.

**Guardrail (как O92/O93):** промпт + parse + UI · **без новых таблиц Neon** · persist в `ai_reasons` JSON · judge-инфру не переписываем.

| N | Промпт (тех.) | UI (→ PM+Design) |
|---|---------------|------------------|
| 1 | Скрипт / 1 файл / 1 вечер | 🟢 1/5 Микро |
| 2 | Типовой FastAPI+DB | 🟡 2/5 Типовой |
| 3 | Несколько систем | 🟠 3/5 Комплекс |
| 4 | Монолит / большое ТЗ | 🔴 4/5 Архитектура |
| 5 | Нет ТЗ / помойка | 💀 5/5 Риск |

**Волны:** w1 @lead-product copy · w2 @designer badge · w3 @coder prompt+UI · w4 bench → vault.

Детали: [`OWNER_INTENT.md`](OWNER_INTENT.md) § **O97**.

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
| FL · Kwork · TG | ✅ prod · O99 browser |
| YouDo · Freelance.ru · FreelanceJob · Пчёл | **код ✅** · FR.ru **live VPS** · YouDo ⏳ chromium/proxy |

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

_Lead Architect · 2026-06-03_
