from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import load_config
from pg_storage import pg_storage_from_config


def _write_report(payload: dict) -> Path:
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"ingest_lag_{stamp}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print("DATABASE_URL is not configured")
        return 1
    lag_24h = pg.ingest_lag_report(lookback_hours=24)
    lag_7d = pg.ingest_lag_report(lookback_hours=24 * 7)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "windows": {
            "24h": lag_24h,
            "7d": lag_7d,
        },
        # Backward-compat for existing consumers.
        "hours_24": lag_24h,
        "hours_168": lag_7d,
    }
    out = _write_report(payload)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
