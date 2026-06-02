"""ИИ-разбор заказа: stateless OpenRouter, system docs/AI.md v6.1 (TZ §5)."""

from __future__ import annotations

import json
import logging
import re
import time
import hashlib
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from budget import display_budget_text
from config import DIRECT_REQUESTS_PROXIES, Config
from rank import normalize_tags
from reply_draft_strip import strip_reply_draft_price_deadline
from lead_category import CATEGORIES, resolve_lead_category
from skills_catalog import (
    CANONICAL_TAGS,
    _L1_MAX_TAGS,
    allowed_tags_prompt_block,
    category_for_canonical_tag,
    partition_lead_tags,
    sanitize_l1_cms_tags,
)

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROFILE_PATH = _PROJECT_ROOT / "docs" / "ops" / "PROFILE.md"
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_AI_FIELDS = (
    "verdict",
    "work_summary",
    "difficulty",
    "approach",
    "time_for_client",
    "money",
    "reply_draft",
    "risks",
    "lead_tags",
)

_VALID_VERDICTS = frozenset({"брать", "брат", "сомнительно", "пропустить", "мимо"})
_SKIP_VERDICTS = frozenset({"пропустить", "мимо"})
_JSON_BLOCK = re.compile(r"\{[\s\S]*\}", re.MULTILINE)
# «ИИ» — только отдельное слово; не ловить «…ии» в «вентиляции», «автоматизации»
_WORD_EDGE = r"(?<![а-яёА-ЯЁa-zA-Z0-9])"
_WORD_EDGE_END = r"(?![а-яёА-ЯЁa-zA-Z0-9])"
_FORBIDDEN_REPLY_RE = re.compile(
    rf"cursor|{_WORD_EDGE}ии{_WORD_EDGE_END}|нейросет|chatgpt|gemini|\bai\b|"
    rf"{_WORD_EDGE}агент{_WORD_EDGE_END}|промпт",
    re.IGNORECASE,
)
_FORBIDDEN_REPLY_GREETING_RE = re.compile(
    r"здравствуйте.*готов\s+реализовать|"
    r"готов\s+взяться|готов\s+реализовать|готов\s+заменить|"
    r"уважаемый\s+заказчик|"
    r"качественно\s+и\s+в\s+срок|имею\s+большой\s+опыт",
    re.IGNORECASE,
)
_REPLY_DRAFT_BAD_START_RE = re.compile(r"^готов\s", re.IGNORECASE)
_REPLY_DRAFT_REQUIRED_GREETING_RE = re.compile(r"^здравствуйте", re.IGNORECASE)
_REPLY_DRAFT_FORBIDDEN_OPENER_RE = re.compile(r"^заинтересовал", re.IGNORECASE)
_REPLY_DRAFT_TAKE_WORK_RE = re.compile(
    r"беру\s+(?:задачу\s+)?в\s+работу|беру\s+задачу",
    re.IGNORECASE,
)
_REPLY_DRAFT_CLICHE_RE = re.compile(
    r"готов\s+взять|готов\s+выполнить|полностью\s+погружусь|"
    r"могу\s+адаптировать|готов\s+адаптировать|"
    r"имею\s+опыт|большой\s+опыт|качественно\s+и\s+в\s+срок|"
    r"беру\s+(?:задачу\s+)?в\s+работу",
    re.IGNORECASE,
)
_REPLY_DRAFT_VAGUE_RE = re.compile(
    r"предлагаю\s+создать\s+несколько(?!\s+\w+\s+концепц)|"
    r"обсудить\s+детали(?!\s*\?)|глубокий\s+аудит\s+без|"
    r"ваш\s+креатив\s+за\s+основу|определить\s+приоритет",
    re.IGNORECASE,
)
_MAX_SHARED_SNIPPET_CHARS = 2_400

_DEFAULT_TIMEOUT_SEC = 60.0
_SHARED_DRAFT_BACKOFF_SEC = (1, 2, 4, 8)
_LITE_TIMEOUT_SEC = 45.0
_MAX_DESCRIPTION_CHARS = 7_000
_MAX_LITE_SNIPPET_CHARS = 600
_MAX_PROFILE_EXCERPT_CHARS = 3_200

_cycle_ai_l1 = 0
_cycle_ai_l2 = 0


def reset_cycle_ai_counters() -> None:
    global _cycle_ai_l1, _cycle_ai_l2
    _cycle_ai_l1 = 0
    _cycle_ai_l2 = 0


def note_ai_l1_call() -> None:
    global _cycle_ai_l1
    _cycle_ai_l1 += 1


def note_ai_l2_call() -> None:
    global _cycle_ai_l2
    _cycle_ai_l2 += 1


def cycle_ai_counts() -> tuple[int, int]:
    return _cycle_ai_l1, _cycle_ai_l2


_draft_events: deque[tuple[float, bool]] = deque()
_ai_last_error: str = ""
_DRAFT_STATS_WINDOW_SEC = 86400


def _prune_draft_events(now: float | None = None) -> None:
    now = now if now is not None else time.time()
    cutoff = now - _DRAFT_STATS_WINDOW_SEC
    while _draft_events and _draft_events[0][0] < cutoff:
        _draft_events.popleft()


def note_draft_request(ok: bool) -> None:
    """O48: on-demand draft ok/fail (rolling 24h)."""
    now = time.time()
    _draft_events.append((now, ok))
    _prune_draft_events(now)


def note_ai_error(msg: str) -> None:
    """O67: последняя ошибка ИИ для /health."""
    global _ai_last_error
    s = (msg or "").strip().replace("\n", " ")
    if s:
        _ai_last_error = s[:200]


def ai_last_error() -> str | None:
    s = (_ai_last_error or "").strip()
    return s or None


def draft_stats_24h() -> dict[str, int]:
    _prune_draft_events()
    ok = sum(1 for _, success in _draft_events if success)
    fail = sum(1 for _, success in _draft_events if not success)
    return {"draft_ok": ok, "draft_fail": fail}


def draft_fail_per_hour() -> int:
    """O67: fail count за последний час."""
    _prune_draft_events()
    now = time.time()
    hour_ago = now - 3600.0
    return sum(1 for ts, ok in _draft_events if not ok and ts >= hour_ago)

# docs/AI.md v6.1
_SYSTEM_PROMPT_HEAD = """Ты — жёсткий ИИ-архитектор фриланс-заказов. Прагматичный техаудитор для Никиты (29). Тон прямой, сухой, на «ты», без соплей.

Стек: Python (FastAPI, Telethon, aiogram 3), Neon/Supabase, WordPress (каркас + REST).
Метод: Vibe Coding — модули до ~250 строк, простые API-мосты, сейвпоинты Git и .md в docs.

Исполнитель:
— В коде начинающий; простыни не пишет и не дебажит сам.
— Главный инструмент: Cursor Agent (Composer 2.5 / Auto) + Sandbox.
— Сложные API (GetCourse, AmoCRM, Bitrix24, OAuth): Gemini Deep Research → выжимка до 150 строк → @file в Cursor.
— Telethon — мониторинг чатов; новые боты — aiogram 3 (не путать в approach).

Экономика: платные API, прокси, сервера, аккаунты-расходники, WP-плагины и подписки платит ЗАКАЗЧИК. Без аванса/компенсации расходников исполнителя — МИМО.

МИМО (verdict «МИМО»):
— Figma, вёрстка, CSS-полировка, чистый фронт (React, Vue), 1С, Bitrix/Битрикс (ядро), mobile с нуля, Cloudflare-bypass парсинг.
— Без ТЗ, дипломы, накрутки, спам без бюджета на расходники, биржа < 3 500 ₽.

БРАТЬ:
— Парсеры сайтов/TG, TG-бот с нуля (aiogram 3), автоматизация, скрипт 1–3 вечера.
— ИИ API (OpenAI/DeepSeek), правки чужого бэкенда 1–2 файла (JS, PHP).

СОМНИТЕЛЬНО: большие платформы/CRM — только если распил на модули (парсер → Neon → WP REST / бот) и запас по срокам; в approach — план распила.
Cursor: >5–7 связанных файлов в голове Agent → Сомнительно/МИМО; линейный пайплайн (получил→обработал→Neon→выдача) → Брать. Ориентир ~8–12 файлов, ~3000 строк.

Порядок (внутри, не выводи списком):
1. Суть задачи простым языком.
2. Фильтр → verdict.
3. Архитектура, Deep Research?, кто платит инфраструктуру.
4. money на 2026: биржа | рынок | старт отклика.

При сомнении между Брать и МИМО — «Сомнительно», не «МИМО».

Поля JSON (один объект, без markdown):
verdict — «Брать» | «Сомнительно» | «МИМО»
work_summary — 2–4 предложения для не-программиста
difficulty — 1 фраза: «Легко для Cursor Agent в 2 сессии» ИЛИ «Средне: Gemini Deep Research + Cursor Agent»
approach — ровно 2 предложения: шаги + Cursor/Neon/WordPress/бот без жаргона
time_for_client — срок заказчику с запасом
money — «На бирже: … | Рынок: … | Старт отклика: …»
reply_draft — «Брать»: 3–5 предл. · 1-е — суть/интерес · 2-е — как сделаешь (шаги из approach, без дубля полей UI) · «Сомнительно»: 2–4 предл., «Сделаю…»/«Возьму…» · «МИМО»: "" · >6 предл. — warn, не fail · **без срока/цены/«от X ₽» в тексте** — time_for_client и money только в своих полях JSON
risks — лимиты Cursor, расходники не оплатит заказчик, бан Telethon, scope creep
lead_tags — max 6 canonical_tag из SKILLS_TOOLS_CATALOG v0.3; при МИМО — []

reply_draft ЗАПРЕЩЕНО: Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт.

Профиль (docs/ops/PROFILE.md):
"""


