#!/usr/bin/env python3
"""SSH/SCP helper for VPS deploy (password or key). Reads VPS_SSH_* from .env."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def connect():
    import paramiko

    host = _env("VPS_SSH_HOST", "62.113.103.231")
    user = _env("VPS_SSH_USER", "root")
    password = _env("VPS_SSH_PASSWORD")
    key_path = _env("VPS_SSH_KEY") or str(Path.home() / ".ssh" / "id_rawlead_vps")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    kwargs: dict = {
        "hostname": host,
        "username": user,
        "timeout": 30,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if password:
        kwargs["password"] = password
    elif key_path and Path(key_path).exists():
        kwargs["key_filename"] = key_path

    client.connect(**kwargs)
    return client


def run(cmd: str, check: bool = True) -> tuple[int, str, str]:
    client = connect()
    try:
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
        del stdin
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        if check and code != 0:
            raise RuntimeError(f"exit {code}: {cmd}\n{out}\n{err}")
        return code, out, err
    finally:
        client.close()


def upload(local: Path, remote: str) -> None:
    client = connect()
    try:
        sftp = client.open_sftp()
        sftp.put(str(local), remote)
        sftp.close()
    finally:
        client.close()


_SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "desktop",
    "data",
    ".cursor",
}
_SKIP_FILES = {".env", ".env.legacy", ".env.site"}

# L1 ingest: менять только вместе (иначе VPS radar TypeError на AiLiteAnalysis).
INGEST_COUPLED_SRC = (
    "ai_analyze.py",
    "l1_pool.py",
    "ai_reasons.py",
    "lead_pipeline.py",
    "pg_storage.py",
    "match_push.py",
    "radar_cycle_log.py",
    "radar_status.py",
    "exchange_health.py",
    "main.py",
    "exchange_proxy.py",
    "exchange_browser_fetch.py",
    "fl_parser.py",
    "kwork_parser.py",
    "tz_attachments.py",
    "l3_human_style.py",
    "health_check.py",
    "config.py",
    "proxy_probe.py",
    "tools_catalog.py",
)


def deploy_ingest_coupled_src(remote_src: str = "/opt/rawlead/src") -> list[str]:
    """Upload INGEST_COUPLED_SRC; return uploaded basenames."""
    uploaded: list[str] = []
    for name in INGEST_COUPLED_SRC:
        local = _ROOT / "src" / name
        if not local.is_file():
            raise FileNotFoundError(local)
        remote = f"{remote_src}/{name}"
        upload(local, remote)
        run(f"chown rawlead:rawlead {remote}")
        uploaded.append(name)
    return uploaded


def sync_project(local_root: Path | None = None, remote_root: str = "/opt/rawlead") -> int:
    """Upload repo from PC (private git on GitHub is not cloneable without token)."""
    root = local_root or _ROOT
    client = connect()
    n = 0
    try:
        sftp = client.open_sftp()

        def ensure_dir(path: str) -> None:
            parts = path.strip("/").split("/")
            cur = ""
            for p in parts:
                cur += "/" + p
                try:
                    sftp.stat(cur)
                except OSError:
                    sftp.mkdir(cur)

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            if rel_dir == ".":
                remote_dir = remote_root
            else:
                remote_dir = f"{remote_root}/{rel_dir}"
            ensure_dir(remote_dir)
            for name in filenames:
                if name in _SKIP_FILES or name.endswith(".pyc"):
                    continue
                local_f = Path(dirpath) / name
                remote_f = f"{remote_dir}/{name}"
                sftp.put(str(local_f), remote_f)
                n += 1
        sftp.close()
    finally:
        client.close()
    return n


def install_pubkey_if_password() -> None:
    """Append local .pub to authorized_keys when logging in with password."""
    password = _env("VPS_SSH_PASSWORD")
    if not password:
        return
    key_path = Path(_env("VPS_SSH_KEY") or (Path.home() / ".ssh" / "id_rawlead_vps"))
    pub = Path(str(key_path) + ".pub")
    if not pub.is_file():
        return
    line = pub.read_text(encoding="utf-8").strip()
    if not line:
        return
    escaped = line.replace("'", "'\"'\"'")
    cmd = (
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
        f"grep -qF '{escaped}' ~/.ssh/authorized_keys 2>/dev/null || "
        f"echo '{escaped}' >> ~/.ssh/authorized_keys && "
        "chmod 600 ~/.ssh/authorized_keys"
    )
    run(cmd)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: deploy_vps_ssh.py <shell command>")
        sys.exit(1)
    _, out, err = run(" ".join(sys.argv[1:]))
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err:
        print(err, file=sys.stderr, end="" if err.endswith("\n") else "\n")
