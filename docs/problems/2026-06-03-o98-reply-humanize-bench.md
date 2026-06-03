# O98-reply · humanize L2/L3 · bench freeze (2026-06-03)

**Статус:** ⏸ пауза · bench не PASS · код в репо, VPS API без отдельного deploy этого трека

**Не путать с:** O99 ingest (парсер FL/Kwork) — другой трек, [`2026-06-03-ingest-l1-tg-youdo.md`](2026-06-03-ingest-l1-tg-youdo.md)

---

## Что делали (O99 human voice)

| Компонент | Файлы |
|-----------|--------|
| Промпты L2/L3 | `src/l3_human_style.py`, `src/ai_analyze.py` (`_shared_reply_system`, `rephrase_reply_draft_per_user`) |
| Regen Neon | `scripts/regen_shared_reply_drafts.py`, `scripts/regen_personal_reply_drafts.py` |
| Bench | `scripts/preprod_ai_prod_audit.py --judge --judge-l1 --judge-l3` |

Изменения по идее владельца: ослабить `l3_too_similar` (0.72→0.63), few-shot в L2, мягче `reply_ai_smell_re`, убрать `seed` в L3 OpenRouter (был HTTP 400), не писать «ИИ/нейросеть» в отклике (конфликт с валидатором на заказах про нейроботов).

---

## Judge Sonnet-4 · 71 лид · `since 2026-06-01`

| Прогон | L2 send | L2 combined | L3 send | L3 human | L3 uniq | L1 | Auto O72 |
|--------|---------|-------------|---------|----------|---------|-----|----------|
| **O98** (до humanize, старый промпт в Neon) | **49.3%** ❌ | 4.12 ✅ | **72%** ✅ | — | 3.28 | PASS | PASS |
| **O99 r1** (regen L2, старый L3 в БД) | 38.0% ❌ | 4.11 ✅ | 40% ❌ | 2.96 | 3.76 | PASS | PASS |
| **O99 r2** (tweaks + частичный L3 regen) | 42.3% ❌ | 4.09 ✅ | 40% ❌ | 3.24 | 3.76 | PASS | PASS |
| **O99 r3** (seed fix, shared 10442/9909, L3 regen ~24/25) | **43.7%** ❌ | 4.10 ✅ | **48%** ❌ | **3.72** | **2.64** ❌ | PASS | PASS |

Пороги gate: L2 `send_as_is` ≥50%, L3 `send` ≥50%, `uniq` ≥3.0, `combined` ≥3.8.

**Вывод:** humanize **не «убило всё»** — L1 и авто-аудит стабильны, combined L2 ~4.1. Но **L2 send не вырос** (даже чуть ниже O98 на regen-текстах). **L3:** тон лучше (`human_tone` ↑), **уникальность просела** ниже порога (`uniq` 2.64) — судья видит копипасту к shared; `send` 48% всё ещё FAIL.

---

## Regen Neon (факт)