class AiAnalyzeError(RuntimeError):
    """Ошибка вызова API или разбора ответа ИИ."""


@dataclass(frozen=True)
class AiLiteAnalysis:
    """L1 ingest: короткий разбор для /lenta/ (без reply_draft и L2-полей)."""

    feed_visible: bool
    task_summary: str
    lead_tags: tuple[str, ...] = ()
    pending_tags: tuple[str, ...] = ()
    ai_reasons: tuple[str, ...] = ()
    primary_category: str = ""

    @property
    def verdict(self) -> str:
        """Backward compat для L2/premium (Neon хранит OK/МИМО отдельно)."""
        return "МИМО" if not self.feed_visible else "Брать"

    def is_skip_verdict(self) -> bool:
        return not self.feed_visible

    def is_take_verdict(self) -> bool:
        return self.feed_visible


@dataclass(frozen=True)
class AiAnalysis:
    verdict: str
    work_summary: str
    difficulty: str
    approach: str
    time_for_client: str
    money: str
    reply_draft: str
    risks: str
    lead_tags: tuple[str, ...] = ()
    tools_required: tuple[str, ...] = ()

    def is_skip_verdict(self) -> bool:
        return self.verdict.strip().casefold() in _SKIP_VERDICTS

    def is_take_verdict(self) -> bool:
        return self.verdict.strip().casefold() in ("брать", "брат")


def load_profile_text(path: Path | None = None) -> str:
    p = path or _PROFILE_PATH
    return p.read_text(encoding="utf-8")


def build_cabinet_profile_excerpt(user_tags: dict[str, float]) -> str:
    """O23: навыки + ниша для on-demand L2 на /lenta/."""
    tags = ", ".join(sorted(user_tags.keys())) if user_tags else "не указаны"
    return (
        f"Навыки пользователя: {tags}.\n"
        "Подставь нишу (разработка / дизайн / маркетинг / тексты) по навыкам и заказу.\n"
        "Пиши от первого лица. "
        "Без упоминания ИИ, Cursor, ChatGPT, Gemini, нейросеть, агент, промпт."
    )


def build_profile_excerpt(path: Path | None = None) -> str:
    text = load_profile_text(path)
    start = 0
    for marker in ("## Жёсткий фильтр", "## Кто ты", "## Как ИИ должен"):
        idx = text.find(marker)
        if idx >= 0:
            start = idx
            break
    head = (
        "Аудитор: Никита, 29; Cursor Agent + Sandbox; "
        "стек FastAPI/Telethon, Neon, WordPress.\n\n"
    )
    excerpt = head + text[start:].strip()
    if len(excerpt) > _MAX_PROFILE_EXCERPT_CHARS:
        excerpt = excerpt[: _MAX_PROFILE_EXCERPT_CHARS - 1] + "…"
    return excerpt


def _build_system_prompt(profile_excerpt: str) -> str:
    return _SYSTEM_PROMPT_HEAD + profile_excerpt


def _truncate_description(description: str) -> tuple[str, bool]:
    s = (description or "").strip()
    if len(s) <= _MAX_DESCRIPTION_CHARS:
        return s, False
    return s[: _MAX_DESCRIPTION_CHARS - 1] + "…", True


def _build_premium_split_system(profile_excerpt: str) -> str:
    return _PREMIUM_SPLIT_SYSTEM + "\n\nПрофиль (docs/ops/PROFILE.md):\n" + profile_excerpt


def _build_premium_user_with_lite(
    *,
    title: str,
    budget_text: str,
    url: str,
    description: str,
    truncated: bool,
    lite: AiLiteAnalysis,
) -> str:
    trunc_note = (
        "\n\n[Описание обрезано — оценивай по видимой части; в risks укажи если ТЗ неполное.]"
        if truncated
        else ""
    )
    tags = ", ".join(lite.lead_tags) if lite.lead_tags else "—"
    reasons = ""
    if lite.ai_reasons:
        reasons = "\nПричины L1: " + "; ".join(lite.ai_reasons[:3])
    fields = ", ".join(_PREMIUM_SPLIT_FIELDS)
    return (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет на бирже (поле «На бирже» в money — как здесь): "
        f"{budget_text.strip()}\n"
        f"Ссылка: {url.strip()}\n\n"
        f"Уже от L1 (не пересказывай task_summary):\n"
        f"verdict: {lite.verdict}\n"
        f"task_summary: {lite.task_summary}\n"
        f"lead_tags: {tags}{reasons}\n\n"
        f"Полное описание заказа:\n---\n{description}\n---{trunc_note}\n\n"
        f"Верни только JSON с полями: {fields}."
    )


def _build_user_message(
    *,
    title: str,
    budget_text: str,
    url: str,
    description: str,
    truncated: bool,
) -> str:
    trunc_note = (
        "\n\n[Описание обрезано — оценивай по видимой части; в risks укажи если ТЗ неполное.]"
        if truncated
        else ""
    )
    fields = ", ".join(_AI_FIELDS)
    return (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет на бирже (поле «На бирже» в money — как здесь): "
        f"{budget_text.strip()}\n"
        f"Ссылка: {url.strip()}\n\n"
        f"Описание заказа:\n---\n{description}\n---{trunc_note}\n\n"
        f"Верни только JSON с полями: {fields}."
    )


def _normalize_difficulty(difficulty: str, approach: str) -> str:
    d = difficulty.strip()
    low = d.casefold()
    if "cursor" in low or "gemini deep research" in low:
        return d or "См. блок «Как сделаем»"
    combined = f"{approach} {d}".casefold()
    if "cursor" in combined or "gemini" in combined:
        return d or "См. блок «Как сделаем»"
    if d:
        return f"Для Cursor Agent: {d}"
    return "Для Cursor Agent: см. блок «Как сделаем»"


def _validate_money(money: str, budget_text: str) -> str:
    m = money.strip()
    low = m.casefold()
    if "на бирже" not in low:
        on_site = (budget_text or "").strip()
        m = f"На бирже: {on_site} | {m}"
        low = m.casefold()
    if "рынок" not in low:
        raise AiAnalyzeError("money: нет части «Рынок»")
    if "старт отклика" not in low:
        raise AiAnalyzeError("money: нет части «Старт отклика»")
    return m


def _count_sentences(text: str) -> int:
    t = text.strip()
    if not t:
        return 0
    parts = re.split(r"(?<=[.!?…])\s+|[\n\r]+", t)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        return len(parts)
    chunks = re.split(r"[.!?…]+", t)
    return len([c for c in chunks if c.strip()]) or 1


def _validate_reply_draft_base(text: str, *, forbid_bureaucratic_greeting: bool) -> str:
    draft = text.strip()
    if _FORBIDDEN_REPLY_RE.search(draft):
        raise AiAnalyzeError("reply_draft: запрещённые слова (ИИ/Cursor/…)")
    if forbid_bureaucratic_greeting and _REPLY_DRAFT_BAD_START_RE.search(draft):
        raise AiAnalyzeError("reply_draft: запрещённое начало «Готов…»")
    if forbid_bureaucratic_greeting and _FORBIDDEN_REPLY_GREETING_RE.search(draft):
        raise AiAnalyzeError("reply_draft: канцелярит «Здравствуйте. Готов реализовать»")
    return draft


def _reply_draft_target_range(verdict: str) -> tuple[int, int] | None:
    v = verdict.strip().casefold()
    if v in ("брать", "брат"):
        return (5, 6)
    if v == "сомнительно":
        return (4, 6)
    return None


def reply_draft_cliche_warn(reply_draft: str) -> str | None:
    """O72c: мягкий сигнал для аудита prod; не блокирует ingest."""
    draft = (reply_draft or "").strip()
    if not draft:
        return None
    if _REPLY_DRAFT_CLICHE_RE.search(draft):
        return "warn:reply_draft_cliche"
    return None


def reply_draft_sentence_warn(verdict: str, reply_draft: str) -> str | None:
    """Опциональный warn для лога; не блокирует отправку."""
    draft = (reply_draft or "").strip()
    if not draft:
        return None
    n = _count_sentences(draft)
    if n > 6:
        return f"warn:reply_draft_sentences={n} verdict={verdict}"
    rng = _reply_draft_target_range(verdict)
    if rng is None:
        return None
    lo, hi = rng
    if lo <= n <= hi:
        return None
    return f"warn:reply_draft_sentences={n} verdict={verdict}"


def _validate_reply_draft_opener(draft: str) -> None:
    if not _REPLY_DRAFT_REQUIRED_GREETING_RE.match(draft):
        raise AiAnalyzeError("reply_draft: обязательное начало «Здравствуйте»")
    if _REPLY_DRAFT_FORBIDDEN_OPENER_RE.match(draft):
        raise AiAnalyzeError("reply_draft: запрещённое начало «Заинтересовал…»")
    if _REPLY_DRAFT_TAKE_WORK_RE.search(draft):
        raise AiAnalyzeError("reply_draft: канцелярит «беру в работу»")


def _validate_reply_draft_take(text: str) -> str:
    draft = _validate_reply_draft_base(text, forbid_bureaucratic_greeting=True)
    if not draft:
        raise AiAnalyzeError("reply_draft пустой при вердикте Брать")
    _validate_reply_draft_opener(draft)
    return draft


