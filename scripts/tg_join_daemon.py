"""DEPRECATED: join для всех monitor acc внутри scripts/tg_main.py (TG_JOIN_IN_TG_MAIN=1)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import load_tg_join_config  # noqa: E402
from tg_join_runner import log_join  # noqa: E402


def main() -> None:
    cfg = load_tg_join_config()
    msg = (
        "join:daemon:deprecated — используйте scripts/tg_main.py "
        "(TG_JOIN_IN_TG_MAIN=1, join для всех TELETHON_MONITOR_ACCOUNTS)"
    )
    log_join(cfg, msg)
    print(msg, flush=True)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
