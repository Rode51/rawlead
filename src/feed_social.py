"""Synthetic display_views for feed cards (O25/O25b). Not persisted."""



from __future__ import annotations

from datetime import datetime, timezone

from public_feed import FEED_ANON_DELAY_MINUTES



_CAP = 150

_PLATEAU_DAYS = 7

_BUCKET_MINUTES = 5



# age_min (bucketed) → base before rate & salt

_AGE_BASE: list[tuple[int, float]] = [

    (0, 2.0),

    (5, 5.5),

    (15, 20.0),

    (60, 28.0),

    (360, 41.5),

    (1440, 70.0),

    (10080, 107.5),

]





def _utc(dt: datetime) -> datetime:

    if dt.tzinfo is None:

        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)





def _lead_rate(lead_id: int) -> float:

    """Per-lead growth multiplier ~0.9..1.55."""

    return 0.9 + (lead_id % 13) / 20.0





def _f_base(age_min: int) -> float:

    pts = _AGE_BASE

    if age_min <= pts[0][0]:

        return pts[0][1]

    last_age, last_val = pts[-1]

    if age_min >= last_age:

        plateau_min = _PLATEAU_DAYS * 24 * 60

        if age_min >= plateau_min:

            extra = min((age_min - plateau_min) * 0.004, 140.0 - last_val)

            return min(last_val + extra, 140.0)

        return last_val

    for i in range(len(pts) - 1):

        a0, v0 = pts[i]

        a1, v1 = pts[i + 1]

        if a0 <= age_min < a1:

            span = a1 - a0

            t = (age_min - a0) / span if span else 0.0

            return v0 + t * (v1 - v0)

    return last_val





def _avoid_round(n: int, lead_id: int) -> int:

    if n < 15:

        return n

    out = n

    if out % 10 == 0:

        out += 3 + (lead_id % 4)

    if out % 50 == 0:

        out += 7 + (lead_id % 3)

    return out





def display_views(

    lead_id: int,

    created_at: datetime | None,

    *,

    feed_delayed: bool = False,

    now: datetime | None = None,

) -> int:

    """Deterministic synthetic views; grows with lead age, plateaus after 7d."""

    if created_at is None or lead_id <= 0:

        return 0

    now = _utc(now or datetime.now(timezone.utc))

    created = _utc(created_at)

    age_sec = max(0.0, (now - created).total_seconds())

    bucket_sec = _BUCKET_MINUTES * 60

    age_sec_b = int(age_sec // bucket_sec) * bucket_sec

    age_min = age_sec_b // 60

    age_min_raw = int(age_sec // 60)



    salt = lead_id % 7

    rate = _lead_rate(lead_id)



    if age_min_raw <= 1 and not feed_delayed:

        return (lead_id % 3) + 1



    views = int(_f_base(age_min) * rate) + salt



    if feed_delayed and age_min >= FEED_ANON_DELAY_MINUTES:

        views += 6 + (lead_id % 5) + int(min(age_min, 120) * 0.08)



    if age_min_raw <= 1:

        views = min(views, 3)



    views = _avoid_round(views, lead_id)

    return min(max(views, 1), _CAP)


def display_replies(lead_id: int, display_views: int) -> int:
    """O116 B5: one synthetic reply when fake views land in 8–15 band."""
    if display_views < 8 or display_views > 15:
        return 0
    threshold = 8 if lead_id % 2 == 0 else 10
    if display_views < threshold:
        return 0
    return 1