def _validate_reply_draft_maybe(text: str) -> str:
    draft = _validate_reply_draft_base(text, forbid_bureaucratic_greeting=True)
    if not draft:
        raise AiAnalyzeError("reply_draft пустой при вердикте Сомнительно")
    _validate_reply_draft_opener(draft)
    return draft


def _normalize_tools_required(raw: Any) -> tuple[str, ...]:
    from tools_catalog import normalize_tools_required

    return normalize_tools_required(raw, limit=8)


def sanitize_tools_for_tz(
    tools: tuple[str, ...] | list[str],
    *,
    title: str = "",
    snippet: str = "",
    task_summary: str = "",
    limit: int = 8,
) -> tuple[str, ...]:
    """O72e-7: tools_required согласованы с текстом ТЗ (GAS/Rhino ≠ Python и т.д.)."""
    from tools_catalog import normalize_tools_required

    hay = f"{title or ''}\n{snippet or ''}\n{task_summary or ''}".casefold()
    py_ok = "python" in hay or "питон" in hay or "yii2" in hay or "django" in hay or "flask" in hay
    out = list(normalize_tools_required(tools, limit=limit))

    def drop(*names: str) -> None:
        nonlocal out
        drop_set = set(names)
        out = [t for t in out if t not in drop_set]

    def ensure(*names: str) -> None:
        nonlocal out
        seen = set(out)
        for name in names:
            mapped = normalize_tools_required([name], limit=1)
            if not mapped:
                continue
            key = mapped[0]
            if key not in seen and len(out) < limit:
                seen.add(key)
                out.append(key)

    gas_rhino = any(
        m in hay
        for m in ("rhino", "рино", "google apps script", "apps script", "google-таблиц", "google таблиц")
    )
    if gas_rhino:
        if not py_ok:
            drop("python", "fastapi", "django", "flask", "api_integration")
        ensure("javascript", "google_apps_script", "rhino")
        if "таблиц" in hay:
            ensure("google_sheets_api")

    wp_stack = any(
        m in hay
        for m in ("wordpress", "elementor", "wp rocket", "woocommerce", "tutor lms")
    )
    wp_perf = wp_stack and any(
        m in hay for m in ("скорост", "оптимизац", "pagespeed", "lcp", "cls", "waterfall")
    )
    if wp_perf or (wp_stack and "elementor" in hay and "скорост" in hay):
        if not py_ok:
            drop("python")
        ensure("wordpress_dev", "php", "elementor")

    email_mkt = any(
        m in hay
        for m in ("e-mail", "email", "рассылк", "dkim", "spf", "dmarc", "во входящие", "коммерческ")
    )
    if email_mkt:
        drop("python", "wordpress_dev", "crm", "api_integration")
        ensure("email_marketing", "consulting")

    landing_pay = any(m in hay for m in ("kaspi", "лендинг", "landing")) and any(
        m in hay for m in ("оплат", "pay", "автодостав", "хостинг", "email клиента")
    )
    if landing_pay:
        if not py_ok:
            drop("python")
        ensure("php")

    branding = any(m in hay for m in ("фирменный шрифт", "fontlab", "логотип", "шрифт", "брендинг"))
    if branding and not any(m in hay for m in ("kaspi", "wordpress", "api", "интеграц")):
        ensure("illustrator", "fontlab")

    return normalize_tools_required(out, limit=limit)


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = _JSON_BLOCK.search(raw)
        if not m:
            raise AiAnalyzeError("Ответ ИИ не содержит JSON.") from None
        data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise AiAnalyzeError("Ответ ИИ: ожидался JSON-объект.")
    return data


def _parse_analysis(data: dict[str, Any], *, budget_text: str) -> AiAnalysis:
    verdict_raw = str(data.get("verdict", "")).strip()
    if not verdict_raw:
        raise AiAnalyzeError("В JSON ИИ нет поля verdict")

    v_key_preview = verdict_raw.casefold()
    skip_like = v_key_preview in ("мимо", "пропустить")
    required = ["work_summary", "difficulty", "risks"]
    if not skip_like:
        required.extend(["approach", "time_for_client", "money"])
    missing = [k for k in required if not str(data.get(k, "")).strip()]
    if missing:
        raise AiAnalyzeError(f"В JSON ИИ нет полей: {', '.join(missing)}")
    v_key = verdict_raw.casefold()
    if v_key not in _VALID_VERDICTS:
        raise AiAnalyzeError(f"Недопустимый verdict: {verdict_raw!r}")

    if v_key in ("мимо", "пропустить"):
        verdict = "МИМО"
    elif v_key == "сомнительно":
        verdict = "Сомнительно"
    else:
        verdict = "Брать"

    approach = str(data.get("approach", "")).strip() or "—"
    difficulty = _normalize_difficulty(
        str(data.get("difficulty", "")).strip() or "МИМО — не под профиль Cursor",
        approach,
    )
    money_raw = str(data.get("money", "")).strip()
    if money_raw and ("на бирже" in money_raw.casefold() or "рынок" in money_raw.casefold()):
        money = _validate_money(money_raw, budget_text)
    elif skip_like:
        on_site = (budget_text or "").strip()
        money = f"На бирже: {on_site} | Рынок: — | Старт отклика: —"
    else:
        money = _validate_money(money_raw or f"На бирже: {budget_text}", budget_text)
    time_for_client = str(data.get("time_for_client", "")).strip() or "—"
    reply_raw = str(data.get("reply_draft", "")).strip()
    if reply_raw in ("-", "—"):
        reply_raw = ""
    if verdict == "Брать":
        reply_draft = _validate_reply_draft_take(reply_raw)
    elif verdict == "Сомнительно":
        reply_draft = _validate_reply_draft_maybe(reply_raw)
    else:
        reply_draft = ""
    if reply_draft:
        reply_draft = strip_reply_draft_price_deadline(reply_draft)

    raw_tags = data.get("lead_tags", [])
    if isinstance(raw_tags, list):
        lead_tags = tuple(normalize_tags([str(t) for t in raw_tags]))
    else:
        lead_tags = ()
    if not skip_like and lead_tags and len(lead_tags) > _L1_MAX_TAGS:
        lead_tags = lead_tags[:_L1_MAX_TAGS]

    raw_tools = data.get("tools_required", data.get("tools", []))
    tools = _normalize_tools_required(raw_tools)

    return AiAnalysis(
        verdict=verdict,
        work_summary=str(data["work_summary"]).strip(),
        difficulty=difficulty,
        approach=approach,
        time_for_client=time_for_client,
        money=money,
        reply_draft=reply_draft,
        risks=str(data["risks"]).strip(),
        lead_tags=lead_tags,
        tools_required=tools,
    )


def _parse_premium_analysis(
    data: dict[str, Any],
    *,
    budget_text: str,
    lite: AiLiteAnalysis | None = None,
) -> AiAnalysis:
    payload = dict(data)
    if lite is not None and not str(payload.get("verdict", "")).strip():
        payload["verdict"] = lite.verdict
    analysis = _parse_analysis(payload, budget_text=budget_text)
    if lite is not None and lite.is_take_verdict():
        n_tools = len(analysis.tools_required)
        if n_tools < 2:
            raise AiAnalyzeError("L2: tools_required — минимум 2 пункта")
        if n_tools > 8:
            raise AiAnalyzeError("L2: tools_required — максимум 8 пунктов")
        if not (analysis.reply_draft or "").strip():
            raise AiAnalyzeError("L2: пустой reply_draft")
        return AiAnalysis(
            verdict="Брать",
            work_summary=analysis.work_summary,
            difficulty=analysis.difficulty,
            approach=analysis.approach,
            time_for_client=analysis.time_for_client,
            money=analysis.money,
            reply_draft=analysis.reply_draft,
            risks=analysis.risks,
            lead_tags=analysis.lead_tags or lite.lead_tags,
            tools_required=analysis.tools_required,
        )
    return analysis


def _ai_error_kind(exc: BaseException) -> str:
    msg = str(exc).casefold()
    if isinstance(exc, requests.RequestException):
        return "http"
    if "http" in msg or "openrouter" in msg and "формат" not in msg:
        return "http"
    return "parse"


def _log_ai_failure(
    errors: list[str] | None,
    log_prefix: str,
    exc: BaseException,
) -> None:
    if not errors or not log_prefix:
        return
    kind = _ai_error_kind(exc)
    detail = f"{type(exc).__name__}: {exc}".replace("\n", " ")[:160]
    errors.append(f"{log_prefix}ai:{kind}:{detail}")


# O72e-3/5: judge anchor fixtures — ≥2 группы терминов в draft (unit + bench)
_O72E3_WORST_TERM_GROUPS: dict[int, tuple[tuple[str, ...], ...]] = {
    8704: (
        ("illustrator", "иллюстратор", "photoshop", "фотошоп", "fontlab"),
        ("глиф", "векторизац", "концепц", "исследован", "брендинг"),
    ),
    8776: (
        ("elementor", "woocommerce", "tutor", "wordpress"),
        ("waterfall", "lcp", "cls", "pagespeed", "критическ"),
        ("трекер", "сторонн", "third", "отложен", "defer", "wp rocket"),
    ),
    8925: (
        ("rhino", "рино"),
        ("javascript", "google apps script", "apps script"),
        ("google таблиц", "таблиц", "es6", "миграц", "синтаксис"),
    ),
    8726: (
        ("spf", "dkim", "dmarc", "доставляем"),
        ("excel", "csv", "баз"),
        ("стоп-слов", "верстк", "reply-to", "отчет", "отчёт"),
    ),
    8836: (
        ("kaspi", "касpi"),
        ("лендинг", "landing", "хостинг"),
        ("автодостав", "email клиента", "оплат", "pay"),
    ),
}

