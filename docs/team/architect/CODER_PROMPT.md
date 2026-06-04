# Coder — горячий контур (активное)

**→ Сейчас:** **§ O72e-L2-r8** — L1 complexity + L2 creative/tools (приоритет качества)

**Gate:** L1 usable ≥70% · L2 combined ≥4.0 · send ≥70% · L3 уже ✅

История: [`archive/CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md) · канон: [`OWNER_INTENT.md`](OWNER_INTENT.md) § O72e

---

## § O72e-L2-r8 — L1 + L2 prompt (**→ @coder**)

**Цель:** максимум качества **без API** — только промпт + unittest. Regen/judge — Lead/owner после сдачи.

### A. L1 — `src/ai_analyze.py` → `_LITE_SYSTEM_HEAD`

**Проблема (full 71):** ~11 id с **пустым complexity**; редко dev вместо design (#9520).

**Вставить** после строки про `complexity — целое 1–4` (одним блоком):

```text
**COMPLEXITY — жёстко (FAIL если пропуск):**
- Поле complexity **обязательно в каждом JSON** — целое 1, 2, 3 или 4. **Никогда null, never omit.**
- Если сомневаешься — ставь **2** (типовой проект с ясным ТЗ), не оставляй пустым.
- Якоря «complexity пустой» из аудита:
  · Google/YouTube Ads, VK таргет, SMM месяц, Power BI отчёт → **2**
  · транскрипция+перевод часового видео → **2**
  · написание/редактура книги, крупный редакторский объём → **3**
  · лидgen 4000 заявок с валидацией → **3**
  · «разместить готовые посты по списку» без создания контента → **1**
- **design vs dev:** «макет страницы / UI в Figma / 3 версии (desktop, mobile)» **без кода** → primary_category **design**, complexity **2** — не dev.
```

**DoD L1:** `tests/test_l1_pipeline.py` или новый `test_l1_complexity_canon.py` — assert substring `Никогда null` / `обязательно в каждом JSON` в `_LITE_SYSTEM`.

---

### B. L2 — `src/l3_human_style.py` → `build_shared_l2_system`

**Проблема #8772 (pilot r7):** judge видит PHP/WP в `tools_required` и ставит send=False, хотя в draft нет tech-слов.

**Добавить** в блок «Тип заказа» (text/design) **одну фразу-шаблон**:

```text
- **creative/text (#8772 и аналоги):** если в tools_required есть PHP/WordPress/Python, а заказ — **рассказ, статья, копирайт, перевод** — **одной короткой фразой** поясни: «Задача творческая, технические теги карточки к тексту не относятся» (или эквивалент); **не называй** PHP/WP/Python в отклике; вопрос — только **объём (знаки/слова)** или **формат файла (doc/pdf)**.
```

**Обновить GOOD (#8772)** — добавить эту фразу в пример:

```text
GOOD (#8772): «Здравствуйte! Задача творческая — технические теги карточки к тексту не относятся. Напишу рассказ про маму Лену: посёлок, платье в краске, беседка. Все 4 пункта ТЗ учту. Подскажите объём — в знаках или словах?»
```

**#8752 (с reconcile r6↔r7):** judge r7 хочет TG/API **если** в `tools_required`. Правило:

```text
- **учебная платформа (#8752):** функционал из **Описания** (экзамены, видео, адаптив, Yii2/Python). **Telegram/API** — **одной фразой**, только если **и** в Описании **и** в tools_required есть telegram/api; иначе **не добавляй**.
```

Обновить BAD/GOOD #8752 под это правило.

**DoD L2:** `tests/test_l3_human_style.py` — дополнить `test_shared_l2_r7_fixes` или `test_shared_l2_r8`: assert «творческая» + «теги карточки» в body; assert правило #8752 telegram.

---

### C. Не трогать

- L3 `build_uniquify_system` — уже PASS
- Модели, Neon, judge, regen-скрипты
- **Не** запускать OpenRouter из Coder-чата

---

### D. После сдачи (Lead)

1. Deploy VPS: `l3_human_style.py` + `ai_analyze.py` → `/opt/rawlead/src/` · restart `rawlead-api rawlead-radar`
2. Owner (когда скажет): regen worst ids · pilot · full 71

---

## Закрыто — сводка

| § | Статус |
|---|--------|
| O72e-L2-r7 | ✅ pilot r7 PASS 4.3/80% |
| O72e-L2-r6 | ✅ pilot r6 |
| O109 | ✅ 1.18.6 |

Очередь: [TASKS.md](../common/TASKS.md)

---

## Правило hot-файла

**≤ ~120 строк** · DoD → `archive/CODER_PROMPT_ARCHIVE.md`
