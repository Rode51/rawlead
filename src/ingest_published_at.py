"""O134: parse FL/Kwork published_at → UTC for ingest lag (O90/O134)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

MSK = timezone(timedelta(hours=3))
UTC = timezone.utc

_REL_UNITS: dict[str, str] = {
    "сек": "seconds",
    "секунд": "seconds",
    "секунды": "seconds",
    "секунду": "seconds",
    "мин": "minutes",
    "минут": "minutes",
    "минуты": "minutes",
    "минуту": "minutes",
    "час": "hours",
    "часа": "hours",
    "часов": "hours",
    "день": "days",
    "дня": "days",
    "дней": "days",
    "нед": "weeks",
    "недел": "weeks",
    "недели": "weeks",
    "недель": "weeks",
    "мес": "days",
    "месяц": "days",
    "месяца": "days",
    "месяцев": "days",
}

_REL_RE = re.compile(
    r"(?i)(?:^|\s)(?:(?:около|~)\s*)?(?P<n>\d+)\s*"
    r"(?P<unit>сек(?:унд(?:ы|у)?)?|мин(?:ут(?:ы|у)?)?|"
    r"час(?:а|ов)?|д(?:ень|ня|ней)|нед(?:ел(?:и|ь))?|мес(?:яц(?:а|ев)?)?)"
    r"(?:\s*назад)?"
)

_ONLY_NOW = re.compile(r"(?i)^(?:только\s+что|сейчас)$")
_TODAY = re.compile(r"(?i)^сегодня(?:\s|$)")
_YESTERDAY = re.compile(r"(?i)^вчера(?:\s|$)")


def _now_utc(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(tz=UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now.astimezone(UTC)


def _unit_delta(unit: str, n: int) -> timedelta:
    key = _REL_UNITS.get(unit.casefold(), "")
    if key == "seconds":
        return timedelta(seconds=n)
    if key == "minutes":
        return timedelta(minutes=n)
    if key == "hours":
        return timedelta(hours=n)
    if key == "days":
        if unit.casefold().startswith("мес"):
            return timedelta(days=n * 30)
        return timedelta(days=n)
    if key == "weeks":
        return timedelta(weeks=n)
    return timedelta(0)


def parse_ru_relative_published_at(
    text: str,
    *,
    now: datetime | None = None,
) -> datetime | None:
    """«2 минуты назад», «5 часов», «вчера» → UTC."""
    raw = (text or "").strip()
    if not raw:
        return None
    ref = _now_utc(now)

    if _ONLY_NOW.search(raw):
        return ref - timedelta(seconds=30)

    if _TODAY.search(raw):
        local = ref.astimezone(MSK).replace(hour=12, minute=0, second=0, microsecond=0)
        return local.astimezone(UTC)

    if _YESTERDAY.search(raw):
        local = ref.astimezone(MSK) - timedelta(days=1)
        local = local.replace(hour=12, minute=0, second=0, microsecond=0)
        return local.astimezone(UTC)

    m = _REL_RE.search(raw)
    if m:
        n = int(m.group("n"))
        unit = m.group("unit")
        return ref - _unit_delta(unit, max(n, 0))

    return None


def _parse_iso_utc(text: str) -> datetime | None:
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return dt.astimezone(UTC)


def _parse_naive_formats(text: str) -> datetime | None:
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    ):
        try:
            dt = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d" or fmt == "%d.%m.%Y":
            dt = dt.replace(hour=0, minute=0, second=0)
        return dt.replace(tzinfo=MSK).astimezone(UTC)
    return None


def parse_fl_published_at(raw: str, *, now: datetime | None = None) -> str:
    """FL listing relative/ISO → ISO8601 UTC string for `ListingProject.published_at`."""
    text = (raw or "").strip()
    if not text:
        return ""
    dt = _parse_iso_utc(text)
    if dt is None:
        dt = _parse_naive_formats(text)
    if dt is None:
        dt = parse_ru_relative_published_at(text, now=now)
    if dt is None:
        return text
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def parse_kwork_date_create(raw: object, *, now: datetime | None = None) -> str:
    """Kwork `date_create` / wantDates → ISO8601 UTC."""
    if raw is None or raw == "":
        return ""
    ref = _now_utc(now)

    if isinstance(raw, (int, float)):
        ts = float(raw)
        if ts > 1e12:
            ts /= 1000.0
        if ts > 1e9:
            return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return ""

    text = str(raw).strip()
    if not text:
        return ""

    if text.isdigit():
        return parse_kwork_date_create(int(text), now=now)

    dt = _parse_iso_utc(text)
    if dt is None:
        dt = _parse_naive_formats(text)
    if dt is None:
        dt = parse_ru_relative_published_at(text, now=now)
    if dt is None:
        return text
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def parse_source_published_at(
    raw: str,
    *,
    source: str | None = None,
    now: datetime | None = None,
) -> datetime | None:
    """Unified parse for Neon `source_published_at`."""
    text = (raw or "").strip()
    if not text:
        return None
    src = (source or "").strip().lower()
    if src == "kwork" or src.startswith("kwork:"):
        iso = parse_kwork_date_create(text, now=now)
    elif src == "fl" or src.startswith("fl:"):
        iso = parse_fl_published_at(text, now=now)
    else:
        iso = parse_fl_published_at(text, now=now)
        if not iso or iso == text:
            iso = parse_kwork_date_create(text, now=now)
    if not iso or iso == text:
        dt = _parse_iso_utc(text) or _parse_naive_formats(text)
        if dt is None:
            dt = parse_ru_relative_published_at(text, now=now)
        return dt
    return _parse_iso_utc(iso)
