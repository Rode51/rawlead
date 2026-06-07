"""O121-w1: /ops/ proxy groups — collect, probe, manual switch."""

from __future__ import annotations

import socket
from typing import Any
from urllib.parse import urlparse

import requests

from config import normalize_proxy_url, radar_timestamp

PROBE_TARGETS: dict[str, str] = {
    "tg-bot": "https://api.telegram.org/",
    "telethon": "https://api.telegram.org/",
    "exchange-fl": "https://www.fl.ru/projects/",
    "exchange-kwork": "https://kwork.ru/projects",
    "exchange-pool": "https://youdo.com/",
}

_SWITCHABLE_GROUPS = frozenset({"tg-bot", "exchange-fl", "exchange-kwork", "exchange-pool"})

PROXY_GROUP_HELP: dict[str, str] = {
    "tg-bot": (
        "@rawlead_bot ходит в Telegram через этот прокси. "
        "Красный = бот может молчать или не слать push."
    ),
    "telethon": (
        "Радар читает TG-группы через acc1/2/3. "
        "Переключить кнопкой пока нельзя — только «Проверить»."
    ),
    "exchange-fl": (
        "Заказы с FL.ru качаются через этот прокси. "
        "Жёлтый/красный = FL в ленте может пропасть."
    ),
    "exchange-kwork": "Заказы с Kwork — то же.",
    "exchange-pool": "Запасной пул для бирж.",
}


def slot_status_label(
    *,
    status: str,
    banned_until: str | None,
    reason_raw: str | None = None,
) -> str:
    """Human-readable proxy slot status for /ops/."""
    raw = (reason_raw or "").strip().lower()
    if "probe_fail" in raw:
        return "Не открывает сайт через прокси"
    if raw == "strikes" or raw.startswith("strikes"):
        return "Много ошибок подряд"
    if banned_until or status == "bad":
        return "Временно отключён (бан)"
    if status == "warn":
        return "Нестабильно — были ошибки"
    return "Работает"

_last_probe_at: str | None = None


def mask(url: str) -> str:
    try:
        n = normalize_proxy_url(url.strip())
    except ValueError:
        return url[:40] + "…" if len(url) > 40 else url
    p = urlparse(n)
    host = p.hostname or "?"
    port = p.port or 8080
    user = p.username or "?"
    return f"{p.scheme}://{user}:***@{host}:{port}"


def tcp_ok(url: str, timeout: float = 8.0) -> tuple[bool, str]:
    try:
        p = urlparse(normalize_proxy_url(url) if "://" in url else url)
        host, port = p.hostname, p.port or 8080
        if not host:
            return False, "no host"
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True, "ok"
    except Exception as e:
        return False, str(e)[:80]


def https_probe(url: str, target: str, timeout: float = 15.0) -> tuple[bool, str]:
    try:
        norm = normalize_proxy_url(url.strip())
        proxies = {"http": norm, "https": norm}
        r = requests.get(
            target,
            proxies=proxies,
            timeout=(5, timeout),
            headers={"User-Agent": "RawLeadProxyProbe/1.0"},
            allow_redirects=True,
        )
        return True, f"HTTP {r.status_code} ({len(r.content)}b)"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


def _probe_target(group_id: str) -> str:
    return PROBE_TARGETS.get(group_id, PROBE_TARGETS["exchange-pool"])


def _run_inline_probe(url: str, group_id: str) -> dict[str, Any]:
    target = _probe_target(group_id)
    tcp_pass, tcp_msg = tcp_ok(url)
    https_pass, https_msg = https_probe(url, target)
    return {
        "tcp": {"ok": tcp_pass, "message": tcp_msg},
        "https": {"ok": https_pass, "message": https_msg, "target": target},
        "ok": tcp_pass and https_pass,
    }


