"""Уведомления в Telegram: MVP и разбор ИИ (TZ §5.4, v3 — блок «Задача»)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

from ai_analyze import AiAnalysis
from config import Config, telegram_requests_proxies
from listing import SOURCE_KWORK, ListingProject

__all__ = [
    "TelegramNotifyError",
    "format_mvp_message",
    "format_ai_message",
    "truncate_task_snippet",
    "send_project_notification",
    "send_project_notification_from_config",
]

_TELEGRAM_TEXT_LIMIT = 4096
_AI_UNAVAILABLE_LINE = "⚠️ Разбор ИИ недоступен — открой заказ и оцени сам."
_TASK_SNIPPET_MAX = 500
_TASK_SNIPPET_MIN = 400

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def truncate_task_snippet(text: str, *, max_len: int = _TASK_SNIPPET_MAX) -> str:
    """Обрезка описания для блока «Задача» по границе предложения (~400–600 симв.)."""
    s = (text or "").strip()
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    chunk = s[:max_len]
    best = -1
    for sep in (". ", "! ", "? ", "… ", ".\n"):
        idx = chunk.rfind(sep)
        if idx >= _TASK_SNIPPET_MIN // 2 and idx > best:
            best = idx + len(sep) - 1
    if best > 0:
        return chunk[:best].strip()
    parts = _SENTENCE_END.split(chunk)
    if len(parts) > 1 and parts[0]:
        return parts[0].strip()
    return chunk.rstrip() + "…"


def _strip_leading_task_label(text: str) -> str:
    """Kwork snippet часто начинается с «Задача:» — не дублировать с «📋 Задача:»."""
    s = (text or "").strip()
    for prefix in ("задача:", "задача", "task:"):
        if s.casefold().startswith(prefix):
            s = s[len(prefix) :].lstrip(" :\n")
            break
    return s


def _task_block_text(
    project: ListingProject,
    analysis: AiAnalysis | None,
    *,
    task_fallback_text: str = "",
) -> str:
    if analysis is not None and analysis.work_summary.strip():
        body = _strip_leading_task_label(analysis.work_summary.strip())
    else:
        raw = (task_fallback_text or project.listing_snippet or project.title).strip()
        body = truncate_task_snippet(_strip_leading_task_label(raw))
    if not body:
        return ""
    return f"📋 Задача:\n{body}"


def format_mvp_message(
    project: ListingProject,
    *,
    ai_unavailable: bool = False,
    task_fallback_text: str = "",
) -> str:
    """Формат MVP + блок «Задача» (snippet)."""
    budget = project.budget_text.strip() or "не указан"
    site, _ = _source_labels(project.source)
    lines = [
        f"🆕 Новый проект на {site}",
        "",
        project.title.strip(),
        "",
    ]
    task = _task_block_text(project, None, task_fallback_text=task_fallback_text)
    if task:
        lines.extend([task, ""])
    lines.append(f"💰 {budget}")
    if ai_unavailable:
        lines.extend(["", _AI_UNAVAILABLE_LINE])
    if project.source.startswith("tg:"):
        lines.extend(_tg_link_lines(project))
    else:
        lines.append(f"🔗 {project.url.strip()}")
    return "\n".join(lines)


def _source_labels(source: str) -> tuple[str, str]:
    if source == SOURCE_KWORK:
        return "Kwork", "Открыть на Kwork"
    if source == "telegram" or source.startswith("tg:"):
        return "Telegram", "Открыть"
    return "FL", "Открыть на FL"


def _is_private_tg_post(url: str) -> bool:
    return "/c/" in (url or "")


def _tg_link_lines(project: ListingProject) -> list[str]:
    lines: list[str] = []
    title = (project.chat_title or "").strip()
    if title:
        lines.append(f"📢 Чат: {title}")
    invite = (project.chat_invite_url or "").strip()
    if invite:
        lines.append(f"🔗 {invite}")
    post = (project.url or "").strip()
    if post:
        if _is_private_tg_post(post):
            lines.append(f"🔗 Пост (нужно состоять в чате): {post}")
        else:
            lines.append(f"🔗 Пост: {post}")
    return lines


def _tg_button_url(project: ListingProject) -> str:
    invite = (project.chat_invite_url or "").strip()
    post = (project.url or "").strip()
    if invite:
        return invite
    if post and not _is_private_tg_post(post):
        return post
    return post


def format_ai_message(
    project: ListingProject,
    analysis: AiAnalysis,
    *,
    task_fallback_text: str = "",
) -> str:
    """Формат TZ §5.4 v3: «Задача» + разбор + черновик."""
    budget = project.budget_text.strip() or "не указан"
    site, _ = _source_labels(project.source)
    task = _task_block_text(project, analysis, task_fallback_text=task_fallback_text)

    head = [
        f"🆕 Новый проект на {site}",
        "",
        project.title.strip(),
        "",
    ]
    if task:
        head.extend([task, ""])
    head.append(f"💰 {budget}")

    link_lines = _tg_link_lines(project) if project.source.startswith("tg:") else [
        f"🔗 {project.url.strip()}"
    ]
    tail = (
        f"———\n"
        f"🤖 Разбор\n\n"
        f"Вердикт: {analysis.verdict}\n"
        f"Техника (Cursor): {analysis.difficulty}\n"
        f"Как сделаем: {analysis.approach}\n"
        f"Срок заказчику: {analysis.time_for_client}\n"
        f"Деньги: {analysis.money}\n"
        f"Риски: {analysis.risks}\n\n"
        f"———\n"
        f"✍️ Черновик отклика (подправь под себя):\n\n"
        f"{analysis.reply_draft}\n\n"
        f"———\n"
        f"{chr(10).join(link_lines)}"
    )

    text = "\n".join(head) + "\n\n" + tail
    if len(text) <= _TELEGRAM_TEXT_LIMIT:
        return text

    overhead = len(text) - len(analysis.reply_draft)
    max_draft = max(120, _TELEGRAM_TEXT_LIMIT - overhead - 24)
    short_draft = analysis.reply_draft[: max_draft - 1] + "…"
    text = text.replace(analysis.reply_draft, short_draft, 1)
    return text[: _TELEGRAM_TEXT_LIMIT]


@dataclass(frozen=True)
class TelegramMessagePayload:
    chat_id: str
    text: str
    reply_markup: str | None
    disable_web_page_preview: bool = True


class TelegramNotifyError(RuntimeError):
    """Ошибка отправки уведомления в Telegram Bot API."""


def _build_reply_markup(project: ListingProject) -> str | None:
    if project.source.startswith("tg:"):
        url = _tg_button_url(project)
    else:
        url = (project.url or "").strip()
    if not url.startswith(("http://", "https://")):
        return None
    _, button = _source_labels(project.source)
    markup = {"inline_keyboard": [[{"text": button, "url": url}]]}
    return json.dumps(markup, ensure_ascii=False, separators=(",", ":"))


def _message_text(
    project: ListingProject,
    analysis: AiAnalysis | None,
    *,
    ai_unavailable: bool = False,
    task_fallback_text: str = "",
) -> str:
    if analysis is not None:
        return format_ai_message(
            project,
            analysis,
            task_fallback_text=task_fallback_text,
        )
    return format_mvp_message(
        project,
        ai_unavailable=ai_unavailable,
        task_fallback_text=task_fallback_text,
    )


def _build_payload(
    project: ListingProject,
    chat_id: str,
    *,
    analysis: AiAnalysis | None = None,
    ai_unavailable: bool = False,
    task_fallback_text: str = "",
) -> TelegramMessagePayload:
    return TelegramMessagePayload(
        chat_id=chat_id,
        text=_message_text(
            project,
            analysis,
            ai_unavailable=ai_unavailable,
            task_fallback_text=task_fallback_text,
        ),
        reply_markup=_build_reply_markup(project),
    )


def send_project_notification(
    project: ListingProject,
    *,
    bot_token: str,
    chat_id: str,
    timeout_sec: float = 20.0,
    proxies: dict[str, str] | None = None,
    analysis: AiAnalysis | None = None,
    ai_unavailable: bool = False,
    task_fallback_text: str = "",
) -> None:
    """Отправляет уведомление о проекте в указанный Telegram-чат."""
    if proxies is None:
        raise TelegramNotifyError(
            "Для Bot API нужен прокси (TG_PROXY_URL); прямой sendMessage не вызывается."
        )

    payload = _build_payload(
        project,
        chat_id,
        analysis=analysis,
        ai_unavailable=ai_unavailable,
        task_fallback_text=task_fallback_text,
    )
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        session = requests.Session()
        session.trust_env = False
        data: dict[str, str | bool] = {
            "chat_id": payload.chat_id,
            "text": payload.text,
            "disable_web_page_preview": payload.disable_web_page_preview,
        }
        if payload.reply_markup:
            data["reply_markup"] = payload.reply_markup
        resp = session.post(
            api_url,
            data=data,
            timeout=timeout_sec,
            proxies=proxies,
        )
    except requests.RequestException as exc:
        raise TelegramNotifyError(f"Сетевой сбой при отправке в Telegram: {exc}") from exc

    if resp.status_code != 200:
        detail = ""
        try:
            err_body = resp.json()
            if isinstance(err_body, dict):
                desc = err_body.get("description")
                if isinstance(desc, str) and desc.strip():
                    detail = " " + desc.strip()
                elif desc is not None and str(desc).strip():
                    detail = " " + str(desc).strip()
        except ValueError:
            pass
        raise TelegramNotifyError(
            f"Telegram Bot API вернул HTTP {resp.status_code}.{detail}"
        )

    try:
        body = resp.json()
    except ValueError as exc:
        raise TelegramNotifyError("Telegram Bot API вернул не-JSON ответ.") from exc

    if not body.get("ok", False):
        description = str(body.get("description") or "unknown error")
        raise TelegramNotifyError(f"Telegram Bot API ошибка: {description}")


def send_project_notification_from_config(
    project: ListingProject,
    cfg: Config,
    *,
    timeout_sec: float = 20.0,
    analysis: AiAnalysis | None = None,
    ai_unavailable: bool = False,
    task_fallback_text: str = "",
) -> None:
    """Обёртка для main: токен и chat_id берутся из Config."""
    send_project_notification(
        project,
        bot_token=cfg.telegram_bot_token,
        chat_id=cfg.telegram_chat_id,
        timeout_sec=timeout_sec,
        proxies=telegram_requests_proxies(cfg),
        analysis=analysis,
        ai_unavailable=ai_unavailable,
        task_fallback_text=task_fallback_text,
    )
