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
_VALID_RADAR_PROFILES = frozenset({"legacy", "site"})
_PROFILE_DEFAULTS: dict[str, dict[str, str]] = {
    "legacy": {
        "RADAR_LOG_PATH": "data/radar_legacy.log",
        "AI_MODE": "legacy",
        "RADAR_CONTROL_PORT": "18765",
        "RADAR_TG_ENABLED": "0",
        "RADAR_EXCHANGES_ENABLED": "0",
        "FILTERS_MD_PATH": "docs/ops/FILTERS_LEGACY.md",
    },
    "site": {
        "RADAR_LOG_PATH": "data/radar_site.log",
        "AI_MODE": "split",
        "RADAR_CONTROL_PORT": "18775",
        "RADAR_TG_ENABLED": "1",
        "RADAR_EXCHANGES_ENABLED": "1",
        "FILTERS_MD_PATH": "docs/ops/FILTERS_SITE.md",
        "TG_JOIN_QUEUE_CSV": "docs/ops/TG_JOIN_QUEUE_v2.csv",
    },
}

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
    legacy_neon_poll_sec: int
    telegram_bot_token: str
    telegram_chat_id: str
    sqlite_path: Path
    radar_log_path: Path
    http_user_agent: str
    tg_proxy_url: str
    ai_enabled: bool
    ai_api_key: str
    ai_api_key_l1_b: str
    ai_model: str
    ai_model_summary: str
    ai_model_premium: str
    ai_model_shared_draft: str
    ai_model_l3_uniquify: str
    ai_model_judge: str
    ai_provider: str
    min_budget_rub: int
    ai_notify_skip: bool
    filter_wide: bool
    database_url: str
    radar_profile: str
    ai_mode: str
    filters_md_path: Path
    site_notify_on_ai_unavailable: bool
    site_notify_owner: bool
    radar_conveyor: bool
    l1_batch_per_cycle: int
    l1_max_workers: int
    l1_backlog_drain: bool
    match_push_enabled: bool
    stars_enabled: bool
    stars_price_xtr: int
    stars_subscription_days: int
    pay_premium_rub: int
    pay_sbp_phone: str
    pay_sbp_bank: str
    pay_btc_address: str
    pay_eth_address: str
    pay_usdt_trc20_address: str
    pay_usdt_erc20_address: str
    pay_ton_address: str
    pay_crypto_memo_prefix: str
    pay_approve_bot: str

    @property
    def ai_active(self) -> bool:
        """ИИ включён в .env и задан ключ."""
        return self.ai_enabled and bool(self.ai_api_key)

    def l1_openrouter_api_key(self, worker_slot: int) -> str:
        """L1 hot path: чётные воркеры → OPENROUTER_API_KEY_L1_B, нечётные → основной."""
        alt = (self.ai_api_key_l1_b or "").strip()
        if not alt:
            return self.ai_api_key
        slot = max(1, int(worker_slot))
        return alt if slot % 2 == 0 else self.ai_api_key

    @property
    def ai_uses_l1_l2(self) -> bool:
        """SITE: L1 → лента, L2 → бот; LEGACY: один analyze_project."""
        return self.ai_mode == "split"

    @property
    def neon_ingest_wide(self) -> bool:
        """SITE: в Neon до словесного FILTERS_SITE (широкий ingest для legacy consumer)."""
        return self.radar_profile == "site"


def apply_profile_argv(argv: list[str] | None = None) -> None:
    """`--profile legacy|site` до load_config (main/tg_main/radar_control)."""
    if argv is None:
        import sys

        argv = sys.argv
    for i, arg in enumerate(argv):
        if arg == "--profile" and i + 1 < len(argv):
            os.environ["RADAR_PROFILE"] = str(argv[i + 1]).strip().casefold()
            break


def radar_profile() -> str:
    raw = os.environ.get("RADAR_PROFILE", "legacy").strip().casefold()
    if raw not in _VALID_RADAR_PROFILES:
        raise ValueError(
            f"RADAR_PROFILE: ожидается 'legacy' или 'site', получено: {raw!r}"
        )
    return raw