def strip_internal_urls(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove _url from slots before JSON response."""
    out = dict(payload)
    groups: list[dict[str, Any]] = []
    for group in out.get("groups") or []:
        g = dict(group)
        slots: list[dict[str, Any]] = []
        for slot in g.get("slots") or []:
            s = {k: v for k, v in slot.items() if k != "_url"}
            slots.append(s)
        g["slots"] = slots
        groups.append(g)
    out["groups"] = groups
    return out


def collect_proxies_payload() -> dict[str, Any]:
    from exchange_proxy import list_ui_groups
    from tg_proxy_pool import list_telethon_ui_group, list_ui_group

    groups = [list_ui_group(), list_telethon_ui_group()] + list_ui_groups()
    return {
        "auto_failover": True,
        "last_probe_at": _last_probe_at,
        "groups": groups,
    }


def resolve_group_url(group_id: str, slot_1based: int) -> str | None:
    payload = collect_proxies_payload()
    for group in payload.get("groups") or []:
        if str(group.get("id")) != group_id:
            continue
        for slot in group.get("slots") or []:
            if int(slot.get("slot") or 0) == slot_1based:
                return str(slot.get("_url") or "") or None
    return None


def run_proxy_control(
    *,
    action: str,
    group: str = "",
    slot: int | None = None,
) -> dict[str, Any]:
    global _last_probe_at
    act = (action or "").strip().lower()
    grp = (group or "").strip().lower()

    if act == "probe-all":
        results: list[dict[str, Any]] = []
        payload = collect_proxies_payload()
        for group_obj in payload.get("groups") or []:
            gid = str(group_obj.get("id") or "")
            for slot_obj in group_obj.get("slots") or []:
                url = str(slot_obj.get("_url") or "").strip()
                if not url:
                    continue
                slot_n = int(slot_obj.get("slot") or 0)
                probe = _run_inline_probe(url, gid)
                results.append({"group": gid, "slot": slot_n, "probe": probe})
        _last_probe_at = radar_timestamp()
        return {
            "ok": True,
            "message": f"Проверено слотов: {len(results)}",
            "results": results,
        }

    if act == "probe":
        if not grp or slot is None or slot < 1:
            return {"ok": False, "message": "Нужны group и slot (1-based)"}
        url = resolve_group_url(grp, int(slot))
        if not url:
            return {"ok": False, "message": f"Слот {slot} в {grp} не найден"}
        probe = _run_inline_probe(url, grp)
        _last_probe_at = radar_timestamp()
        return {
            "ok": True,
            "message": "Проверка завершена",
            "group": grp,
            "slot": int(slot),
            "probe": probe,
        }

    if act == "switch":
        if not grp or slot is None or slot < 1:
            return {"ok": False, "message": "Нужны group и slot (1-based)"}
        if grp not in _SWITCHABLE_GROUPS:
            return {"ok": False, "message": "Ручное переключение недоступно для этой группы"}
        if grp == "tg-bot":
            from tg_proxy_pool import set_active_slot

            ok, msg = set_active_slot(int(slot))
            payload = collect_proxies_payload()
            out: dict[str, Any] = {"ok": ok, "message": msg}
            if ok:
                out["proxies"] = strip_internal_urls(payload)
            return out
        from exchange_proxy import set_active_slot_manual

        ok, msg = set_active_slot_manual(grp, int(slot))
        payload = collect_proxies_payload()
        return {"ok": ok, "message": msg, "proxies": strip_internal_urls(payload)}

    if act == "clear-bans":
        from exchange_proxy import clear_all_bans as clear_exchange_bans
        from tg_proxy_pool import clear_all_bans as clear_tg_bans

        tg_n = clear_tg_bans()
        ex_n = clear_exchange_bans()
        payload = collect_proxies_payload()
        total = tg_n + ex_n
        if total:
            msg = (
                f"Сбросили {total} записей о банах (TG: {tg_n}, биржи: {ex_n}). "
                "Сейчас перезапустим радар — подожди 10 сек и обнови страницу."
            )
        else:
            msg = (
                "В базе банов не было. Если слот жёлтый/красный — это не бан, "
                "а «прокси не отвечает» или «не настроен». Нажми «Проверить»."
            )
        return {
            "ok": True,
            "message": msg,
            "cleared": total,
            "proxies": strip_internal_urls(payload),
        }

    return {"ok": False, "message": "Unsupported proxy action"}


def run_ops_proxy_control(
    *,
    target: str,
    action: str,
    group: str = "",
    slot: int | None = None,
) -> dict[str, Any]:
    if (target or "").strip().lower() != "proxy":
        return {"ok": False, "message": "Unsupported control target/action"}
    return run_proxy_control(action=action, group=group, slot=slot)
