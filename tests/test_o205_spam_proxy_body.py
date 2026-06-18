"""O205 t2: WP rawlead_api_post must JSON-encode empty body as {} not []."""

from __future__ import annotations

from pathlib import Path


def test_rawlead_api_post_empty_array_encodes_object() -> None:
    php = Path("wordpress/rawlead-kadence-child/inc/rawlead-api.php").read_text(encoding="utf-8")
    assert "function rawlead_api_post" in php
    assert "$body === [] ? '{}' : wp_json_encode($body)" in php
