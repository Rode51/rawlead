"""O272: quiz tag import must refresh feed/cabinet match bars in same tab."""

from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_FEED_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js"
_CABINET_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js"
_QUIZ_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-quiz.js"


class TestO272QuizFeedTagsSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.feed_js = _FEED_JS.read_text(encoding="utf-8")
        cls.cabinet_js = _CABINET_JS.read_text(encoding="utf-8")
        cls.quiz_js = _QUIZ_JS.read_text(encoding="utf-8")

    def test_quiz_dispatches_tags_imported(self) -> None:
        self.assertIn('CustomEvent("rawlead-tags-imported"', self.quiz_js)

    def test_feed_listens_same_tab(self) -> None:
        self.assertIn('addEventListener("rawlead-tags-imported"', self.feed_js)
        self.assertIn("reloadTagsFromSync();", self.feed_js)

    def test_cabinet_listens_same_tab(self) -> None:
        self.assertIn('addEventListener("rawlead-tags-imported"', self.cabinet_js)
        self.assertIn("reloadTagsFromSync();", self.cabinet_js)

    def test_feed_quiz_complete_skips_stale_reload(self) -> None:
        self.assertIn('addEventListener("rawlead-quiz-complete"', self.feed_js)
        self.assertIn("readTagsSyncRev() === state.tagsSyncRev", self.feed_js)


if __name__ == "__main__":
    unittest.main()