O72E5_ANCHOR_IDS: frozenset[int] = frozenset(_O72E3_WORST_TERM_GROUPS)


def o72e3_worst_draft_term_groups(lead_id: int) -> tuple[tuple[str, ...], ...] | None:
    return _O72E3_WORST_TERM_GROUPS.get(int(lead_id))


def count_o72e3_niche_term_groups(draft: str, groups: tuple[tuple[str, ...], ...]) -> int:
    low = (draft or "").casefold()
    if not low:
        return 0
    return sum(1 for group in groups if any(term.casefold() in low for term in group))


def draft_passes_o72e3_worst_terms(draft: str, lead_id: int, *, min_groups: int = 2) -> bool:
    groups = o72e3_worst_draft_term_groups(lead_id)
    if not groups:
        return True
    return count_o72e3_niche_term_groups(draft, groups) >= min_groups


def _shared_draft_too_vague(draft: str) -> str | None:
    if _REPLY_DRAFT_VAGUE_RE.search(draft):
        return "vague:generic_pitch"
    if "обсуд" in draft.casefold() and "?" not in draft:
        return "vague:discuss_without_question"
    return None


def sanitize_l1_dev_design_marketing_tags(
    lead_tags: tuple[str, ...],
    *,
    title: str = "",
    snippet: str = "",
) -> tuple[str, ...]:
    """O72e-3: post-validate L1 tags vs dev/design/marketing в тексте ТЗ."""
    if not lead_tags:
        return lead_tags
    hay = f"{title or ''}\n{snippet or ''}".casefold()
    tags = list(lead_tags)

    perf_wp = any(
        m in hay
        for m in (
            "elementor",
            "woocommerce",
            "pagespeed",
            "оптимизац",
            "скорост",
            "tutor lms",
            "wp rocket",
            "waterfall",
            "lcp",
            "cls",
        )
    )
    if perf_wp:
        if "web_design" in tags:
            tags = [t for t in tags if t != "web_design"]
        if "wordpress_dev" not in tags and len(tags) < _L1_MAX_TAGS:
            tags.append("wordpress_dev")

    gas_rhino = any(
        m in hay
        for m in ("rhino", "рино", "google apps script", "apps script", "google-таблиц", "google таблиц")
    )
    py_ok = "python" in hay or "питон" in hay or "yii2" in hay
    if gas_rhino and not py_ok:
        tags = [t for t in tags if t not in ("python", "api_integration")]
        if "javascript" not in tags and len(tags) < _L1_MAX_TAGS:
            tags.append("javascript")

    dev_code_ctx = any(
        m in hay
        for m in (
            "скрипт",
            "script",
            "программ",
            "код",
            "yii2",
            "python",
            "php",
            "wordpress",
            "webhook",
            "rest api",
            "kaspi",
            "хостинг",
            "автодостав",
            "google apps script",
            "apps script",
            "postgresql",
            "mysql",
        )
    )
    integration_dev = dev_code_ctx and any(
        m in hay
        for m in (
            "api",
            "интеграц",
            "yii2",
            "kaspi",
            "лендинг",
            "landing",
            "хостинг",
            "копию сайта",
            "платформ",
            "автодостав",
        )
    )
    if integration_dev:
        for drop_tag in ("web_design", "landing_page_design"):
            if drop_tag in tags:
                tags = [t for t in tags if t != drop_tag]
        if "api_integration" not in tags and len(tags) < _L1_MAX_TAGS:
            tags.append("api_integration")
        if any(m in hay for m in ("kaspi", "хостинг", "автодостав")) and "php" not in tags:
            if len(tags) < _L1_MAX_TAGS:
                tags.append("php")

    email_mkt = any(m in hay for m in ("e-mail", "email", "рассылк", "во входящие", "коммерческ", "dkim", "spf", "dmarc"))
    blogger_mkt = any(m in hay for m in ("блогер", "размещен", "smm", "таргет", "авито"))
    if email_mkt or blogger_mkt:
        drop_dev = {"api_integration", "python", "wordpress_dev"}
        tags = [t for t in tags if t not in drop_dev]
        if email_mkt:
            if "email_marketing" not in tags and len(tags) < _L1_MAX_TAGS:
                tags.append("email_marketing")
            if "email_copywriting" not in tags and len(tags) < _L1_MAX_TAGS:
                tags.append("email_copywriting")
        if blogger_mkt:
            if "smm" not in tags and len(tags) < _L1_MAX_TAGS:
                tags.append("smm")

    return tuple(tags[:_L1_MAX_TAGS])


def sanitize_l1_category(
    category: str,
    *,
    title: str = "",
    snippet: str = "",
) -> str:
    """O72e-5: post-validate stored category vs dev/design/marketing в тексте ТЗ."""
    cat = (category or "").strip().casefold() or "dev"
    hay = f"{title or ''}\n{snippet or ''}".casefold()

    email_mkt = any(
        m in hay
        for m in (
            "e-mail",
            "email",
            "рассылк",
            "во входящие",
            "коммерческ",
            "спам-фильтр",
            "dkim",
            "spf",
            "excel",
            "csv",
        )
    )
    landing_dev = any(m in hay for m in ("kaspi", "лендинг", "landing")) and any(
        m in hay for m in ("оплат", "pay", "интеграц", "хостинг", "автодостав")
    )
    perf_wp = any(
        m in hay
        for m in (
            "elementor",
            "woocommerce",
            "pagespeed",
            "скорост",
            "оптимизац",
            "tutor lms",
            "wp rocket",
            "waterfall",
            "lcp",
            "cls",
            "сторонн",
            "трекер",
        )
    )
    figma_only = "figma" in hay and any(
        m in hay for m in ("разработ", "платформ", "yii", "python", "backend", "api")
    )

    copy_site = any(m in hay for m in ("копию сайта", "копия сайта", "аналитики для маркетплейс"))
    wp_setup = "wordpress" in hay and any(
        m in hay for m in ("установ", "настро", "тем", "календар", "форм")
    )
    blogger_mkt = any(m in hay for m in ("блогер", "размещен", "smm", "таргет", "авито"))
    crm_mkt = any(
        m in hay
        for m in ("crm", "бонус", "такси", "уведомлен", "статус заказ", "статусы заказ")
    )

    server_admin = any(
        m in hay
        for m in ("3x-ui", "3x ui", "vps", "ssh", "сервер", "server admin", "установка по")
    )
    wb_infographic = any(m in hay for m in ("инфографик", "wildberries", " wb", "маркетплейс"))

    tilda_seo = any(m in hay for m in ("тильда", "tilda")) and any(
        m in hay
        for m in (
            "индексац",
            "search console",
            "gsc",
            "robots",
            "sitemap",
            "вебмастер",
            "google search",
        )
    )
    traffic_mkt = any(
        m in hay
        for m in (
            "привлечен",
            "трафик",
            "реферал",
            "партнер",
            "партнёр",
            "sora",
            "kling",
            "привлечь пользовател",
        )
    ) and any(m in hay for m in ("бот", "telegram", "тг", "чат-бот"))
    sprites_design = any(m in hay for m in ("спрайт", "sprite")) or (
        any(m in hay for m in ("иллюстрац", "illustration"))
        and not any(m in hay for m in ("разработ", "код", "api", "wordpress", "скрипт"))
    )
    transcribe_text = any(m in hay for m in ("транскриб", "расшифров"))
    ux_audit_design = any(m in hay for m in ("ux", "ui/ux", "ui audit", "ux audit", "аудит экран")) and any(
        m in hay for m in ("профил", "экран", "приложен", "figma", "макет")
    )

    if server_admin or landing_dev or perf_wp or figma_only or copy_site or wp_setup or tilda_seo:
        return "dev"
    if email_mkt or blogger_mkt or crm_mkt or traffic_mkt:
        return "marketing"
    if wb_infographic or sprites_design or ux_audit_design:
        return "design"
    if transcribe_text:
        return "text"
    if any(m in hay for m in ("шрифт", "логотип", "fontlab", "брендинг", "illustrator")):
        if not any(m in hay for m in ("разработ", "wordpress", "api", "интеграц", "kaspi")):
            return "design"
    return cat if cat in ("dev", "design", "marketing", "text") else "dev"


def _normalize_primary_category(raw: str) -> str:
    c = (raw or "").strip().casefold()
    return c if c in CATEGORIES else ""


def _infer_primary_from_tags(lead_tags: tuple[str, ...]) -> str:
    if not lead_tags:
        return ""
    counts: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for tag in lead_tags:
        cat = category_for_canonical_tag(tag)
        if cat in counts:
            counts[cat] += 1
    best = max(counts.values())
    if best == 0:
        return ""
    winners = [c for c in CATEGORIES if counts[c] == best]
    if len(winners) == 1:
        return winners[0]
    for cat in ("dev", "design", "marketing", "text"):
        if cat in winners:
            return cat
    return "dev"


def validate_l1_tags_for_category(
    lead_tags: tuple[str, ...],
    primary_category: str,
) -> tuple[str, ...]:
    """O72e-9: каждый lead_tag из словаря выбранной primary_category."""
    cat = _normalize_primary_category(primary_category)
    if not cat or not lead_tags:
        return lead_tags
    out: list[str] = []
    for tag in lead_tags:
        if category_for_canonical_tag(tag) == cat:
            out.append(tag)
    return tuple(out[:_L1_MAX_TAGS])


