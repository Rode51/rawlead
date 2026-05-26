# TG: снос старых каналов → пачка из PDF (2026-05-26)

**Решение владельца:** текущие dogfood-чаты (MVP) — **отписаться**, заказов ноль. Переход на каналы из PDF  
`Поиск Telegram-каналов фриланс-вакансий.pdf`.

**Продукт:** 4 ниши §0i — dev · design · marketing · text. Берём каналы с **премодерацией**, **заказами/проектами**, вилкой/текстом задачи.  
**Не берём:** помойки, «работа без опыта», чистый штат без проектов, 1C/WP-узкие чаты, каналы без @handle в PDF.

**Подписки:** **не отписываемся** (решение владельца 2026-05-26) — пусть чаты остаются в acc. Радар **не слушает** их (`P1 listen filter` + allowlist). Отписка опциональна только для порядка в UI Telegram.

---

## 1. Снести (все текущие из `TG_JOIN_QUEUE.csv`)

Отписаться / `status=drop` в очереди — **весь** текущий список (~85 каналов), включая:

| Волна | Примеры | Почему |
|-------|---------|--------|
| MVP | `ipomogator`, `frilanc`, `workk_on`, `tgjob`, `task_1C` | Ты: помойка, 0 заказов |
| Волна 2–3 | WP/1C (`wordpress_jobs`, `jobs1c`, `Bitrix_1C_Dev_Job`, …), агрегаторы без модерации | Не PDF, шум, не 4 ниши |
| Уже в join, но не PDF | `allgigs`, `FreeWorkFeed`, `frilancekomfort`, … | Замена на отфильтрованный PDF |

Полный перечень для отписки: [`TG_DROPLIST_2026-05-26.txt`](TG_DROPLIST_2026-05-26.txt)

---

## 2. PDF → фильтр

### ✅ Tier A — публичная лента + dogfood (премодерация, все 4 ниши)

Записано в [`TG_PUBLIC_FEED_ALLOWLIST.txt`](TG_PUBLIC_FEED_ALLOWLIST.txt).

| Ниша | Канал | Комментарий |
|------|--------|-------------|
| Универсал | @distantsiya | Офиц. «Дистанция», все digital |
| Универсал | @theyseeku | Крупный фриланс-агрегатор |
| Универсал | @normrabota | Понятные вакансии, условия |
| Универсал | @zapwork | Удалёнка + советы |
| Универсал | @perezvonyu | Digital/media, прямые контакты |
| Универсал | @workoo | Стабильные заказы |
| Dev | @habr_career | IT, вилки, модерация |
| Dev | @remoteit | Remote IT |
| Dev | @webfrl | Веб-заказы с бирж, фриланс |
| Dev | @job_it_digital | IT широкий (часть штат — режет FILTERS) |
| Design | @designhunters | UX/UI, вилки |
| Design | @designbirzha | Заказы + штат студий |
| Design | @designer_jobs | Продуктовый UX |
| Design | @designwork_vacansii | Middle/Senior |
| Design | @uxwork | UI/UX, теги |
| Design | @uiux_jobs_resumes | Короткие структурированные |
| Design | @jobs_designglory | Агентства |
| Marketing | @digital_jobster | Digital, KPI |
| Marketing | @rabota_go | Performance, лиды |
| Marketing | @rabota_freelance | Проекты таргет/SMM |
| Marketing | @smmlancer | SMM заказы |
| Marketing | @dnative_job | Агентства, высокий чек |
| Marketing | @digitaltender | SEO/контекст тендеры |
| Text | @textodromo | Крупнейший текст (проверить handle живой) |
| Text | @work_copywriters | Прескрининг |
| Text | @work_editor | Редактура |
| Text | @kopirayter_kopirayting | IT/агентства |
| Text | @edit_zp | Акцент на оплату |
| Text | @glvrd_job | Разбор условий |
| Text | @forallmedia | Бренд-медиа |

**Ссылки:** `https://t.me/<handle>` (без @) — в allowlist-файле.

---

### 🟡 Tier B — только dogfood (не в публичку до проверки 7 дней)

| Канал | Почему B |
|--------|----------|
| @jvm_jobs | Узко Java |
| @getitrussia | ~1 пост/нед |
| @gamedev_jobs | Только геймдев |
| @digital_hr | Чаще штат через агентство |
| @tproger | Много статей, мало заказов |
| @designer_ru | Очень большой, шумнее A |
| @self_ma | Резюме + вакансии |
| https://t.me/Work4writers | Нет @ в PDF, только ссылка |
| @INFOGRAPHIKAQ | Узко инфографика/маркетплейсы |
| @jun_jobs | Джуниор, демпинг |

---

### ❌ Не подключаем (из PDF или текущие)

| Канал / тип | Почему |
|-------------|--------|
| **Все из `TG_DROPLIST`** | Старая помойка |
| @workk_on | Ты: 0 заказов; в PDF есть, но **исключён** |
| «Удалённая работа без опыта» | Нет handle, низкий порог → спам |
| «UGC / рилсмейкеры» | В PDF только «Ссылка» без URL |
| «TGwork» / «Фриланс подработка» | В PDF без @handle |
| 1C / WordPress чаты (старая очередь) | Вне 4 ниш §0i, узкий стек |

---

## 3. Очередь join (новая)

**Правило:** 2–3 канала/неделю на аккаунт · сначала Tier A · см. [`TG_JOIN_SCHEDULE.md`](TG_JOIN_SCHEDULE.md)

Coder: новый CSV `TG_JOIN_QUEUE_v2.csv` или замена очереди после твоего «отписался».

---

## 4. С тебя

1. **Ничего в Telegram** — отписка не нужна.
2. Coder: join Tier A + listen **только** allowlist (без старого TG-A JSON).
3. Приёмка: `P1 listen filter: N из M` (N ≪ M) — мусор не обрабатывается.

Тикет: [`docs/problems/2026-05-26-p1-tg-migration-gaps.md`](../problems/2026-05-26-p1-tg-migration-gaps.md)

---

_Lead · 2026-05-26 · PDF владельца_
