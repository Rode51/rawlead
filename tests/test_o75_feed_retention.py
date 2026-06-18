"""O75: feed visibility window + retention SQL."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from public_feed import FEED_ANON_DELAY_MINUTES, FEED_VISIBILITY_DAYS, feed_visibility_where_sql
from api_server import _feed_where_sql


def test_feed_visibility_days_constant() -> None:
    assert FEED_VISIBILITY_DAYS == 7


def test_feed_visibility_where_includes_age_and_visible() -> None:
    sql, params = feed_visibility_where_sql()
    assert "is_visible = TRUE" in sql
    assert "make_interval(days => %s)" in sql
    assert FEED_VISIBILITY_DAYS in params


def test_feed_where_delay_param() -> None:
    sql, params = _feed_where_sql(apply_delay=True)
    assert "make_interval(mins => %s)" in sql
    assert FEED_ANON_DELAY_MINUTES in params
    assert len(params) >= 3


def test_feed_visibility_alias() -> None:
    sql, _ = feed_visibility_where_sql(alias="l")
    assert "l.is_visible" in sql
    assert "l.created_at" in sql
