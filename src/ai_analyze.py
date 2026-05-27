"""ИИ-разбор заказа: stateless OpenRouter, system docs/AI.md v6.1 (TZ §5)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from budget import display_budget_text
from config import DIRECT_REQUESTS_PROXIES, Config
from rank import normalize_tags

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
    r"здравствуйте.*готов\s+реализовать",
    re.IGNORECASE,
)

_DEFAULT_TIMEOUT_SEC = 60.0
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
reply_draft — «Брать»: стремись к 4–8 предл., «Здравствуйте. Готов реализовать…», цена «от …» · «Сомнительно»: стремись к 2–4 предл., «Сделаю…»/«Возьму…», без канцелярита · «МИМО»: "" · длина вне диапазона — всё равно заполни текст, не обнуляй
risks — лимиты Cursor, расходники не оплатит заказчик, бан Telethon, scope creep
lead_tags — массив 3–8 навыков lowercase без # (python, fastapi, wordpress, парсер, telegram bot, excel); при МИМО — []

reply_draft ЗАПРЕЩЕНО: Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт.

Профиль (docs/ops/PROFILE.md):
"""


class AiAnalyzeError(RuntimeError):
    """Ошибка вызова API или разбора ответа ИИ."""


@dataclass(frozen=True)
class AiLiteAnalysis:
    """L1 ingest: короткий разбор для /lenta/ (без reply_draft и L2-полей)."""

    verdict: str
    task_summary: str
    lead_tags: tuple[str, ...] = ()
    ai_reasons: tuple[str, ...] = ()

    def is_skip_verdict(self) -> bool:
        return self.verdict.strip().casefold() in _SKIP_VERDICTS

    def is_take_verdict(self) -> bool:
        return self.verdict.strip().casefold() in ("брать", "брат")


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
    if forbid_bureaucratic_greeting and _FORBIDDEN_REPLY_GREETING_RE.search(draft):
        raise AiAnalyzeError("reply_draft: канцелярит «Здравствуйте. Готов реализовать»")
    return draft


def _reply_draft_target_range(verdict: str) -> tuple[int, int] | None:
    v = verdict.strip().casefold()
    if v in ("брать", "брат"):
        return (4, 8)
    if v == "сомнительно":
        return (2, 4)
    return None


def reply_draft_sentence_warn(verdict: str, reply_draft: str) -> str | None:
    """Опциональный warn для лога legacy; не блокирует отправку в TG."""
    draft = (reply_draft or "").strip()
    if not draft:
        return None
    rng = _reply_draft_target_range(verdict)
    if rng is None:
        return None
    lo, hi = rng
    n = _count_sentences(draft)
    if lo <= n <= hi:
        return None
    return f"warn:reply_draft_sentences={n} verdict={verdict}"


def _validate_reply_draft_take(text: str) -> str:
    draft = _validate_reply_draft_base(text, forbid_bureaucratic_greeting=False)
    if not draft:
        raise AiAnalyzeError("reply_draft пустой при вердикте Брать")
    return draft


def _validate_reply_draft_maybe(text: str) -> str:
    draft = _validate_reply_draft_base(text, forbid_bureaucratic_greeting=True)
    if not draft:
        raise AiAnalyzeError("reply_draft пустой при вердикте Сомнительно")
    return draft


