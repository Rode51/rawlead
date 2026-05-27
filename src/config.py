"""Загрузка настроек из окружения и `.env` (python-dotenv)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# http://host:port:user:pass — удобный формат провайдеров; requests ждёт user:pass@host:port
_PROXY_HOST_PORT_USER_PASS = re.compile(
    r"^(https?)://([^:/]+):(\d+):([^:]+):([^:]+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Config:
    fl_projects_url: str
    kwork_projects_url: str
    poll_interval_minutes: int
    telegram_bot_token: str
    telegram_chat_id: str
    sqlite_path: Path
    radar_log_path: Path
    http_user_agent: str
    tg_proxy_url: str
    ai_enabled: bool
    ai_api_key: str
    ai_model: str
    ai_model_summary: str
    ai_model_premium: str
    ai_provider: str
    min_budget_rub: int
    ai_notify_skip: bool
    filter_wide: bool
    database_url: str

    @property
    def ai_active(self) -> bool:
        """ИИ включён в .env и задан ключ."""
        return self.ai_enabled and bool(self.ai_api_key)


def _require_str(name: str) -> str:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        raise ValueError(
            f"Отсутствует обязательная переменная окружения {name!r}. "
            "Задайте её в `.env` или в окружении до запуска."
        )
    return str(raw).strip()


def _validate_http_url(url: str, var_name: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"{var_name}: нужен корректный URL с http(s) и хостом, сейчас: {url!r}"
        )


def _parse_poll_interval_minutes(raw: str) -> int:
    try:
        n = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"POLL_INTERVAL_MINUTES: ожидается целое число минут, получено: {raw!r}"
        ) from exc
    if n < 10:
        raise ValueError(
            f"POLL_INTERVAL_MINUTES: по ТЗ минимум 10 минут, получено: {n}"
        )
    return n


def _parse_bool_flag(raw: str | None, *, default: bool = False) -> bool:
    if raw is None or not str(raw).strip():
        return default
    v = str(raw).strip().casefold()
    return v in ("1", "true", "yes", "on")


def _parse_min_budget_rub() -> int:
    """Порог до ИИ; пусто в .env → 1000 (docs/AI.md)."""
    raw = os.environ.get("MIN_BUDGET_RUB")
    if raw is None or not str(raw).strip():
        return 1000
    try:
        n = int(str(raw).strip())
    except ValueError as exc:
        raise ValueError(
            f"MIN_BUDGET_RUB: ожидается целое число, получено: {raw!r}"
        ) from exc
    if n < 0:
        raise ValueError(f"MIN_BUDGET_RUB: не может быть отрицательным, получено: {n}")
    return n


def _parse_ai_provider(raw: str | None) -> str:
    if raw is None or not str(raw).strip():
        return "openrouter"
    provider = str(raw).strip().casefold()
    allowed = ("openrouter",)
    if provider not in allowed:
        raise ValueError(
            f"AI_PROVIDER: ожидается {allowed[0]!r}, получено: {raw!r}"
        )
    return provider


def _path_from_env(name: str, default: str) -> Path:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return Path(default)
    return Path(str(raw).strip())


def normalize_proxy_url(raw: str) -> str:
    """
    Приводит TG_PROXY_URL к виду для requests.proxies.
    Поддерживает стандарт `http://user:pass@host:port` и сокращение `http://host:port:user:pass`.
    """
    url = raw.strip()
    if not url:
        return ""

    m = _PROXY_HOST_PORT_USER_PASS.match(url)
    if m:
        scheme, host, port, user, password = m.groups()
        return f"{scheme}://{user}:{password}@{host}:{port}"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"TG_PROXY_URL: нужен http(s) прокси, например "
            f"http://host:port:user:pass или http://user:pass@host:port, сейчас: {raw!r}"
        )
    return url


def _require_proxy_url(name: str) -> str:
    raw = _require_str(name)
    return normalize_proxy_url(raw)


def telegram_requests_proxies(cfg: Config) -> dict[str, str]:
    """Прокси только для Bot API; парсеры FL/Kwork/Avito его не используют."""
    return {"http": cfg.tg_proxy_url, "https": cfg.tg_proxy_url}


# Явно без прокси — не брать HTTP_PROXY/HTTPS_PROXY из окружения ОС.
DIRECT_REQUESTS_PROXIES: dict[str, None] = {"http": None, "https": None}


def radar_tz() -> ZoneInfo:
    """Часовой пояс логов и ночного окна TG (по умолчанию Asia/Irkutsk, UTC+8)."""
    tz_name = os.environ.get("NIGHT_TZ", "Asia/Irkutsk").strip() or "Asia/Irkutsk"
    try:
        return ZoneInfo(tz_name)
    except Exception as exc:
        raise ValueError(f"NIGHT_TZ: неизвестная зона {tz_name!r}: {exc}") from exc


def radar_timestamp(*, now: datetime | None = None) -> str:
    """Метка времени для radar.log в NIGHT_TZ."""
    tz = radar_tz()
    dt = datetime.now(tz) if now is None else now.astimezone(tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class TgMonitorAccountConfig:
    account: str
    chat_ids: tuple[int, ...]
    ids_path: Path


@dataclass(frozen=True)
class TgMonitorConfig:
    accounts: tuple[TgMonitorAccountConfig, ...]
    night_tz: ZoneInfo
    night_start: time
    night_end: time
    reconnect_sec: int
    reconnect_night_sec: int
    radar_log_path: Path

    @property
    def chat_ids(self) -> tuple[int, ...]:
        """Все id (совместимость со старым кодом)."""
        out: list[int] = []
        for ac in self.accounts:
            out.extend(ac.chat_ids)
        return tuple(out)


def _parse_hh_mm(raw: str, var_name: str) -> time:
    parts = raw.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"{var_name}: ожидается HH:MM, получено: {raw!r}")
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(f"{var_name}: ожидается HH:MM, получено: {raw!r}") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"{var_name}: неверное время: {raw!r}")
    return time(hour, minute)


DEFAULT_TELETHON_MONITOR_ACCOUNT = "acc1"
DEFAULT_TELETHON_CHAT_IDS_PATH = "data/telethon_chat_ids.txt"
_LEGACY_TELETHON_CHAT_IDS_PATH = "data/telethon_chat_ids.txt"


def telethon_monitor_account() -> str:
    raw = os.environ.get("TELETHON_MONITOR_ACCOUNT", DEFAULT_TELETHON_MONITOR_ACCOUNT)
    account = str(raw).strip().lower() if raw else DEFAULT_TELETHON_MONITOR_ACCOUNT
    return account or DEFAULT_TELETHON_MONITOR_ACCOUNT


def telethon_monitor_accounts() -> tuple[str, ...]:
    """Аккаунты, которые слушает tg_main (multi-session)."""
    raw = os.environ.get("TELETHON_MONITOR_ACCOUNTS", "").strip()
    if raw:
        parts = tuple(a.strip().lower() for a in raw.split(",") if a.strip())
        if parts:
            return parts
    return (telethon_monitor_account(),)


def _resolve_path_from_env(raw: str) -> Path:
    path = Path(raw.strip())
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    return path


def resolve_telethon_chat_ids_path() -> Path | None:
    """Путь к файлу id, если TELETHON_CHAT_IDS — не inline-список (legacy acc1)."""
    raw = os.environ.get("TELETHON_CHAT_IDS", "").strip()
    if not raw:
        return None
    if "," in raw:
        return None
    try:
        int(raw)
        return None
    except ValueError:
        pass
    return _resolve_path_from_env(raw)


def telethon_chat_ids_path_for_account(account: str) -> Path:
    """Файл listen-списка для аккаунта (data/telethon_chat_ids_accN.txt)."""
    account = account.strip().lower()
    env_key = f"TELETHON_CHAT_IDS_{account.upper()}"
    per_acc = os.environ.get(env_key, "").strip()
    if per_acc:
        return _resolve_path_from_env(per_acc)
    if account == telethon_monitor_account():
        legacy = resolve_telethon_chat_ids_path()
        if legacy is not None:
            return legacy
    default = _PROJECT_ROOT / f"data/telethon_chat_ids_{account}.txt"
    legacy_single = _PROJECT_ROOT / _LEGACY_TELETHON_CHAT_IDS_PATH
    if account == "acc1" and not default.is_file() and legacy_single.is_file():
        return legacy_single
    return default


def _seed_chat_ids_from_queue_csv(queue_csv: Path, account: str) -> list[int]:
    import csv

    if not queue_csv.is_file():
        return []
    account = account.strip().lower()
    out: list[int] = []
    with queue_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("account", "").strip().lower() != account:
                continue
            if row.get("status", "").strip().lower() != "done":
                continue
            raw_cid = row.get("chat_id", "").strip()
            if not raw_cid:
                continue
            try:
                out.append(int(raw_cid))
            except ValueError:
                continue
    return out


def _seed_chat_ids_from_env_inline() -> list[int]:
    raw = os.environ.get("TELETHON_CHAT_IDS", "").strip()
    if not raw or "," not in raw:
        return []
    try:
        return parse_telethon_chat_ids(raw)
    except ValueError:
        return []


def ensure_telethon_chat_ids_file(
    path: Path | None = None,
    *,
    account: str | None = None,
    queue_csv: Path | None = None,
) -> Path:
    """Создаёт файл id из CSV (done по account) или inline .env, если файла ещё нет."""
    if path is None:
        if account is None:
            path = resolve_telethon_chat_ids_path()
            if path is None:
                raise ValueError("TELETHON_CHAT_IDS не указывает на файл")
        else:
            path = telethon_chat_ids_path_for_account(account)
    target = path
    if target.is_file():
        return target

    acc = (account or telethon_monitor_account()).strip().lower()
    legacy_single = _PROJECT_ROOT / _LEGACY_TELETHON_CHAT_IDS_PATH
    if acc == "acc1" and legacy_single.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(legacy_single.read_text(encoding="utf-8"), encoding="utf-8")
        return target

    csv_path = queue_csv or (
        _PROJECT_ROOT
        / _path_from_env("TG_JOIN_QUEUE_CSV", "docs/ops/TG_JOIN_QUEUE.csv")
    )
    ids = _seed_chat_ids_from_queue_csv(csv_path, acc)
    if not ids and acc == telethon_monitor_account():
        ids = _seed_chat_ids_from_env_inline()

    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Telethon chat ids для tg_main ({acc}, один id на строку)\n"]
    for cid in ids:
        lines.append(f"{cid}\n")
    target.write_text("".join(lines), encoding="utf-8")
    return target


def append_telethon_chat_id(
    chat_id: int,
    path: Path | None = None,
    *,
    account: str | None = None,
) -> bool:
    """Дописывает id в файл, если его ещё нет. True — добавлен."""
    if path is None:
        if account is None:
            path = resolve_telethon_chat_ids_path()
            if path is None:
                return False
        else:
            path = telethon_chat_ids_path_for_account(account)
    target = path
    ensure_telethon_chat_ids_file(target, account=account)
    existing = set(parse_telethon_chat_ids(str(target)))
    if int(chat_id) in existing:
        return False
    with target.open("a", encoding="utf-8") as fh:
        fh.write(f"{int(chat_id)}\n")
    return True


def parse_telethon_chat_ids(raw: str) -> list[int]:
    """Список id через запятую или путь к файлу (по одному id на строку)."""
    text = raw.strip()
    if not text:
        return []
    path = Path(text)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        parts: list[str] = []
        for ln in lines:
            s = ln.strip()
            if s and not s.startswith("#"):
                parts.append(s)
    else:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    out: list[int] = []
    for part in parts:
        try:
            out.append(int(part))
        except ValueError as exc:
            raise ValueError(
                f"TELETHON_CHAT_IDS: ожидается число, получено: {part!r}"
            ) from exc
    return out


def load_tg_monitor_config() -> TgMonitorConfig:
    """Настройки только для scripts/tg_main.py (не нужны main.py)."""
    load_dotenv(_PROJECT_ROOT / ".env")

    monitor_accounts = telethon_monitor_accounts()
    account_rows: list[TgMonitorAccountConfig] = []
    for acc in monitor_accounts:
        ids_path = telethon_chat_ids_path_for_account(acc)
        ensure_telethon_chat_ids_file(ids_path, account=acc)
        ids = tuple(parse_telethon_chat_ids(str(ids_path)))
        account_rows.append(
            TgMonitorAccountConfig(account=acc, chat_ids=ids, ids_path=ids_path)
        )

    if not any(row.chat_ids for row in account_rows):
        print(
            "Задайте TELETHON_CHAT_IDS / TELETHON_MONITOR_ACCOUNTS и файлы "
            f"data/telethon_chat_ids_accN.txt (или {DEFAULT_TELETHON_CHAT_IDS_PATH}). "
            "Сид: python scripts/tg_sync_chat_ids.py --account all"
        )
        raise SystemExit(1)

    try:
        night_tz = radar_tz()
    except ValueError as exc:
        print(exc)
        raise SystemExit(1) from exc

    night_start = _parse_hh_mm(
        os.environ.get("NIGHT_START", "02:00").strip() or "02:00",
        "NIGHT_START",
    )
    night_end = _parse_hh_mm(
        os.environ.get("NIGHT_END", "07:00").strip() or "07:00",
        "NIGHT_END",
    )

    def _pos_int(name: str, default: int) -> int:
        raw = os.environ.get(name)
        if raw is None or not str(raw).strip():
            return default
        try:
            n = int(str(raw).strip())
        except ValueError as exc:
            print(f"{name}: ожидается целое число секунд")
            raise SystemExit(1) from exc
        if n < 1:
            print(f"{name}: минимум 1 секунда")
            raise SystemExit(1)
        return n

    reconnect_sec = _pos_int("TG_RECONNECT_SEC", 30)
    reconnect_night_sec = _pos_int("TG_RECONNECT_NIGHT_SEC", 300)
    radar_log_path = _path_from_env("RADAR_LOG_PATH", "data/radar.log")

    return TgMonitorConfig(
        accounts=tuple(account_rows),
        night_tz=night_tz,
        night_start=night_start,
        night_end=night_end,
        reconnect_sec=reconnect_sec,
        reconnect_night_sec=reconnect_night_sec,
        radar_log_path=radar_log_path,
    )


def is_night_window(cfg: TgMonitorConfig, *, now=None) -> bool:
    """02:00–07:00 в NIGHT_TZ (конец исключающий, если start < end)."""
    return _is_night_window(
        cfg.night_tz,
        cfg.night_start,
        cfg.night_end,
        now=now,
    )


def _is_night_window(
    night_tz: ZoneInfo,
    night_start: time,
    night_end: time,
    *,
    now=None,
) -> bool:
    from datetime import datetime

    if now is None:
        now = datetime.now(night_tz)
    else:
        now = now.astimezone(night_tz)
    t = now.time()
    start, end = night_start, night_end
    if start < end:
        return start <= t < end
    return t >= start or t < end


@dataclass(frozen=True)
class TgJoinConfig:
    max_per_hour: int
    min_delay_sec: int
    max_delay_sec: int
    max_per_day: int
    night_tz: ZoneInfo
    night_start: time
    night_end: time
    state_path: Path
    log_path: Path
    queue_csv: Path
    daemon_interval_sec: int


def tg_join_in_tg_main() -> bool:
    """Фоновый join всех TELETHON_MONITOR_ACCOUNTS внутри tg_main."""
    raw = os.environ.get("TG_JOIN_IN_TG_MAIN", "").strip().lower()
    if raw:
        return raw not in ("0", "false", "no", "off")
    legacy = os.environ.get("TG_JOIN_AUTO_ACC1", "1").strip().lower()
    return legacy not in ("0", "false", "no", "off")


def tg_join_auto_acc1() -> bool:
    """Deprecated: используйте tg_join_in_tg_main()."""
    return tg_join_in_tg_main()


def tg_join_daemon_accounts() -> list[str]:
    """Deprecated: acc для ручного tg_join_daemon.py (не автозапуск)."""
    raw = os.environ.get("TG_JOIN_DAEMON_ACCOUNTS", "acc2,acc3").strip()
    if not raw:
        return []
    return [a.strip().lower() for a in raw.split(",") if a.strip()]


def load_tg_join_config() -> TgJoinConfig:
    """Настройки scripts/tg_join_queue.py (без TELETHON_CHAT_IDS)."""
    load_dotenv(_PROJECT_ROOT / ".env")

    def _pos_int(name: str, default: int, *, minimum: int = 1) -> int:
        raw = os.environ.get(name)
        if raw is None or not str(raw).strip():
            return default
        try:
            n = int(str(raw).strip())
        except ValueError as exc:
            raise ValueError(f"{name}: ожидается целое число, получено: {raw!r}") from exc
        if n < minimum:
            raise ValueError(f"{name}: минимум {minimum}, получено: {n}")
        return n

    try:
        night_tz = radar_tz()
    except ValueError as exc:
        print(exc)
        raise SystemExit(1) from exc

    night_start = _parse_hh_mm(
        os.environ.get("NIGHT_START", "02:00").strip() or "02:00",
        "NIGHT_START",
    )
    night_end = _parse_hh_mm(
        os.environ.get("NIGHT_END", "07:00").strip() or "07:00",
        "NIGHT_END",
    )

    min_delay = _pos_int("TG_JOIN_MIN_DELAY_SEC", 900)
    max_delay_raw = os.environ.get("TG_JOIN_MAX_DELAY_SEC")
    if max_delay_raw is None or not str(max_delay_raw).strip():
        max_delay = min_delay + 300
    else:
        max_delay = _pos_int("TG_JOIN_MAX_DELAY_SEC", min_delay + 300)
    if max_delay < min_delay:
        max_delay = min_delay

    return TgJoinConfig(
        max_per_hour=_pos_int("TG_JOIN_MAX_PER_HOUR", 4),
        min_delay_sec=min_delay,
        max_delay_sec=max_delay,
        max_per_day=_pos_int("TG_JOIN_MAX_PER_DAY", 25),
        night_tz=night_tz,
        night_start=night_start,
        night_end=night_end,
        state_path=_PROJECT_ROOT / _path_from_env("TG_JOIN_STATE_PATH", "data/tg_join_state.json"),
        log_path=_PROJECT_ROOT / _path_from_env("TG_JOIN_LOG_PATH", "data/tg_join.log"),
        queue_csv=_PROJECT_ROOT / _path_from_env(
            "TG_JOIN_QUEUE_CSV",
            "docs/ops/TG_JOIN_QUEUE.csv",
        ),
        daemon_interval_sec=_pos_int("TG_JOIN_DAEMON_INTERVAL_SEC", 3600),
    )


def is_join_night_window(cfg: TgJoinConfig, *, now=None) -> bool:
    return _is_night_window(
        cfg.night_tz,
        cfg.night_start,
        cfg.night_end,
        now=now,
    )


def load_config() -> Config:
    """Читает `.env`, проверяет обязательные поля MVP до сетевых вызовов."""
    load_dotenv(_PROJECT_ROOT / ".env")

    fl_url = _require_str("FL_PROJECTS_URL")
    _validate_http_url(fl_url, "FL_PROJECTS_URL")

    kwork_raw = os.environ.get("KWORK_PROJECTS_URL")
    kwork_url = str(kwork_raw).strip() if kwork_raw is not None else ""
    if kwork_url:
        _validate_http_url(kwork_url, "KWORK_PROJECTS_URL")

    poll_raw = _require_str("POLL_INTERVAL_MINUTES")
    poll_minutes = _parse_poll_interval_minutes(poll_raw)

    token = _require_str("TELEGRAM_BOT_TOKEN")
    chat_id = _require_str("TELEGRAM_CHAT_ID")

    sqlite_path = _path_from_env("SQLITE_PATH", "data/projects.db")
    radar_log_path = _path_from_env("RADAR_LOG_PATH", "data/radar.log")

    ua_raw = os.environ.get("HTTP_USER_AGENT")
    http_user_agent = (
        str(ua_raw).strip()
        if ua_raw and str(ua_raw).strip()
        else "Mozilla/5.0 (compatible; FLRadar/1.0; personal monitoring)"
    )

    tg_proxy_url = _require_proxy_url("TG_PROXY_URL")

    ai_enabled = _parse_bool_flag(os.environ.get("AI_ENABLED"), default=False)
    ai_key_raw = os.environ.get("AI_API_KEY")
    ai_api_key = str(ai_key_raw).strip() if ai_key_raw is not None else ""

    ai_model_raw = os.environ.get("AI_MODEL")
    ai_model = (
        str(ai_model_raw).strip()
        if ai_model_raw and str(ai_model_raw).strip()
        else "google/gemini-2.5-flash-lite"
    )
    summary_raw = os.environ.get("OPENROUTER_MODEL_SUMMARY")
    ai_model_summary = (
        str(summary_raw).strip()
        if summary_raw and str(summary_raw).strip()
        else ai_model
    )
    premium_raw = os.environ.get("OPENROUTER_MODEL_PREMIUM")
    ai_model_premium = (
        str(premium_raw).strip()
        if premium_raw and str(premium_raw).strip()
        else ai_model
    )

    ai_provider = _parse_ai_provider(os.environ.get("AI_PROVIDER"))
    min_budget_rub = _parse_min_budget_rub()
    ai_notify_skip = _parse_bool_flag(os.environ.get("AI_NOTIFY_SKIP"), default=False)
    # 1 = почти все новые заказы идут в ИИ (режет только «стоп»); 0 = нужно слово из «берём»
    filter_wide = _parse_bool_flag(os.environ.get("FILTER_WIDE"), default=True)

    db_raw = os.environ.get("DATABASE_URL")
    database_url = str(db_raw).strip() if db_raw is not None else ""

    return Config(
        fl_projects_url=fl_url,
        kwork_projects_url=kwork_url,
        poll_interval_minutes=poll_minutes,
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        sqlite_path=sqlite_path,
        radar_log_path=radar_log_path,
        http_user_agent=http_user_agent,
        tg_proxy_url=tg_proxy_url,
        ai_enabled=ai_enabled,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
        ai_model_summary=ai_model_summary,
        ai_model_premium=ai_model_premium,
        ai_provider=ai_provider,
        min_budget_rub=min_budget_rub,
        ai_notify_skip=ai_notify_skip,
        filter_wide=filter_wide,
        database_url=database_url,
    )
