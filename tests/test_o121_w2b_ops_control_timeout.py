"""O121-w2b: /ops/control WP REST timeouts — clear-bans/restart 90s, delist 120s."""

from __future__ import annotations

from pathlib import Path

_API = (
    Path(__file__).resolve().parents[1]
    / "wordpress/rawlead-kadence-child/inc/rawlead-api.php"
)


def _ops_control_block() -> str:
    src = _API.read_text(encoding="utf-8")
    marker = "register_rest_route('rawlead/v1', '/ops/control'"
    start = src.index(marker)
    end = src.index("register_rest_route('rawlead/v1', '/site-stats'", start)
    return src[start:end]


def test_ops_control_clear_bans_and_restart_use_90s() -> None:
    block = _ops_control_block()
    assert "clear-bans" in block
    assert "$timeout = 90" in block
    assert "action === 'restart'" in block
    assert "$target === 'radar'" in block
    assert "$target === 'site'" in block
    assert "str_starts_with($target, 'bots-')" in block


def test_ops_control_probe_all_stays_60s() -> None:
    block = _ops_control_block()
    assert "probe-all" in block
    assert "$timeout = 60" in block
    # probe-all branch before clear-bans/restart 90s branch
    assert block.index("probe-all") < block.index("clear-bans")


def test_ops_control_delist_stays_120s() -> None:
    block = _ops_control_block()
    assert "$target === 'delist'" in block
    assert "$timeout = 120" in block
    assert block.index("delist") < block.index("probe-all")


def test_ops_control_passes_timeout_to_api_post() -> None:
    block = _ops_control_block()
    assert "rawlead_api_post('/v1/admin/control', $body, $headers, $timeout)" in block
