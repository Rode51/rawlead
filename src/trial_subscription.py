"""O107: Trial Premium 3 дня — старт, expiry, TG-напоминания."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import psycopg
import requests

from config import Config, telegram_requests_proxies

logger = logging.getLogger(__name__)

TRIAL_DAYS = 3
_PAID_PLANS = frozenset({"agent", "pro", "beta"})
_TRIAL_MAINT_INTERVAL_SEC = 3600
_TRIAL_MAINT_LAST_RUN_KEY = "trial_maint_last_run_epoch"

_MSG_TRIAL_STARTED = (
    "Premium на 3 дня активен. Лента без задержки, черновики — в один клик."
)
_MSG_TRIAL_24H = (
    "Завтра trial заканчивается. Продлить — 790 ₽/мес на rawlead.ru/cabinet"
)
_MSG_TRIAL_ENDED = (
    "Trial закончился. Лента снова с задержкой 15 мин. Premium — rawlead.ru/pricing"
)

SubscriptionStatus = Literal["free", "active", "paused", "expired", "beta", "trial"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def trial_days_left(active_until: datetime | None, now: datetime | None = None) -> int | None:
    if active_until is None:
        return None
    ref = now or utc_now()
    end = as_utc(active_until)
    if end is None:
        return None
    remaining = (end - ref).total_seconds()
    if remaining <= 0:
        return 0
    return max(1, int((remaining + 86399) // 86400))


def has_active_premium(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    paused_until: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    ref = now or utc_now()
    pu = as_utc(paused_until)
    if pu is not None and pu > ref:
        return True
    if plan == "owner":
        return True
    au = as_utc(active_until)
    if plan == "trial" and is_active and au is not None and au > ref:
        return True
    if plan in _PAID_PLANS and is_active:
        if au is None or au > ref:
            return True
    return False


def resolve_subscription_status(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    paused_until: datetime | None,
    *,
    now: datetime | None = None,
) -> tuple[SubscriptionStatus, bool]:
    """Return (status, effective_access)."""
    ref = now or utc_now()
    pu = as_utc(paused_until)
    au = as_utc(active_until)
    paused = pu is not None and pu > ref

    if plan == "owner":
        return "beta", True

    if plan == "trial" and is_active and au is not None and au > ref and not paused:
        return "trial", True

    paid_plan = plan in _PAID_PLANS
    expired = paid_plan and is_active and au is not None and au <= ref

    if paused:
        return "paused", False
    if expired:
        return "expired", False
    if paid_plan and is_active and (au is None or au > ref):
        return "active", True
    return "free", False


def subscription_extra_fields(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    trial_used_at: datetime | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    ref = now or utc_now()
    au = as_utc(active_until)
    is_trial = plan == "trial" and is_active and au is not None and au > ref
    days = trial_days_left(au, ref) if is_trial else None
    return {
        "is_trial": is_trial,
        "trial_used": trial_used_at is not None,
        "trial_days_left": days,
    }


def fetch_subscription_row(
    cur: Any, user_id: str
) -> tuple[str, bool, datetime | None, datetime | None, datetime | None, datetime | None]:
    cur.execute(
        """
        SELECT plan, is_active, active_until, paused_until, trial_used_at, paid_active_until
        FROM subscriptions
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return "free", False, None, None, None, None
    return (
        row[0],
        bool(row[1]),
        as_utc(row[2]),
        as_utc(row[3]),
        as_utc(row[4]),
        as_utc(row[5]) if len(row) > 5 else None,
    )


def expire_stale_trials(cur: Any, *, now: datetime | None = None) -> int:
    ref = now or utc_now()
    cur.execute(
        """
        UPDATE subscriptions
        SET plan = 'agent',
            is_active = TRUE,
            active_until = paid_active_until,
            paid_active_until = NULL
        WHERE plan = 'trial' AND is_active = TRUE
          AND active_until IS NOT NULL AND active_until <= %s
          AND paid_active_until IS NOT NULL AND paid_active_until > %s
        """,
        (ref, ref),
    )
    promoted = int(cur.rowcount or 0)
    cur.execute(
        """
        UPDATE subscriptions
        SET plan = 'free', is_active = FALSE, active_until = NULL, paid_active_until = NULL
        WHERE plan = 'trial' AND is_active = TRUE
          AND active_until IS NOT NULL AND active_until <= %s
        """,
        (ref,),
    )
    return promoted + int(cur.rowcount or 0)


class TrialStartError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