def _normalize_tools_required(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, list):
        items = [str(t) for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        items = [raw.strip()]
    else:
        return ()
    return tuple(normalize_tags(items)[:8])


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

    raw_tags = data.get("lead_tags", [])
    if isinstance(raw_tags, list):
        lead_tags = tuple(normalize_tags([str(t) for t in raw_tags]))
    else:
        lead_tags = ()
    if not skip_like and lead_tags and (len(lead_tags) < 3 or len(lead_tags) > 8):
        lead_tags = lead_tags[:8]

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


# Канон: docs/team/architect/AI.md § L1/L2 «Тексты system»
_LITE_SYSTEM = """Ты — фильтр фриланс-заказов для ленты RawLead (Digital: код, дизайн, маркетинг, тексты).

Верни один JSON без markdown:
verdict — «Брать» | «Сомнительно» | «МИМО»
task_summary — 1–2 предложения: что нужно сделать простым языком (не копипаста описания)
lead_tags — 3–6 навыков lowercase без #
ai_reasons — массив 2–3 коротких строк «почему такой verdict»

МИМО: Figma/чистый фронт, 1С, mobile с нуля, накрутки, крипта, инфобиз, дипломы, нет бюджета.
Брать: парсеры, TG-боты, Python-автоматизация, правки бэкенда 1–2 файла.
Сомнительно: между Брать и МИМО.

Не выводи reply_draft, approach, money, risks."""

_PREMIUM_SPLIT_SYSTEM = """Ты — ИИ-архитектор фриланс-заказов (L2 premium) для Telegram-уведомления

Заказ уже отфильтрован — verdict «Брать» (блок L1). Не меняй verdict, не переспрашивай и не копируй task_summary; в work_summary не дублируй L1 — только развёрнутый смысл для исполнителя.

Дай: work_summary (2–4 предл.), tools_required (массив 2–5 инструментов lowercase, конкретно для этого заказа), difficulty, approach (ровно 2 предл.), time_for_client, money («На бирже: … | Рынок: … | Старт отклика: …»), risks, reply_draft, lead_tags (дополни теги из L1 до 3–8, не переписывай список с нуля).

Стек: Python (FastAPI, Telethon, aiogram 3), Neon, WordPress. Cursor Agent + Sandbox; сложные API — Gemini Deep Research → выжимка → @file в Cursor. Расходники платит заказчик.

JSON без markdown: work_summary, tools_required, difficulty, approach, time_for_client, money, reply_draft, risks, lead_tags.
Не выводи verdict, task_summary, ai_reasons.

reply_draft: 2–4 предложения, начало «Сделаю…» / «Возьму…»; разговорный, без воды, «как ты решишь». ЗАПРЕЩЕНО в reply_draft: Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт, «Здравствуйте. Готов реализовать»."""

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
        "Верни только JSON: verdict, task_summary, lead_tags, ai_reasons."
    )


def _parse_lite_analysis(data: dict[str, Any]) -> AiLiteAnalysis:
    verdict_raw = str(data.get("verdict", "")).strip()
    if not verdict_raw:
        raise AiAnalyzeError("L1: нет verdict")
    v_key = verdict_raw.casefold()
    if v_key not in _VALID_VERDICTS:
        raise AiAnalyzeError(f"L1: недопустимый verdict: {verdict_raw!r}")
    if v_key in ("мимо", "пропустить"):
        verdict = "МИМО"
    elif v_key == "сомнительно":
        verdict = "Сомнительно"
    else:
        verdict = "Брать"

    task_summary = str(data.get("task_summary", "")).strip()
    if not task_summary:
        task_summary = str(data.get("work_summary", "")).strip()
    if not task_summary and verdict != "МИМО":
        raise AiAnalyzeError("L1: пустой task_summary")

    raw_tags = data.get("lead_tags", [])
    if isinstance(raw_tags, list):
        lead_tags = tuple(normalize_tags([str(t) for t in raw_tags]))[:8]
    else:
        lead_tags = ()

    raw_reasons = data.get("ai_reasons", [])
    reasons: list[str] = []
    if isinstance(raw_reasons, list):
        for item in raw_reasons[:3]:
            s = str(item).strip()
            if s:
                reasons.append(s)
    elif isinstance(raw_reasons, str) and raw_reasons.strip():
        reasons.append(raw_reasons.strip())

    return AiLiteAnalysis(
        verdict=verdict,
        task_summary=task_summary,
        lead_tags=lead_tags,
        ai_reasons=tuple(reasons),
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
) -> AiLiteAnalysis:
    last_err: Exception | None = None
    for json_mode in (True, False):
        try:
            raw = _openrouter_chat(
                cfg,
                model=cfg.ai_model_summary,
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
                cfg, _LITE_SYSTEM, user, timeout_sec=timeout_sec
            )
            note_ai_l1_call()
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
            if errors is not None and cfg.ai_mode == "legacy":
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
    timeout_sec: float = _DEFAULT_TIMEOUT_SEC,
    errors: list[str] | None = None,
    log_prefix: str = "",
) -> AiAnalysis | None:
    """L2 для Telegram-бота; при lite — system/user с блоком L1 (без дубля verdict)."""
    if not cfg.ai_active or cfg.ai_provider != "openrouter":
        return None

    desc, truncated = _truncate_description(description)
    excerpt = build_profile_excerpt(profile_path)
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
                lite=lite,
            )
            note_ai_l2_call()
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


analyze = analyze_project