def _apply_profile_defaults(profile: str) -> None:
    for key, value in _PROFILE_DEFAULTS[profile].items():
        if not os.environ.get(key, "").strip():
            os.environ[key] = value


def load_radar_env(*, merge_root_env: bool = True) -> str:
    """Профиль → defaults → `.env.{profile}`; опц. fallback `.env`."""
    if os.environ.get("RADAR_ENV_NO_MERGE", "").strip().lower() in ("1", "true", "yes"):
        merge_root_env = False
    apply_profile_argv()
    profile = radar_profile()
    os.environ["RADAR_PROFILE"] = profile
    _apply_profile_defaults(profile)
    specific = _PROJECT_ROOT / f".env.{profile}"
    fallback = _PROJECT_ROOT / ".env"
    if specific.is_file():
        load_dotenv(specific, override=True)
    if merge_root_env and fallback.is_file():
        load_dotenv(fallback, override=False)
    return profile


def radar_tg_enabled() -> bool:
    """Telethon/tg_main: site=1, legacy=0 (биржи + бот без acc)."""
    load_radar_env()
    profile = radar_profile()
    default = profile == "site"
    return _parse_bool_flag(os.environ.get("RADAR_TG_ENABLED"), default=default)


def radar_exchanges_enabled() -> bool:
    """main.py (FL/Kwork/FH): site=1 (единственный парсер), legacy=0 (Neon consumer)."""
    load_radar_env()
    profile = radar_profile()
    default = profile == "site"
    return _parse_bool_flag(os.environ.get("RADAR_EXCHANGES_ENABLED"), default=default)


def legacy_neon_consumer_enabled() -> bool:
    """Legacy без бирж: читать Neon вместо main.py."""
    load_radar_env()
    return radar_profile() == "legacy" and not radar_exchanges_enabled()


