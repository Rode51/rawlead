"""PUBLIC_FEED_SOURCES build: web + O63 secondary + tg peers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "build_public_feed_sources.py"


def _load_build_module():
    spec = importlib.util.spec_from_file_location("build_public_feed_sources", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_public_feed_sources"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_build_includes_o63_secondary() -> None:
    mod = _load_build_module()
    sources = mod.build_sources()
    for sid in mod._SECONDARY_WEB:
        assert sid in sources, sid
    assert "fl" in sources
    assert "kwork" in sources
    assert "freelancehunt" not in sources


def test_feed_sources_csv_no_prefix() -> None:
    mod = _load_build_module()
    csv = mod.feed_sources_csv()
    assert "=" not in csv
    assert csv.startswith("fl,")
    assert "youdo" in csv
