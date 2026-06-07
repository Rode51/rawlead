"""O107: Trial Premium 3 дня."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-trial")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-trial")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import app  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402
from src.trial_subscription import (  # noqa: E402
    TrialStartError,
    expire_stale_trials,
    has_active_premium,
    resolve_subscription_status,
    start_trial,
    subscription_extra_fields,
    trial_days_left,
)


class TestTrialHelpers(unittest.TestCase):
    def test_trial_days_left_three_days(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        until = now + timedelta(days=3)
        self.assertEqual(trial_days_left(until, now), 3)

    def test_trial_days_left_expired(self) -> None:
        now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
        until = datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(trial_days_left(until, now), 0)

    def test_resolve_trial_status(self) -> None:
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = now + timedelta(days=2)
        status, access = resolve_subscription_status(
            "trial", True, until, None, now=now
        )
        self.assertEqual(status, "trial")
        self.assertTrue(access)

    def test_resolve_free_after_trial_expired(self) -> None:
        now = datetime(2026, 6, 5, tzinfo=timezone.utc)
        until = datetime(2026, 6, 4, tzinfo=timezone.utc)
        status, access = resolve_subscription_status(
            "trial", True, until, None, now=now
        )
        self.assertEqual(status, "free")
        self.assertFalse(access)

    def test_subscription_extra_fields(self) -> None:
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = now + timedelta(days=3)
        extra = subscription_extra_fields("trial", True, until, now, now=now)
        self.assertTrue(extra["is_trial"])
        self.assertTrue(extra["trial_used"])
        self.assertEqual(extra["trial_days_left"], 3)

    def test_has_active_premium_paid(self) -> None:
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        self.assertTrue(
            has_active_premium(
                "agent", True, now + timedelta(days=10), None, now=now
            )
        )

    def test_start_trial_rejects_used(self) -> None:
        cur = MagicMock()
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        with patch(
            "src.trial_subscription.fetch_subscription_row",
            return_value=("free", False, None, None, now),
        ):
            with self.assertRaises(TrialStartError) as ctx:
                start_trial(cur, "00000000-0000-0000-0000-000000000099", now=now)
        self.assertEqual(ctx.exception.code, "trial_already_used")

    def test_expire_stale_trials_updates(self) -> None:
        cur = MagicMock()
        cur.rowcount = 2
        n = expire_stale_trials(cur)
        self.assertEqual(n, 2)
        cur.execute.assert_called_once()


class TestTrialApi(unittest.TestCase):
    def test_trial_start_endpoint(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000088"
        token = issue_access_token(user_id, tg_user_id=88001)
        until = datetime(2026, 6, 8, tzinfo=timezone.utc)

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "expire_stale_trials"):
                with patch.object(api_server, "start_trial", return_value=until):
                    with patch.object(api_server, "notify_trial_started"):
                        with patch.object(
                            api_server,
                            "fetch_subscription_row",
                            return_value=("trial", True, until, None, until),
                        ):
                            client = TestClient(app)
                            resp = client.post(
                                "/v1/me/subscription/trial-start",
                                headers={"Authorization": f"Bearer {token}"},
                            )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "trial")
        self.assertTrue(body["effective_access"])
        self.assertTrue(body["is_trial"])


if __name__ == "__main__":
    unittest.main()
