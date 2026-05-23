"""ИИ-разбор заказа: stateless OpenRouter, system docs/AI.md v6 (TZ §5)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from config import DIRECT_REQUESTS_PROXIES, Config

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

_DEFAULT_TIMEOUT_SEC = 60.0
_MAX_DESCRIPTION_CHARS = 7_000
_MAX_PROFILE_EXCERPT_CHARS = 3_200

# docs/AI.md v6
_SYSTEM_PROMPT_HEAD = """Ты — жёсткий ИИ-архитектор фриланс-заказов. Прагматичный техаудитор для Никиты (29). Тон прямой, сухой, на «ты», без соплей.

Стек: Python (FastAPI, Telethon), Neon/Supabase, WordPress (каркас фронта и подписок).
Метод: Vibe Coding по изолированным модулям (до ~250 строк на файл), сейвпоинты в Git.

Исполнитель:
— В коде начинающий; простыни не пишет и не дебажит сам.
— Главный инструмент: Cursor Agent (Composer 2.5 / Auto) + Sandbox.
— Сложные API (GetCourse, AmoCRM, Bitrix24, OAuth): сначала Gemini Deep Research → выжимка до 150 строк → @file в Cursor.

МИМО (verdict «МИМО»):
— Figma, вёрстка, чистый фронт (React, Vue), 1С, mobile с нуля, Cloudflare-bypass парсинг.
— Задачи без ТЗ, дипломы, накрутки, бюджет на бирже < 3 500 ₽.

БРАТЬ:
— Парсеры сайтов/TG, TG-бот с нуля, автоматизация, скрипт на 1–3 вечера.
— ИИ API (OpenAI/DeepSeek), лёгкие правки чужого бэкенда 1–2 файла (JS, PHP).

СОМНИТЕЛЬНО: большие платформы — только если распил на модули (парсер / Neon / WordPress REST) и есть запас по срокам; в approach — план распила.

Порядок (внутри, не выводи списком):
1. Суть задачи простым языком.
2. Фильтр → verdict.
3. Архитектура: уложится в 8–12 файлов и ~3000 строк? Нужен Gemini Deep Research?
4. money на 2026: биржа | рынок | старт отклика.

При сомнении между Брать и МИМО — «Сомнительно», не «МИМО».

Поля JSON (один объект, без markdown):
verdict — «Брать» | «Сомнительно» | «МИМО»
work_summary — 2–4 предложения для не-программиста
difficulty — 1 фраза: «Легко для Cursor Agent в 2 сессии» ИЛИ «Средне: Gemini Deep Research + Cursor Agent»
approach — ровно 2 предложения: шаги + Cursor/Neon/WordPress/TG-бот без жаргона
time_for_client — срок заказчику с запасом
money — «На бирже: … | Рынок: … | Старт отклика: …»
reply_draft — 4–8 предложений только при «Брать»; цена «от …»; иначе ""
risks — лимиты Cursor, нет песочницы, бан Telethon, scope creep

reply_draft ЗАПРЕЩЕНО: Cursor, ИИ, нейросеть, ChatGPT, Gemini, AI, агент, промпт.

Профиль (docs/ops/PROFILE.md):
"""


class AiAnalyzeError(RuntimeError):
    """Ошибка вызова API или разбора ответа ИИ."""


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

    def is_skip_verdict(self) -> bool:
        return self.verdict.strip().casefold() in _SKIP_VERDICTS


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
        f"{budget_text.strip() or 'не указан'}\n"
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
        on_site = (budget_text or "").strip() or "не указан"
        m = f"На бирже: {on_site} | {m}"
        low = m.casefold()
    if "рынок" not in low:
        raise AiAnalyzeError("money: нет части «Рынок»")
    if "старт отклика" not in low:
        raise AiAnalyzeError("money: нет части «Старт отклика»")
    return m


def _validate_reply_draft(text: str) -> str:
    draft = text.strip()
    if _FORBIDDEN_REPLY_RE.search(draft):
        raise AiAnalyzeError("reply_draft: запрещённые слова (ИИ/Cursor/…)")
    return draft


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
        on_site = (budget_text or "").strip() or "не указан"
        money = f"На бирже: {on_site} | Рынок: — | Старт отклика: —"
    else:
        money = _validate_money(money_raw or f"На бирже: {budget_text}", budget_text)
    time_for_client = str(data.get("time_for_client", "")).strip() or "—"
    reply_raw = str(data.get("reply_draft", "")).strip()
    if verdict == "Брать":
        reply_draft = _validate_reply_draft(reply_raw)
        if not reply_draft:
            raise AiAnalyzeError("reply_draft пустой при вердикте Брать")
    else:
        reply_draft = reply_raw

    return AiAnalysis(
        verdict=verdict,
        work_summary=str(data["work_summary"]).strip(),
        difficulty=difficulty,
        approach=approach,
        time_for_client=time_for_client,
        money=money,
        reply_draft=reply_draft,
        risks=str(data["risks"]).strip(),
    )


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


def _openrouter_chat(
    cfg: Config,
    *,
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
        "model": cfg.ai_model,
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
    budget_text: str,
    timeout_sec: float,
) -> AiAnalysis:
    last_err: Exception | None = None
    for json_mode in (True, False):
        try:
            raw = _openrouter_chat(
                cfg,
                system=system,
                user=user,
                timeout_sec=timeout_sec,
                json_mode=json_mode,
            )
            return _parse_analysis(_extract_json_object(raw), budget_text=budget_text)
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
) -> AiAnalysis | None:
    """Один stateless-запрос (OpenRouter). При ошибке после retry → None."""
    if not cfg.ai_active:
        return None
    if cfg.ai_provider != "openrouter":
        return None

    desc, truncated = _truncate_description(description)
    system = _build_system_prompt(build_profile_excerpt(profile_path))
    user = _build_user_message(
        title=title,
        budget_text=budget_text,
        url=url,
        description=desc,
        truncated=truncated,
    )

    last_exc: BaseException | None = None
    for attempt in range(2):
        try:
            return _call_once(
                cfg,
                system,
                user,
                budget_text=budget_text,
                timeout_sec=timeout_sec,
            )
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
