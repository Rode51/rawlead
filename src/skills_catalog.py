"""Canonical skills pool (SKILLS_TOOLS_CATALOG v0.3) — L1 tags, catalog API, pending queue."""

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
        ("js", "node.js", "nodejs", "node", "нода", "vue", "vue.js", "джаваскрипт"),
    ),
    ("php", "dev", "A", "PHP", True, ("пхп", "laravel", "ларавел")),
    (
        "wordpress_dev",
        "dev",
        "A",
        "WordPress разработка",
        True,
        ("wp dev", "вордпресс разработка", "плагин wp"),
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
        ("aiogram bot", "python telegram bot", "asyncio telegram", "телеграм бот aiogram"),
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
    ("html_css", "dev", "B", "HTML/CSS", False, ("верстка", "вёрстка", "frontend markup")),
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
        "Таргетированная реклама",
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
    ("google_ads", "marketing", "A", "Google Ads", True, ("google adwords", "гугл реклама", "ppc google")),
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
)

# v0.2 → v0.3 merge (t3-5 partial — для resolve старых тегов в БД/L1)
_V02_MERGE_ALIASES: dict[str, str] = {
    "ai_integration": "llm_integration",
    "node_js": "javascript",
    "laravel": "php",
    "vue_js": "javascript",
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
    "transcription": "editing_proofreading",
    "resume_cv_writing": "technical_writing",
}

_USER_MAX_TAGS = 6

# Tier A default per niche (picker)
TIER_A_BY_NICHE: dict[str, tuple[str, ...]] = {
    "dev": (
        "python",
        "javascript",
        "php",
        "wordpress_dev",
        "telegram_bot_dev",
        "api_integration",
    ),
    "design": (
        "figma",
        "ui_ux",
        "web_design",
        "logo_design",
        "brand_identity",
        "banner_design",
    ),
    "marketing": (
        "smm",
        "target_ads",
        "yandex_direct",
        "google_ads",
        "seo",
        "email_marketing",
    ),
    "text": (
        "copywriting",
        "seo_copywriting",
        "article_writing",
        "translation",
        "technical_writing",
        "editing_proofreading",
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
    """Число уникальных canonical после merge (до обрезки max 6)."""
    seen: set[str] = set()
    for raw in normalize_tags(raw_tags):
        canonical = resolve_canonical_tag(raw)
        if canonical and canonical in CANONICAL_TAGS:
            seen.add(canonical)
    return len(seen)


def normalize_user_tags(raw_tags: list[str]) -> list[str]:
    """user_tags: v0.2→v0.3 merge, canonical only, max 6."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in normalize_tags(raw_tags):
        canonical = resolve_canonical_tag(raw)
        if canonical and canonical in CANONICAL_TAGS and canonical not in seen:
            seen.add(canonical)
            out.append(canonical)
        if len(out) >= _USER_MAX_TAGS:
            break
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


def allowed_tags_prompt_block() -> str:
    """Блок для L1 system: разрешённые canonical_tag по нишам."""
    lines = [
        "",
        "lead_tags — только canonical_tag из списка ниже (EN slug, без #, без русских слов).",
        f"Максимум {_L1_MAX_TAGS} тегов. Навык не в списке — не добавляй.",
        "Синонимы из заказа → canonical (яндекс.директ → yandex_direct; gpt/openai → llm_integration).",
        "ЗАПРЕЩЕНО как теги: ai, automation, #ai — только canonical из пула.",
        "",
        f"Разрешённые canonical_tag (v0.3, {len(CANONICAL_TAGS)}):",
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
    """Статический каталог (fallback / dev)."""
    cat_filter = set(categories) if categories else None
    buckets: dict[str, list[dict[str, Any]]] = {c: [] for c in CATEGORIES}
    flat: list[dict[str, Any]] = []
    for entry in sorted(_SKILLS_BY_TAG.values(), key=lambda e: (e.category, e.tier, e.tag)):
        if cat_filter is not None and entry.category not in cat_filter:
            continue
        if ui_only and not entry.shows_in_ui:
            continue
        item = {
            "tag": entry.tag,
            "title_ru": entry.title_ru,
            "category": entry.category,
            "tier": entry.tier,
        }
        flat.append(item)
        buckets[entry.category].append(
            {
                "tag": entry.tag,
                "title_ru": entry.title_ru,
                "tier": entry.tier,
            }
        )
    group_cats = [c for c in CATEGORIES if cat_filter is None or c in cat_filter]
    groups = [
        {
            "category": cat,
            "title": CATEGORY_TITLES[cat],
            "skills": buckets[cat],
        }
        for cat in group_cats
        if buckets[cat]
    ]
    return groups, flat
