"""Canonical skills pool (SKILLS_TOOLS_CATALOG v0.5) — L1 tags, catalog API, pending queue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lead_category import CATEGORIES, CATEGORY_TITLES
from rank import normalize_tags

# canonical_tag, category, tier, title_ru, shows_in_ui, synonyms (lowercase)
_CATALOG_ROWS: tuple[tuple[str, str, str, str, bool, tuple[str, ...]], ...] = (
    ("python", "dev", "A", "Python", True, ("py", "питон", "python3")),
    (
        "javascript",
        "dev",
        "A",
        "JavaScript",
        True,
        ("js", "node", "нода", "джаваскрипт"),
    ),
    ("php", "dev", "B", "PHP", True, ("пхп",)),
    ("typescript", "dev", "B", "TypeScript", True, ("ts", "тайпскрипт")),
    ("laravel", "dev", "B", "Laravel", False, ("ларавел",)),
    ("flask", "dev", "B", "Flask", False, ("фласк",)),
    ("scrapy", "dev", "B", "Scrapy", False, ("скрапи", "веб-скрейпинг")),
    ("pandas", "dev", "B", "Pandas", False, ()),
    ("vue", "dev", "B", "Vue.js", False, ("vue.js",)),
    ("nextjs", "dev", "B", "Next.js", False, ("next.js", "некст")),
    ("nodejs", "dev", "B", "Node.js", False, ("node.js",)),
    ("react_native", "dev", "B", "React Native", False, ("react native",)),
    ("flutter", "dev", "B", "Flutter", False, ()),
    (
        "mobile_dev",
        "dev",
        "B",
        "Мобильные приложения",
        True,
        ("mobile app", "мобильная разработка", "ios android"),
    ),
    ("data_analysis", "dev", "B", "Анализ данных", True, ("data science", "аналитика данных")),
    (
        "ecommerce_dev",
        "dev",
        "B",
        "Интернет-магазины",
        True,
        ("e-commerce", "интернет магазин", "ecommerce"),
    ),
    ("woocommerce", "dev", "B", "WooCommerce", False, ("woo commerce",)),
    ("opencart", "dev", "B", "OpenCart", False, ("open cart",)),
    (
        "wordpress_dev",
        "dev",
        "A",
        "WordPress",
        True,
        ("wp dev", "вордпресс разработка", "плагин wp", "wordpress"),
    ),
    (
        "telegram_bot_dev",
        "dev",
        "A",
        "Telegram-боты",
        True,
        ("telegram bot", "телеграм бот", "тг бот"),
    ),
    (
        "api_integration",
        "dev",
        "A",
        "API интеграции",
        True,
        ("rest api", "интеграция api", "webhook", "postgresql", "mysql", "база данных"),
    ),
    (
        "aiogram",
        "dev",
        "B",
        "aiogram (Python)",
        False,
        ("aiogram bot", "python telegram bot", "asyncio telegram", "телеграм бот aiogram", "aiogram 3"),
    ),
    (
        "telethon",
        "dev",
        "B",
        "Telethon (юзербот/парсер)",
        False,
        ("telethon python", "userbot", "юзербот", "парсер tg"),
    ),
    ("react", "dev", "B", "React", False, ("reactjs", "реакт")),
    ("django", "dev", "B", "Django", False, ("джанго", "django rest", "drf")),
    ("fastapi", "dev", "B", "FastAPI", False, ("фастапи", "python api")),
    ("html_css", "dev", "B", "HTML/CSS", False, ("верстка", "вёрстка", "frontend markup", "html", "css")),
    ("tilda_dev", "dev", "B", "Tilda", False, ("tilda site", "тильда", "tilda разработка")),
    (
        "llm_integration",
        "dev",
        "B",
        "ИИ-интеграция",
        False,
        (
            "openai",
            "openai api",
            "gpt",
            "gpt api",
            "langchain",
            "ai integration",
            "claude api",
            "llm",
            "нейросеть",
            "интеграция ai",
            "ai_integration",
        ),
    ),
    (
        "web_scraping",
        "dev",
        "B",
        "Парсинг сайтов",
        False,
        ("scraping", "парсер", "сбор данных", "веб-скрейпинг"),
    ),
    ("figma", "design", "A", "Figma", True, ("фигма", "wireframes", "прототипирование")),
    ("ui_ux", "design", "A", "UI/UX дизайн", True, ("ui ux", "ux/ui", "ux audit", "user research")),
    ("web_design", "design", "A", "Веб-дизайн", True, ("website design", "дизайн сайта", "сайт дизайн")),
    ("logo_design", "design", "A", "Логотипы", True, ("logotype", "логотип", "лого")),
    ("brand_identity", "design", "A", "Фирменный стиль", True, ("брендбук", "айдентика")),
    ("banner_design", "design", "A", "Баннеры/креативы", True, ("ads creatives", "баннеры", "рекламные баннеры")),
    ("landing_page_design", "design", "B", "Дизайн лендинга", False, ("лендинг дизайн", "landing design")),
    ("mobile_app_design", "design", "B", "Дизайн мобильных приложений", False, ("app design", "mobile ui")),
    ("presentation_design", "design", "B", "Презентации", False, ("pitch deck", "дизайн презентации")),
    ("motion_design", "design", "B", "Моушн-дизайн", False, ("motion", "анимация", "after effects", "ae")),
    ("video_editing", "design", "B", "Видеомонтаж", False, ("монтаж видео", "edit video", "premiere", "монтаж reels")),
    ("illustration", "design", "B", "Иллюстрации", False, ("illustration design", "иллюстратор")),
    (
        "threed_modeling",
        "design",
        "B",
        "3D-моделирование",
        False,
        ("3d model", "blender", "cinema 4d", "3д моделирование", "3d персонаж", "3d анимация"),
    ),
    ("smm", "marketing", "A", "SMM", True, ("social media marketing", "смм", "ведение соцсетей")),
    (
        "target_ads",
        "marketing",
        "A",
        "Таргет (Meta/IG)",
        True,
        ("таргет", "paid social", "таргетолог", "реклама инстаграм"),
    ),
    (
        "yandex_direct",
        "marketing",
        "A",
        "Яндекс Директ",
        True,
        ("директ", "yandex ads", "яндекс.директ", "я.директ", "контекстная реклама", "яндекс директ"),
    ),
    ("google_ads", "marketing", "A", "Google Ads", True, ("google adwords", "гугл реклама", "ppc google", "google ads")),
    ("seo", "marketing", "A", "SEO", True, ("сео", "search optimization", "продвижение сайта")),
    (
        "email_marketing",
        "marketing",
        "A",
        "Email-маркетинг",
        True,
        ("рассылки", "email рассылка", "crm mailings", "email automation"),
    ),
    ("vk_ads", "marketing", "B", "Реклама ВКонтакте", False, ("vk ads", "реклама вк", "вк реклама")),
    (
        "content_marketing",
        "marketing",
        "B",
        "Контент-маркетинг",
        False,
        ("контент стратегия", "content plan", "контент план"),
    ),
    ("web_analytics", "marketing", "B", "Веб-аналитика", False, ("ga4", "аналитика сайта", "яндекс метрика")),
    ("marketplace_promotion", "marketing", "B", "Маркетплейсы", False, ("ozon", "wb", "wildberries", "маркетплейс")),
    (
        "chatbot_marketing",
        "marketing",
        "B",
        "Маркетинг-боты",
        False,
        ("senler bot", "salebot funnels", "чат-бот воронка"),
    ),
    (
        "crm_marketing",
        "marketing",
        "B",
        "CRM-маркетинг",
        False,
        ("crm сегментация", "lifecycle email", "ретаргетинг"),
    ),
    ("copywriting", "text", "A", "Копирайтинг", True, ("тексты", "writing", "текст на заказ")),
    ("seo_copywriting", "text", "A", "SEO-копирайтинг", True, ("seo тексты", "оптимизированные тексты")),
    ("article_writing", "text", "A", "Статьи/блог", True, ("blog posts", "лонгриды", "статьи")),
    ("translation", "text", "A", "Перевод", True, ("localization", "перевод текстов", "локализация")),
    ("technical_writing", "text", "A", "Технические тексты", True, ("документация", "technical docs", "техническое задание")),
    ("editing_proofreading", "text", "A", "Редактура и корректура", True, ("proofreading", "вычитка", "корректура")),
    ("sales_copywriting", "text", "B", "Продажные тексты", False, ("sales pages", "рекламные тексты", "продающий текст")),
    ("script_writing", "text", "B", "Сценарии", False, ("video script", "сценарий reels", "сценарий ролика")),
    ("product_description", "text", "B", "Описания товаров", False, ("ecom карточки", "карточки товаров", "marketplace text")),
    ("email_copywriting", "text", "B", "Тексты для email", False, ("email sequence", "письмо-воронка")),
    ("ux_writing", "text", "B", "UX-райтинг", False, ("microcopy", "тексты интерфейсов")),
    (
        "server_administration",
        "dev",
        "B",
        "Администрирование серверов",
        False,
        (
            "3x-ui",
            "3x ui",
            "vps",
            "ssh",
            "linux server",
            "настройка сервера",
            "установка по",
            "сервер macos",
            "серверная",
        ),
    ),
    (
        "technical_seo",
        "marketing",
        "B",
        "Техническое SEO",
        False,
        (
            "robots.txt",
            "sitemap",
            "search console",
            "вебмастер",
            "индексац",
            "gsc",
            "google search console",
            "техническ seo",
            "техническое seo",
        ),
    ),
    (
        "infographic_design",
        "design",
        "B",
        "Инфографика",
        False,
        (
            "инфографик",
            "wildberries",
            "ozon",
            "маркетплейс",
            "wb ",
            "карточк товар",
            "маркетплейса",
        ),
    ),
    (
        "transcription",
        "text",
        "B",
        "Транскрибация",
        False,
        (
            "транскриб",
            "расшифров",
            "audio transcription",
            "видео в текст",
            "расшифровк",
        ),
    ),
)

# v0.2 → v0.3 merge (t3-5 partial — для resolve старых тегов в БД/L1)
_V02_MERGE_ALIASES: dict[str, str] = {
    "ai_integration": "llm_integration",
    "node_js": "nodejs",
    "vue_js": "vue",
    "meta_ads": "target_ads",
    "subtitles": "translation",
    "sql": "api_integration",
    "email_automation": "email_marketing",
    "ppc": "yandex_direct",
    "wordpress_marketing": "wordpress_dev",
    "telegram_bot_marketing": "telegram_bot_dev",
    "ux_research": "ui_ux",
    "wireframing": "figma",
    "docker": "api_integration",
    "influencer_marketing": "smm",
    "conversion_rate_optimization": "seo",
    "typography": "brand_identity",
    "naming": "brand_identity",
    "resume_cv_writing": "technical_writing",
}

# O94 v0.5 — 4-niche tree picker (SKILLS_TOOLS_CATALOG v0.5)
DEV_USE_CASE_L1: tuple[str, ...] = (
    "telegram_bot_dev",
    "wordpress_dev",
    "web_scraping",
    "api_integration",
    "llm_integration",
    "mobile_dev",
    "data_analysis",
    "ecommerce_dev",
)
DEV_TECHNOLOGY_L1: tuple[str, ...] = ("python", "javascript", "php", "typescript")
DEV_PICKER_L1: tuple[str, ...] = DEV_USE_CASE_L1 + DEV_TECHNOLOGY_L1

PICKER_GROUP_LABELS: dict[str, str] = {
    "use_case": "По задаче",
    "technology": "По технологии",
    "product_web": "Продукт & Web",
    "brand_graphics": "Бренд & Графика",
    "video_motion": "Видео & Моушн",
    "organic": "Органика",
    "paid_platform": "По платформе",
    "commercial": "Коммерческий текст",
    "editorial": "Редактура & Публикации",
    "language": "Перевод & Локализация",
}

# picker_group key, UI label, L1 parent tags (order preserved)
_NICHE_SUBHEAD_L1: dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]] = {
    "dev": (
        ("use_case", "По задаче", DEV_USE_CASE_L1),
        ("technology", "По технологии", DEV_TECHNOLOGY_L1),
    ),
    "design": (
        ("product_web", "Продукт & Web", ("ui_ux", "figma")),
        ("brand_graphics", "Бренд & Графика", ("logo_design", "banner_design", "presentation_design")),
        ("video_motion", "Видео & Моушн", ("video_editing", "motion_design", "threed_modeling")),
    ),
    "marketing": (
        ("organic", "Органика", ("smm", "seo", "email_marketing", "marketplace_promotion")),
        ("paid_platform", "По платформе", ("target_ads", "yandex_direct", "google_ads", "vk_ads")),
    ),
    "text": (
        ("commercial", "Коммерческий текст", ("copywriting", "seo_copywriting", "sales_copywriting")),
        (
            "editorial",
            "Редактура & Публикации",
            ("article_writing", "technical_writing", "editing_proofreading", "script_writing"),
        ),
        ("language", "Перевод & Локализация", ("translation", "ux_writing", "product_description")),
    ),
}

# parent → expanded tags for keyword_match (includes parent) — v0.5 full map
EXPAND_MAP: dict[str, tuple[str, ...]] = {
    "telegram_bot_dev": ("telegram_bot_dev", "aiogram", "telethon"),
    "wordpress_dev": ("wordpress_dev", "php", "html_css"),
    "web_scraping": ("web_scraping", "telethon", "scrapy"),
    "api_integration": ("api_integration",),
    "llm_integration": ("llm_integration",),
    "mobile_dev": ("mobile_dev", "react_native", "flutter"),
    "data_analysis": ("data_analysis", "pandas"),
    "ecommerce_dev": ("ecommerce_dev", "woocommerce", "opencart"),
    "python": ("python", "django", "fastapi", "flask", "scrapy"),
    "javascript": ("javascript", "react", "vue", "nextjs", "nodejs", "typescript"),
    "php": ("php", "laravel", "woocommerce"),
    "typescript": ("typescript", "javascript"),
    "ui_ux": ("ui_ux", "web_design", "landing_page_design", "mobile_app_design"),
    "figma": ("figma",),
    "logo_design": ("logo_design", "brand_identity"),
    "banner_design": ("banner_design", "motion_design", "video_editing"),
    "brand_identity": ("brand_identity", "illustration"),
    "video_editing": ("video_editing", "motion_design"),
    "smm": ("smm", "content_marketing"),
    "seo": ("seo", "web_analytics", "technical_seo"),
    "email_marketing": ("email_marketing", "crm_marketing", "chatbot_marketing"),
    "target_ads": ("target_ads",),
    "yandex_direct": ("yandex_direct",),
    "google_ads": ("google_ads",),
    "vk_ads": ("vk_ads",),
    "copywriting": ("copywriting", "sales_copywriting", "email_copywriting", "ux_writing"),
    "article_writing": ("article_writing", "seo_copywriting", "technical_writing"),
    "translation": ("translation",),
}

L3_BY_PARENT: dict[str, tuple[str, ...]] = {
    "telegram_bot_dev": ("aiogram", "telethon"),
    "wordpress_dev": ("php", "html_css"),
    "web_scraping": ("telethon", "scrapy"),
    "mobile_dev": ("react_native", "flutter"),
    "data_analysis": ("pandas",),
    "ecommerce_dev": ("woocommerce", "opencart"),
    "python": ("django", "fastapi", "flask", "scrapy"),
    "javascript": ("react", "vue", "nextjs", "nodejs", "typescript"),
    "php": ("laravel", "woocommerce"),
    "ui_ux": ("web_design", "mobile_app_design"),
    "logo_design": ("brand_identity", "illustration"),
    "banner_design": ("motion_design", "video_editing"),
    "video_editing": ("motion_design",),
    "seo": ("web_analytics", "technical_seo"),
    "smm": ("content_marketing",),
    "email_marketing": ("crm_marketing", "chatbot_marketing"),
    "copywriting": ("sales_copywriting", "email_copywriting", "ux_writing"),
    "article_writing": ("technical_writing",),
}

TIER_A_BY_NICHE: dict[str, tuple[str, ...]] = {
    "dev": (
        "telegram_bot_dev",
        "wordpress_dev",
        "web_scraping",
        "api_integration",
        "llm_integration",
        "python",
        "javascript",
    ),
    "design": ("ui_ux", "figma", "logo_design", "banner_design"),
    "marketing": ("smm", "seo", "email_marketing", "target_ads", "yandex_direct", "google_ads"),
    "text": (
        "copywriting",
        "seo_copywriting",
        "article_writing",
        "technical_writing",
        "editing_proofreading",
        "translation",
    ),
}


@dataclass(frozen=True)
class SkillEntry:
    tag: str
    category: str
    tier: str
    title_ru: str
    shows_in_ui: bool
    synonyms: tuple[str, ...]


def _build_index() -> tuple[dict[str, SkillEntry], frozenset[str], dict[str, str]]:
    by_tag: dict[str, SkillEntry] = {}
    synonym_map: dict[str, str] = {}
    for row in _CATALOG_ROWS:
        tag, cat, tier, title, ui, syns = row
        entry = SkillEntry(tag=tag, category=cat, tier=tier, title_ru=title, shows_in_ui=ui, synonyms=syns)
        by_tag[tag] = entry
        for syn in syns:
            key = syn.strip().lower().lstrip("#")
            if key and key not in synonym_map:
                synonym_map[key] = tag
        synonym_map[tag] = tag
    for alias, canonical in _V02_MERGE_ALIASES.items():
        if alias not in synonym_map:
            synonym_map[alias] = canonical
    return by_tag, frozenset(by_tag.keys()), synonym_map


_SKILLS_BY_TAG, CANONICAL_TAGS, _SYNONYM_TO_CANONICAL = _build_index()

_L1_MAX_TAGS = 6


def category_for_canonical_tag(canonical: str) -> str | None:
    """Категория из пула навыков (dev/design/marketing/text)."""
    entry = _SKILLS_BY_TAG.get(canonical)
    return entry.category if entry else None


def user_tags_input_count(raw_tags: list[str]) -> int:
    """Число уникальных canonical после merge."""
    seen: set[str] = set()
    for raw in normalize_tags(raw_tags):
        canonical = resolve_canonical_tag(raw)
        if canonical and canonical in CANONICAL_TAGS:
            seen.add(canonical)
    return len(seen)


def normalize_user_tags(raw_tags: list[str]) -> list[str]:
    """user_tags: v0.2→v0.3 merge, canonical only (quiz-first — no cap)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in normalize_tags(raw_tags):
        canonical = resolve_canonical_tag(raw)
        if canonical and canonical in CANONICAL_TAGS and canonical not in seen:
            seen.add(canonical)
            out.append(canonical)
    return out


