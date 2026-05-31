# Coder — **→ Следующее:** **O75** лента 7d · backlog O63/O74

**O72b ✅ Lead verify 2026-05-31** · draft-only **97.8%** · `src/tools_catalog.py`

---

# § O72b — (**✅ Lead verify 2026-05-31**)

**Сдача:** `draft_only_pass` **97.8%** (45/46) · tools bucket **89.1%** · combined **87%** · canonical **51** без изменений · 8/8 unittest OK.

**Остаток (не блокер O72b):** 1× `L2:reply_draft` (#7051 «Готов…») · 5× `tools:empty_but_desc_hints` · 25 L1 empty — отдельно.

---

# § O72 — (**✅ фаза 1 · Lead verify 2026-05-31**)

**Контекст:** Owner **9/10** draft OK · 1 завис · 1 «разбор недоступен» → O72 **+ L1** + top fail cases для правки промпта.

**План:** [`PRE_LAUNCH_MARKETING.md`](../../ops/PRE_LAUNCH_MARKETING.md) § O72

## o72-1 — Скрипт выборки + auto-metrics (**P1**)

| # | Задача |
|---|--------|
| s1 | Новый `scripts/preprod_ai_prod_audit.py` (или флаг `--prod-sample` у matrix) — читает Neon, **не** дергает OpenRouter на фазе 1 |
| s2 | Выборка: **N=100–200** лидов · stratify category + source · **+** лиды с пустым L1/`task_summary` |
| s3 | **L2:** validators `reply_draft` · **L1:** пустой разбор при visible lead · tools vs catalog |
| s4 | **tools_required:** пустой массив · slug не из `/v1/skills/catalog` · дубликаты · эвристика «в описании есть Figma/Python/…, а tools пуст» |
| s5 | JSON → `data/preprod_ai_prod_audit.json` · markdown → `data/preprod_ai_prod_audit_human.md` |

## o72-2 — LLM judge (опционально, **P2**)

| # | Задача |
|---|--------|
| j1 | Флаг `--judge --limit 30` — второй проход OpenRouter на подвыборке |
| j2 | Промпт: релевантность 1–5 · конкретность 1–5 · tools match да/нет/частично · «отправил бы as-is» да/нет |
| j3 | В отчёт: avg scores · **top-10 worst** · **рекомендации правок промпта** (1 абзац на паттерн) |
| j4 | Если owner дал lead_id проблемных карточек — **root cause** в отчёте |

## o72-3 — Accept O72

| # | Критерий |
|---|----------|
| a1 | Скрипт отрабатывает на prod Neon без ручных правок |
| a2 | Отчёт JSON + human md в `data/` |
| a3 | **≥85%** auto-pass (нет fail validators + tools ok) |
| a4 | Если `--judge`: avg **≥3.5/5** по релевантности и конкретности |
| a5 | STATUS блок + ссылка на отчёт |

**Не в задаче:** дашборд в WP · CI cron (только ручной запуск Lead/владелец).

**Файлы (ожидаемо):** `scripts/preprod_ai_prod_audit.py` · `data/preprod_ai_prod_audit.json` · опц. тест smoke на mock rows.

---

# § O63 — парсеры YouDo · Freelance.ru · FreelanceJob · Пчёл.нет (**📋 backlog · владелец 2026-05-30**)

**Gate:** **после O37-UX PASS** · не блокирует pre-prod.

| source_id | UI | URL старт |
|-----------|-----|-----------|
| `youdo` | YouDo | https://youdo.com/ |
| `freelance_ru` | Freelance.ru | https://freelance.ru/project/ |
| `freelancejob` | FreelanceJob | URL при ТЗ |
| `pchyol` | Пчёл.нет | URL при ТЗ |

| # | Задача |
|---|--------|
| p1 | Парсеры listing (как `fl_parser.py`) ×4 |
| p2 | `main.py` + лог цикла |
| p3 | Neon + `PUBLIC_FEED_SOURCES` |
| p4 | Proxy env per source |
| p5 | WP фильтр/badge источника |
| p6 | VPS smoke ≥1 visible/биржу |

**Accept:** 4 source в env → радар → `/lenta/` с фильтром по source.

---

# § O74 — TG: прямая ссылка на заказ (**📋 backlog · владелец 2026-05-30**)

**Суть:** в push @rawlead_bot / @FLPARSINGBOT — **кликабельная ссылка** на заказ на бирже (или первоисточник), не только текст карточки.

| # | Задача |
|---|--------|
| t1 | Кнопка URL / inline link · `project.url` или canonical source URL |
| t2 | Site push + Legacy consumer · единый формат |
| t3 | Accept: push на TG-лид → ссылка открывает биржу |

**Gate:** после O72 · параллельно O63 ok.

---

# § O75 — Лента: закрытые + старше 7 дней (**📋 backlog · владелец 2026-05-30**)

**Суть:** в `/lenta/` **не показывать** заказы закрытые на бирже и **старше 7 суток** (от `created_at` или published на source).

| # | Задача |
|---|--------|
| f1 | **Закрытые:** усилить **O65** `delist_checker` — все source_id · smoke |
| f2 | **>7d:** API `/v1/feed` + `/v1/me/feed` — filter или `is_visible=false` batch |
| f3 | Не путать с **purge** БД (RETENTION) — здесь только **скрытие из ленты** |
| f4 | Accept: в ленте нет лидов `age>7d` · delisted не в feed |

**O65 ✅ код** — verify на prod + f2.

---

## O63 — cross-source dedup

**Риск:** одно задание на FL + YouDo + Freelance.ru → **дубли в ленте**.

**Уже есть (не ломать):**

| Слой | Как |
|------|-----|
| **Neon** | `content_hash` = SHA-256 **нормализованного** title+snippet · **UNIQUE глобально** (не per-source) · `ON CONFLICT DO NOTHING` |
| **SQLite** | только `(source, external_id)` — **не** cross-source |

→ **Одинаковый текст** с двух бирж → **одна** карточка в `/lenta/` (вторая отсекается на ingest).

**Дырки (закрыть в O63):**

| # | Задача |
|---|--------|
| d1 | **Нормализация:** единый `listing_content_hash` для всех новых парсеров · title+body без URL/₽/«FL.ru»/«YouDo» в шуме |
| d2 | **Счётчик в логе:** `cross_source_dup` / `neon_dup_hash` — когда insert отбит hash'ем, лог **какой source выиграл** (первый в Neon) |
| d3 | **Accept:** один и тот же текст с FL и `youdo` → **1** lead в feed · smoke-тест |
| d4 | **Backlog O63b (если мало):** fuzzy / эмбеддинги для «пересказанных» дублей — **не блокер** первой волны |

**Не делать:** отдельный dedup per-source · снимать UNIQUE `content_hash`.

---

## Закрыто (индекс)

Детали § → [`archive/CODER_PROMPT_ARCHIVE.md`](../archive/CODER_PROMPT_ARCHIVE.md). **Grep** по номеру задачи.

| Задача | Статус | Где |
|--------|--------|-----|
| O71 — API HTTPS + shared draft gate | ✅ | archive |
| O70 — O37c triage | ✅ | archive |
| O69 — Лента: сортировка в счётчике + навыки «Ещё» / 2 ниши | ✅ | archive |
| O65 — Снятие с ленты: заказ закрыт | ✅ | archive |
| O37c-filters — навыки по специализации + highlight | ✅ | archive |
| WAVE-UX-MOBILE — пересборка mobile feed + ЛК | ✅ | archive |
| O61 — draft без порога km | ✅ | archive |
| O60 — hotfix приёмки владельца | ✅ | archive |
| O58 — | ✅ | archive |
| O56+O57 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O55 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O54 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX O53 — | ✅ | archive |
| WAVE-2-ACCEPT-FIX — O52 | ✅ | archive |
| PRE-STRESS-WAVE-2 — | ✅ | archive |
| PRE-STRESS-PACK — | ✅ | archive |
| WAVE-4-MICRO — микроправки UI | ✅ | archive |
| DEPLOY-CRLF — radar не должен падать после deploy | ✅ | archive |
| WAVE-2-CSS — Neo-Brutalist Wave 2 | ✅ | archive |
| BACKLOG-TAIL-CLEAR-O40 — хвост без L1 старше N дней | ✅ | archive |

| … | | полный список в архиве |

---

## Правило hot-файла

| | |
|--|--|
| **Лимит** | **≤ ~120 строк** в CODER_PROMPT.md |
| **Активное** | одна § в шапке + backlog (O63) |
| **После ✅** | § → архив · в hot — строка в индекс · в TASKS — ✅ |
| **Lead** | раз в 1–2 недели или при >150 строк — ревизия архива |

