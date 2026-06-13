"""O174b: YooKassa checkout, webhook, trial 1 ₽, subscription 790 ₽, auto-renewal."""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

import psycopg
import requests
from psycopg import errors as pg_errors

from config import Config
from trial_subscription import (
    TRIAL_DAYS,
    TrialStartError,
    fetch_subscription_row,
    has_active_premium,
    notify_trial_started,
    start_trial,
)

logger = logging.getLogger(__name__)

PaymentKind = Literal["trial", "subscription", "renewal"]

_YOOKASSA_API = "https://api.yookassa.ru/v3/payments"
_TRIAL_RUB = 1


class CheckoutError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ConfirmError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


def yookassa_available(cfg: Config) -> bool:
    return (
        bool(cfg.yookassa_shop_id.strip())
        and bool(cfg.yookassa_secret_key.strip())
        and bool(cfg.database_url.strip())
    )


def _auth_header(cfg: Config) -> dict[str, str]:
    token = base64.b64encode(
        f"{cfg.yookassa_shop_id}:{cfg.yookassa_secret_key}".encode()
    ).decode()
    return {"Authorization": f"Basic {token}"}


def _amount_str(rub: int) -> str:
    return f"{max(0, int(rub)):.2f}"


def _return_url(cfg: Config) -> str:
    url = (cfg.yookassa_return_url or "https://rawlead.ru/cabinet/").strip()
    if "?" in url:
        return f"{url}&pay=return"
    return f"{url}?pay=return"


def _gateway_error_detail(resp: requests.Response) -> str:
    default = "Не удалось создать платёж"
    try:
        data = resp.json()
        if isinstance(data, dict):
            desc = str(data.get("description") or "").strip()
            if desc:
                return desc
    except (ValueError, TypeError):
        pass
    return default


def _api_request(
    cfg: Config,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    idempotence_key: str | None = None,
) -> dict[str, Any]:
    headers = {
        **_auth_header(cfg),
        "Content-Type": "application/json",
    }
    if idempotence_key:
        headers["Idempotence-Key"] = idempotence_key
    if not path:
        url = _YOOKASSA_API
    elif path.startswith("http"):
        url = path
    else:
        url = f"{_YOOKASSA_API}/{path.lstrip('/')}"
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.warning("yookassa:http %s %s: %s", method, path, exc)
        raise CheckoutError("gateway_error", "Платёжный шлюз недоступен") from exc
    if resp.status_code not in (200, 201):
        detail = _gateway_error_detail(resp)
        logger.warning(
            "yookassa:api %s %s status=%s body=%s",
            method,
            path,
            resp.status_code,
            (resp.text or "")[:300],
        )
        raise CheckoutError("gateway_error", detail)
    data = resp.json()
    if not isinstance(data, dict):
        raise CheckoutError("gateway_error", "Некорректный ответ платёжного шлюза")
    return data


def _price_for_kind(cfg: Config, kind: PaymentKind) -> int:
    if kind == "trial":
        return _TRIAL_RUB
    return max(1, int(cfg.pay_premium_rub))


def _description_for_kind(kind: PaymentKind) -> str:
    if kind == "trial":
        return f"RawLead Premium — trial {_TRIAL_RUB} ₽ / {TRIAL_DAYS} дня"
    return "RawLead Premium — подписка 790 ₽ / мес"


