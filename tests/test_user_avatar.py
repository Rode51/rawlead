"""O185 t3: local avatar cache on login."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from user_avatar import (  # noqa: E402
    avatar_public_url,
    cache_user_avatar,
    ensure_avatar_cached,
    read_avatar_bytes,
)


class TestUserAvatar(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["RAWLEAD_AVATAR_DIR"] = self._tmpdir.name
        os.environ["RAWLEAD_AVATAR_PUBLIC_BASE"] = "https://example.test/avatars"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        os.environ.pop("RAWLEAD_AVATAR_DIR", None)
        os.environ.pop("RAWLEAD_AVATAR_PUBLIC_BASE", None)

    def test_cache_accepts_octet_stream_jpeg(self) -> None:
        uid = "00000000-0000-0000-0000-000000000077"
        fake = b"\xff\xd8\xff" + b"x" * 100
        with patch("user_avatar.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                content=fake,
                headers={"Content-Type": "application/octet-stream"},
                raise_for_status=MagicMock(),
            )
            self.assertTrue(
                cache_user_avatar(uid, "https://api.telegram.org/file/bot/x/photos/file.jpg")
            )
        uid = "00000000-0000-0000-0000-000000000099"
        fake = b"\xff\xd8\xff" + b"x" * 100
        with patch("user_avatar.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                content=fake,
                headers={"Content-Type": "image/jpeg"},
                raise_for_status=MagicMock(),
            )
            self.assertTrue(cache_user_avatar(uid, "https://t.me/i/userpic/320/x.jpg"))
        payload = read_avatar_bytes(uid)
        self.assertIsNotNone(payload)
        url = avatar_public_url(uid)
        self.assertIn(uid, url or "")
        self.assertIn("example.test", url or "")

    def test_cache_accepts_octet_stream_jpeg(self) -> None:
        uid = "00000000-0000-0000-0000-000000000077"
        fake = b"\xff\xd8\xff" + b"x" * 100
        with patch("user_avatar.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                content=fake,
                headers={"Content-Type": "application/octet-stream"},
                raise_for_status=MagicMock(),
            )
            self.assertTrue(
                cache_user_avatar(uid, "https://api.telegram.org/file/bot/x/photos/file.jpg")
            )

    def test_ensure_from_neon_url(self) -> None:
        uid = "00000000-0000-0000-0000-000000000088"
        cur = MagicMock()
        cur.fetchone.return_value = ("https://t.me/i/userpic/320/y.jpg", 888)
        fake = b"\xff\xd8\xff" + b"y" * 100
        with patch("user_avatar.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                content=fake,
                headers={"Content-Type": "image/jpeg"},
                raise_for_status=MagicMock(),
            )
            self.assertTrue(ensure_avatar_cached(cur, uid))
        cur.execute.assert_called()


if __name__ == "__main__":
    unittest.main()
