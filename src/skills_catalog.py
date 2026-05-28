"""Canonical skills pool (SKILLS_TOOLS_CATALOG v0.2) — L1 tags, catalog API, pending queue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lead_category import CATEGORIES, CATEGORY_TITLES
from rank import normalize_tags

# canonical_tag, category, tier, title_ru, shows_in_ui, synonyms (lowercase)
_CATALOG_ROWS: tuple[tuple[str, str, str, str, bool, tuple[str, ...]], ...] = (
    ("python", "dev", "A", "Python", True, ("py", "питон")),
    ("javascript", "dev", "A", "JavaScript", True, ("js", "джаваскрипт")),
    ("react", "dev", "A", "React", True, ("reactjs", "реакт")),
    ("node_js", "dev", "A", "Node.js", True, ("node", "нода")),
    ("php", "dev", "A", "PHP", True, ("пхп",)),
    ("wordpress_dev", "dev", "A", "WordPress разработка", True, ("wp dev", "вордпресс разработка")),
    ("laravel", "dev", "A", "Laravel", True, ("ларавел",)),
    ("telegram_bot_dev", "dev", "A", "Telegram-боты", True, ("telegram bot", "телеграм бот")),
    ("api_integration", "dev", "A", "API интеграции", True, ("rest api", "интеграция api")),
    ("sql", "dev", "A", "SQL", True, ("postgresql", "mysql", "скл")),
    ("web_scraping", "dev", "B", "Парсинг сайтов", False, ("scraping", "веб-скрейпинг", "парсер", "сбор данных")),
    ("docker", "dev", "B", "Docker", False, ("докер",)),
    ("django", "dev", "B", "Django", False, ("джанго",)),
    ("fastapi", "dev", "B", "FastAPI", False, ("фастапи",)),
    ("vue_js", "dev", "B", "Vue.js", False, ("vue", "вью")),
    ("html_css", "dev", "B", "HTML/CSS", False, ("верстка", "frontend markup")),
    ("ai_integration", "dev", "B", "Интеграция AI", False, ("openai api", "llm integration")),
    ("tilda_dev", "dev", "B", "Tilda разработка", False, ("tilda", "тильда", "tilda site")),
    ("email_automation", "dev", "B", "Email-автоматизация", False, ("email рассылка", "email integration", "шаблоны писем")),
    ("ui_ux", "design", "A", "UI/UX дизайн", True, ("ui ux", "ux/ui")),
    ("web_design", "design", "A", "Веб-дизайн", True, ("website design", "дизайн сайта")),
    ("figma", "design", "A", "Figma", True, ("фигма",)),
    ("landing_page_design", "design", "A", "Дизайн лендинга", True, ("лендинг дизайн", "landing design")),
    ("mobile_app_design", "design", "A", "Дизайн мобильных приложений", True, ("app design", "mobile ui")),
    ("banner_design", "design", "A", "Баннеры/креативы", True, ("ads creatives", "баннеры")),
    ("brand_identity", "design", "A", "Фирменный стиль", True, ("брендбук", "айдентика")),
    ("presentation_design", "design", "A", "Презентации", True, ("pitch deck", "дизайн презентации")),
    ("logo_design", "design", "A", "Логотипы", True, ("logotype", "логотип")),
    ("motion_design", "design", "B", "Моушн-дизайн", False, ("motion", "анимация")),
    ("video_editing", "design", "B", "Видеомонтаж", False, ("монтаж видео", "edit video")),
    ("ux_research", "design", "B", "UX-исследования", False, ("user research", "ux audit")),
    ("wireframing", "design", "B", "Вайрфреймы", False, ("прототипирование", "wireframes")),
    ("typography", "design", "B", "Типографика", False, ("шрифты", "type design")),
    ("illustration", "design", "B", "Иллюстрации", False, ("illustration design", "иллюстратор")),
    (
        "threed_modeling",
        "design",
        "A",
        "3D и текстуры",
        True,
        (
            "3d model",
            "blender",
            "блендер",
            "3д моделирование",
            "текстуры",
            "текстурирование",
            "текстуры в blender",
            "texture painting",
        ),
    ),
    ("smm", "marketing", "A", "SMM", True, ("social media marketing", "смм")),
    ("target_ads", "marketing", "A", "Таргетированная реклама", True, ("таргет", "paid social", "таргетированная реклама")),
    ("vk_ads", "marketing", "A", "Реклама ВКонтакте", True, ("vk ads", "реклама вк", "вк реклама", "вконтакте реклама")),
    (
        "yandex_direct",
        "marketing",
        "A",
        "Яндекс Директ",
        True,
        ("директ", "yandex ads", "яндекс.директ", "я.директ", "яндекс директ"),
    ),
    ("google_ads", "marketing", "A", "Google Ads", True, ("google adwords", "гугл реклама")),
    ("seo", "marketing", "A", "SEO", True, ("сео", "search optimization")),
    ("ppc", "marketing", "A", "PPC", True, ("контекстная реклама", "paid search")),
    ("email_marketing", "marketing", "A", "Email-маркетинг", True, ("рассылки", "crm mailings")),
    ("content_marketing", "marketing", "A", "Контент-маркетинг", True, ("контент стратегия", "content plan")),
    ("web_analytics", "marketing", "A", "Веб-аналитика", True, ("ga4", "аналитика сайта")),
    ("marketplace_promotion", "marketing", "B", "Продвижение маркетплейсов", False, ("ozon", "wb", "wildberries")),
    ("influencer_marketing", "marketing", "B", "Инфлюенсер-маркетинг", False, ("блогеры", "influencer ads")),
    ("crm_marketing", "marketing", "B", "CRM-маркетинг", False, ("сегментация crm", "lifecycle")),
    ("conversion_rate_optimization", "marketing", "B", "CRO/конверсия", False, ("оптимизация конверсии", "cro")),
    ("chatbot_marketing", "marketing", "B", "Маркетинг-боты", False, ("senler bot", "salebot funnels")),
    ("wordpress_marketing", "marketing", "B", "WordPress (маркетинг)", False, ("wp сайт", "wordpress сайт")),
    ("telegram_bot_marketing", "marketing", "B", "Telegram-боты (маркетинг)", False, ("тг бот",)),
    ("copywriting", "text", "A", "Копирайтинг", True, ("тексты", "writing")),
    ("seo_copywriting", "text", "A", "SEO-копирайтинг", True, ("seo тексты", "оптимизированные тексты")),
    ("sales_copywriting", "text", "A", "Продажные тексты", True, ("sales pages", "рекламные тексты")),
    ("editing_proofreading", "text", "A", "Редактура и корректура", True, ("proofreading", "вычитка")),
    ("article_writing", "text", "A", "Статьи/блог", True, ("blog posts", "лонгриды")),
    ("technical_writing", "text", "A", "Технические тексты", True, ("документация", "technical docs")),
    ("translation", "text", "A", "Перевод", True, ("localization", "перевод текстов")),
    ("script_writing", "text", "A", "Сценарии", True, ("video script", "сценарий reels")),
    ("product_description", "text", "B", "Описания товаров", False, ("ecom карточки", "marketplace text")),
    ("naming", "text", "B", "Нейминг", False, ("brand naming", "название бренда")),
    ("email_copywriting", "text", "B", "Тексты для email", False, ("email sequence", "письмо-воронка")),
    ("ux_writing", "text", "B", "UX-райтинг", False, ("microcopy", "тексты интерфейсов")),
    ("transcription", "text", "B", "Транскрибация", False, ("speech-to-text", "расшифровка")),
    ("resume_cv_writing", "text", "B", "Резюме/CV", False, ("cv writing", "резюме на заказ")),
)


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
    return by_tag, frozenset(by_tag.keys()), synonym_map


_SKILLS_BY_TAG, CANONICAL_TAGS, _SYNONYM_TO_CANONICAL = _build_index()

_L1_MAX_TAGS = 5


def category_for_canonical_tag(canonical: str) -> str | None:
    """Категория из пула навыков (dev/design/marketing/text)."""
    entry = _SKILLS_BY_TAG.get(canonical)
    return entry.category if entry else None


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
    return tuple(known[:_L1_MAX_TAGS]), tuple(pending)


def allowed_tags_prompt_block() -> str:
    """Блок для L1 system: разрешённые canonical_tag по нишам."""
    lines = [
        "",
        "lead_tags — только из списка canonical_tag ниже (строго, без своих слов).",
        "Максимум 5 тегов. Если навык не в списке — не добавляй (мы увидим его отдельно).",
        "Синонимы из текста заказа переводи в canonical_tag (яндекс.директ → yandex_direct).",
        "",
        "Границы категорий:",
        "- text: тексты, копирайт, статьи, перевод — НЕ 3D, Blender, видеомонтаж (это design).",
        "- dev: код, API, боты, автоматизация — НЕ нейминг и описания товаров (это text/marketing).",
        "",
        "Разрешённые теги:",
    ]
    for cat in CATEGORIES:
        tags = [e.tag for e in _SKILLS_BY_TAG.values() if e.category == cat]
        tags.sort()
        lines.append(f"{CATEGORY_TITLES[cat]} ({cat}): " + ", ".join(tags))
    return "\n".join(lines)


def build_catalog_groups(
    *,
    categories: list[str] | None = None,
    ui_only: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Статический каталог для GET /v1/skills/catalog."""
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
        buckets[entry.category].append({"tag": entry.tag, "title_ru": entry.title_ru})
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