def resolve_l1_primary_category(
    primary_category: str,
    lead_tags: tuple[str, ...],
    *,
    title: str = "",
    snippet: str = "",
) -> str:
    """Итоговая category для Neon: primary_category → sanitize по тексту ТЗ."""
    cat = _normalize_primary_category(primary_category)
    if not cat and lead_tags:
        cat = _infer_primary_from_tags(lead_tags)
    if not cat:
        cat = resolve_lead_category(None, title, snippet, lead_tags)
    return sanitize_l1_category(cat, title=title, snippet=snippet)


def _finalize_lite_analysis(
    result: AiLiteAnalysis,
    *,
    title: str,
    snippet: str,
) -> AiLiteAnalysis:
    """Post-validate: primary_category, теги по нише, sanitize."""
    primary = _normalize_primary_category(result.primary_category)
    if not primary:
        primary = _infer_primary_from_tags(result.lead_tags)
    tags = validate_l1_tags_for_category(result.lead_tags, primary)
    if not primary and tags:
        primary = _infer_primary_from_tags(tags)
    if not primary:
        primary = resolve_lead_category(None, title, snippet, tags)
    category = resolve_l1_primary_category(primary, tags, title=title, snippet=snippet)
    return AiLiteAnalysis(
        feed_visible=result.feed_visible,
        task_summary=result.task_summary,
        lead_tags=tags,
        pending_tags=result.pending_tags,
        ai_reasons=result.ai_reasons,
        primary_category=category,
    )


# O72e-9: сжатые few-shot по worst gate 063753Z (~кэшируемый head)
_LITE_FEWSHOT_BLOCK = """
Примеры (primary_category + lead_tags):
- «Установка 3X-UI на VPS Mac» → dev · server_administration
- «Инфографика пластиковых игрушек для WB» → design · infographic_design
- «Тильда: страницы не в индексе, GSC» → dev · technical_seo, tilda_dev
- «Привлечь трафик в TG-бот, реферальная программа» → marketing · chatbot_marketing
- «Спрайты для игры» → design · illustration
- «6 вкладок фильтров, БД, детальные страницы» → dev · javascript, api_integration
- «Транскрибация видео + перевод EN» → text · transcription, translation
- «Скрипт Google Sheets + SMTP рассылка» → dev · javascript, api_integration
- «UX-аудит экрана профиля в приложении» → design · ui_ux
- «Оформление группы ВК: обложка, виджеты, описание» → design · ui_ux, banner_design (не smm)
"""

# Канон: docs/team/architect/AI.md § L1/L2 «Тексты system»
_LITE_SYSTEM_HEAD = """Ты — фильтр фриланс-заказов для ленты RawLead (Digital: код, дизайн, маркетинг, тексты).

Верни один JSON без markdown:
primary_category — dev | design | marketing | text (главная ниша заказа; все lead_tags только из её словаря)
feed_visible — true | false (false = скрыть из ленты: спам, вакансии/подбор персонала, 3D-архвиз, крипта, инфобиз, нет ТЗ, чистый фронт без бэкенда, mobile с нуля, накрутки)
task_summary — 1–2 предложения: **что именно** нужно сделать (формат результата, платформа, ключевой стек из ТЗ); при feed_visible=true **всегда непустой**; минимум **2 конкретных факта** из описания (не «разработка по ТЗ», не копипаста заголовка); **сохраняй ключевые слова из заголовка** (спрайты, 3X-UI, WB…)
lead_tags — max 6 canonical_tag **только из словаря primary_category**; при feed_visible=false — []; **только из ТЗ**, не додумывай стек
ai_reasons — массив 2–3 коротких строк «почему показывать/скрыть»; каждая строка — **факт из ТЗ** (платформа/тип работ); **всегда 2–3 строки**, не пустой массив
**Бюджет в task_summary/ai_reasons — только если явно в поле «Бюджет» или тексте заказа; не выдумывай суммы.**

Ниши (lead_tags отражают тип работы, **не путай dev/design/marketing** — проверь перед JSON):
- **dev:** код, API, интеграции, WP-тема/плагин, оптимизация скорости (PageSpeed, Elementor, WooCommerce, WP Rocket, LCP), парсинг, Rhino/Google Apps Script, лендинг с Kaspi/хостингом
- **design:** логотип, фирменный шрифт, UI/UX-макет, брендинг, иллюстрация — **без** программирования как основной задачи
- **marketing:** email-рассылки, SMM, блогеры, таргет — **даже если** в ТЗ SPF/DKIM/DMARC (это не dev)
- **text:** копирайт, художественные тексты, сценарии

**Четыре частых ошибки (исправь в lead_tags — перепроверь перед JSON):**
1. email-рассылка + Excel/CSV база → marketing (email_marketing), **не** dev/python/crm
2. лендинг + Kaspi Pay / автодоставка → dev (api_integration, php), **не** design/web_design
3. WP speed / PageSpeed / Waterfall / Elementor / WP Rocket / LCP / сторонние трекеры → dev (wordpress_dev), **не** design
4. Google Apps Script / Rhino V8 / google-таблица → dev (**javascript** в lead_tags), **не python** — это JavaScript, не Python

**Самопроверка category (по смыслу ТЗ, до JSON):**
- Код/скрипты/API/WP speed/Elementor/Kaspi/хостинг/парсинг → **dev**
- Логотип/шрифт/UI-макет/брендинг **без** программирования → **design**
- Email-рассылки/SMM/блогеры/таргет — **даже с SPF/DKIM/DMARC** → **marketing**, не dev
- GAS/Rhino/google-таблица → **dev** + тег **javascript**, не python

Жёстко dev ≠ design (типовые якоря):
- Аудит скорости WP+Elementor+WooCommerce+Tutor LMS + Waterfall + отложенные трекеры → **wordpress_dev** (dev), не web_design
- Лендинг с Kaspi Pay / интеграциями / хостингом → dev (api_integration, wordpress_dev), не design
- Готовый Figma + разработка платформы на yii2/Python → dev
- Копирование сайта с API/дашбордами → dev (api_integration), не web_design
- Email-массовые КП «во входящие» / SPF+DKIM+DMARC → **marketing**, не dev
- Лендинг + Kaspi Pay / автодоставка на email / установка на хостинг → **dev** (api_integration, wordpress_dev), не design
- Оптимизация скорости WP+Elementor+WooCommerce+Tutor → **dev** (wordpress_dev), не design; теги woocommerce/tutor_lms если в ТЗ

Правила категоризации (теги из одной ниши, кроме cross_niche):
- Ниша обязательна: dev / design / marketing / text — при сомнении ближайшая, не пусто
- Telegram-бот: разработка → telegram_bot_dev (dev); воронка/рассылка в TG → chatbot_marketing (marketing)
- CMS (жёстко): Joomla, Bitrix/Битрикс, OpenCart, BaForms, MODX, Drupal — НЕ wordpress_dev
- wordpress_dev только при явном WordPress / WooCommerce / WP theme / WP plugin / wp hooks / Elementor-pro
- Joomla/Bitrix/OpenCart: правки модулей/форм/капчи → php (dev); не путать с WordPress
- WordPress: тема/плагин/код → wordpress_dev (dev); «сайт на WP» без кода → web_design (design)
- 3D: персонаж/explainer/лого 3D → threed_modeling (design); архвиз/интерьер/ландшафт → МИМО, не тегировать
- ИИ: openai/gpt/claude/langchain/llm → только llm_integration (не api_integration одновременно); max 1 ИИ-тег
- Парсинг: сайты/данные → web_scraping (dev); юзербот/парсер Telegram → telethon (dev)
- Таргет vs SMM: «таргет/директ/ads» → target_ads или yandex_direct/google_ads; «вести соцсети» → smm
- Копирайт vs SEO: без SEO → copywriting; явно SEO-текст → seo_copywriting
- Инструменты (Figma, Photoshop, After Effects…) → НЕ в lead_tags (это L2 tools_required)

Границы: text ≠ 3D/Blender/видеомонтаж (design); dev ≠ нейминг/описания товаров (text/marketing).
Только canonical_tag из пула; синонимы → canonical; не из пула — не добавляй (не ai, не automation, не #ai).

feed_visible=false: Figma/чистый фронт, 1С, mobile с нуля, накрутки, крипта, инфобиз, дипломы, нет бюджета, архвиз 3D.
feed_visible=false: список **вакансий** / подбор персонала без ТЗ — summary «вакансии, не фриланс-заказ», lead_tags [].
Сбор баз компаний/рекламодателей, лидов, email — ниша **marketing**, не dev.
CRM/бонусы/уведомления/статусы заказов (такси, доставка) без явного «написать CRM с нуля» → **marketing**, не dev.
Работа с блогерами, SMM, размещение у блогеров → **marketing**, не dev.
Установка/настройка WP-темы, календарь событий, формы → **dev** (wordpress_dev), не design.
**Figma готов + код платформы (yii2/Python, LMS, тесты)** → dev, не design; теги без web_design как основной.
**Копия сайта / API маркетплейсов / дашборд аналитики** → dev (api_integration, php), не design.
**Интеграция каталога через API (Автопитер и т.п.)** → dev, не design.
**Иллюстрации, открытки, брендинг без программирования** → design.
feed_visible=true: парсеры, TG-боты, Python-автоматизация, правки бэкенда 1–2 файла; простой сайт/правки WP с ясным ТЗ.
Excel/Google Sheets/отчёт/финанализ/остатки/доработка отчёта: автоматизация/скрипт → python (dev); метрики/аналитика → web_analytics (marketing); структура/текст отчёта → technical_writing (text).

Не выводи reply_draft, approach, money, risks, tools_required."""