def start_trial(cur: Any, user_id: str, *, now: datetime | None = None) -> datetime:
    ref = now or utc_now()
    until = ref + timedelta(days=TRIAL_DAYS)
    plan, is_active, active_until, paused_until, trial_used_at, _paid_until = fetch_subscription_row(
        cur, user_id
    )
    if trial_used_at is not None:
        raise TrialStartError("trial_already_used", "Trial уже использован")
    if has_active_premium(plan, is_active, active_until, paused_until, now=ref):
        raise TrialStartError("already_premium", "Уже есть активный Premium")
    cur.execute(
        """
        UPDATE subscriptions
        SET plan = 'trial',
            is_active = TRUE,
            active_until = %s,
            paused_until = NULL,
            trial_used_at = %s
        WHERE user_id = %s::uuid
        """,
        (until, ref, user_id),
    )
    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, is_active, active_until, trial_used_at
            )
            VALUES (%s::uuid, 'trial', TRUE, %s, %s)
            """,
            (user_id, until, ref),
        )
    return until


def _fetch_user_chat_id(cur: Any, user_id: str) -> int | None:
    cur.execute(
        "SELECT tg_chat_id FROM users WHERE id = %s::uuid",
        (user_id,),
    )
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    return int(row[0])


def send_trial_chat(cfg: Config, chat_id: int, text: str) -> bool:
    if not cfg.telegram_bot_token.strip():
        return False
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={
                "chat_id": str(chat_id),
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=20.0,
            proxies=proxies,
        )
        if resp.status_code != 200:
            return False
        return bool(resp.json().get("ok"))
    except requests.RequestException as exc:
        logger.warning("trial:tg send chat=%s: %s", chat_id, exc)
        return False


def notify_trial_started(cfg: Config, cur: Any, user_id: str) -> None:
    chat_id = _fetch_user_chat_id(cur, user_id)
    if chat_id is None:
        return
    send_trial_chat(cfg, chat_id, _MSG_TRIAL_STARTED)


def process_trial_reminders(cfg: Config, cur: Any, *, now: datetime | None = None) -> int:
    ref = now or utc_now()
    sent = 0
    window_24h = ref + timedelta(hours=24)

    cur.execute(
        """
        SELECT s.user_id, u.tg_chat_id
        FROM subscriptions s
        INNER JOIN users u ON u.id = s.user_id
        WHERE s.plan = 'trial' AND s.is_active = TRUE
          AND s.active_until IS NOT NULL AND s.active_until > %s
          AND s.trial_remind_24h_at IS NULL
          AND s.active_until <= %s
          AND u.tg_chat_id IS NOT NULL
        """,
        (ref, window_24h),
    )
    for user_id, chat_id in cur.fetchall():
        if send_trial_chat(cfg, int(chat_id), _MSG_TRIAL_24H):
            cur.execute(
                """
                UPDATE subscriptions
                SET trial_remind_24h_at = %s
                WHERE user_id = %s::uuid
                """,
                (ref, str(user_id)),
            )
            sent += 1

    cur.execute(
        """
        SELECT s.user_id, u.tg_chat_id
        FROM subscriptions s
        INNER JOIN users u ON u.id = s.user_id
        WHERE s.plan = 'trial' AND s.is_active = TRUE
          AND s.active_until IS NOT NULL
          AND s.active_until <= %s
          AND s.trial_ended_notified_at IS NULL
          AND u.tg_chat_id IS NOT NULL
        """,
        (ref,),
    )
    for user_id, chat_id in cur.fetchall():
        if send_trial_chat(cfg, int(chat_id), _MSG_TRIAL_ENDED):
            cur.execute(
                """
                UPDATE subscriptions
                SET trial_ended_notified_at = %s
                WHERE user_id = %s::uuid
                """,
                (ref, str(user_id)),
            )
            sent += 1
    return sent


def run_trial_maintenance(cfg: Config, storage: Any, errors: list[str] | None = None) -> dict[str, int]:
    """Expire trials + TG reminders; throttle via SQLite settings (site radar)."""
    err = errors if errors is not None else []
    stats = {"expired": 0, "reminders": 0}
    if cfg.radar_profile != "site" or not cfg.database_url.strip():
        return stats

    import time

    now_mono = time.time()
    raw = storage.get_setting(_TRIAL_MAINT_LAST_RUN_KEY, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    if now_mono - last < _TRIAL_MAINT_INTERVAL_SEC:
        return stats

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                try:
                    from yookassa_billing import process_auto_renewals

                    stats["renewals"] = process_auto_renewals(cfg, cur)
                except Exception as renew_exc:
                    logger.warning("trial:renewals: %s", renew_exc)
                stats["expired"] = expire_stale_trials(cur)
                stats["reminders"] = process_trial_reminders(cfg, cur)
                conn.commit()
    except Exception as exc:
        err.append(f"trial_maint:{type(exc).__name__}")
        logger.warning("trial_maint: %s", exc)
        return stats

    storage.set_setting(_TRIAL_MAINT_LAST_RUN_KEY, str(now_mono))
    return stats


def user_has_premium_access(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    paused_until: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Paid/trial access for drafts and match push."""
    return has_active_premium(plan, is_active, active_until, paused_until, now=now)


def apply_neon_migration(database_url: str) -> bool:
    """Apply sql/020 on Neon (deploy helper)."""
    root = Path(__file__).resolve().parent.parent
    sql_path = root / "sql" / "020_trial_subscription.sql"
    if not sql_path.is_file():
        return False
    sql = sql_path.read_text(encoding="utf-8")
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        return True
    except Exception as exc:
        logger.warning("trial:migration: %s", exc)
        return False
