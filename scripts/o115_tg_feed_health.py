#!/usr/bin/env python3
"""O115: health-check TG ingest → Neon → /lenta/ (local Neon + optional VPS SSH).

  python scripts/o115_tg_feed_health.py
  python scripts/o115_tg_feed_health.py --vps
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402

apply_profile_argv(["--profile", "site"])


def _neon_tg_stats(cfg) -> dict[str, object]:
    import os

    import psycopg

    url = (cfg.database_url or os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL не задан")

    out: dict[str, object] = {}
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*), max(created_at) FROM leads "
                "WHERE source LIKE 'tg:%%' AND is_visible = true"
            )
            vis_all, last_vis = cur.fetchone()
            cur.execute(
                "SELECT count(*), max(created_at) FROM leads "
                "WHERE source LIKE 'tg:%%' AND created_at >= now() - interval '24 hours'"
            )
            any_24h, last_any = cur.fetchone()
            cur.execute(
                "SELECT count(*) FROM leads "
                "WHERE source LIKE 'tg:%%' AND is_visible = true "
                "AND created_at >= now() - interval '24 hours'"
            )
            vis_24h = cur.fetchone()[0]
            cur.execute(
                "SELECT id, source, created_at::text FROM leads "
                "WHERE source LIKE 'tg:%%' ORDER BY created_at DESC LIMIT 3"
            )
            recent = cur.fetchall()
    out["tg_visible_all"] = int(vis_all or 0)
    out["tg_last_visible_at"] = str(last_vis or "")
    out["tg_any_24h"] = int(any_24h or 0)
    out["tg_visible_24h"] = int(vis_24h or 0)
    out["tg_last_any_at"] = str(last_any or "")
    out["tg_recent"] = recent
    return out


def _vps_probe() -> str:
    try:
        import deploy_vps_ssh as ssh  # noqa: E402
    except ImportError as exc:
        return f"VPS skip: {exc}"

    chunks: list[str] = []
    for label, cmd in (
        ("radar", "systemctl is-active rawlead-radar 2>/dev/null || echo inactive"),
        (
            "tg_log",
            "tail -15 /opt/rawlead/data/radar_site_tg.log 2>/dev/null || echo no_tg_log",
        ),
        (
            "tg_proc",
            "pgrep -af 'tg_main.py' 2>/dev/null | head -3 || echo no_tg_main",
        ),
        (
            "feed_tg",
            "curl -sf 'http://127.0.0.1:8000/v1/feed?limit=3' 2>/dev/null | "
            "python3 -c \"import sys,json; d=json.load(sys.stdin); "
            "print([x.get('source') for x in (d.get('items') or [])[:5]])\" "
            "2>/dev/null || echo feed_curl_fail",
        ),
    ):
        _, out, _ = ssh.run(cmd, check=False)
        chunks.append(f"--- {label} ---\n{(out or '').strip()}")
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description="O115 TG feed health")
    parser.add_argument("--vps", action="store_true", help="SSH: tg_main log + radar status")
    args = parser.parse_args()

    load_radar_env()
    cfg = load_config()
    import os

    feed = (os.environ.get("PUBLIC_FEED_SOURCES") or "")[:160]
    tg_n = sum(1 for p in feed.split(",") if p.strip().startswith("tg:"))
    print(f"PUBLIC_FEED_SOURCES tg_channels={tg_n}")
    print(f"snippet: {feed!r}")

    stats = _neon_tg_stats(cfg)
    print(f"neon tg_visible_all={stats['tg_visible_all']} last_visible={stats['tg_last_visible_at']}")
    print(f"neon tg_any_24h={stats['tg_any_24h']} tg_visible_24h={stats['tg_visible_24h']}")
    print(f"neon tg_last_any={stats['tg_last_any_at']}")
    for row in stats["tg_recent"]:
        print(f"  recent id={row[0]} {row[1]} {row[2]}")

    ok_24h = int(stats["tg_any_24h"]) >= 1
    if not ok_24h:
        print("WARN: нет новых tg-лидов за 24ч — проверь VPS tg_main / listen chats")
    else:
        print("OK: есть tg ingest за 24ч")

    if args.vps:
        print("\n=== VPS ===")
        print(_vps_probe())

    return 0 if ok_24h else 1


if __name__ == "__main__":
    raise SystemExit(main())