def lead_tags_for_feed(raw: Any) -> tuple[list[str], list[str]]:
    """Карточка ленты: canonical slugs + RU labels, без pending."""
    if raw is None:
        tags_in: list[str] = []
    elif isinstance(raw, list):
        tags_in = normalize_tags([str(t) for t in raw])
    else:
        tags_in = []
    slugs: list[str] = []
    labels: list[str] = []
    seen: set[str] = set()
    for tag_raw in tags_in:
        canonical = resolve_canonical_tag(tag_raw)
        if canonical and canonical in CANONICAL_TAGS and canonical not in seen:
            seen.add(canonical)
            slugs.append(canonical)
            labels.append(title_for_tag(canonical))
    return slugs, labels


def resolve_canonical_tag(raw: str) -> str | None:
    """Synonym или canonical → canonical_tag; иначе None."""
    t = str(raw).strip().lower().lstrip("#")
    if not t:
        return None
    if t in CANONICAL_TAGS:
        return t
    return _SYNONYM_TO_CANONICAL.get(t)


def partition_lead_tags(raw_tags: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Разделить L1-теги: known (canonical pool) и unknown (→ pending_tags)."""
    known: list[str] = []
    pending: list[str] = []
    seen_known: set[str] = set()
    seen_pending: set[str] = set()
    for raw in normalize_tags(raw_tags):
        canonical = resolve_canonical_tag(raw)
        if canonical and canonical not in seen_known:
            seen_known.add(canonical)
            known.append(canonical)
        elif not canonical and raw not in seen_pending:
            seen_pending.add(raw)
            pending.append(raw)
        if len(known) >= _L1_MAX_TAGS:
            break
    if "llm_integration" in known and "api_integration" in known:
        known = [t for t in known if t != "api_integration"]
    return tuple(known[:_L1_MAX_TAGS]), tuple(pending)


_CMS_NON_WP_MARKERS = ("joomla", "bitrix", "opencart", "baforms")


def _text_has_non_wp_cms(title: str, snippet: str) -> bool:
    hay = f"{title or ''}\n{snippet or ''}".casefold()
    return any(m in hay for m in _CMS_NON_WP_MARKERS)


def sanitize_l1_cms_tags(
    lead_tags: tuple[str, ...],
    *,
    title: str = "",
    snippet: str = "",
) -> tuple[str, ...]:
    """Post-validate L1: Joomla/Bitrix/OpenCart/BaForms ≠ wordpress_dev (O47)."""
    if not lead_tags or "wordpress_dev" not in lead_tags:
        return lead_tags
    if not _text_has_non_wp_cms(title, snippet):
        return lead_tags
    tags = [t for t in lead_tags if t != "wordpress_dev"]
    has_dev = any(category_for_canonical_tag(t) == "dev" for t in tags)
    if (has_dev or not tags) and "php" not in tags and len(tags) < _L1_MAX_TAGS:
        tags.append("php")
    return tuple(tags[:_L1_MAX_TAGS])


def l1_gate_anti_rules_block() -> str:
    """O72e-9: анти-правила из gate 063753Z (категория + теги)."""
    return """
Анти-ошибки category/lead_tags (перед JSON):
- 3X-UI / VPS / SSH / установка ПО на сервер → primary_category **dev**, теги server_administration (не api_integration/javascript «наугад»)
- инфографика WB/Ozon/маркетплейс → **design**, infographic_design (не dev)
- Tilda + GSC/индексация/robots/sitemap/Search Console → **dev**, technical_seo (не design; tilda_dev только если правки сайта, не «дизайн»)
- привлечение трафика в TG-бот / реферал / Sora / Kling / партнёрка → **marketing** (не design)
- спрайты / иллюстрация без кода → **design**, illustration (не dev)
- Google Sheets + SMTP-скрипт / Apps Script автоматизация → **dev** (javascript), не marketing
- транскрибация / расшифровка аудио+перевод → **text**, transcription + translation
- UX/UI аудит экрана приложения → **design**, ui_ux (не dev)
- оформление группы ВК (обложка, виджеты, описание) → **design** (ui_ux, banner_design), не smm/vk_ads если нет рекламы
- api_integration — только при явном API/скрипте/интеграции в ТЗ, не от слов «api»/«лендинг» без dev-контекста
"""


def allowed_tags_prompt_block() -> str:
    """Блок для L1 system: разрешённые canonical_tag по нишам."""
    lines = [
        "",
        "lead_tags — только canonical_tag из списка ниже (EN slug, без #, без русских слов).",
        "**2–5 тегов на заказ** (не меньше 2 при feed_visible=true); максимум "
        f"{_L1_MAX_TAGS} тегов. Каждый тег должен быть из словаря **primary_category**.",
        "Синонимы из заказа → canonical (яндекс.директ → yandex_direct; gpt/openai → llm_integration).",
        "ЗАПРЕЩЕНО как теги: ai, automation, #ai — только canonical из пула.",
        l1_gate_anti_rules_block().strip(),
        "",
        f"Разрешённые canonical_tag (v0.5, {len(CANONICAL_TAGS)}):",
    ]
    for cat in CATEGORIES:
        tags = sorted(e.tag for e in _SKILLS_BY_TAG.values() if e.category == cat)
        lines.append(f"{CATEGORY_TITLES[cat]} ({cat}): " + ", ".join(tags))
    return "\n".join(lines)


def title_for_tag(tag: str) -> str:
    """Label из SKILLS_TOOLS_CATALOG или slug как есть."""
    entry = _SKILLS_BY_TAG.get(tag)
    if entry:
        return entry.title_ru
    return str(tag).replace("_", " ")


def expand_user_tags_for_match(user_tags: set[str]) -> set[str]:
    """Parent L1 → children for keyword_match (O93 EXPAND_MAP)."""
    expanded: set[str] = set()
    for tag in user_tags:
        children = EXPAND_MAP.get(tag)
        if children:
            expanded.update(children)
        else:
            expanded.add(tag)
    return expanded


def _l3_children(parent_tag: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for l3 in L3_BY_PARENT.get(parent_tag, ()):
        entry = _SKILLS_BY_TAG.get(l3)
        if not entry:
            continue
        out.append(
            {
                "tag": l3,
                "title_ru": entry.title_ru,
                "tier": entry.tier,
                "picker_level": "L3",
                "parent_id": parent_tag,
            }
        )
    return out


def _tree_picker_skills(category: str) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    for group_key, _label, l1_tags in _NICHE_SUBHEAD_L1.get(category, ()):
        for tag in l1_tags:
            entry = _SKILLS_BY_TAG.get(tag)
            if not entry:
                continue
            skills.append(
                {
                    "tag": tag,
                    "title_ru": entry.title_ru,
                    "tier": entry.tier,
                    "picker_level": "L1",
                    "picker_group": group_key,
                    "children": _l3_children(tag),
                }
            )
    return skills


def _picker_subheads_for(category: str) -> list[dict[str, str]]:
    return [
        {"key": group_key, "label": PICKER_GROUP_LABELS.get(group_key, label)}
        for group_key, label, _tags in _NICHE_SUBHEAD_L1.get(category, ())
    ]


def build_dynamic_catalog_groups(
    rows: list[tuple[str, int]],
    *,
    categories: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Каталог из lead_tags (count по canonical) + label из канона."""
    from lead_category import build_skills_groups

    merged: dict[str, int] = {}
    for raw_tag, cnt in rows:
        canonical = resolve_canonical_tag(raw_tag) or str(raw_tag).strip().lower()
        if not canonical or canonical not in CANONICAL_TAGS:
            continue
        merged[canonical] = merged.get(canonical, 0) + int(cnt)
    sorted_rows = sorted(merged.items(), key=lambda x: (-x[1], x[0]))
    groups, flat = build_skills_groups(sorted_rows, categories=categories)
    for item in flat:
        item["title_ru"] = title_for_tag(item["tag"])
    for group in groups:
        for skill in group.get("skills", []):
            skill["title_ru"] = title_for_tag(skill["tag"])
    return groups, flat


def build_catalog_groups(
    *,
    categories: list[str] | None = None,
    ui_only: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Статический каталог (fallback / full mode). O93 tree for dev."""
    cat_filter = set(categories) if categories else None
    buckets: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    flat: list[dict[str, Any]] = []
    flat_seen: set[str] = set()

    def append_flat(item: dict[str, Any], category: str) -> None:
        tag = item.get("tag")
        if not tag or tag in flat_seen:
            return
        flat_seen.add(tag)
        flat.append({**item, "category": category})

    tree_cats = [c for c in CATEGORIES if c in _NICHE_SUBHEAD_L1]
    if cat_filter is not None:
        tree_cats = [c for c in tree_cats if c in cat_filter]

    picker_l1_all: set[str] = set()
    for _cat, subheads in _NICHE_SUBHEAD_L1.items():
        for _gk, _lbl, tags in subheads:
            picker_l1_all.update(tags)

    for cat in tree_cats:
        tree_skills = _tree_picker_skills(cat)
        buckets[cat] = tree_skills
        for skill in tree_skills:
            append_flat(skill, cat)
            for child in skill.get("children") or []:
                append_flat(child, cat)
        if not ui_only:
            for entry in sorted(_SKILLS_BY_TAG.values(), key=lambda e: e.tag):
                if entry.category != cat:
                    continue
                if entry.tag in flat_seen or entry.tag in picker_l1_all:
                    continue
                append_flat(
                    {
                        "tag": entry.tag,
                        "title_ru": entry.title_ru,
                        "tier": entry.tier,
                        "picker_level": "L3" if entry.tag in _all_l3_tags() else "L1",
                    },
                    cat,
                )

    group_cats = [c for c in CATEGORIES if cat_filter is None or c in cat_filter]
    groups: list[dict[str, Any]] = []
    for cat in group_cats:
        if not buckets[cat]:
            continue
        group: dict[str, Any] = {
            "category": cat,
            "title": CATEGORY_TITLES[cat],
            "skills": buckets[cat],
        }
        if cat in _NICHE_SUBHEAD_L1:
            group["picker_subheads"] = _picker_subheads_for(cat)
        groups.append(group)
    return groups, flat


def _all_l3_tags() -> frozenset[str]:
    tags: set[str] = set()
    for children in L3_BY_PARENT.values():
        tags.update(children)
    return frozenset(tags)
