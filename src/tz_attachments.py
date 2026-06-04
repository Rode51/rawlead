"""O108: TZ из вложений на странице заказа (FL/Kwork) — download + extract + enrich body."""

from __future__ import annotations

import io
import logging
import os
import re
import zipfile
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_get, request_timeout_tuple

logger = logging.getLogger(__name__)

ATTACHMENT_EXTRACTED_MARKER = "[TZ attachment — извлечено"
SKIPPED_MARKER_PREFIX = "[TZ attachment — файл на странице"
MAX_EXTRACT_CHARS = 8000
MAX_ZIP_INNER_FILES = 24
MAX_INNER_TEXT_BYTES = 64_000

ALLOWED_SUFFIXES = (".docx", ".pdf", ".txt", ".zip", ".rar")
_ARCHIVE_SUFFIXES = (".zip", ".rar")
_TEXT_SUFFIXES = (".docx", ".pdf", ".txt")
_ZIP_TEXT_SUFFIXES = (".html", ".htm", ".txt", ".md", ".csv")

_FILE_CLAIM_RE = re.compile(
    r"вижу\s+(?:"
    r"zip|zips?|архив|файл|вложени\w*|"
    r"документ|docx|pdf|"
    r"готов\w*\s+в[её]рстк|"
    r"готов\w*\s+html|"
    r"прикрепл\w*\s+(?:файл|архив|tz|тз)"
    r")",
    re.I,
)
_ATTACHMENT_PROMISE_RE = re.compile(
    r"zip|zips?|архив|\.docx|\.pdf|прикреп|скачать|вложени|download",
    re.I,
)
_SKIP_ACK_RE = re.compile(
    r"вижу,?\s+что\s+прикрепил|ознакомлюсь\s+в\s+диалоге|архив\s+\d+\s*mb",
    re.I,
)
_INNER_CONTENT_CLAIM_RE = re.compile(
    r"(?:внутри|содержим|готов\w*\s+html|index\.html|лендинг\w*\s+в\s+архиве|"
    r"загружу\s+html|вёрстк\w*\s+в\s+zip)",
    re.I,
)


