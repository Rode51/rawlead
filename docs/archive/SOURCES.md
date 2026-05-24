# Источники FL.ru

Lead/Coder уточняют актуальные URL при первом запуске.

## Стартовые ссылки (проверить в браузере)
- Все проекты: https://www.fl.ru/projects/
- Общая лента заказов (`kind=1`): https://www.fl.ru/projects/?kind=1 — удобно под **широкую ленту + жёсткий отсев** в `docs/ops/FILTERS.md`
- Программирование: https://www.fl.ru/projects/category/programmirovanie/
- Администрирование сайтов: https://www.fl.ru/projects/category/administrirovanie-saytov/

**Шум vs охват:** «Все проекты» — больше заказов, но больше мусора; фильтр по словам (`docs/ops/FILTERS.md`) обязателен. Узкая категория — меньше шума, но можно пропустить заказ в соседней рубрике. **Твой финальный URL** впишешь в `.env` → `FL_PROJECTS_URL`, когда бот уже шлёт уведомления (можно начать с программирования и потом сменить).

## Сортировка по дате (проверка 2026-05-20)
- В листинге **нет** отдельного query «новые сверху» (кнопки `b_button_projects_sort_block` / `pt` / `pf` — только **режим отображения**: заголовки vs заголовки+описание, не порядок ленты).
- На `?kind=1` сверху остаются **закреплённые** заказы («N закреплённых заказа»); остальные идут ниже. Парсер их не отбрасывает; дубли id с других страниц схлопываются.
- **Рекомендуемый URL в `.env`:** `FL_PROJECTS_URL=https://www.fl.ru/projects/?kind=1` (широкая лента + фильтр слов).

## Пагинация (`src/fl_parser.py`)
- За цикл: **до 3 страниц** (`FL_LISTING_MAX_PAGES = 3`), без прокси.
- Формат FL: путь **`/projects/page-2/?kind=1`** (и для категории: `.../category/.../page-2/`). Эквивалент **`?page=2`** тоже отдаёт ту же ленту — в коде строится путь `page-N`.
- Страница 1 — ровно `FL_PROJECTS_URL` из `.env`; страницы 2–3 — тот же path/query + `/page-N/`.
- **~30 карточек на страницу** → `cards_fl` в логе обычно **~80–90** за цикл (с дедупом id между страницами).
- Пустая страница 2+ — конец ленты, цикл страниц останавливается (ошибки нет).

## Если список пустой в requests
Записать в STATUS → рассмотреть **Playwright** (этап 1.1).

---

# Kwork (этап 1.5)

## URL ленты (фактический)
- **Лента биржи проектов:** https://kwork.ru/projects  
- В `.env` → `KWORK_PROJECTS_URL=https://kwork.ru/projects`  
- Пустая строка / переменная не задана → радар опрашивает только FL.

## Пагинация (MVP)
- Один GET первой страницы; карточки приходят во **встроенном JSON** `"wants":[...]` в HTML (SSR для Vue), отдельной пагинации в коде нет.
- На проверке 2026-05-20 в массиве **12** заказов — для MVP достаточно.

## Парсинг (`src/kwork_parser.py`)
- **Без прокси** (`DIRECT_REQUESTS_PROXIES`), тот же `HTTP_USER_AGENT`, что FL.
- Источник данных: подстрока `"wants":[` в HTML → JSON-массив объектов.
- Поля объекта want → `ListingProject`:
  - `id` → `project_id`
  - `name` → `title`
  - `description` → `listing_snippet`
  - `priceLimit` + `isHigherPrice` → `budget_text` (например «до 20 000 ₽»)
  - `date_create` или `wantDates.dateCreate` → `published_at`
  - URL карточки: `https://kwork.ru/projects/{id}/view` (редирект с `/projects/{id}`)
- `source='kwork'` в SQLite и уведомлениях.

## Если список пустой / нет `"wants"`
- В лог: `kwork:fetch:...`  
- Проверить в браузере без VPN; при смене вёрстки — обновить парсер или STATUS → Playwright.

---

# Avito (опционально — **нет биржи**)

**Вывод Lead:** отдельной «биржи проектов» **нет**. Это [раздел «Услуги»](https://www.avito.ru/all/predlozheniya_uslug?cd=1): объявления «оказываю услугу» и редкие «нужен мастер/исполнитель» вперемешку. Для радара **FL + Kwork** — основа; Avito только как **эксперимент** с сильным шумом.

Подключение — **отложено** в `docs/team/common/TASKS.md`. Если вернёшься к идее:

## Что брать в `.env` → `AVITO_PROJECTS_URL`

Coder после инспекции фиксирует **один** рабочий URL. Стартовые варианты (проверить в браузере, что список карточек грузится):

| Вариант | URL | Когда |
|--------|-----|--------|
| **A — IT-узко (рекомендуем старт)** | [Компьютерная помощь, вся Россия](https://www.avito.ru/all/predlozheniya_uslug/komp'yuternaya_pomoshch'-ASgBAgICAUSYC_78jQM?cd=1) | Сайты, боты, «настроить», ремонт ПК — ближе к твоим словам |
| **B — деловые услуги** | [Деловые услуги](https://www.avito.ru/all/predlozheniya_uslug/delovye_uslugi-ASgBAgICAUSYC7KfAQ?cd=1) | Шире: маркетинг, тексты, «под ключ» |
| **C — поиск по слову** | [Услуги + `q=разработка сайта`](https://www.avito.ru/all/predlozheniya_uslug?q=%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%BA%D0%B0+%D1%81%D0%B0%D0%B9%D1%82%D0%B0) | Мало заказов, но точнее; query можно менять |
| **D — вся «Услуги»** | [Все предложения услуг](https://www.avito.ru/all/predlozheniya_uslug?cd=1) | Максимум шума; только если фильтры жёсткие |

**Не брать:** главная `avito.ru`, «Работа»/вакансии (`employer`) — это найм, не разовые заказы.

## Для `.env`
```
AVITO_PROJECTS_URL=https://www.avito.ru/all/predlozheniya_uslug/komp'yuternaya_pomoshch'-ASgBAgICAUSYC_78jQM?cd=1
```
Пусто = Avito не опрашиваем (как с Kwork до URL).

## Парсинг
- **Без прокси**, как FL/Kwork.
- HTML-карточки или JSON в странице — Coder фиксирует селекторы здесь после первого успешного разбора.
- `source='avito'` в SQLite и TG.
- Если `requests` пустой / антибот — STATUS → Playwright или тикет Mechanic.
