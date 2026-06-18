"""O227: WP /me/tags/import proxy must forward niches to API."""

from __future__ import annotations

from pathlib import Path


def test_tags_import_proxy_forwards_niches() -> None:
    php = Path("wordpress/rawlead-kadence-child/inc/rawlead-api.php").read_text(encoding="utf-8")
    start = php.index("register_rest_route('rawlead/v1', '/me/tags/import'")
    end = php.index("register_rest_route('rawlead/v1', '/me/tags/weight_delta'")
    block = php[start:end]
    assert "'niches'" in block
    assert "is_array($body['niches'])" in block
