"""O272: site profile must never use Neon DATABASE_URL."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF_fake_test_token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "999001")

from config import (  # noqa: E402
    assert_site_not_neon,
    database_url_kind,
    require_database_url,
)


class TestO272NeonGuard(unittest.TestCase):
    def test_database_url_kind_local(self) -> None:
        self.assertEqual(
            database_url_kind("postgresql://u:p@127.0.0.1:5432/rawlead"),
            "local",
        )

    def test_database_url_kind_neon(self) -> None:
        self.assertEqual(
            database_url_kind("postgresql://u:p@ep-foo.eu-central-1.aws.neon.tech/neondb"),
            "neon",
        )

    def test_database_url_kind_unset(self) -> None:
        self.assertEqual(database_url_kind(""), "unset")

    def test_site_neon_raises(self) -> None:
        neon = "postgresql://u:p@ep-x.neon.tech/db"
        with patch.dict(os.environ, {"RADAR_PROFILE": "site"}, clear=False):
            with self.assertRaises(RuntimeError):
                assert_site_not_neon(neon)

    def test_site_local_ok(self) -> None:
        local = "postgresql://u:p@127.0.0.1:5432/rawlead"
        with patch.dict(os.environ, {"RADAR_PROFILE": "site"}, clear=False):
            assert_site_not_neon(local)

    def test_legacy_neon_ok(self) -> None:
        neon = "postgresql://u:p@ep-x.neon.tech/db"
        with patch.dict(os.environ, {"RADAR_PROFILE": "legacy"}, clear=False):
            assert_site_not_neon(neon)

    @patch("config.load_config")
    @patch("config.load_radar_env")
    def test_require_database_url_site_neon(
        self,
        _load_env: unittest.mock.MagicMock,
        load_cfg: unittest.mock.MagicMock,
    ) -> None:
        neon = "postgresql://u:p@ep-x.neon.tech/db"
        load_cfg.return_value.database_url = neon
        with patch.dict(os.environ, {"RADAR_PROFILE": "site"}, clear=False):
            with self.assertRaises(RuntimeError):
                require_database_url()

    @patch("config.load_config")
    @patch("config.load_radar_env")
    def test_require_database_url_site_local(
        self,
        _load_env: unittest.mock.MagicMock,
        load_cfg: unittest.mock.MagicMock,
    ) -> None:
        local = "postgresql://u:p@127.0.0.1:5432/rawlead"
        load_cfg.return_value.database_url = local
        with patch.dict(os.environ, {"RADAR_PROFILE": "site"}, clear=False):
            self.assertEqual(require_database_url(), local)


if __name__ == "__main__":
    unittest.main()
