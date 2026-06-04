# Coder — горячий контур (активное)

**→ Сейчас:** **§ O72e-L2-r6** — экономный добой L2 gate (pilot 10 → один full 71)

**Gate:** L2 combined **≥4.0** · send as-is **≥70%** · **бюджет сегодня ≤ ~$3** на API (без `--full` / regen 71)

История: [`archive/CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · канон: [`OWNER_INTENT.md`](OWNER_INTENT.md) § O72e

---

## § O72e-L2-r6 — экономный цикл (**→ @coder**)

**Контекст (факты):**

| Прогон | combined | send | Accept L2 |
|--------|----------|------|-----------|
| **full 71** (2026-06-03) | **4.16 ✅** | **40.8% ❌** | ❌ |
| **pilot 10 r5** | **3.97 ❌** | **70% ✅** | ❌ |

Pilot bench ids (фиксированные 10): `8772,10442,8752,8925,9843,9581,9831,9374,9326,10362`

**3 провала send (r5):** `#8772` (литература vs php/wp tools) · `#10442` (нейродизайн, нет HTML/Figma вилки) · `#8752` (учебная платформа, нет API/Telegram из tools)

**Цель к 10:00:** pilot **оба** gate ✅ → **один** full judge 71 (без regen всех 71).

### Шаг 0 — Coder (**$0**, только промпт)

Файл: `src/l3_human_style.py` (shared L2 / BAD-GOOD якоря).

| id | Паттерн fix |
|----|-------------|
| 8772 | creative/text лиды — **не** тащить dev-tools из `tools_required`; акцент литературный |
| 10442 | design+AI: Midjourney → **Figma или HTML/CSS** (если в ТЗ оба) + 1 уточняющий вопрос |
| 8752 | платформа/ЛMS: перечислить функционал из ТЗ + **API/Telegram** если в tools, без лишней БД-простыни |

**DoD:** unittest `tests/test_l3_human_style.py` зелёный · **не** трогать L1/L3 judge · **не** regen из Coder-чата.

### Шаг 1 — владелец regen (**~$0.2–0.5**)

Только 3 id:

```text
python scripts/regen_shared_reply_drafts.py --profile site --apply --lead-ids 8772,10442,8752
```

### Шаг 2 — владелец pilot judge (**~$0.4–0.6**)

Только 10 id, **без** L1/L3:

```text
python scripts/preprod_ai_prod_audit.py --profile site --limit 1 --empty-l1-limit 0 ^
  --lead-ids 8772,10442,8752,8925,9843,9581,9831,9374,9326,10362 ^
  --judge --judge-limit 10 ^
  --judge-md-out data/preprod_ai_prod_audit_judge_pilot_r6.md
```

**Stop-rule:** если pilot снова ❌ — **стоп API** → Lead смотрит `pilot_r6.md`, Coder **ещё один** узкий патч по worst-1..2 (не regen 71).

### Шаг 3 — один full judge (**~$2–3**, только если pilot ✅ оба gate)

```text
python scripts/preprod_ai_prod_audit.py --profile site --judge --judge-limit 71 --limit 71 ^
  --judge-md-out data/preprod_ai_prod_audit_judge_full_r6.md
```

**Без** `--judge-l1` · **без** `--judge-l3` · **без** `regen --limit 80`.

### Запрещено сегодня (экономия)

- `qa_prompt_loop.py --full` / `--apply` (~$3–8)
- `regen_shared_reply_drafts.py --apply --limit 71`
- Повторный full judge без нового pilot PASS
- L1/L3 re-judge (уже ✅)

---

## Закрыто — сводка

| § | Статус | Theme |
|---|--------|-------|
| O109 | ✅ delist + deeplink | 1.18.6 |
| O108-BC | ✅ TZ B+C | 1.18.5 |
| PRE-RELEASE-AUDIT | ✅ | 1.18.4 |

Очередь: [TASKS.md](../common/TASKS.md)

---

## Правило hot-файла

**≤ ~120 строк** · закрытый DoD → `archive/CODER_PROMPT_ARCHIVE.md`