def filters_md_path() -> Path:
    raw = os.environ.get("FILTERS_MD_PATH", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else _PROJECT_ROOT / path
    name = (
        "FILTERS_LEGACY.md" if radar_profile() == "legacy" else "FILTERS_SITE.md"
    )
    return _PROJECT_ROOT / "docs" / "ops" / name


def radar_lock_path(name: str) -> Path:
    """Lock-файл с суффиксом профиля: main, tg_main, bot_poll, radar_desktop, radar_ops."""
    profile = radar_profile()
    return _PROJECT_ROOT / "data" / f".{name}_{profile}.lock"


def bot_poll_lock_path(bot_token: str) -> Path:
    """Lock getUpdates — один poller на bot token (Site/Legacy не делят offset и poll)."""
    token = (bot_token or "").strip()
    bot_id = token.split(":", 1)[0] if token else ""
    if not bot_id.isdigit():
        bot_id = "0"
    return _PROJECT_ROOT / "data" / f".bot_poll_{bot_id}.lock"


def bot_poll_external() -> bool:
    """VPS: polling в rawlead-bot-poll.service — main/tg_main не дублируют getUpdates."""
    raw = os.environ.get("RAWLEAD_BOT_POLL_EXTERNAL", "").strip().casefold()
    return raw in ("1", "true", "yes", "on")


def _parse_ai_mode(raw: str | None, *, profile: str) -> str:
    if raw is None or not str(raw).strip():
        return _PROFILE_DEFAULTS[profile]["AI_MODE"]
    mode = str(raw).strip().casefold()
    if mode not in ("legacy", "split"):
        raise ValueError(
            f"AI_MODE: ожидается 'legacy' или 'split', получено: {raw!r}"
        )
    return mode


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


def _parse_poll_interval_minutes(raw: str, *, min_minutes: int = 10) -> int:
    try:
        n = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"POLL_INTERVAL_MINUTES: ожидается целое число минут, получено: {raw!r}"
        ) from exc
    if n < min_minutes:
        raise ValueError(
            f"POLL_INTERVAL_MINUTES: минимум {min_minutes} мин, получено: {n}"
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


def telegram_requests_proxies(cfg: Config) -> dict[str, str | None]:
    """Прокси только для Bot API; парсеры FL/Kwork/Avito его не используют."""
    from tg_proxy_pool import get_active_proxies_dict

    _ = cfg  # пул из env; cfg.tg_proxy_url — fallback внутри get_active_proxies_dict
    return get_active_proxies_dict()


# Явно без прокси — не брать HTTP_PROXY/HTTPS_PROXY из окружения ОС.
DIRECT_REQUESTS_PROXIES: dict[str, None] = {"http": None, "https": None}

_openrouter_proxy_cache: list[str] | None = None


def _load_openrouter_proxy_urls() -> list[str]:
    """O135: OpenRouter-only pool (OPENROUTER_HTTP_PROXY / OPENROUTER_PROXY_URLS)."""
    urls: list[str] = []
    single = os.environ.get("OPENROUTER_HTTP_PROXY", "").strip()
    if single:
        try:
            urls.append(normalize_proxy_url(single))
        except ValueError:
            pass
    multi = os.environ.get("OPENROUTER_PROXY_URLS", "").strip()
    if multi:
        for part in multi.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                urls.append(normalize_proxy_url(part))
            except ValueError:
                continue
    return urls


def openrouter_proxy_urls() -> list[str]:
    global _openrouter_proxy_cache
    if _openrouter_proxy_cache is None:
        _openrouter_proxy_cache = _load_openrouter_proxy_urls()
    return _openrouter_proxy_cache


def openrouter_proxy_hint() -> str:
    """Host:port for startup log — no credentials."""
    urls = openrouter_proxy_urls()
    if not urls:
        return "direct"
    try:
        parsed = urlparse(urls[0])
        host = parsed.hostname or "?"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return f"{host}:{port}"
    except Exception:
        return "set"


def openrouter_requests_proxies(*, slot: int = 0) -> dict[str, str | None]:
    urls = openrouter_proxy_urls()
    if not urls:
        return DIRECT_REQUESTS_PROXIES
    url = urls[slot % len(urls)]
    return {"http": url, "https": url}


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
    load_radar_env()

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
    load_radar_env()

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
    """Читает `.env.{profile}` / `.env`, проверяет обязательные поля MVP."""
    profile = load_radar_env()

    fl_url = _require_str("FL_PROJECTS_URL")
    _validate_http_url(fl_url, "FL_PROJECTS_URL")

    kwork_raw = os.environ.get("KWORK_PROJECTS_URL")
    kwork_url = str(kwork_raw).strip() if kwork_raw is not None else ""
    if kwork_url:
        _validate_http_url(kwork_url, "KWORK_PROJECTS_URL")

    poll_raw = _require_str("POLL_INTERVAL_MINUTES")
    radar_conveyor = _parse_bool_flag(os.environ.get("RADAR_CONVEYOR"), default=False)
    min_poll = 1 if profile == "site" and radar_conveyor else 10
    poll_minutes = _parse_poll_interval_minutes(poll_raw, min_minutes=min_poll)
    if profile == "legacy":
        legacy_poll_raw = os.environ.get("LEGACY_NEON_POLL_SEC", "60").strip()
        try:
            legacy_neon_poll_sec = max(30, min(3600, int(legacy_poll_raw)))
        except ValueError:
            legacy_neon_poll_sec = 60
    else:
        legacy_neon_poll_sec = max(60, poll_minutes * 60)
    l1_batch_raw = os.environ.get("L1_BATCH_PER_CYCLE", "40").strip()
    try:
        l1_batch_per_cycle = max(1, min(500, int(l1_batch_raw)))
    except ValueError:
        l1_batch_per_cycle = 40
    l1_workers_raw = os.environ.get("L1_MAX_WORKERS", "3").strip()
    try:
        l1_max_workers = max(1, min(16, int(l1_workers_raw)))
    except ValueError:
        l1_max_workers = 3
    l1_backlog_drain = _parse_bool_flag(
        os.environ.get("L1_BACKLOG_DRAIN"),
        default=False,
    )

    token = _require_str("TELEGRAM_BOT_TOKEN")
    chat_id = _require_str("TELEGRAM_CHAT_ID")

    sqlite_path = _path_from_env("SQLITE_PATH", "data/projects.db")
    radar_log_path = _path_from_env("RADAR_LOG_PATH", "data/radar.log")

    ua_raw = os.environ.get("HTTP_USER_AGENT")
    http_user_agent = (
        str(ua_raw).strip()
        if ua_raw and str(ua_raw).strip()
        else (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    )

    tg_proxy_url = _require_proxy_url("TG_PROXY_URL")

    ai_enabled = _parse_bool_flag(os.environ.get("AI_ENABLED"), default=False)
    ai_key_raw = os.environ.get("AI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    ai_api_key = str(ai_key_raw).strip() if ai_key_raw is not None else ""
    ai_key_b_raw = os.environ.get("OPENROUTER_API_KEY_L1_B", "").strip()
    ai_api_key_l1_b = str(ai_key_b_raw).strip() if ai_key_b_raw else ""

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
    shared_raw = os.environ.get("OPENROUTER_MODEL_SHARED_DRAFT")
    ai_model_shared_draft = (
        str(shared_raw).strip()
        if shared_raw and str(shared_raw).strip()
        else ai_model_premium
    )
    l3_uniquify_raw = os.environ.get("OPENROUTER_MODEL_L3_UNIQUIFY")
    ai_model_l3_uniquify = (
        str(l3_uniquify_raw).strip()
        if l3_uniquify_raw and str(l3_uniquify_raw).strip()
        else ai_model_shared_draft
    )
    judge_raw = os.environ.get("OPENROUTER_MODEL_JUDGE")
    ai_model_judge = (
        str(judge_raw).strip()
        if judge_raw and str(judge_raw).strip()
        else "anthropic/claude-sonnet-4"
    )

    ai_provider = _parse_ai_provider(os.environ.get("AI_PROVIDER"))
    min_budget_rub = _parse_min_budget_rub()
    ai_notify_skip = _parse_bool_flag(os.environ.get("AI_NOTIFY_SKIP"), default=False)
    # 1 = почти все новые заказы идут в ИИ (режет только «стоп»); 0 = нужно слово из «берём»
    filter_wide = _parse_bool_flag(os.environ.get("FILTER_WIDE"), default=True)

    db_raw = os.environ.get("DATABASE_URL")
    database_url = str(db_raw).strip() if db_raw is not None else ""

    ai_mode = _parse_ai_mode(os.environ.get("AI_MODE"), profile=profile)
    filters_path = filters_md_path()
    site_notify_on_ai_unavailable = _parse_bool_flag(
        os.environ.get("SITE_NOTIFY_ON_AI_UNAVAILABLE"),
        default=False,
    )
    site_notify_owner = _parse_bool_flag(
        os.environ.get("SITE_NOTIFY_OWNER"),
        default=False,
    )

    match_push_enabled = _parse_bool_flag(
        os.environ.get("MATCH_PUSH"),
        default=False,
    )
    stars_enabled = _parse_bool_flag(
        os.environ.get("STARS_ENABLED"),
        default=False,
    )
    stars_price_raw = os.environ.get("STARS_PRICE_XTR", "600").strip()
    try:
        stars_price_xtr = max(1, int(stars_price_raw))
    except ValueError:
        stars_price_xtr = 600
    stars_days_raw = os.environ.get("STARS_SUBSCRIPTION_DAYS", "30").strip()
    try:
        stars_subscription_days = max(1, min(365, int(stars_days_raw)))
    except ValueError:
        stars_subscription_days = 30

    pay_rub_raw = os.environ.get("PAY_PREMIUM_RUB", "790").strip()
    try:
        pay_premium_rub = max(0, int(pay_rub_raw))
    except ValueError:
        pay_premium_rub = 790
    pay_sbp_phone = str(os.environ.get("PAY_SBP_PHONE") or "").strip()
    pay_sbp_bank = str(os.environ.get("PAY_SBP_BANK") or "T-Bank").strip()
    pay_btc_address = str(os.environ.get("PAY_BTC_ADDRESS") or "").strip()
    pay_eth_address = str(os.environ.get("PAY_ETH_ADDRESS") or "").strip()
    pay_usdt_trc20_address = str(os.environ.get("PAY_USDT_TRC20_ADDRESS") or "").strip()
    pay_usdt_erc20_address = str(os.environ.get("PAY_USDT_ERC20_ADDRESS") or "").strip()
    pay_ton_address = str(os.environ.get("PAY_TON_ADDRESS") or "").strip()
    pay_crypto_memo_prefix = str(os.environ.get("PAY_CRYPTO_MEMO_PREFIX") or "RL").strip()
    pay_approve_bot = str(os.environ.get("PAY_APPROVE_BOT") or "legacy").strip()

    return Config(
        fl_projects_url=fl_url,
        kwork_projects_url=kwork_url,
        poll_interval_minutes=poll_minutes,
        legacy_neon_poll_sec=legacy_neon_poll_sec,
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        sqlite_path=sqlite_path,
        radar_log_path=radar_log_path,
        http_user_agent=http_user_agent,
        tg_proxy_url=tg_proxy_url,
        ai_enabled=ai_enabled,
        ai_api_key=ai_api_key,
        ai_api_key_l1_b=ai_api_key_l1_b,
        ai_model=ai_model,
        ai_model_summary=ai_model_summary,
        ai_model_premium=ai_model_premium,
        ai_model_shared_draft=ai_model_shared_draft,
        ai_model_l3_uniquify=ai_model_l3_uniquify,
        ai_model_judge=ai_model_judge,
        ai_provider=ai_provider,
        min_budget_rub=min_budget_rub,
        ai_notify_skip=ai_notify_skip,
        filter_wide=filter_wide,
        database_url=database_url,
        radar_profile=profile,
        ai_mode=ai_mode,
        filters_md_path=filters_path,
        site_notify_on_ai_unavailable=site_notify_on_ai_unavailable,
        site_notify_owner=site_notify_owner,
        radar_conveyor=radar_conveyor,
        l1_batch_per_cycle=l1_batch_per_cycle,
        l1_max_workers=l1_max_workers,
        l1_backlog_drain=l1_backlog_drain,
        match_push_enabled=match_push_enabled,
        stars_enabled=stars_enabled,
        stars_price_xtr=stars_price_xtr,
        stars_subscription_days=stars_subscription_days,
        pay_premium_rub=pay_premium_rub,
        pay_sbp_phone=pay_sbp_phone,
        pay_sbp_bank=pay_sbp_bank,
        pay_btc_address=pay_btc_address,
        pay_eth_address=pay_eth_address,
        pay_usdt_trc20_address=pay_usdt_trc20_address,
        pay_usdt_erc20_address=pay_usdt_erc20_address,
        pay_ton_address=pay_ton_address,
        pay_crypto_memo_prefix=pay_crypto_memo_prefix,
        pay_approve_bot=pay_approve_bot,
    )


def load_config_for_profile(
    profile: str,
    *,
    merge_root_env: bool = True,
) -> Config:
    """Загрузить `.env.{profile}` без смены процесса (ops-алерты site → legacy бот)."""
    prev = os.environ.get("RADAR_PROFILE")
    prev_no_merge = os.environ.get("RADAR_ENV_NO_MERGE")
    prof = profile.strip().casefold()
    os.environ["RADAR_PROFILE"] = prof
    if not merge_root_env:
        os.environ["RADAR_ENV_NO_MERGE"] = "1"
    try:
        return load_config()
    finally:
        if prev is None:
            os.environ.pop("RADAR_PROFILE", None)
        else:
            os.environ["RADAR_PROFILE"] = prev
        if prev_no_merge is None:
            os.environ.pop("RADAR_ENV_NO_MERGE", None)
        else:
            os.environ["RADAR_ENV_NO_MERGE"] = prev_no_merge
