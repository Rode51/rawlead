"""O43: match push eligibility + per-user threshold."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from match_push import _user_push_eligible  # noqa: E402
from rank import keyword_match, tags_as_weights  # noqa: E402


class TestMatchPushEligible(TestCase):
    def test_owner_always(self) -> None:
        now = datetime.now(timezone.utc)
        self.assertTrue(_user_push_eligible("owner", False, None, now))

    def test_agent_active(self) -> None:
        now = datetime.now(timezone.utc)
        self.assertTrue(_user_push_eligible("agent", True, None, now))

    def test_free_inactive(self) -> None:
        now = datetime.now(timezone.utc)
        self.assertFalse(_user_push_eligible("free", False, None, now))

    def test_paused(self) -> None:
        now = datetime.now(timezone.utc)
        until = now + timedelta(days=1)
        self.assertFalse(_user_push_eligible("agent", True, until, now))


class TestMatchPushThreshold(TestCase):
    def test_km_45_between_thresholds(self) -> None:
        lead = [f"tag{i}" for i in range(20)]
        user = tags_as_weights([f"tag{i}" for i in range(9)])
        km = keyword_match(lead, user)
        self.assertEqual(km, 45)
        self.assertGreaterEqual(km, 30)
        self.assertLess(km, 60)
