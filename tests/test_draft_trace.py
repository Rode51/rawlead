"""draft:trace stage timing helper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from draft_trace import DraftTimer, log_draft_stage  # noqa: E402


class TestDraftTrace(unittest.TestCase):
    @patch("draft_trace.logger")
    def test_log_draft_stage_format(self, mock_logger: unittest.mock.MagicMock) -> None:
        timer = DraftTimer()
        log_draft_stage(
            "lenta:draft:99:",
            stage="tools",
            timer=timer,
            lead_id=99,
            count=2,
        )
        msg = mock_logger.info.call_args[0][0]
        self.assertIn("trace stage=tools", msg)
        self.assertIn("lead=99", msg)
        self.assertIn("ms=", msg)
        self.assertIn("total_ms=", msg)
        self.assertIn("count=2", msg)


if __name__ == "__main__":
    unittest.main()
