#!/usr/bin/env python3
"""O133-TZ-SMOKE deploy: FL/Kwork TZ session cookies + auth detail fetch."""
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

_RADAR_FILES = (
    "src/tz_attachments.py",
    "src/tz_session.py",
)

_COOKIE_FILES = (
    ("data/kwork_tz_cookies.json", "/opt/rawlead/data/kwork_tz_cookies.json"),
    ("data/fl_tz_cookies.json", "/opt/rawlead/data/fl_tz_cookies.json"),
)

_ENV_KEYS = (
    "FL_TZ_EMAIL",
    "FL_TZ_PASSWORD",
    "KWORK_TZ_EMAIL",
    "KWORK_TZ_PASSWORD",
    "KWORK_TZ_SESSION",
    "FL_TZ_SESSION",
)

_VPS_SESSION_PATHS = {
    "KWORK_TZ_SESSION": "/opt/rawlead/data/kwork_tz_cookies.json",
    "FL_TZ_SESSION": "/opt/rawlead/data/fl_tz_cookies.json",
}


def _sync_env_keys_vps() -> None:
    pairs: list[tuple[str, str]] = []
    for key in _ENV_KEYS:
        val = (os.environ.get(key) or "").strip()
        if key in _VPS_SESSION_PATHS and (_ROOT / _VPS_SESSION_PATHS[key].replace("/opt/rawlead/", "")).is_file():
            val = _VPS_SESSION_PATHS[key]
        if val:
            pairs.append((key, val))
    if not pairs:
        print("WARN: no TZ creds/session keys to sync")
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


def _upload_cookie_files() -> None:
    ssh.run("mkdir -p /opt/rawlead/data", check=False)
    uploaded: list[str] = []
    for rel, remote in _COOKIE_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print(f"WARN: missing {rel} — skip upload")
            continue
        ssh.upload(local, remote)
        uploaded.append(remote)
        print("up", rel)
    if uploaded:
        ssh.run("chown rawlead:rawlead " + " ".join(uploaded), check=False)


def _purge_freelancehunt_env_vps() -> None:
    remote_py = """python3 <<'PYEOF'
import re
from pathlib import Path
for name in (".env", ".env.site", ".env.legacy"):
    p = Path("/opt/rawlead") / name
    if not p.is_file():
        continue
    lines_out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if re.match(r"^FREELANCEHUNT_", line):
            continue
        if line.startswith("PUBLIC_FEED_SOURCES="):
            val = line.split("=", 1)[1]
            parts = [x for x in val.split(",") if x.strip().lower() != "freelancehunt"]
            line = "PUBLIC_FEED_SOURCES=" + ",".join(parts)
        lines_out.append(line)
    p.write_text("\\n".join(lines_out) + ("\\n" if lines_out else ""), encoding="utf-8")
    print("purged_fh", name)
PYEOF"""
    _, out, err = ssh.run(remote_py, check=False)
    text = (out or "") + (err or "")
    print("fh purge:", "OK" if "purged_fh" in text else "CHECK")


def main() -> int:
    print("=== O133-TZ-SMOKE deploy ===")
    _upload_cookie_files()
    _sync_env_keys_vps()
    _purge_freelancehunt_env_vps()

    remotes: list[str] = []
    for rel in _RADAR_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && "
        "grep -c _fl_session_ready /opt/rawlead/src/tz_session.py && "
        "grep -c fetch_detail_html_with_auth /opt/rawlead/src/tz_session.py && "
        "grep -c find_kwork_embedded_attachment_urls /opt/rawlead/src/tz_attachments.py && "
        "echo o133_tz_smoke_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    if "o133_tz_smoke_ok" not in text or "active" not in text:
        print("DEPLOY CHECK — verify tz_session/tz_attachments on VPS")
        return 1
    print("RADAR DEPLOY OK — smoke owner #3193806 on next ingest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