_LITE_SYSTEM = _LITE_SYSTEM_HEAD + _LITE_FEWSHOT_BLOCK + allowed_tags_prompt_block()

_PREMIUM_SPLIT_SYSTEM = """Ты — ИИ-архитектор фриланс-заказов (L2 premium) для Telegram-уведомления

Заказ уже отфильтрован — verdict «Брать» (блок L1). Не меняй verdict, не переспрашивай и не копируй task_summary; в work_summary не дублируй L1 — только развёрнутый смысл для исполнителя.

Дай: work_summary (2–4 предл.), tools_required (массив 2–5 инструментов lowercase **из ТЗ заказа**, не из стека RawLead; не дублируй lead_tags), difficulty, approach (ровно 2 предл.), time_for_client, money («На бирже: … | Рынок: … | Старт отклика: …»), risks, reply_draft, lead_tags (дополни теги из L1 до max 6 canonical v0.3, не переписывай список с нуля).

tools_required — **обобщённо по тексту заказа:** postgresql (не neon/supabase); telegram или telegram_bot (не telethon/aiogram); python/php как язык; figma, wordpress, mysql… **Запрещено** без явного упоминания в ТЗ: neon, supabase, telethon, aiogram, fastapi, cursor, openrouter, gemini.

JSON без markdown: work_summary, tools_required, difficulty, approach, time_for_client, money, reply_draft, risks, lead_tags.
Не выводи verdict, task_summary, ai_reasons.

reply_draft: как §1–§3 shared-agent — «Здравствуйте!» + глагол выполнения, стек **из ТЗ**, 2–3 нишевых термина, шаги «Сначала…», один вопрос; **без срока/цены**. ЗАПРЕЩЕНО: «Заинтересовал…», «Беру в работу», «Готов…», «большой опыт», FastAPI/Neon без ТЗ; Cursor/ИИ/промпт. >6 предл. — warn."""

# O72e-3 / O57 / O23 — Senior Freelance Acquisition Agent (shared + cabinet)
_SHARED_REPLY_CORE = """Ты — senior freelance acquisition agent. Сухое сопроводительное письмо к заказу на бирже.

§1 СТЕК ИЗ ТЗ (перед текстом письма):
- Среда только из Заголовка, task_summary и Описания заказа.
- **Запрещено** подставлять инструменты из tools_required / lead_tags / canonical_tag, если они противоречат тексту (Rhino V8 + Google Apps Script ≠ Python; WordPress+Elementor ≠ FastAPI/Neon/Telethon).
- Google Apps Script / Rhino V8 → пиши **JavaScript / Google Apps Script**, не Python; tools_required — **javascript + google_apps_script + rhino**, не python.
- Если в ТЗ или tools_required есть PHP, JavaScript, HTML/CSS — назови **≥2** из них в письме.
- В письме **обязательно ≥2 инструмента/технологии словами из ТЗ** (FontLab, DMARC, WP Rocket, LCP, Illustrator…).

§2 НИШЕВАЯ КОНКРЕТИКА (2–3 термина/проблемы из ТЗ, не шаблон «аудит»):
- WP/Elementor/WC/Tutor: PageSpeed **Waterfall**, LCP/CLS, WP Rocket, критический CSS; раздутый DOM Elementor; **отложенная загрузка сторонних трекеров** (аналитика, пиксели); Ajax/видео Tutor LMS.
- Брендинг/шрифт: Illustrator, Photoshop, **FontLab**; исследование → концепции → векторизация → глифы (не только «логотип»).
- Скрипты: миграция Google Apps Script → Rhino V8, ES6+, изменения API, разбор трёх сценариев с таблицей.
- Email-рассылки: SPF/DKIM/**DMARC**, стоп-слова, верстка письма, Reply-to, **импорт базы Excel/CSV**, отчёт (открытия/переходы) — **без цены/срока/тарифов 1000/2000/5000 в reply_draft**.
- Парсинг баз + рассылка: веб-скрапинг/API, Google Таблица, Mailchimp/SendGrid, UTM/пиксели, bounce — сначала экспертиза, вопрос в конце.
- LMS/платформа (yii2/Python): Django/Flask или yii2, видеохостинг, PostgreSQL/MySQL для курсов/тестов; **не** Telegram без ТЗ.
- Копия сайта/API: PHP, JavaScript, парсинг API маркетплейсов, схема БД, верстка дашборда.
- SEO-аудит: robots.txt, sitemap.xml, шаблоны title/description/H1-H3, Search Console/Вебмастер.
- MailWizz/SMTP: SSL, SPF/DKIM, bounce/FBL, наращивание объёма — **без цены в reply_draft**.
- Маркетинг/Авито: заголовки, фото туров, цены vs конкуренты, отзывы/сезонность — по нише из ТЗ.
- Лендинг+Kaspi Pay: PHP/верстка, интеграция оплаты, автодоставка файла на email, деплой на хостинг.
- Художественный/text: объём (напр. 1000 слов), тон, подход — покажи готовность, не только вопрос.

§3 СТРУКТУРА (**ровно 5 предложений**, **без срока, цены, «от X ₽», тарифов 1000/2000/5000**):
(0) **обязательно** «Здравствуйте!» в начале ·
(1) глагол выполнения (**Сделаю…** / **Выполню…** / **Настрою…** / **Адаптирую…** / **Разработаю…** / **Проведу…**) + **одна** конкретика из ТЗ ·
(2–3) шаги «Сначала…, затем…» — **≥2 инструмента из ТЗ в тексте** (FontLab, DMARC, WP Rocket, LCP…) ·
(4) **один** уточняющий вопрос по пробелу в ТЗ (не «готов приступить», не «обсудить детали» без «?»).

ЗАПРЕЩЕНО: «Заинтересовал…» / «Заинтересовала…»; «Беру в работу» / «беру задачу»; начало с «Готов…»; «Уважаемый заказчик», «Готов взяться», «Имею большой/огромный опыт», «качественно и в срок»;
«готов взять/выполнить», «полностью погружусь», «могу адаптировать», «несколько концепций» без этапов;
«предлагаю обсудить детали» без вопроса; Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт.

JSON без markdown: reply_draft."""

# O23 / L2-REPLY-SCENARIO — on-demand отклик на /lenta/
_CABINET_REPLY_SYSTEM = (
    _SHARED_REPLY_CORE
    + "\n\nКонтекст: profile_excerpt (ниша исполнителя) + task_summary + Описание заказа."
)

# O57: один универсальный отклик на lead — без profile_excerpt
_SHARED_REPLY_SYSTEM = (
    _SHARED_REPLY_CORE
    + "\n\nКонтекст: task_summary, Описание заказа; tools_required — справочно, не перебивай §1."
)

_PREMIUM_SPLIT_FIELDS = (
    "work_summary",
    "tools_required",
    "difficulty",
    "approach",
    "time_for_client",
    "money",
    "reply_draft",
    "risks",
    "lead_tags",
)


def _build_lite_user_message(
    *,
    title: str,
    budget_text: str,
    url: str,
    snippet: str,
) -> str:
    return (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет: {budget_text.strip()}\n"
        f"Ссылка: {url.strip()}\n\n"
        f"Краткое описание:\n---\n{snippet.strip()}\n---\n\n"
        "Сформулируй task_summary по фактам из описания (технологии, формат, объём).\n"
        "Если описание короткое — опирайся на заголовок, но не оставляй summary пустым или общим.\n"
        "Верни только JSON: primary_category, feed_visible, task_summary, lead_tags, ai_reasons."
    )


def _parse_feed_visible(data: dict[str, Any]) -> bool:
    if "feed_visible" in data:
        raw = data["feed_visible"]
        if isinstance(raw, bool):
            return raw
        text = str(raw).strip().casefold()
        if text in ("true", "1", "yes", "да"):
            return True
        if text in ("false", "0", "no", "нет"):
            return False
        raise AiAnalyzeError(f"L1: недопустимый feed_visible: {raw!r}")
    verdict_raw = str(data.get("verdict", "")).strip()
    if not verdict_raw:
        raise AiAnalyzeError("L1: нет feed_visible")
    v_key = verdict_raw.casefold()
    if v_key not in _VALID_VERDICTS:
        raise AiAnalyzeError(f"L1: недопустимый verdict (legacy): {verdict_raw!r}")
    return v_key not in ("мимо", "пропустить")


def _parse_lite_analysis(data: dict[str, Any]) -> AiLiteAnalysis:
    feed_visible = _parse_feed_visible(data)

    task_summary = str(data.get("task_summary", "")).strip()
    if not task_summary:
        task_summary = str(data.get("work_summary", "")).strip()
    if not task_summary and feed_visible:
        raise AiAnalyzeError("L1: пустой task_summary")

    raw_tags = data.get("lead_tags", [])
    if isinstance(raw_tags, list):
        known, pending = partition_lead_tags([str(t) for t in raw_tags])
        lead_tags = known
        pending_tags = pending
        if pending_tags:
            logger.warning("L1 smoke: pending_tags=%s", list(pending_tags)[:6])
        bad = [t for t in lead_tags if t not in CANONICAL_TAGS]
        if bad:
            logger.warning("L1 smoke: non-canonical lead_tags=%s", bad[:6])
    else:
        lead_tags = ()
        pending_tags = ()

    raw_reasons = data.get("ai_reasons", [])
    reasons: list[str] = []
    if isinstance(raw_reasons, list):
        for item in raw_reasons[:3]:
            s = str(item).strip()
            if s:
                reasons.append(s)
    elif isinstance(raw_reasons, str) and raw_reasons.strip():
        reasons.append(raw_reasons.strip())

    primary_category = _normalize_primary_category(str(data.get("primary_category", "")))
    if not primary_category:
        legacy = str(data.get("category", "")).strip()
        primary_category = _normalize_primary_category(legacy)

    return AiLiteAnalysis(
        feed_visible=feed_visible,
        task_summary=task_summary,
        lead_tags=lead_tags,
        pending_tags=pending_tags,
        ai_reasons=tuple(reasons),
        primary_category=primary_category,
    )


