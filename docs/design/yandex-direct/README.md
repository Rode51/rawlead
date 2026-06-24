# Яндекс.Директ — материалы M1

**Кампания:** `m1_direct_v1` · **Дата:** 2026-06-22  
**Статус:** HTML-баннеры готовы · PNG — сделать скриншоты (см. ниже)

---

## Файлы

| Файл | Назначение |
|------|-----------|
| `DIRECT_AD_COPY.md` | Все рекламные тексты: заголовки, тексты, уточнения, быстрые ссылки, минус-слова |
| `banner-v1-feed.html` | Баннер «Лента» — 2 карточки (Dev + Design), акцент на персональную ленту |
| `banner-v2-draft.html` | Баннер «Черновик» — Dev (закрыт) + Marketing с раскрытым ИИ-черновиком |
| `banner-v3-match.html` | Баннер «Match» — левая колонка текст, правая 2 карточки с Match% (Dev + Текст) |

**PNG после скриншота → `docs/design/assets/yandex-direct/`**

---

## Как сделать PNG 1080×1080

### Вариант 1 — Chrome DevTools (вручную)

1. Открыть файл в Chrome: `File → Open File` → выбрать `.html`
2. DevTools (F12) → вкладка **Device Toolbar** (Ctrl+Shift+M)
3. Задать размер: **1080 × 1080**, Device Pixel Ratio: **1**
4. Правый клик на странице → **Capture screenshot**
5. Сохранить как `banner-v1-feed.png` / `banner-v2-draft.png` / `banner-v3-match.png`
6. Переместить в `docs/design/assets/yandex-direct/`

### Вариант 2 — Playwright (автоматический)

```bash
# Из корня репозитория
npx playwright screenshot --viewport-size="1080,1080" docs/design/yandex-direct/banner-v1-feed.html docs/design/assets/yandex-direct/banner-v1-feed.png
npx playwright screenshot --viewport-size="1080,1080" docs/design/yandex-direct/banner-v2-draft.html docs/design/assets/yandex-direct/banner-v2-draft.png
npx playwright screenshot --viewport-size="1080,1080" docs/design/yandex-direct/banner-v3-match.html docs/design/assets/yandex-direct/banner-v3-match.png
```

### Вариант 3 — Python / Camoufox (если Playwright не установлен)

```python
# scripts/screenshot_banners.py
from playwright.sync_api import sync_playwright
import pathlib

BANNERS = [
    ("docs/design/yandex-direct/banner-v1-feed.html", "docs/design/assets/yandex-direct/banner-v1-feed.png"),
    ("docs/design/yandex-direct/banner-v2-draft.html", "docs/design/assets/yandex-direct/banner-v2-draft.png"),
    ("docs/design/yandex-direct/banner-v3-match.html", "docs/design/assets/yandex-direct/banner-v3-match.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for html_path, png_path in BANNERS:
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.goto("file:///" + str(pathlib.Path(html_path).resolve()))
        page.wait_for_timeout(500)  # ждём шрифты
        page.screenshot(path=png_path, clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        print(f"✓ {png_path}")
    browser.close()
```

```bash
python scripts/screenshot_banners.py
```

---

## Баннеры — краткое описание

### V1 — «Лента» (`rsya_a`)

- **Угол:** персональная лента под стек
- **Структура:** чёрный хедер → жёлтый hero («Лента заказов под твой стек») → 2 карточки (Dev + Design) → чёрный футер с CTA
- **ЦА:** разработчик + дизайнер

### V2 — «Черновик» (`rsya_b`)

- **Угол:** ИИ-черновик отклика
- **Структура:** жёлтый хедер («ИИ пишет черновик под каждый заказ») → Dev карточка закрытая → Marketing карточка раскрытая с черновиком
- **ЦА:** маркетолог + разработчик
- **Черновик отклика:** профессиональный тон, без «делал похожих» / «кейсы покажу», конкретные вопросы к заказчику

### V3 — «Match» (`rsya_c`)

- **Угол:** совместимость заказа с профилем
- **Структура:** жёлтая левая колонка (текст + CTA) · белая правая (2 карточки Dev + Текст с Match % и полоской)
- **ЦА:** копирайтер + разработчик

---

## UTM при загрузке в кабинет Директа

| Баннер | utm_content |
|--------|-------------|
| V1 Лента | `rsya_a` |
| V2 Черновик | `rsya_b` |
| V3 Match | `rsya_c` |

Полная UTM-строка: `?utm_source=yandex&utm_medium=cpc&utm_campaign=m1_direct_v1&utm_content=rsya_X`

---

_Lead Marketing · 2026-06-22_
