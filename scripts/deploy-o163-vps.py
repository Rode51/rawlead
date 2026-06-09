#!/usr/bin/env python3
"""O163+O162+O133 deploy: TG gate, L2 guards, TZ session, O161 ops (API+radar)."""
from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)

_API_FILES = (
    "src/owner_admin.py",
    "src/api_server.py",
    "src/ops_log_stream.py",
    "src/draft_async.py",
)
_RADAR_FILES = (
    "src/main.py",
    "src/lead_pipeline.py",
    "src/tg_spam_filter.py",
    "src/ai_analyze.py",
    "src/tz_attachments.py",
    "src/tz_session.py",
)

_ENV_KEYS = (
    "RAWLEAD_OPS_KEY",
    "OPS_PASSWORD",
    "FL_TZ_EMAIL",
    "FL_TZ_PASSWORD",
    "KWORK_TZ_EMAIL",
    "KWORK_TZ_PASSWORD",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def _sync_env_keys_vps() -> None:
    """Mirror selected keys from local .env → /opt/rawlead/.env (no echo values)."""
    ops_pwd = (os.environ.get("OPS_PASSWORD") or os.environ.get("RAWLEAD_OPS_KEY") or "").strip()
    pairs: list[tuple[str, str]] = []
    if ops_pwd:
        pairs.append(("RAWLEAD_OPS_KEY", ops_pwd))
    for key in ("FL_TZ_EMAIL", "FL_TZ_PASSWORD", "KWORK_TZ_EMAIL", "KWORK_TZ_PASSWORD"):
        val = (os.environ.get(key) or "").strip()
        if val:
            pairs.append((key, val))
    if not pairs:
        print("WARN: no env keys to sync")
        return
    payload = base64.b64encode(
        "\n".join(f"{k}={v}" for k, v in pairs).encode("utf-8")
    ).decode("ascii")
    remote_py = f"""python3 <<'PYEOF'
import base64, re
from pathlib import Path
p = Path("/opt/rawlead/.env")
text = p.read_text(encoding="utf-8")
block = base64.b64decode("{payload}").decode("utf-8")
for line in block.splitlines():
    if "=" not in line:
        continue
    key, val = line.split("=", 1)
    pat = rf"^{{re.escape(key)}}=.*$"
    repl = key + "=" + val
    if re.search(pat, text, re.M):
        text = re.sub(pat, repl, text, flags=re.M)
    else:
        text = text.rstrip() + "\\n" + repl + "\\n"
p.write_text(text, encoding="utf-8")
print("env_synced", len(block.splitlines()))
PYEOF"""
    _, out, err = ssh.run(remote_py, check=False)
    text = (out or "") + (err or "")
    print("env sync:", "OK" if "env_synced" in text else "CHECK")


def main() -> int:
    print("=== O163 deploy: TG gate + L2 + TZ session + ops ===")
    _sync_env_keys_vps()

    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))
    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c ops_login_html /opt/rawlead/src/owner_admin.py && "
        "grep -c iter_radar_log_sse /opt/rawlead/src/ops_log_stream.py && "
        "grep -c '/ops/login' /opt/rawlead/src/api_server.py && "
        "echo o163_api_ok",
        check=False,
    )
    print(out_api.strip())
    if "o163_api_ok" not in (out_api or "") or "active" not in (out_api or ""):
        print("API DEPLOY CHECK")
        return 1
    print("API DEPLOY OK")

    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))
    _, out_radar, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && "
        "grep -c is_tg_spam /opt/rawlead/src/tg_spam_filter.py && "
        "grep -c process_new_listing_from_tg /opt/rawlead/src/lead_pipeline.py && "
        "test -f /opt/rawlead/src/tz_session.py && "
        "echo o163_radar_ok",
        check=False,
    )
    print(out_radar.strip())
    if "o163_radar_ok" not in (out_radar or "") or "active" not in (out_radar or ""):
        print("RADAR DEPLOY CHECK")
        return 1
    print("RADAR DEPLOY OK")
    print("DEPLOY OK — smoke: /ops/ login · TG без raw forward · draft #5508756-like")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