| Скрипт | Результат |
|--------|-----------|
| `regen_shared_reply_drafts.py --apply --since 2026-06-01` | **59/61** OK (fail #10442, #9909 → позже **2/2** после промпта без «нейросеть») |
| `regen_personal_reply_drafts.py --force` (25 judge пар) | после фикса seed: **~24/25** OK; fail **#10025** (пустой content API) |

Судья **читает** `leads.reply_draft` + `user_lead_replies` — без regen judge гоняет старый текст.

---

## Известные баги / долги (когда возобновим)

1. **L2:** судья хочет больше якорей из ТЗ; часть fail — «лишний вопрос», «tools не те», не только «робот».
2. **L3:** баланс uniq vs humanize; возможно поднять порог similar осторожно или усилить «другая структура» в `build_uniquify_system`.
3. **Модель L3:** bench regen через `ai_model_shared_draft` (pro); прод-клик может идти через `ai_model_summary` (flash-lite) — сверить `.env.site`.
4. **Deploy:** промпты O99 в репо; на VPS отклики в UI обновятся после deploy API + regen.
5. **#10025** — добить personal regen вручную.

---

## Артефакты

| Файл | Содержание |
|------|------------|
| `data/preprod_ai_prod_audit_judge.md` | последний полный отчёт судьи (r3) |
| `data/preprod_ai_prod_audit.json` | сырой audit + judge_l3_results |
| `data/o99_judge_r3.log` | stdout r3 |
| `data/o99_judge_r3_summary.log` | однострочная сводка |
| `data/o98_full_judge.log` | baseline до humanize |
| `data/regen_shared_reply_drafts.json` | последний shared regen |
| `data/regen_personal_reply_drafts.json` | последний L3 regen |

---

## Команды (возобновление)

```powershell
# 1) shared L2 в Neon
.venv\Scripts\python.exe scripts\regen_shared_reply_drafts.py --profile site --apply --limit 80 --since 2026-06-01

# 2) personal L3 (judge-пары)
.venv\Scripts\python.exe scripts\regen_personal_reply_drafts.py --profile site --apply --force --lead-ids <ids> --since 2026-06-01

# 3) judge
.venv\Scripts\python.exe scripts\preprod_ai_prod_audit.py --profile site --limit 71 --judge --judge-limit 71 --judge-l1 --judge-l1-limit 71 --judge-l3 --judge-l3-limit 25 --judge-since 2026-06-01
```

---

## Wave 2 — L1/L2/L3 premium (Lead + владелец · 2026-06-03)

**Пока @coder на O63-FIX.** Код — отдельный чат § **O72e-10** (queued).

### Диагноз судьи (r3 · 71 лид · Sonnet-4)

| Слой | Gate | Факт | Главная боль |
|------|------|------|--------------|
| **L1** | ✅ PASS | usable **84.5%** · complexity_ok **85.9%** | ~14% без `complexity`; путаница design/dev («макет» → dev) |
| **L2 shared** | ❌ send **43.7%** (<50%) | combined **4.1** ✅ · spec **3.62** | **Не «робот»** — мало якорей из ТЗ, лишние вопросы, галлюцинации стека, tools_required ≠ тип заказа |
| **L3 uniquify** | ❌ send **48%** · uniq **2.64** (<3) | human **3.72** ↑ · meaning **5.0** | Flash-lite делает **синоним-сwap** — судья видит копию shared |

**O98 humanize:** L2 send **49.3%→43.7%** после regen; L3 uniq **3.28→2.64**. Тон лучше, **качество отправки хуже** — не катить ещё regen до смены промпта.

### Стратегия premium (Lead)

**Принцип:** сначала **содержание** (якоря ТЗ), потом **голос**. Коротко ≠ пусто.

| Волна | Что | Файлы | DoD judge |
|-------|-----|-------|-----------|
| **w1 L1** | `complexity` обязателен (post-validate default 2 если пусто); «макет/UI/figma» → design; few-shot complexity из worst-10 | `ai_analyze.py` L1 lite | complexity_ok **≥90%** |
| **w2 L2** | Shared prompt v3: (1) **2–3 якоря** из Описания дословно/почти; (2) **тип заказа** — text/design → игнор PHP/tools_required; (3) **0–1 вопрос**, только пробел в ТЗ; (4) **запрет** tech не из ТЗ (WP Rocket, WooCommerce при Tilda); (5) min плотность — 4 предл. с конкретикой | `l3_human_style.py` `build_shared_l2_system` · `ai_analyze.py` | L2 send **≥50%** (цель premium **≥55%**) |
| **w3 L3** | Uniquify v2: **структурные паттерны** по `user_id` (вопрос первым / опыт / план); поднять `l3_too_similar` **0.63→0.70**; retry с «другой каркас»; модель **flash-lite → gemini-2.5-flash** (или pro на judge-25) | `l3_human_style.py` · `ai_analyze.py` rephrase | L3 send **≥50%** · uniq **≥3.0** |
| **w4 regen** | shared 71 → L3 judge-25 → full judge | `regen_*` scripts | все три gate PASS |
| **w5 deploy** | API VPS + smoke «Написать отклик» | deploy | owner 3× глазами |

### Не делаем (premium ≠ FL.ru шаблон)

- ❌ Ещё один regen на текущих промптах (деньги + регресс).
- ❌ Ослаблять валидаторы ради pass.
- ❌ L3 только синонимами — судья уже ловит uniq=2 пачками.

### Открытые решения владельца

1. **L3 модель:** flash-lite (дешево, uniq FAIL) vs **flash** (~×3, рекомендует Lead для premium).
2. **Gate send:** оставить **50%** или поднять до **55%** после w2.
3. **Чат:** отдельный `@coder` § O72e-10 параллельно O63 (разные файлы) — **да/нет**.

---

_Зафиксировано O98-reply чат · 2026-06-03 · ⏸ до решения владельца_
