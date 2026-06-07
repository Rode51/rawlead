#!/usr/bin/env python3
"""Revert L2 prod models: Gemini 2.5 Pro (not Sonnet). O82-w2 regression fix."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_GEMINI_PRO = "google/gemini-2.5-pro"


def _ensure_env_line(key: str, value: str) -> str:
    # sed delimiter | — values contain / (google/gemini-2.5-pro)
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={value}|' /opt/rawlead/.env.site || "
        f"echo '{key}={value}' >> /opt/rawlead/.env.site"
    )


def _dedupe_model_keys() -> str:
    """Remove duplicate PREMIUM/SHARED lines (sed / bug left Sonnet + Gemini)."""
    return (
        "ENV=/opt/rawlead/.env.site && "
        "cp \"$ENV\" \"${ENV}.bak-l2-models-fix\" && "
        "grep -v '^OPENROUTER_MODEL_PREMIUM=' \"$ENV\" "
        "| grep -v '^OPENROUTER_MODEL_SHARED_DRAFT=' > /tmp/env.site.new && "
        "echo 'OPENROUTER_MODEL_PREMIUM=google/gemini-2.5-pro' >> /tmp/env.site.new && "
        "echo 'OPENROUTER_MODEL_SHARED_DRAFT=google/gemini-2.5-pro' >> /tmp/env.site.new && "
        "mv /tmp/env.site.new \"$ENV\" && "
        "chown rawlead:rawlead \"$ENV\" && chmod 600 \"$ENV\""
    )


def main() -> int:
    print("=== fix L2 models on VPS (gemini-2.5-pro, not Sonnet) ===")
    env_cmd = " && ".join(
        [
            _dedupe_model_keys(),
            _ensure_env_line("OPENROUTER_MODEL_PREMIUM", _GEMINI_PRO),
            _ensure_env_line("OPENROUTER_MODEL_SHARED_DRAFT", _GEMINI_PRO),
            "grep -E '^(OPENROUTER_MODEL_SUMMARY|OPENROUTER_MODEL_PREMIUM|OPENROUTER_MODEL_SHARED_DRAFT|OPENROUTER_MODEL_JUDGE)=' "
            "/opt/rawlead/.env.site || true",
            "systemctl restart rawlead-radar rawlead-api",
            "sleep 3",
            "systemctl is-active rawlead-radar rawlead-api",
            "echo l2_models_ok",
        ]
    )
    _, out, err = ssh.run(env_cmd, check=False)
    print(out.strip())
    if err.strip():
        print(err.strip())
    ok = "l2_models_ok" in (out or "") and "active" in (out or "")
    if ok:
        print("DEPLOY OK — L2 = gemini-2.5-pro")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
