"""HTML через headless Chromium (Playwright) — fallback при антиботе."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from config import normalize_proxy_url


class HtmlFetchError(RuntimeError):
    pass


def _playwright_proxy(proxy_url: str) -> dict[str, str] | None:
    raw = (proxy_url or "").strip()
    if not raw:
        return None
    url = normalize_proxy_url(raw)
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    out: dict[str, str] = {"server": f"{parsed.scheme}://{parsed.hostname}:{port}"}
    if parsed.username:
        out["username"] = parsed.username
    if parsed.password:
        out["password"] = parsed.password
    return out


def fetch_html_playwright(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_url: str = "",
    wait_until: str = "domcontentloaded",
) -> str:
    """GET страницы в Chromium. Нужен `pip install playwright` + `playwright install chromium`."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise HtmlFetchError(
            "Playwright не установлен (pip install playwright && playwright install chromium)."
        ) from exc

    proxy = _playwright_proxy(proxy_url)
    timeout_ms = max(int(timeout_sec * 1000), 5000)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=proxy)  # type: ignore[arg-type]
        try:
            ctx = browser.new_context(user_agent=user_agent, locale="ru-RU")
            page = ctx.new_page()
            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            html = page.content()
        finally:
            browser.close()

    low = html.lower()
    if "cloudflare" in low and ("blocked" in low or "challenge" in low):
        raise HtmlFetchError(
            "Cloudflare блокирует IP — попробуйте прокси (proxy_url) или другой источник."
        )
    if len(html.strip()) < 500:
        raise HtmlFetchError("Слишком короткий ответ Playwright.")
    return html