def _openrouter_chat(
    cfg: Config,
    *,
    model: str,
    system: str,
    user: str,
    timeout_sec: float,
    json_mode: bool,
) -> str:
    headers = {
        "Authorization": f"Bearer {cfg.ai_api_key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    resp = requests.post(
        _OPENROUTER_URL,
        headers=headers,
        json=body,
        timeout=timeout_sec,
        proxies=DIRECT_REQUESTS_PROXIES,
    )
    if resp.status_code != 200:
        raise AiAnalyzeError(f"OpenRouter HTTP {resp.status_code}")

    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AiAnalyzeError("OpenRouter: неожиданный формат ответа.") from exc


def _call_once(
    cfg: Config,
    system: str,
    user: str,
    *,
    model: str,
    budget_text: str,
    timeout_sec: float,
    lite: AiLiteAnalysis | None = None,
) -> AiAnalysis:
    last_err: Exception | None = None
    for json_mode in (True, False):
        try:
            raw = _openrouter_chat(
                cfg,
                model=model,
                system=system,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=json_mode,
            )
            return _parse_premium_analysis(
                _extract_json_object(raw),
                budget_text=budget_text,
                lite=lite,
            )
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_err = exc
    if last_err:
        raise last_err
    raise AiAnalyzeError("OpenRouter: пустой ответ.")


def _call_lite_once(
    cfg: Config,
    system: str,
    user: str,
    *,
    timeout_sec: float,
    model: str | None = None,
) -> AiLiteAnalysis:
    last_err: Exception | None = None
    use_model = (model or cfg.ai_model_summary).strip()
    for json_mode in (True, False):
        try:
            raw = _openrouter_chat(
                cfg,
                model=use_model,
                system=system,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=json_mode,
            )
            return _parse_lite_analysis(_extract_json_object(raw))
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_err = exc
    if last_err:
        raise last_err
    raise AiAnalyzeError("L1: пустой ответ OpenRouter.")


def analyze_lite(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    snippet: str,
    url: str,
    timeout_sec: float = _LITE_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
    model: str | None = None,
) -> AiLiteAnalysis | None:
    """L1: дешёвая модель, title + snippet ≤600 симв → лента."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None

    snip = (snippet or title or "").strip()
    if len(snip) > _MAX_LITE_SNIPPET_CHARS:
        snip = snip[: _MAX_LITE_SNIPPET_CHARS - 1] + "…"
    budget_for_prompt = display_budget_text(
        budget_text,
        is_telegram="t.me" in (url or "").casefold(),
    )
    user = _build_lite_user_message(
        title=title,
        budget_text=budget_for_prompt,
        url=url,
        snippet=snip,
    )

    last_exc: BaseException | None = None
    for attempt in range(2):
        try:
            result = _call_lite_once(
                cfg, _LITE_SYSTEM, user, timeout_sec=timeout_sec, model=model
            )
            note_ai_l1_call()
            clean_tags = sanitize_l1_cms_tags(
                result.lead_tags,
                title=title,
                snippet=snip,
            )
            clean_tags = sanitize_l1_dev_design_marketing_tags(
                clean_tags,
                title=title,
                snippet=snip,
            )
            if clean_tags != result.lead_tags:
                logger.info(
                    "L1 cms sanitize: stripped wordpress_dev → %s",
                    list(clean_tags),
                )
                result = AiLiteAnalysis(
                    feed_visible=result.feed_visible,
                    task_summary=result.task_summary,
                    lead_tags=clean_tags,
                    pending_tags=result.pending_tags,
                    ai_reasons=result.ai_reasons,
                    primary_category=result.primary_category,
                )
            finalized = _finalize_lite_analysis(result, title=title, snippet=snip)
            need_retry = (
                attempt == 0
                and finalized.feed_visible
                and result.lead_tags
                and not finalized.lead_tags
            )
            if need_retry:
                logger.info("L1 tag/category mismatch — retry 1×")
                continue
            return finalized
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt == 0:
                continue

    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


def analyze_project(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    description: str,
    url: str,
    profile_path: Path | None = None,
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
    model: str | None = None,
) -> AiAnalysis | None:
    """L2 premium: полный разбор (OpenRouter). При ошибке после retry → None."""
    if not cfg.ai_active:
        return None
    if cfg.ai_provider != "openrouter":
        return None

    desc, truncated = _truncate_description(description)
    system = _build_system_prompt(build_profile_excerpt(profile_path))
    budget_for_prompt = display_budget_text(
        budget_text,
        is_telegram="t.me" in (url or "").casefold(),
    )
    user = _build_user_message(
        title=title,
        budget_text=budget_for_prompt,
        url=url,
        description=desc,
        truncated=truncated,
    )
    use_model = (model or cfg.ai_model_premium).strip()

    last_exc: BaseException | None = None
    for attempt in range(2):
        try:
            result = _call_once(
                cfg,
                system,
                user,
                model=use_model,
                budget_text=budget_for_prompt,
                timeout_sec=timeout_sec,
            )
            note_ai_l2_call()
            if errors is not None:
                warn = reply_draft_sentence_warn(result.verdict, result.reply_draft)
                if warn:
                    errors.append(f"{log_prefix}{warn}" if log_prefix else warn)
            return result
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt == 0:
                continue

    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


def analyze_premium(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    description: str,
    url: str,
    lite: AiLiteAnalysis | None = None,
    profile_path: Path | None = None,
    profile_excerpt: str | None = None,
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
    max_retries: int = 2,
) -> AiAnalysis | None:
    """L2 для Telegram-бота; при lite — system/user с блоком L1 (без дубля verdict)."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None

    desc, truncated = _truncate_description(description)
    excerpt = profile_excerpt if profile_excerpt is not None else build_profile_excerpt(profile_path)
    budget_for_prompt = display_budget_text(
        budget_text,
        is_telegram="t.me" in (url or "").casefold(),
    )
    if lite is not None:
        system = _build_premium_split_system(excerpt)
        user = _build_premium_user_with_lite(
            title=title,
            budget_text=budget_for_prompt,
            url=url,
            description=desc,
            truncated=truncated,
            lite=lite,
        )
    else:
        system = _build_system_prompt(excerpt)
        user = _build_user_message(
            title=title,
            budget_text=budget_for_prompt,
            url=url,
            description=desc,
            truncated=truncated,
        )
    use_model = cfg.ai_model_premium.strip()

    attempts = max(1, int(max_retries))
    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            result = _call_once(
                cfg,
                system,
                user,
                model=use_model,
                budget_text=budget_for_prompt,
                timeout_sec=timeout_sec,
                lite=lite,
            )
            note_ai_l2_call()
            if lite is not None and result.tools_required:
                clean_tools = sanitize_tools_for_tz(
                    result.tools_required,
                    title=title,
                    snippet=desc,
                    task_summary=lite.task_summary,
                )
                if clean_tools != result.tools_required:
                    result = AiAnalysis(
                        verdict=result.verdict,
                        work_summary=result.work_summary,
                        difficulty=result.difficulty,
                        approach=result.approach,
                        time_for_client=result.time_for_client,
                        money=result.money,
                        reply_draft=result.reply_draft,
                        risks=result.risks,
                        lead_tags=result.lead_tags,
                        tools_required=clean_tools,
                    )
            return result
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt < attempts - 1:
                continue

    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


_TOOLS_ONLY_SYSTEM = """Ты извлекаешь инструменты/стек из фриланс-заказа для блока «Инструменты» на RawLead.

Верни JSON без markdown: tools_required — массив 2–5 строк lowercase **из ТЗ заказа** (Заголовок + Описание + task_summary).

Правила:
- postgresql (не neon/supabase); telegram или telegram_bot (не telethon/aiogram)
- python, php, excel, google sheets, google sheets api, google apps script, rhino, figma, wordpress, elementor, mysql, 1c…
- Google Apps Script / Rhino V8 / google-таблица — если в тексте; **не** python, если заказ про GAS→Rhino (tools = **javascript + google_apps_script + rhino + google_sheets_api**)
- WordPress speed / Elementor / WP Rocket → wordpress_dev + elementor + php, не python без ТЗ
- Email SPF/DKIM/DMARC → email_marketing + consulting, не python/crm
- **Запрещено** без явного упоминания в ТЗ: neon, supabase, telethon, aiogram, fastapi, cursor, openrouter, gemini, rawlead
- Это **инструменты исполнения**, не canonical lead_tags

Не выводи другие поля."""


