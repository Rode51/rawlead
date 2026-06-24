"""YouDo IMAP discovery — model B: last N emails + PG dedup (§ YOUDO-IMAP-ONLY).

Env:
    YOUDO_IMAP_ENABLED=1
    YOUDO_IMAP_HOST=imap.mail.ru
    YOUDO_IMAP_PORT=993
    YOUDO_IMAP_USER=owner@mail.ru
    YOUDO_IMAP_PASSWORD=app-password
    YOUDO_IMAP_FOLDER=INBOX/Newsletters
    YOUDO_IMAP_SEARCH=FROM "youdo"
    YOUDO_IMAP_POLL_SEC=90
    YOUDO_IMAP_FETCH_LAST=30
    YOUDO_IMAP_DETAIL_FROM_EMAIL=1
"""

from __future__ import annotations

import email
import email.policy
import imaplib
import logging
import os
import re
import time
from html.parser import HTMLParser
from typing import Any

logger = logging.getLogger(__name__)

_YOUDO_TASK_RE = re.compile(r"youdo\.com/t(\d+)")
_YOUDO_FROM_RE = re.compile(r"youdo", re.IGNORECASE)
_INVISIBLE_CHARS_RE = re.compile(
    r"[\u034f\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\ufffc]+"
)
_IMAP_MIN_DETAIL_LEN = 300
_IMAP_LISTING_SNIPPET_MAX = 5000


def youdo_imap_enabled() -> bool:
    return os.getenv("YOUDO_IMAP_ENABLED", "0").strip().lower() in ("1", "true", "yes")


def youdo_imap_detail_from_email() -> bool:
    return os.getenv("YOUDO_IMAP_DETAIL_FROM_EMAIL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _imap_fetch_last_n() -> int:
    raw = os.getenv("YOUDO_IMAP_FETCH_LAST", "30").strip()
    try:
        return max(1, min(200, int(raw)))
    except ValueError:
        return 30


def _imap_config() -> dict[str, Any]:
    return {
        "host": os.getenv("YOUDO_IMAP_HOST", "imap.mail.ru"),
        "port": int(os.getenv("YOUDO_IMAP_PORT", "993")),
        "user": os.getenv("YOUDO_IMAP_USER", ""),
        "password": os.getenv("YOUDO_IMAP_PASSWORD", ""),
        "folder": os.getenv("YOUDO_IMAP_FOLDER", "INBOX/Newsletters"),
        "search": os.getenv("YOUDO_IMAP_SEARCH", 'FROM "youdo"'),
        "poll_sec": int(os.getenv("YOUDO_IMAP_POLL_SEC", "90")),
    }


# --- HTML body extraction (skip <style>, <head>, scripts) ---


class _EmailBodyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("style", "script", "head"):
            self._skip_depth += 1
        # Extract href URLs (task links are in <a> tags)
        if self._skip_depth == 0 and tag == "a":
            for name, val in attrs:
                if name == "href" and val:
                    self._parts.append(val)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script", "head") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._parts)


def _strip_invisible_text(text: str) -> str:
    """Remove zero-width / bidi junk YouDo puts in newsletter preheaders."""
    return _INVISIBLE_CHARS_RE.sub("", text)


def extract_email_body(html: str) -> str:
    """Extract visible text from YouDo newsletter HTML, skipping CSS/JS."""
    if not html or not html.strip():
        return ""
    parser = _EmailBodyParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = parser.get_text()
  # Clean up: strip invisible chars, collapse whitespace, drop noise lines
    lines: list[str] = []
    for ln in text.splitlines():
        ln = _strip_invisible_text(ln.strip())
        if not ln or len(ln) < 2:
            continue
        lines.append(ln)
    return "\n".join(lines)


def extract_task_ids(subject: str, body_text: str) -> list[str]:
    """Extract YouDo task IDs from subject + body text."""
    ids: set[str] = set()
    for m in _YOUDO_TASK_RE.finditer(subject or ""):
        ids.add(m.group(1))
    for m in _YOUDO_TASK_RE.finditer(body_text or ""):
        ids.add(m.group(1))
    return sorted(ids)


# --- IMAP connection ---


def _imap_connect(cfg: dict[str, Any]) -> imaplib.IMAP4_SSL | None:
    if not cfg["user"] or not cfg["password"]:
        logger.warning("youdo:imap missing user/password — disabled")
        return None
    try:
        conn = imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
        conn.login(cfg["user"], cfg["password"])
        return conn
    except Exception as exc:
        logger.warning("youdo:imap connect failed: %s", exc)
        return None


def _imap_fetch_last_n_emails(
    conn: imaplib.IMAP4_SSL,
    folder: str,
    search: str,
    n: int,
) -> list[tuple[int, str, str, str]]:
    """Fetch last N emails matching search. Returns [(uid, subject, from, html_body)]."""
    try:
        conn.select(folder, readonly=True)
    except Exception as exc:
        logger.warning("youdo:imap select %s failed: %s", folder, exc)
        return []

    search_criteria = f"({search})"
    try:
        status, data = conn.uid("search", None, search_criteria)
    except Exception as exc:
        logger.warning("youdo:imap search failed: %s", exc)
        return []

    if status != "OK" or not data or not data[0]:
        return []

    uid_list = data[0].split()
    # Take last N UIDs (most recent)
    uid_list = uid_list[-n:] if len(uid_list) > n else uid_list
    results: list[tuple[int, str, str, str]] = []

    for uid_bytes in uid_list:
        uid = int(uid_bytes)
        try:
            status, msg_data = conn.uid("fetch", uid_bytes, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw, policy=email.policy.default)
            from_addr = str(msg.get("From", ""))
            if not _YOUDO_FROM_RE.search(from_addr):
                continue
            subject = str(msg.get("Subject", ""))
            html_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    if ct == "text/html":
                        html_body = str(part.get_content())
                        break
            else:
                html_body = str(msg.get_content())
            results.append((uid, subject, from_addr, html_body))
        except Exception as exc:
            logger.warning("youdo:imap fetch uid=%s failed: %s", uid_bytes, exc)
            continue

    return results


# --- Public API ---


def poll_youdo_imap(
    storage: Any = None,
    *,
    min_detail_len: int = _IMAP_MIN_DETAIL_LEN,
) -> list[dict[str, Any]]:
    """Model B: fetch last N IMAP emails, return discovered tasks.

    Each dict: {project_id, subject, body, detail_ok, uid, url}
    No UID cursor — dedup happens in poller via PG.
    """
    if not youdo_imap_enabled():
        return []

    cfg = _imap_config()
    conn = _imap_connect(cfg)
    if conn is None:
        return []

    fetch_n = _imap_fetch_last_n()
    emails = _imap_fetch_last_n_emails(conn, cfg["folder"], cfg["search"], fetch_n)
    try:
        conn.logout()
    except Exception:
        pass

    results: list[dict[str, Any]] = []
    detail_from_email = youdo_imap_detail_from_email()

    for uid, subject, from_addr, html_body in emails:
        body_text = extract_email_body(html_body)
        task_ids = extract_task_ids(subject, body_text)
        for tid in task_ids:
            url = f"https://youdo.com/t{tid}"
            body_len = len(body_text)
            detail_ok = detail_from_email and body_len >= min_detail_len
            results.append(
                {
                    "project_id": tid,
                    "subject": subject,
                    "body": body_text[:5000],
                    "detail_ok": detail_ok,
                    "uid": uid,
                    "url": url,
                }
            )

    logger.info(
        "youdo:imap fetched=%d emails=%d ids=%d",
        fetch_n,
        len(emails),
        len(results),
    )
    return results