def tz_attachments_enabled() -> bool:
    return os.getenv("TZ_ATTACHMENTS_ENABLED", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _env_mb(name: str, default: str) -> int:
    try:
        mb = float(os.getenv(name, default).strip())
    except ValueError:
        mb = float(default)
    return max(1, int(mb * 1024 * 1024))


def max_text_bytes() -> int:
    return _env_mb("TZ_ATTACHMENT_MAX_TEXT_MB", "8")


def max_archive_bytes() -> int:
    return _env_mb("TZ_ATTACHMENT_MAX_ARCHIVE_MB", "2")


def has_extracted_attachment_marker(text: str) -> bool:
    return ATTACHMENT_EXTRACTED_MARKER in (text or "")


def has_skipped_attachment_marker(text: str) -> bool:
    return SKIPPED_MARKER_PREFIX in (text or "")


_SKIPPED_SIZE_RE = re.compile(
    rf"{re.escape(SKIPPED_MARKER_PREFIX)},\s*([\d.]+)\s*MB",
    re.I,
)


def infer_tz_attachment_from_body(body: str) -> dict[str, Any] | None:
    """Восстановить meta для ai_reasons из маркеров в body (async L1 pool)."""
    text = body or ""
    if has_extracted_attachment_marker(text):
        m = re.search(
            rf"{re.escape(ATTACHMENT_EXTRACTED_MARKER)}\s+из\s+([^\]]+)\]",
            text,
            re.I,
        )
        name = _safe_filename(m.group(1)) if m else "file"
        return {
            "status": "extracted",
            "filename": name,
            "size_mb": 0.0,
            "reason": "extracted",
        }
    if not has_skipped_attachment_marker(text):
        return None
    if "нужен вход на биржу" in text:
        return {
            "status": "skipped_auth",
            "filename": "file",
            "size_mb": 0.0,
            "reason": "auth",
        }
    if "файл без текста" in text:
        reason = "пустой_pdf" if "пустой_pdf" in text else "empty"
        return {
            "status": "skipped_empty",
            "filename": "file",
            "size_mb": 0.0,
            "reason": reason,
        }
    sm = _SKIPPED_SIZE_RE.search(text)
    size_mb = float(sm.group(1)) if sm else 0.0
    return {
        "status": "skipped_size",
        "filename": "file",
        "size_mb": size_mb,
        "reason": "size",
    }


def body_promises_attachment(text: str) -> bool:
    return bool(_ATTACHMENT_PROMISE_RE.search(text or ""))


def _is_archive(name: str) -> bool:
    low = name.casefold()
    return any(low.endswith(ext) for ext in _ARCHIVE_SUFFIXES)


def _limit_bytes_for_filename(filename: str) -> int:
    return max_archive_bytes() if _is_archive(filename) else max_text_bytes()


def _size_mb(num_bytes: int) -> float:
    return round(num_bytes / (1024 * 1024), 1)


@dataclass(frozen=True)
class TzAttachmentMeta:
    status: str
    filename: str
    size_mb: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "filename": self.filename,
            "size_mb": self.size_mb,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class TzEnrichment:
    body: str
    attachment_extracted: bool
    attachment_files: tuple[str, ...]
    tz_attachment: TzAttachmentMeta | None = None


def reply_attachment_claim_reason(draft: str, description: str) -> str | None:
    """Retry if draft pretends to have seen file content without extracted block."""
    text = (draft or "").strip()
    desc = description or ""
    if not text:
        return None
    if has_extracted_attachment_marker(desc):
        if _FILE_CLAIM_RE.search(text):
            return None
        return None
    if has_skipped_attachment_marker(desc):
        if _INNER_CONTENT_CLAIM_RE.search(text):
            return "attachment_content_without_extract"
        if _FILE_CLAIM_RE.search(text) and not _SKIP_ACK_RE.search(text):
            return "attachment_claim_without_file"
        return None
    if _FILE_CLAIM_RE.search(text):
        return "attachment_claim_without_file"
    return None


def attachment_prompt_hint(description: str) -> str:
    if has_extracted_attachment_marker(description):
        return (
            "Файл ТЗ извлечён (блок [TZ attachment — извлечено]) — "
            "можно ссылаться на его содержимое.\n"
        )
    if has_skipped_attachment_marker(description):
        return (
            "Файл ТЗ на странице заказа, но текст не извлечён (размер/доступ). "
            "Можно: «вижу, что прикрепили архив N MB — ознакомлюсь в диалоге». "
            "Запрещено описывать содержимое архива/ZIP/HTML внутри.\n"
        )
    return (
        "⚠ Файл ТЗ НЕ извлечён системой. "
        "Запрещено: «вижу ZIP/архив/файл/готовую вёрстку/прикреплённое ТЗ». "
        "Если заказчик только обещает прислать файл — «когда будет архив» или попроси выслать.\n"
    )


def _safe_filename(name: str) -> str:
    base = (name or "file").strip().replace("\\", "/").split("/")[-1]
    return base[:120] or "file"


def _skipped_marker(size_mb: float, *, reason: str = "размера") -> str:
    return (
        f"{SKIPPED_MARKER_PREFIX}, {size_mb:g} MB, "
        f"текст не извлечён из-за {reason}]"
    )


def find_attachment_urls(html: str, page_url: str) -> list[tuple[str, str]]:
    if not (html or "").strip():
        return []
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    page_host = urlparse(page_url).netloc.casefold()

    for node in soup.find_all("a", href=True):
        href = (node.get("href") or "").strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        abs_url = urljoin(page_url, href)
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            continue
        path = unescape(parsed.path or "")
        low_path = path.casefold()
        name = _safe_filename(path)
        label = (node.get_text(" ", strip=True) or name).strip()
        allowed = any(low_path.endswith(ext) for ext in ALLOWED_SUFFIXES)
        if not allowed:
            low_href = abs_url.casefold()
            if "download" in low_href and any(
                ext in low_href for ext in ALLOWED_SUFFIXES
            ):
                allowed = True
                for ext in ALLOWED_SUFFIXES:
                    if ext in low_href:
                        name = name if low_path.endswith(ext) else f"download{ext}"
                        break
        if not allowed:
            continue
        if parsed.netloc and page_host and parsed.netloc.casefold() != page_host:
            if not any(low_path.endswith(ext) for ext in ALLOWED_SUFFIXES):
                continue
        if abs_url in seen:
            continue
        seen.add(abs_url)
        out.append((abs_url, _safe_filename(name or label)))
    return out[:3]


def probe_content_length(
    url: str,
    source: str,
    cfg: Config,
    *,
    timeout_sec: float = 15.0,
) -> int | None:
    headers = {"User-Agent": cfg.http_user_agent}
    session = exchange_fetch_begin(source)
    timeout = request_timeout_tuple() if timeout_sec is None else (
        5.0,
        float(timeout_sec),
    )
    try:
        resp = requests.head(
            url,
            headers=headers,
            timeout=timeout,
            proxies=session.current_proxies(),
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        logger.debug("tz_attachment head fail %s: %s", url[:80], exc)
        return None
    if resp.status_code in (401, 403):
        return -1
    if resp.status_code >= 400:
        return None
    cl = resp.headers.get("Content-Length")
    if not cl:
        return None
    try:
        return int(cl)
    except ValueError:
        return None


def _extract_docx(data: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            raw = zf.read("word/document.xml")
        text = re.sub(r"<w:tab[^/]*/>", "\t", raw.decode("utf-8", errors="replace"))
        text = re.sub(r"</w:p>", "\n", text)
        text = re.sub(r"<[^>]+>", " ", text)
        return unescape(re.sub(r"\s+", " ", text)).strip()
    doc = Document(io.BytesIO(data))
    parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts).strip()


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for page in reader.pages[:20]:
        t = (page.extract_text() or "").strip()
        if t:
            chunks.append(t)
    return "\n".join(chunks).strip()


def _zip_namelist(data: bytes) -> tuple[str, tuple[str, ...]]:
    names: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist()[:MAX_ZIP_INNER_FILES]:
            if info.is_dir():
                continue
            names.append(_safe_filename(info.filename))
    listing = ", ".join(names[:16])
    if len(names) > 16:
        listing += f" … (+{len(names) - 16})"
    body = f"Содержимое архива (имена файлов): {listing}" if listing else ""
    return body, tuple(names)


def _extract_zip(data: bytes) -> tuple[str, tuple[str, ...]]:
    names: list[str] = []
    chunks: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist()[:MAX_ZIP_INNER_FILES]:
            if info.is_dir():
                continue
            inner_name = _safe_filename(info.filename)
            names.append(inner_name)
            low = inner_name.casefold()
            if not any(low.endswith(ext) for ext in _ZIP_TEXT_SUFFIXES):
                continue
            if info.file_size > MAX_INNER_TEXT_BYTES:
                continue
            try:
                raw = zf.read(info.filename)
            except (KeyError, RuntimeError, zipfile.BadZipFile):
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("cp1251", errors="replace")
            if low.endswith((".html", ".htm")):
                text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                chunks.append(f"--- {inner_name} ---\n{text}")
    combined = "\n\n".join(chunks).strip()
    return combined, tuple(names)


def extract_attachment_text(data: bytes, filename: str) -> tuple[str, tuple[str, ...]]:
    if not data:
        return "", ()
    name = _safe_filename(filename)
    low = name.casefold()
    if low.endswith(".txt"):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("cp1251", errors="replace")
        return re.sub(r"\s+", " ", text).strip(), (name,)
    if low.endswith(".docx"):
        return _extract_docx(data), (name,)
    if low.endswith(".pdf"):
        return _extract_pdf(data), (name,)
    if low.endswith(".zip"):
        text, inner = _extract_zip(data)
        files = (name,) + inner if inner else (name,)
        return text, files
    if low.endswith(".rar"):
        return "", (name,)
    return "", (name,)


def download_attachment(
    url: str,
    source: str,
    cfg: Config,
    *,
    filename: str = "",
    timeout_sec: float = 30.0,
) -> tuple[bytes | None, str | None]:
    """GET file; returns (data, error_reason). error_reason: auth | None."""
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get(source, url, headers=headers, timeout_sec=timeout_sec)
    except Exception as exc:
        logger.debug("tz_attachment download fail %s: %s", url[:80], exc)
        return None, None
    if resp.status_code in (401, 403):
        return None, "auth"
    if resp.status_code != 200:
        return None, None
    return resp.content or b"", None


def enrich_body_with_attachments(
    source: str,
    page_html: str,
    base_text: str,
    cfg: Config,
    *,
    page_url: str,
    errors: list[str] | None = None,
) -> TzEnrichment:
    body = (base_text or "").strip()
    if not tz_attachments_enabled():
        return TzEnrichment(body=body, attachment_extracted=False, attachment_files=())

    links = find_attachment_urls(page_html, page_url)
    if not links:
        return TzEnrichment(body=body, attachment_extracted=False, attachment_files=())

    extracted_blocks: list[str] = []
    skipped_blocks: list[str] = []
    all_files: list[str] = []
    tz_meta: TzAttachmentMeta | None = None

    for url, filename in links:
        safe_name = _safe_filename(filename)
        limit = _limit_bytes_for_filename(safe_name)
        head_len = probe_content_length(url, source, cfg)
        size_bytes = head_len if head_len and head_len > 0 else 0

        if head_len == -1:
            block = (
                f"{SKIPPED_MARKER_PREFIX}, нужен вход на биржу, "
                "текст не извлечён]"
            )
            skipped_blocks.append(block)
            tz_meta = TzAttachmentMeta(
                status="skipped_auth",
                filename=safe_name,
                size_mb=0.0,
                reason="auth",
            )
            if errors is not None:
                errors.append(f"tz_attachment:skipped_auth:{safe_name}")
            continue

        if head_len and head_len > limit:
            size_mb = _size_mb(head_len)
            skipped_blocks.append(_skipped_marker(size_mb))
            tz_meta = TzAttachmentMeta(
                status="skipped_size",
                filename=safe_name,
                size_mb=size_mb,
                reason="size",
            )
            if errors is not None:
                errors.append(f"tz_attachment:skipped_size:{safe_name}:{size_mb}MB")
            continue

        data, dl_err = download_attachment(
            url, source, cfg, filename=safe_name
        )
        if dl_err == "auth":
            skipped_blocks.append(
                f"{SKIPPED_MARKER_PREFIX}, нужен вход на биржу, "
                "текст не извлечён]"
            )
            tz_meta = TzAttachmentMeta(
                status="skipped_auth",
                filename=safe_name,
                size_mb=_size_mb(size_bytes),
                reason="auth",
            )
            if errors is not None:
                errors.append(f"tz_attachment:skipped_auth:{safe_name}")
            continue
        if not data:
            if errors is not None:
                errors.append(f"tz_attachment:skip_download:{safe_name}")
            continue

        actual_len = len(data)
        if actual_len > limit:
            size_mb = _size_mb(actual_len)
            if safe_name.casefold().endswith(".zip"):
                listing, names = _zip_namelist(data)
                all_files.extend(names)
                block = _skipped_marker(size_mb)
                if listing:
                    block = f"{block}\n{listing}"
                skipped_blocks.append(block)
            else:
                skipped_blocks.append(_skipped_marker(size_mb))
            tz_meta = TzAttachmentMeta(
                status="skipped_size",
                filename=safe_name,
                size_mb=size_mb,
                reason="size",
            )
            if errors is not None:
                errors.append(f"tz_attachment:skipped_size:{safe_name}:{size_mb}MB")
            continue

        text, files = extract_attachment_text(data, safe_name)
        all_files.extend(files)
        if not text.strip():
            reason = "пустой_pdf" if safe_name.casefold().endswith(".pdf") else "empty"
            skipped_blocks.append(
                f"{SKIPPED_MARKER_PREFIX}, файл без текста, "
                f"текст не извлечён ({reason})]"
            )
            tz_meta = TzAttachmentMeta(
                status="skipped_empty",
                filename=safe_name,
                size_mb=_size_mb(actual_len),
                reason=reason,
            )
            if errors is not None:
                errors.append(f"tz_attachment:skipped_empty:{safe_name}")
            continue

        if len(text) > MAX_EXTRACT_CHARS:
            text = text[: MAX_EXTRACT_CHARS - 1] + "…"
        extracted_blocks.append(
            f"{ATTACHMENT_EXTRACTED_MARKER} из {safe_name}]\n{text}"
        )
        tz_meta = TzAttachmentMeta(
            status="extracted",
            filename=safe_name,
            size_mb=_size_mb(actual_len),
            reason="extracted",
        )
        if errors is not None:
            errors.append(f"tz_attachment:ok:{safe_name}")

    parts: list[str] = []
    if body:
        parts.append(body)
    parts.extend(extracted_blocks)
    parts.extend(skipped_blocks)
    enriched = "\n\n".join(parts).strip() if parts else body

    return TzEnrichment(
        body=enriched,
        attachment_extracted=bool(extracted_blocks),
        attachment_files=tuple(all_files),
        tz_attachment=tz_meta,
    )
