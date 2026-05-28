"""Telegram Stars (3f-C): invoice, pre_checkout, successful_payment → subscriptions."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import psycopg
import requests

from config import Config, telegram_requests_proxies

logger = logging.getLogger(__name__)

_INVOICE_TITLE = "RawLead — ИИ-агент"
_INVOICE_DESC_TEMPLATE = (
    "Персональная лента, L2-черновики и push match в Telegram на 30 дней. "
    "Оплата: {stars} Telegram Stars (~400–720 ₽ при покупке Stars)."
)


def stars_available(cfg: Config) -> bool:
    return cfg.stars_enabled and bool(cfg.telegram_bot_token.strip()) and bool(
        cfg.database_url.strip()
    )


def _bot_api(cfg: Config, method: str, data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/{method}"
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(api_url, data=data, timeout=25.0, proxies=proxies)
        if resp.status_code != 200:
            return False, {}
        body = resp.json()
        if not isinstance(body, dict):
            return False, {}
        return bool(body.get("ok")), body
    except requests.RequestException as exc:
        logger.warning("stars:%s: %s", method, exc)
        return False, {}


def send_stars_invoice(
    cfg: Config, chat_id: int, *, tg_user_id: int
) -> tuple[bool, str]:
    """sendInvoice XTR для @rawlead_bot. (ok, error_detail)."""
    if not stars_available(cfg):
        return False, "Stars не настроены (STARS_ENABLED или DATABASE_URL)"
    payload = json.dumps({"kind": "agent_sub", "tg_user_id": tg_user_id}, ensure_ascii=False)
    prices = json.dumps(
        [{"label": _INVOICE_TITLE, "amount": cfg.stars_price_xtr}],
        ensure_ascii=False,
    )
    ok, body = _bot_api(
        cfg,
        "sendInvoice",
        {
            "chat_id": str(chat_id),
            "title": _INVOICE_TITLE,
            "description": _INVOICE_DESC_TEMPLATE.format(stars=cfg.stars_price_xtr),
            "payload": payload[:128],
            "provider_token": "",
            "currency": "XTR",
            "prices": prices,
        },
    )
    if ok:
        return True, ""
    desc = str(body.get("description") or "sendInvoice failed")[:200]
    logger.warning("stars:sendInvoice tg=%s: %s", tg_user_id, desc)
    return False, desc


def answer_pre_checkout(cfg: Config, query_id: str, *, ok: bool = True) -> bool:
    ok_resp, _ = _bot_api(
        cfg,
        "answerPreCheckoutQuery",
        {"pre_checkout_query_id": query_id, "ok": ok},
    )
    return ok_resp


def _ensure_user_for_payment(cur: Any, tg_user_id: int, tg_chat_id: int | None) -> str:
    cur.execute("SELECT id FROM users WHERE tg_user_id = %s", (tg_user_id,))
    row = cur.fetchone()
    if row:
        user_id = str(row[0])
        if tg_chat_id is not None:
            cur.execute(
                "UPDATE users SET tg_chat_id = COALESCE(tg_chat_id, %s) WHERE id = %s::uuid",
                (tg_chat_id, user_id),
            )
        return user_id
    user_id = str(uuid4())
    cur.execute(
        """
        INSERT INTO users (id, tg_user_id, tg_chat_id)
        VALUES (%s::uuid, %s, %s)
        """,
        (user_id, tg_user_id, tg_chat_id),
    )
    cur.execute(
        """
        INSERT INTO subscriptions (user_id, plan, is_active)
        VALUES (%s::uuid, 'free', FALSE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    return user_id


def activate_subscription(
    database_url: str,
    *,
    tg_user_id: int,
    tg_chat_id: int | None,
    days: int,
) -> bool:
    url = database_url.strip()
    if not url:
        return False
    until = datetime.now(timezone.utc) + timedelta(days=max(1, days))
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                user_id = _ensure_user_for_payment(cur, tg_user_id, tg_chat_id)
                cur.execute(
                    """
                    UPDATE subscriptions
                    SET plan = 'agent',
                        is_active = TRUE,
                        active_until = GREATEST(COALESCE(active_until, NOW()), %s),
                        paused_until = NULL
                    WHERE user_id = %s::uuid
                    """,
                    (until, user_id),
                )
                conn.commit()
        return True
    except Exception as exc:
        logger.warning("stars:activate tg=%s: %s", tg_user_id, exc)
        return False


def handle_successful_payment(
    cfg: Config,
    *,
    tg_user_id: int,
    tg_chat_id: int | None,
    payment: dict[str, Any],
    errors: list[str] | None = None,
) -> bool:
    currency = str(payment.get("currency") or "").strip()
    if currency != "XTR":
        return False
    total = int(payment.get("total_amount") or 0)
    if total < cfg.stars_price_xtr:
        return False
    ok = activate_subscription(
        cfg.database_url,
        tg_user_id=tg_user_id,
        tg_chat_id=tg_chat_id,
        days=cfg.stars_subscription_days,
    )
    if ok and errors is not None:
        errors.append(f"stars:paid tg={tg_user_id} amount={total}")
    return ok
