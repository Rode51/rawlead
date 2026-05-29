"""O54: strip price/deadline from reply_draft (site + TG)."""

from __future__ import annotations

import re

_INLINE_TAIL_RES = (
    re.compile(
        r"(?<=[.!?…])\s+(?:Ориентировочный\s+)?(?:срок|Sрок)\s*[—\-–][^.!?…]*"
        r"(?:,\s*(?:стоимость|цена)\s*[—\-–][^.!?…]*)?[.!?…]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"[,.]\s*(?:стоимость|цена)\s*[—\-–:]\s*(?:от\s+)?[\d\s\u00a0]+(?:руб\.?|₽|р\.?)[.!?…]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"[,.]\s*(?:Ориентировочный\s+)?(?:срок|Sрок)\s*[—\-–:]\s*[^.!?…]+[.!?…]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"[,.]\s*(?:срок|Sрок)\s*[^,]+,\s*(?:цена|стоимость)\s*[^.!?…]+[.!?…]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<=[.!?…])\s+(?:Срок|срок)\s+[^.!?…]+[.!?…]?\s*$",
        re.MULTILINE,
    ),
)

_DEDICATED_LINE_RES = (
    re.compile(r"^\s*(?:ориентировочн(?:ый|ая|ое)\s+)?(?:срок|стоимость|цена)\b", re.IGNORECASE),
    re.compile(r"^\s*старт\s+от\s+[\d\s\u00a0]+", re.IGNORECASE),
    re.compile(
        r"^(?:[^\n]{0,30})?(?:срок\s+\d+|\d+\s*(?:дн(?:я|ей|ь)|недел(?:ь|и|ю|ей)))"
        r"[^.!?…]{0,60}(?:₽|руб\.?|р\.?|старт\s+от)",
        re.IGNORECASE,
    ),
)


def strip_reply_draft_price_deadline(text: str) -> str:
    """Remove price/deadline lines and inline tails from L2 reply_draft."""
    draft = (text or "").strip()
    if not draft:
        return draft

    out = draft
    for pat in _INLINE_TAIL_RES:
        out = pat.sub("", out).strip()

    kept: list[str] = []
    for line in out.splitlines():
        if any(p.search(line) for p in _DEDICATED_LINE_RES):
            continue
        kept.append(line.rstrip())
    out = "\n".join(kept).strip()

    out = re.sub(r"[,\s]+$", "", out).strip()
    return out or draft


strip_tg_draft_price_deadline = strip_reply_draft_price_deadline