def _is_active_trial(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    ref = now or datetime.now(timezone.utc)
    if plan != "trial" or not is_active or active_until is None:
        return False
    au = active_until if active_until.tzinfo else active_until.replace(tzinfo=timezone.utc)
    return au > ref


def validate_checkout(
    cur: Any,
    user_id: str,
    kind: PaymentKind,
    *,
    now: datetime | None = None,
) -> None:
    ref = now or datetime.now(timezone.utc)
    plan, is_active, active_until, paused_until, trial_used_at = fetch_subscription_row(
        cur, user_id
    )
    on_trial = _is_active_trial(plan, is_active, active_until, now=ref)
    if kind == "subscription" and on_trial:
        return
    if has_active_premium(plan, is_active, active_until, paused_until, now=ref):
        raise CheckoutError("already_premium", "Уже есть активный Premium")
    if kind == "trial":
        if trial_used_at is not None:
            raise CheckoutError("trial_already_used", "Trial уже использован")


def create_checkout(
    cfg: Config,
    cur: Any,
    user_id: str,
    kind: PaymentKind,
) -> dict[str, str]:
    if not yookassa_available(cfg):
        raise CheckoutError("not_configured", "Оплата временно недоступна")
    validate_checkout(cur, user_id, kind)
    amount_rub = _price_for_kind(cfg, kind)
    payload: dict[str, Any] = {
        "amount": {"value": _amount_str(amount_rub), "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": _return_url(cfg),
        },
        "description": _description_for_kind(kind),
        "metadata": {"user_id": user_id, "kind": kind},
    }
    if cfg.yookassa_save_payment_method and kind in ("trial", "subscription"):
        payload["save_payment_method"] = True
    payment = _api_request(
        cfg,
        "POST",
        "",
        body=payload,
        idempotence_key=str(uuid4()),
    )
    payment_id = str(payment.get("id") or "").strip()
    confirmation = payment.get("confirmation")
    confirm_url = ""
    if isinstance(confirmation, dict):
        confirm_url = str(confirmation.get("confirmation_url") or "").strip()
    if not payment_id or not confirm_url:
        raise CheckoutError("gateway_error", "Не удалось получить ссылку на оплату")
    cur.execute(
        """
        INSERT INTO yookassa_payments (
            yookassa_payment_id, user_id, kind, amount_rub, status, metadata
        )
        VALUES (%s, %s::uuid, %s, %s, 'pending', %s::jsonb)
        ON CONFLICT (yookassa_payment_id) DO NOTHING
        """,
        (
            payment_id,
            user_id,
            kind,
            Decimal(amount_rub),
            json.dumps({"user_id": user_id, "kind": kind}, ensure_ascii=False),
        ),
    )
    return {"payment_id": payment_id, "confirmation_url": confirm_url}


def fetch_subscription_billing_fields(cur: Any, user_id: str) -> dict[str, Any]:
    empty = {
        "auto_renew": False,
        "has_payment_method": False,
        "renew_canceled_at": None,
    }
    sql_full = """
        SELECT auto_renew, yookassa_payment_method_id, renew_canceled_at
        FROM subscriptions
        WHERE user_id = %s::uuid
    """
    sql_legacy = """
        SELECT auto_renew, yookassa_payment_method_id
        FROM subscriptions
        WHERE user_id = %s::uuid
    """
    try:
        cur.execute(sql_full, (user_id,))
    except pg_errors.UndefinedColumn:
        cur.execute(sql_legacy, (user_id,))
    row = cur.fetchone()
    if not row:
        return empty
    if len(row) >= 3:
        return {
            "auto_renew": bool(row[0]),
            "has_payment_method": bool(row[1]),
            "renew_canceled_at": row[2],
        }
    return {
        "auto_renew": bool(row[0]),
        "has_payment_method": bool(row[1]),
        "renew_canceled_at": None,
    }


def confirm_pending_payment(
    cfg: Config,
    cur: Any,
    user_id: str,
    *,
    payment_id: str | None = None,
) -> dict[str, str]:
    """Poll YooKassa for latest pending payment and apply if succeeded."""
    if payment_id:
        cur.execute(
            """
            SELECT yookassa_payment_id, status
            FROM yookassa_payments
            WHERE user_id = %s::uuid AND yookassa_payment_id = %s
            LIMIT 1
            """,
            (user_id, payment_id),
        )
    else:
        cur.execute(
            """
            SELECT yookassa_payment_id, status
            FROM yookassa_payments
            WHERE user_id = %s::uuid AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
    row = cur.fetchone()
    if not row:
        return {"status": "no_pending"}
    pid = str(row[0])
    db_status = str(row[1])
    if db_status == "succeeded":
        return {"status": "already_active"}
    payment = fetch_payment(cfg, pid)
    if not payment:
        raise ConfirmError("gateway_error", "Не удалось проверить статус платежа")
    pay_status = str(payment.get("status") or "")
    if pay_status == "succeeded":
        ok = apply_payment_succeeded(cfg, cur, payment)
        return {"status": "activated" if ok else "skipped"}
    if pay_status == "pending":
        return {"status": "pending"}
    return {"status": "failed"}


def cancel_subscription(cur: Any, user_id: str) -> bool:
    sql_full = """
        UPDATE subscriptions
        SET auto_renew = FALSE,
            yookassa_payment_method_id = NULL,
            renew_canceled_at = COALESCE(renew_canceled_at, NOW())
        WHERE user_id = %s::uuid
          AND plan NOT IN ('owner')
          AND (auto_renew = TRUE OR yookassa_payment_method_id IS NOT NULL)
    """
    sql_legacy = """
        UPDATE subscriptions
        SET auto_renew = FALSE,
            yookassa_payment_method_id = NULL
        WHERE user_id = %s::uuid
          AND plan NOT IN ('owner')
          AND (auto_renew = TRUE OR yookassa_payment_method_id IS NOT NULL)
    """
    try:
        cur.execute(sql_full, (user_id,))
    except pg_errors.UndefinedColumn:
        cur.execute(sql_legacy, (user_id,))
    return bool(cur.rowcount)


def fetch_payment(cfg: Config, payment_id: str) -> dict[str, Any] | None:
    if not yookassa_available(cfg):
        return None
    try:
        return _api_request(cfg, "GET", f"/{payment_id}")
    except CheckoutError:
        return None


def _payment_method_id(payment: dict[str, Any]) -> str | None:
    pm = payment.get("payment_method")
    if not isinstance(pm, dict):
        return None
    saved = pm.get("saved")
    pm_id = pm.get("id")
    if saved and pm_id:
        return str(pm_id).strip() or None
    return None


def _activate_trial(
    cfg: Config,
    cur: Any,
    user_id: str,
    *,
    payment_method_id: str | None,
) -> None:
    start_trial(cur, user_id)
    if payment_method_id:
        cur.execute(
            """
            UPDATE subscriptions
            SET yookassa_payment_method_id = %s,
                auto_renew = TRUE
            WHERE user_id = %s::uuid
            """,
            (payment_method_id, user_id),
        )
    notify_trial_started(cfg, cur, user_id)


def _activate_subscription(
    cur: Any,
    user_id: str,
    *,
    days: int,
    payment_method_id: str | None,
) -> None:
    until = datetime.now(timezone.utc) + timedelta(days=max(1, days))
    cur.execute(
        """
        UPDATE subscriptions
        SET plan = 'agent',
            is_active = TRUE,
            active_until = GREATEST(COALESCE(active_until, NOW()), %s),
            paused_until = NULL,
            yookassa_payment_method_id = COALESCE(%s, yookassa_payment_method_id),
            auto_renew = TRUE
        WHERE user_id = %s::uuid
        """,
        (until, payment_method_id, user_id),
    )
    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, is_active, active_until,
                yookassa_payment_method_id, auto_renew
            )
            VALUES (%s::uuid, 'agent', TRUE, %s, %s, TRUE)
            """,
            (user_id, until, payment_method_id),
        )


def _claim_payment_row(
    cur: Any,
    payment_id: str,
    payment: dict[str, Any],
) -> tuple[str, str] | None:
    """Atomically claim pending payment; idempotent if already succeeded."""
    cur.execute(
        """
        UPDATE yookassa_payments
        SET status = 'processing'
        WHERE yookassa_payment_id = %s AND status = 'pending'
        RETURNING user_id::text, kind
        """,
        (payment_id,),
    )
    row = cur.fetchone()
    if row:
        return str(row[0]), str(row[1])
    cur.execute(
        """
        SELECT status, user_id::text, kind
        FROM yookassa_payments
        WHERE yookassa_payment_id = %s
        """,
        (payment_id,),
    )
    existing = cur.fetchone()
    if existing and str(existing[0]) == "succeeded":
        return None
    if existing and str(existing[0]) == "processing":
        return None
    metadata = payment.get("metadata")
    kind = ""
    user_id = ""
    if isinstance(metadata, dict):
        kind = str(metadata.get("kind") or "").strip()
        user_id = str(metadata.get("user_id") or "").strip()
    if not user_id or kind not in ("trial", "subscription", "renewal"):
        return None
    amount_val = (payment.get("amount") or {}).get("value") or "0"
    cur.execute(
        """
        INSERT INTO yookassa_payments (
            yookassa_payment_id, user_id, kind, amount_rub, status, metadata
        )
        VALUES (%s, %s::uuid, %s, %s, 'processing', %s::jsonb)
        ON CONFLICT (yookassa_payment_id) DO UPDATE
        SET status = 'processing'
        WHERE yookassa_payments.status = 'pending'
        RETURNING user_id::text, kind
        """,
        (
            payment_id,
            user_id,
            kind,
            Decimal(str(amount_val)),
            json.dumps({"user_id": user_id, "kind": kind}, ensure_ascii=False),
        ),
    )
    row = cur.fetchone()
    if row:
        return str(row[0]), str(row[1])
    cur.execute(
        "SELECT status FROM yookassa_payments WHERE yookassa_payment_id = %s",
        (payment_id,),
    )
    again = cur.fetchone()
    if again and str(again[0]) == "succeeded":
        return None
    return None


def apply_payment_succeeded(
    cfg: Config,
    cur: Any,
    payment: dict[str, Any],
) -> bool:
    payment_id = str(payment.get("id") or "").strip()
    if not payment_id:
        return False
    claimed = _claim_payment_row(cur, payment_id, payment)
    if claimed is None:
        cur.execute(
            "SELECT status FROM yookassa_payments WHERE yookassa_payment_id = %s",
            (payment_id,),
        )
        row = cur.fetchone()
        return bool(row and str(row[0]) == "succeeded")
    user_id, kind = claimed
    if kind not in ("trial", "subscription", "renewal"):
        logger.warning("yookassa:apply skip id=%s kind=%s user=%s", payment_id, kind, user_id)
        return False
    pm_id = _payment_method_id(payment)
    days = TRIAL_DAYS if kind == "trial" else max(1, cfg.stars_subscription_days)
    try:
        if kind == "trial":
            _activate_trial(cfg, cur, user_id, payment_method_id=pm_id)
        else:
            _activate_subscription(cur, user_id, days=days, payment_method_id=pm_id)
    except TrialStartError as exc:
        logger.warning("yookassa:trial_fail user=%s: %s", user_id, exc.detail)
        cur.execute(
            """
            UPDATE yookassa_payments
            SET status = 'pending'
            WHERE yookassa_payment_id = %s AND status = 'processing'
            """,
            (payment_id,),
        )
        return False
    cur.execute(
        """
        UPDATE yookassa_payments
        SET status = 'succeeded',
            payment_method_id = COALESCE(%s, payment_method_id),
            processed_at = NOW()
        WHERE yookassa_payment_id = %s AND status = 'processing'
        """,
        (pm_id, payment_id),
    )
    return bool(cur.rowcount)


def handle_webhook_notification(cfg: Config, body: dict[str, Any]) -> bool:
    event = str(body.get("event") or "").strip()
    obj = body.get("object")
    if event != "payment.succeeded" or not isinstance(obj, dict):
        return False
    payment_id = str(obj.get("id") or "").strip()
    if not payment_id:
        return False
    payment = fetch_payment(cfg, payment_id) or obj
    if str(payment.get("status") or "") != "succeeded":
        return False
    url = cfg.database_url.strip()
    if not url:
        return False
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                ok = apply_payment_succeeded(cfg, cur, payment)
                conn.commit()
                return ok
    except Exception as exc:
        logger.warning("yookassa:webhook id=%s: %s", payment_id, exc)
        return False


def _create_autopayment(
    cfg: Config,
    *,
    user_id: str,
    payment_method_id: str,
    kind: PaymentKind,
) -> str | None:
    amount_rub = _price_for_kind(cfg, "renewal" if kind == "renewal" else kind)
    if kind == "renewal":
        amount_rub = max(1, int(cfg.pay_premium_rub))
    payload: dict[str, Any] = {
        "amount": {"value": _amount_str(amount_rub), "currency": "RUB"},
        "capture": True,
        "payment_method_id": payment_method_id,
        "description": _description_for_kind("subscription"),
        "metadata": {"user_id": user_id, "kind": kind},
    }
    try:
        payment = _api_request(
            cfg,
            "POST",
            "",
            body=payload,
            idempotence_key=str(uuid4()),
        )
    except CheckoutError as exc:
        logger.warning("yookassa:autopay user=%s: %s", user_id, exc.detail)
        return None
    payment_id = str(payment.get("id") or "").strip()
    status = str(payment.get("status") or "")
    if payment_id and status == "succeeded":
        return payment_id
    return None


def process_auto_renewals(cfg: Config, cur: Any, *, now: datetime | None = None) -> int:
    """Charge saved payment method when trial/subscription period ends."""
    if not yookassa_available(cfg):
        return 0
    ref = now or datetime.now(timezone.utc)
    window = ref + timedelta(hours=6)
    charged = 0

    cur.execute(
        """
        SELECT s.user_id::text, s.plan, s.yookassa_payment_method_id
        FROM subscriptions s
        WHERE s.auto_renew = TRUE
          AND s.yookassa_payment_method_id IS NOT NULL
          AND s.is_active = TRUE
          AND s.active_until IS NOT NULL
          AND s.active_until <= %s
          AND s.active_until > %s - INTERVAL '1 day'
          AND s.plan IN ('trial', 'agent', 'pro')
        """,
        (window, ref),
    )
    for user_id, plan, pm_id in cur.fetchall():
        kind: PaymentKind = "renewal"
        payment_id = _create_autopayment(
            cfg,
            user_id=str(user_id),
            payment_method_id=str(pm_id),
            kind=kind,
        )
        if not payment_id:
            continue
        payment = fetch_payment(cfg, payment_id)
        if not payment:
            continue
        if apply_payment_succeeded(cfg, cur, payment):
            charged += 1

    return charged