def analyze_lead_tools(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    description: str,
    lite: AiLiteAnalysis | None = None,
    timeout_sec: float = 45.0,
    errors: list[str] | None = None,
    log_prefix: str = "",
    max_retries: int = 2,
) -> tuple[str, ...] | None:
    """L2 tools-only (Sonnet/premium): заполнить tools_required без полного premium."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None
    desc, truncated = _truncate_description(description)
    summary = (lite.task_summary if lite else "") or desc[:400]
    budget_for_prompt = display_budget_text(budget_text, is_telegram=False)
    user = (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет: {budget_for_prompt.strip()}\n\n"
        f"Суть (task_summary):\n{summary.strip()}\n\n"
    )
    if desc and desc.strip() != summary.strip():
        user += f"Описание:\n{desc.strip()}\n"
    if truncated:
        user += "\n(описание обрезано)\n"
    user += "\nВерни JSON: tools_required."
    use_model = cfg.ai_model_premium.strip()
    attempts = max(1, int(max_retries))
    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            raw = _openrouter_chat(
                cfg,
                model=use_model,
                system=_TOOLS_ONLY_SYSTEM,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=True,
            )
            data = _extract_json_object(raw)
            tools = _normalize_tools_required(data.get("tools_required", data.get("tools", [])))
            tools = sanitize_tools_for_tz(
                tools,
                title=title,
                snippet=description,
                task_summary=summary,
            )
            if len(tools) < 2:
                raise AiAnalyzeError("tools-only: минимум 2 инструмента")
            note_ai_l2_call()
            return tools
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt < attempts - 1:
                continue
    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


def _build_cabinet_reply_user(
    *,
    title: str,
    budget_text: str,
    lite: AiLiteAnalysis,
) -> str:
    return (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет: {budget_text.strip()}\n\n"
        f"Суть заказа (task_summary):\n{lite.task_summary.strip()}\n\n"
        "Верни JSON: reply_draft — сопроводительное письмо от первого лица."
    )


def _tz_stack_hints_for_reply(title: str, description: str, task_summary: str) -> str:
    hay = f"{title or ''}\n{description or ''}\n{task_summary or ''}".casefold()
    hints: list[str] = []
    if any(m in hay for m in ("rhino v8", "rhino", "google apps script", "google-таблиц")):
        hints.append(
            "⚠ Стек из ТЗ: Google Apps Script (JavaScript) → Rhino V8. "
            "Назови JavaScript, Apps Script и Rhino в письме; "
            "tools_required: javascript + google_apps_script + rhino, не Python."
        )
    if any(m in hay for m in ("elementor", "tutor lms", "woocommerce", "wp rocket", "pagespeed", "lcp", "waterfall")):
        hints.append(
            "⚠ WP-стек: WordPress/Elementor/WP Rocket — "
            "упомяни PageSpeed Waterfall, LCP/CLS, критический CSS, "
            "отложенную загрузку сторонних трекеров и DOM Elementor или Ajax Tutor LMS."
        )
    if any(m in hay for m in ("fontlab", "фирменный шрифт", "логотип", "illustrator")):
        hints.append(
            "⚠ Брендинг: Illustrator, Photoshop, FontLab — этапы до глифов шрифта."
        )
    if any(m in hay for m in ("e-mail", "email", "рассылк", "spf", "dkim", "dmarc", "во входящие", "excel", "csv")):
        hints.append(
            "⚠ Email-маркетинг: SPF/DKIM/DMARC, импорт базы Excel/CSV, Reply-to, "
            "верстка без стоп-слов — без тарифов/цены в reply_draft."
        )
    if not hints:
        return ""
    return "Подсказки §1:\n" + "\n".join(hints) + "\n\n"


def _build_shared_reply_user(
    *,
    title: str,
    budget_text: str,
    lite: AiLiteAnalysis,
    tools_required: list[str],
    description: str = "",
) -> str:
    tools_line = ", ".join(t.strip() for t in tools_required if str(t).strip())
    desc = (description or "").strip()
    if len(desc) > _MAX_SHARED_SNIPPET_CHARS:
        desc = desc[: _MAX_SHARED_SNIPPET_CHARS - 1] + "…"
    body_block = f"Описание заказа:\n{desc}\n\n" if desc else ""
    hints = _tz_stack_hints_for_reply(title, desc, lite.task_summary)
    return (
        f"Заголовок: {title.strip()}\n"
        f"Бюджет: {budget_text.strip()}\n\n"
        f"Суть заказа (task_summary):\n{lite.task_summary.strip()}\n\n"
        f"{body_block}"
        f"{hints}"
        f"Инструменты (tools_required, справочно — §1 стек из текста выше): "
        f"{tools_line or 'не указаны'}\n\n"
        "Верни JSON: reply_draft — универсальное сопроводительное письмо от первого лица."
    )


def analyze_shared_reply_draft(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    lite: AiLiteAnalysis,
    tools_required: list[str] | None = None,
    description: str = "",
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
) -> str | None:
    """O57: shared L2 — один отклик на lead, без profile_excerpt."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None
    if not (lite.task_summary or "").strip():
        return None

    budget_for_prompt = display_budget_text(budget_text, is_telegram=False)
    tools = [str(t).strip() for t in (tools_required or []) if str(t).strip()]
    user = _build_shared_reply_user(
        title=title,
        budget_text=budget_for_prompt,
        lite=lite,
        tools_required=tools,
        description=description,
    )
    use_model = cfg.ai_model_shared_draft.strip()

    last_exc: BaseException | None = None
    for attempt in range(4):
        try:
            raw = _openrouter_chat(
                cfg,
                model=use_model,
                system=_SHARED_REPLY_SYSTEM,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=True,
            )
            if not raw:
                raise AiAnalyzeError("OpenRouter: пустой ответ")
            data = _extract_json_object(raw)
            draft = strip_reply_draft_price_deadline(
                _validate_reply_draft_take(str(data.get("reply_draft", "")).strip())
            )
            vague = _shared_draft_too_vague(draft)
            if vague:
                raise AiAnalyzeError(f"reply_draft: {vague}")
            note_ai_l2_call()
            return draft
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
            AttributeError,
        ) as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(_SHARED_DRAFT_BACKOFF_SEC[min(attempt, len(_SHARED_DRAFT_BACKOFF_SEC) - 1)])
                continue

    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


_UNIQUIFY_REPLY_SYSTEM = """Ты делаешь безопасный перефраз отклика для конкретного пользователя.

Задача:
- Возьми base_reply_draft и перефразируй его под тот же смысл.
- Тон: деловой, короткий, как отклик на бирже.
- Верни JSON: {"reply_draft":"..."}.

Жёсткие правила:
- Сохрани ключевой смысл и шаги base_reply_draft.
- Запрещено добавлять или менять цену/срок/бюджет/тарифы.
- Запрещено слова: Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт.
- 4-6 предложений, первое слово «Здравствуйте!».
- Не выдумывай новый стек, используй только то, что уже есть в base_reply_draft.
"""


def rephrase_reply_draft_per_user(
    cfg: Config,
    *,
    base_reply_draft: str,
    user_id: str,
    lead_id: int,
    timeout_sec: float = 30.0,
    errors: list[str] | None = None,
    log_prefix: str = "",
) -> str | None:
    """O89: cheap per-user uniquify with deterministic seed and guardrails."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None
    base = (base_reply_draft or "").strip()
    if not base:
        return None
    # Stable seed for reproducible per-user variation.
    seed = int(hashlib.sha256(f"{user_id}:{lead_id}".encode("utf-8")).hexdigest()[:8], 16)
    model = (cfg.ai_model_summary or cfg.ai_model or "").strip()
    if not model:
        return None
    user = (
        f"user_id={user_id}\n"
        f"lead_id={lead_id}\n"
        f"variation_seed={seed}\n\n"
        f"base_reply_draft:\n{base}\n\n"
        "Верни только JSON с полем reply_draft."
    )
    last_exc: BaseException | None = None
    for _attempt in range(2):
        try:
            headers = {
                "Authorization": f"Bearer {cfg.ai_api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": _UNIQUIFY_REPLY_SYSTEM},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.35,
                "seed": seed,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(
                _OPENROUTER_URL,
                headers=headers,
                json=body,
                timeout=timeout_sec,
                proxies=DIRECT_REQUESTS_PROXIES,
            )
            if resp.status_code != 200:
                raise AiAnalyzeError(f"OpenRouter HTTP {resp.status_code}")
            raw = resp.json()["choices"][0]["message"]["content"]
            data = _extract_json_object(raw)
            draft = strip_reply_draft_price_deadline(
                _validate_reply_draft_take(str(data.get("reply_draft", "")).strip())
            )
            if draft.casefold() == base.casefold():
                # Tiny deterministic nudge when model echoes input.
                draft = draft.replace("Здравствуйте!", "Здравствуйте! ", 1).strip()
            note_ai_l2_call()
            return draft
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


def analyze_cabinet_reply_draft(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    lite: AiLiteAnalysis,
    profile_excerpt: str,
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
) -> str | None:
    """O23: L2-REPLY-SCENARIO — только reply_draft для inbox."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None
    if not (lite.task_summary or "").strip():
        return None

    budget_for_prompt = display_budget_text(budget_text, is_telegram=False)
    system = _CABINET_REPLY_SYSTEM + "\n\n" + profile_excerpt
    user = _build_cabinet_reply_user(
        title=title,
        budget_text=budget_for_prompt,
        lite=lite,
    )
    use_model = cfg.ai_model_premium.strip()

    last_exc: BaseException | None = None
    for attempt in range(2):
        try:
            raw = _openrouter_chat(
                cfg,
                model=use_model,
                system=system,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=True,
            )
            data = _extract_json_object(raw)
            draft = strip_reply_draft_price_deadline(
                _validate_reply_draft_take(str(data.get("reply_draft", "")).strip())
            )
            note_ai_l2_call()
            return draft
        except (
            AiAnalyzeError,
            requests.RequestException,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_exc = exc
            if attempt == 0:
                continue

    if last_exc is not None:
        _log_ai_failure(errors, log_prefix, last_exc)
    return None


analyze = analyze_project
