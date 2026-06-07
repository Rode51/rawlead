"""O105-w1: Premium pay — СБП / crypto pending + owner approve via @FLPARSINGBOT."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import psycopg
import requests

from config import Config, load_config_for_profile, telegram_requests_proxies
from stars_billing import activate_subscription

logger = logging.getLogger(__name__)

_OWNER_CALLBACK_RE = re.compile(r"^p(ok|nx):(\d+)$")

_MENU_TEXT = """RawLead Premium — ИИ-агент на месяц

📥 Лента без задержки — заказы сразу
✍️ Уникальный черновик отклика под твой профиль
🔒 До 10 откликов на один заказ — без каннибализма

{price_rub} ₽ / мес

Выбери способ оплаты:"""


class PayRates:
    def __init__(
        self,
        usdt_rub: Decimal | None,
        ton_rub: Decimal | None,
        btc_rub: Decimal | None,
        eth_rub: Decimal | None,
    ) -> None:
        self.usdt_rub = usdt_rub
        self.ton_rub = ton_rub
        self.btc_rub = btc_rub
        self.eth_rub = eth_rub

    def usdt_for_rub(self, rub: int) -> Decimal | None:
        if self.usdt_rub and self.usdt_rub > 0:
            return (Decimal(rub) / self.usdt_rub).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return None

    def ton_for_rub(self, rub: int) -> Decimal | None:
        if self.ton_rub and self.ton_rub > 0:
            return (Decimal(rub) / self.ton_rub).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return None

    def to_json(self) -> dict[str, float]:
        out: dict[str, float] = {}
        if self.usdt_rub:
            out["usdt_rub"] = float(self.usdt_rub)
        if self.ton_rub:
            out["ton_rub"] = float(self.ton_rub)
        if self.btc_rub:
            out["btc_rub"] = float(self.btc_rub)
        if self.eth_rub:
            out["eth_rub"] = float(self.eth_rub)
        return out


def pay_available(cfg: Config) -> bool:
    return (
        cfg.pay_premium_rub > 0
        and bool(cfg.database_url.strip())
        and (
            bool(cfg.pay_sbp_phone.strip())
            or bool(cfg.pay_usdt_trc20_address.strip())
            or bool(cfg.pay_ton_address.strip())
            or bool(cfg.pay_btc_address.strip())
        )
    )


def fetch_pay_rates() -> PayRates:
    """Курс на момент оплаты (CoinGecko, best-effort)."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "tether,the-open-network,bitcoin,ethereum",
        "vs_currencies": "rub",
    }
    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            return PayRates(None, None, None, None)
        data = resp.json()
        if not isinstance(data, dict):
            return PayRates(None, None, None, None)

        def _rate(coin: str) -> Decimal | None:
            block = data.get(coin)
            if not isinstance(block, dict):
                return None
            raw = block.get("rub")
            if raw is None:
                return None
            try:
                val = Decimal(str(raw))
                return val if val > 0 else None
            except Exception:
                return None

        return PayRates(
            usdt_rub=_rate("tether"),
            ton_rub=_rate("the-open-network"),
            btc_rub=_rate("bitcoin"),
            eth_rub=_rate("ethereum"),
        )
    except requests.RequestException as exc:
        logger.warning("pay:rates: %s", exc)
        return PayRates(None, None, None, None)


def _inline_markup(rows: list[list[dict[str, str]]]) -> str:
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)


def pay_menu_markup(cfg: Config) -> str:
    rows: list[list[dict[str, str]]] = []
    if cfg.pay_sbp_phone.strip():
        rows.append([{"text": "💳 Банковская карта РФ / СБП", "callback_data": "pay:sbp"}])
    if _crypto_configured(cfg):
        rows.append([{"text": "🪙 Crypto (USDT / TON)", "callback_data": "pay:crypto"}])
    if cfg.stars_enabled:
        rows.append(
            [{"text": f"⭐ Telegram Stars ({cfg.stars_price_xtr} ⭐)", "callback_data": "pay:stars"}]
        )
    return _inline_markup(rows)


def _crypto_configured(cfg: Config) -> bool:
    return bool(
        cfg.pay_usdt_trc20_address.strip()
        or cfg.pay_usdt_erc20_address.strip()
        or cfg.pay_ton_address.strip()
        or cfg.pay_btc_address.strip()
        or cfg.pay_eth_address.strip()
    )


def format_pay_menu(cfg: Config) -> str:
    return _MENU_TEXT.format(price_rub=cfg.pay_premium_rub)


def format_sbp_screen(cfg: Config, tg_user_id: int, pending_id: int) -> str:
    bank = cfg.pay_sbp_bank.strip() or "банк"
    return (
        f"Генерация инвойса для User #{tg_user_id}…\n\n"
        f"Сумма к оплате: {cfg.pay_premium_rub} ₽\n\n"
        f"Реквизиты (СБП):\n"
        f"{cfg.pay_sbp_phone.strip()}\n"
        f"{bank}\n\n"
        f"После перевода нажми «Проверить оплату» — сверим вручную.\n"
        f"Заявка #{pending_id}"
    )


def format_crypto_screen(
    cfg: Config,
    tg_user_id: int,
    pending_id: int,
    rates: PayRates,
    *,
    amount_usdt: Decimal | None,
    amount_ton: Decimal | None,
) -> str:
    memo = f"{cfg.pay_crypto_memo_prefix.strip() or 'RL'}{tg_user_id}"
    lines = [
        f"Инвойс User #{tg_user_id}",
        "",
        f"{cfg.pay_premium_rub} ₽",
    ]
    if amount_usdt is not None:
        lines.append(f"≈ {amount_usdt} USDT (TRC20)")
    if amount_ton is not None:
        lines.append(f"или {amount_ton} TON")
    lines.append("")
    addr = cfg.pay_usdt_trc20_address.strip()
    if addr:
        lines.extend(["USDT (TRC20):", addr, ""])
    addr = cfg.pay_usdt_erc20_address.strip()
    if addr:
        lines.extend(["USDT (ERC20):", addr, ""])
    addr = cfg.pay_ton_address.strip()
    if addr:
        lines.extend(["TON:", addr, ""])
    addr = cfg.pay_btc_address.strip()
    if addr and rates.btc_rub:
        btc = (Decimal(cfg.pay_premium_rub) / rates.btc_rub).quantize(
            Decimal("0.00000001"), ROUND_HALF_UP
        )
        lines.extend([f"BTC (~{btc}):", addr, ""])
    elif cfg.pay_btc_address.strip():
        lines.extend(["BTC:", cfg.pay_btc_address.strip(), ""])
    addr = cfg.pay_eth_address.strip()
    if addr and rates.eth_rub:
        eth = (Decimal(cfg.pay_premium_rub) / rates.eth_rub).quantize(
            Decimal("0.0001"), ROUND_HALF_UP
        )
        lines.extend([f"ETH (~{eth}):", addr, ""])
    elif cfg.pay_eth_address.strip():
        lines.extend(["ETH:", cfg.pay_eth_address.strip(), ""])
    lines.extend(
        [
            f"В комментарии к переводу укажи: {memo}",
            "",
            "После перевода — «Проверить оплату».",
            f"Заявка #{pending_id}",
            "",
            "Оплата с Trust Wallet или MetaMask — скопируй адрес вручную.",
        ]
    )
    return "\n".join(lines)


def _change_method_row() -> dict[str, str]:
    return {"text": "← Изменить способ оплаты", "callback_data": "pay:menu"}


def sbp_action_markup(pending_id: int) -> str:
    return _inline_markup(
        [
            [{"text": "Проверить оплату", "callback_data": f"pay:chk:{pending_id}"}],
            [_change_method_row()],
        ]
    )


def crypto_action_markup(cfg: Config, pending_id: int) -> str:
    rows: list[list[dict[str, str]]] = [
        [{"text": "Проверить оплату", "callback_data": f"pay:chk:{pending_id}"}],
    ]
    if cfg.pay_usdt_trc20_address.strip():
        rows.append(
            [{"text": "Скопировать адрес USDT", "callback_data": f"pay:cpy:usdt:{pending_id}"}]
        )
    if cfg.pay_ton_address.strip():
        rows.append(
            [{"text": "Скопировать адрес TON", "callback_data": f"pay:cpy:ton:{pending_id}"}]
        )
    rows.append([_change_method_row()])
    return _inline_markup(rows)


def format_stars_intro(cfg: Config) -> str:
    return (
        "RawLead Premium — ИИ-агент на 30 дней\n\n"
        f"Оплата: {cfg.stars_price_xtr} Telegram Stars "
        "(~800–1440 ₽ при покупке Stars).\n\n"
        "Кнопка «Оплатить» откроет счёт Telegram — язык кнопки "
        "зависит от языка приложения Telegram."
    )


def stars_intro_markup(cfg: Config) -> str:
    return _inline_markup(
        [
            [{"text": f"⭐ Оплатить {cfg.stars_price_xtr} Stars", "callback_data": "pay:stinv"}],
            [_change_method_row()],
        ]
    )


def create_pending(
    cfg: Config,
    *,
    tg_user_id: int,
    tg_chat_id: int,
    method: str,
) -> tuple[int | None, str]:
    if not pay_available(cfg):
        return None, "Оплата Premium временно недоступна."
    rates = fetch_pay_rates()
    amount_usdt = rates.usdt_for_rub(cfg.pay_premium_rub)
    amount_ton = rates.ton_for_rub(cfg.pay_premium_rub)
    url = cfg.database_url.strip()
    try:
        from stars_billing import _ensure_user_for_payment

        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                user_uuid = _ensure_user_for_payment(cur, tg_user_id, tg_chat_id)
                cur.execute(
                    """
                    INSERT INTO payment_pending (
                        tg_user_id, tg_chat_id, user_id, method,
                        amount_rub, amount_usdt, amount_ton, rate_snapshot, status
                    )
                    VALUES (%s, %s, %s::uuid, %s, %s, %s, %s, %s::jsonb, 'open')
                    RETURNING id
                    """,
                    (
                        tg_user_id,
                        tg_chat_id,
                        user_uuid,
                        method,
                        cfg.pay_premium_rub,
                        amount_usdt,
                        amount_ton,
                        json.dumps(rates.to_json(), ensure_ascii=False),
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                if not row:
                    return None, "Не удалось создать заявку."
                return int(row[0]), ""
    except Exception as exc:
        logger.warning("pay:create tg=%s: %s", tg_user_id, exc)
        return None, "Ошибка базы данных."


def _load_pending(database_url: str, pending_id: int) -> dict[str, Any] | None:
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tg_user_id, tg_chat_id, method, amount_rub,
                           amount_usdt, amount_ton, status
                    FROM payment_pending
                    WHERE id = %s
                    """,
                    (pending_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "id": int(row[0]),
                    "tg_user_id": int(row[1]),
                    "tg_chat_id": int(row[2]) if row[2] is not None else None,
                    "method": str(row[3]),
                    "amount_rub": int(row[4]),
                    "amount_usdt": row[5],
                    "amount_ton": row[6],
                    "status": str(row[7]),
                }
    except Exception as exc:
        logger.warning("pay:load id=%s: %s", pending_id, exc)
        return None


def _set_pending_status(
    database_url: str,
    pending_id: int,
    status: str,
    *,
    owner_notified: bool = False,
) -> bool:
    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                if owner_notified:
                    cur.execute(
                        """
                        UPDATE payment_pending
                        SET status = %s,
                            updated_at = NOW(),
                            owner_notified_at = NOW()
                        WHERE id = %s
                        """,
                        (status, pending_id),
                    )
                elif status in ("approved", "rejected"):
                    cur.execute(
                        """
                        UPDATE payment_pending
                        SET status = %s,
                            updated_at = NOW(),
                            reviewed_at = NOW()
                        WHERE id = %s
                        """,
                        (status, pending_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE payment_pending
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        (status, pending_id),
                    )
                conn.commit()
                return cur.rowcount > 0
    except Exception as exc:
        logger.warning("pay:status id=%s: %s", pending_id, exc)
        return False


def _legacy_credentials() -> tuple[str, str, str]:
    from health_check import _legacy_alert_credentials

    return _legacy_alert_credentials()


def _send_flparsing_message(text: str, reply_markup: str | None = None) -> tuple[bool, str]:
    token, chat_id, err = _legacy_credentials()
    if err:
        return False, err
    from health_check import _verify_flparsing_bot_token

    ok_bot, bot_detail = _verify_flparsing_bot_token(token)
    if not ok_bot:
        return False, bot_detail
    cfg = load_config_for_profile("legacy", merge_root_env=False)
    proxies = telegram_requests_proxies(cfg)
    data: dict[str, str | bool] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            timeout=25.0,
            proxies=proxies,
        )
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}"
        body = resp.json()
        if isinstance(body, dict) and body.get("ok"):
            return True, bot_detail
        return False, str(body.get("description") or "send fail")
    except requests.RequestException as exc:
        return False, str(exc)


def _owner_approve_markup(pending_id: int, tg_user_id: int, days: int) -> str:
    return _inline_markup(
        [
            [
                {
                    "text": f"✅ User #{tg_user_id} Premium {days}d",
                    "callback_data": f"pok:{pending_id}",
                },
                {"text": "❌ Отклонить", "callback_data": f"pnx:{pending_id}"},
            ]
        ]
    )


def notify_owner_pending(cfg: Config, pending: dict[str, Any]) -> tuple[bool, str]:
    if cfg.pay_approve_bot.strip().casefold() != "legacy":
        return False, "approve bot not legacy"
    method_label = "СБП" if pending["method"] == "sbp" else "Crypto"
    text = (
        f"💳 Оплата Premium\n"
        f"User TG: {pending['tg_user_id']}\n"
        f"Способ: {method_label}\n"
        f"Сумма: {pending['amount_rub']} ₽\n"
        f"Заявка #{pending['id']}\n\n"
        f"Пользователь нажал «Проверить оплату»."
    )
    markup = _owner_approve_markup(
        pending["id"],
        pending["tg_user_id"],
        cfg.stars_subscription_days,
    )
    return _send_flparsing_message(text, markup)


def _send_site_message(chat_id: int, text: str, *, reply_markup: str | None = None) -> bool:
    from health_check import send_rawlead_user_text

    ok, detail = send_rawlead_user_text(chat_id, text)
    if not ok:
        logger.warning("pay:rawlead_msg chat=%s: %s", chat_id, detail)
    return ok


def _notify_owner_approved(
    pending: dict[str, Any],
    *,
    active_until: str,
) -> None:
    method_label = "СБП" if pending.get("method") == "sbp" else "Crypto"
    text = (
        f"✅ Premium выдан\n"
        f"User TG: {pending['tg_user_id']}\n"
        f"Способ: {method_label}\n"
        f"До: {active_until}\n"
        f"Заявка #{pending['id']}"
    )
    _send_flparsing_message(text)


def _bot_api(cfg: Config, method: str, data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    proxies = telegram_requests_proxies(cfg)
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            f"https://api.telegram.org/bot{cfg.telegram_bot_token}/{method}",
            data=data,
            timeout=25.0,
            proxies=proxies,
        )
        if resp.status_code != 200:
            return False, {}
        body = resp.json()
        return bool(body.get("ok")), body if isinstance(body, dict) else {}
    except requests.RequestException as exc:
        logger.warning("pay:%s: %s", method, exc)
        return False, {}


def _answer_callback(cfg: Config, callback_id: str, text: str) -> None:
    _bot_api(
        cfg,
        "answerCallbackQuery",
        {"callback_query_id": callback_id, "text": text[:200]},
    )


def _answer_callback_alert(cfg: Config, callback_id: str, text: str) -> None:
    _bot_api(
        cfg,
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id,
            "text": text[:200],
            "show_alert": True,
        },
    )


def _is_legacy_owner(user_id: int | None) -> bool:
    if user_id is None:
        return False
    _, chat_id, err = _legacy_credentials()
    if err:
        return False
    try:
        return int(chat_id) == int(user_id)
    except ValueError:
        return str(chat_id) == str(user_id)


def _parse_user_callback(data: str) -> tuple[str, str, str] | None:
    """Return (action, arg1, arg2) from pay:* callback."""
    if not data.startswith("pay:"):
        return None
    parts = data.split(":")
    if len(parts) < 2:
        return None
    action = parts[1]
    arg1 = parts[2] if len(parts) > 2 else ""
    arg2 = parts[3] if len(parts) > 3 else ""
    return action, arg1, arg2


def handle_user_pay_callback(
    cfg: Config,
    callback_query: dict[str, Any],
    errors: list[str],
) -> bool:
    """Site bot: pay:* callbacks."""
    data = str(callback_query.get("data") or "").strip()
    parsed = _parse_user_callback(data)
    if parsed is None:
        return False

    action, arg1, arg2 = parsed
    from_user = callback_query.get("from") or {}
    tg_user_id = from_user.get("id")
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    callback_id = callback_query.get("id")

    if tg_user_id is None or chat_id is None:
        return True

    if action == "menu":
        _answer_callback(cfg, str(callback_id), "")
        _bot_api(
            cfg,
            "editMessageText",
            {
                "chat_id": str(chat_id),
                "message_id": message.get("message_id"),
                "text": format_pay_menu(cfg),
                "reply_markup": pay_menu_markup(cfg),
            },
        )
        return True

    if action == "stars":
        _answer_callback(cfg, str(callback_id), "")
        _bot_api(
            cfg,
            "editMessageText",
            {
                "chat_id": str(chat_id),
                "message_id": message.get("message_id"),
                "text": format_stars_intro(cfg),
                "reply_markup": stars_intro_markup(cfg),
            },
        )
        errors.append(f"pay:stars_intro tg={tg_user_id}")
        return True

    if action == "stinv":
        from stars_billing import send_stars_invoice

        _answer_callback(cfg, str(callback_id), "Открываю счёт Stars…")
        ok, detail = send_stars_invoice(cfg, int(chat_id), tg_user_id=int(tg_user_id))
        if not ok:
            _send_site_message(int(chat_id), detail or "Stars недоступны.")
        errors.append(f"pay:stinv tg={tg_user_id} ok={ok}")
        return True

    if action in ("sbp", "crypto"):
        if action == "sbp" and not cfg.pay_sbp_phone.strip():
            _answer_callback(cfg, str(callback_id), "СБП недоступен")
            return True
        if action == "crypto" and not _crypto_configured(cfg):
            _answer_callback(cfg, str(callback_id), "Crypto недоступен")
            return True
        pending_id, err = create_pending(
            cfg,
            tg_user_id=int(tg_user_id),
            tg_chat_id=int(chat_id),
            method=action,
        )
        if pending_id is None:
            _answer_callback(cfg, str(callback_id), err[:200])
            return True
        _answer_callback(cfg, str(callback_id), "")
        if action == "sbp":
            text = format_sbp_screen(cfg, int(tg_user_id), pending_id)
            markup = sbp_action_markup(pending_id)
        else:
            rates = fetch_pay_rates()
            pending = _load_pending(cfg.database_url, pending_id) or {}
            usdt = pending.get("amount_usdt")
            ton = pending.get("amount_ton")
            text = format_crypto_screen(
                cfg,
                int(tg_user_id),
                pending_id,
                rates,
                amount_usdt=Decimal(str(usdt)) if usdt is not None else rates.usdt_for_rub(cfg.pay_premium_rub),
                amount_ton=Decimal(str(ton)) if ton is not None else rates.ton_for_rub(cfg.pay_premium_rub),
            )
            markup = crypto_action_markup(cfg, pending_id)
        _bot_api(
            cfg,
            "editMessageText",
            {
                "chat_id": str(chat_id),
                "message_id": message.get("message_id"),
                "text": text,
                "reply_markup": markup,
            },
        )
        errors.append(f"pay:{action} tg={tg_user_id} id={pending_id}")
        return True

    if action == "chk":
        try:
            pending_id = int(arg1)
        except ValueError:
            return True
        pending = _load_pending(cfg.database_url, pending_id)
        if not pending or pending["tg_user_id"] != int(tg_user_id):
            _answer_callback(cfg, str(callback_id), "Заявка не найдена")
            return True
        if pending["status"] == "approved":
            _answer_callback(cfg, str(callback_id), "Premium уже активен")
            return True
        if pending["status"] in ("rejected", "cancelled"):
            _answer_callback(cfg, str(callback_id), "Заявка закрыта")
            return True
        _set_pending_status(cfg.database_url, pending_id, "awaiting_owner", owner_notified=True)
        ok, detail = notify_owner_pending(cfg, pending)
        _answer_callback(cfg, str(callback_id), "Ищем перевод…")
        reply = (
            "Ищем перевод… Обычно до 2 минут.\n\n"
            "Если оплата не подтвердится — проверь сумму и реквизиты."
        )
        if not ok:
            reply += f"\n\n(Уведомление владельцу: {detail[:80]})"
        _send_site_message(int(chat_id), reply)
        errors.append(f"pay:chk tg={tg_user_id} id={pending_id} owner_ok={ok}")
        return True

    if action == "cnl":
        try:
            pending_id = int(arg1)
        except ValueError:
            return True
        pending = _load_pending(cfg.database_url, pending_id)
        if pending and pending["tg_user_id"] == int(tg_user_id):
            _set_pending_status(cfg.database_url, pending_id, "cancelled")
        _answer_callback(cfg, str(callback_id), "Отменено")
        _bot_api(
            cfg,
            "editMessageText",
            {
                "chat_id": str(chat_id),
                "message_id": message.get("message_id"),
                "text": format_pay_menu(cfg),
                "reply_markup": pay_menu_markup(cfg),
            },
        )
        return True

    if action == "cpy":
        kind = arg1
        try:
            pending_id = int(arg2)
        except ValueError:
            return True
        pending = _load_pending(cfg.database_url, pending_id)
        if not pending or pending["tg_user_id"] != int(tg_user_id):
            _answer_callback(cfg, str(callback_id), "Заявка не найдена")
            return True
        if kind == "usdt":
            addr = cfg.pay_usdt_trc20_address.strip() or cfg.pay_usdt_erc20_address.strip()
        elif kind == "ton":
            addr = cfg.pay_ton_address.strip()
        else:
            addr = ""
        if not addr:
            _answer_callback(cfg, str(callback_id), "Адрес не настроен")
            return True
        _answer_callback_alert(cfg, str(callback_id), addr)
        return True

    return False


def handle_owner_pay_callback(
    cfg: Config,
    callback_query: dict[str, Any],
    errors: list[str],
) -> bool:
    """Legacy @FLPARSINGBOT: pok:/pnx: approve/reject."""
    data = str(callback_query.get("data") or "").strip()
    m = _OWNER_CALLBACK_RE.match(data)
    if not m:
        return False

    verb = m.group(1)
    try:
        pending_id = int(m.group(2))
    except ValueError:
        return True

    from_user = callback_query.get("from") or {}
    owner_id = from_user.get("id")
    callback_id = callback_query.get("id")

    if not _is_legacy_owner(owner_id):
        _bot_api(
            cfg,
            "answerCallbackQuery",
            {"callback_query_id": str(callback_id), "text": "Нет доступа", "show_alert": True},
        )
        return True

    site_cfg = load_config_for_profile("site", merge_root_env=False)
    db_url = site_cfg.database_url.strip()
    pending = _load_pending(db_url, pending_id)
    if not pending:
        _answer_callback(cfg, str(callback_id), "Заявка не найдена")
        return True

    tg_user_id = pending["tg_user_id"]
    tg_chat_id = pending["tg_chat_id"]

    if verb == "ok":
        if pending["status"] == "approved":
            _answer_callback(cfg, str(callback_id), "Уже одобрено")
            return True
        ok = activate_subscription(
            db_url,
            tg_user_id=tg_user_id,
            tg_chat_id=tg_chat_id,
            days=site_cfg.stars_subscription_days,
        )
        if ok:
            _set_pending_status(db_url, pending_id, "approved")
            _answer_callback(cfg, str(callback_id), "Premium активирован")
            until = datetime.now(timezone.utc) + timedelta(days=site_cfg.stars_subscription_days)
            date_str = until.strftime("%d.%m.%Y")
            _notify_owner_approved(pending, active_until=date_str)
            if tg_chat_id:
                _send_site_message(
                    int(tg_chat_id),
                    f"✅ Premium активен до {date_str}.\n"
                    f"Лента без задержки — https://rawlead.ru/lenta/",
                )
            errors.append(f"pay:approved id={pending_id} tg={tg_user_id}")
        else:
            _answer_callback(cfg, str(callback_id), "Ошибка активации")
        return True

    if verb == "nx":
        _set_pending_status(db_url, pending_id, "rejected")
        _answer_callback(cfg, str(callback_id), "Отклонено")
        if tg_chat_id:
            _send_site_message(
                int(tg_chat_id),
                "Платёж пока не видим. Проверь сумму и реквизиты или напиши в поддержку.",
            )
        errors.append(f"pay:rejected id={pending_id} tg={tg_user_id}")
        return True

    return False


def _method_screen(
    cfg: Config,
    tg_user_id: int,
    tg_chat_id: int,
    method: str,
) -> tuple[str, str] | None:
    """Build text + markup for sbp/crypto; None if method unavailable."""
    if method == "sbp":
        if not cfg.pay_sbp_phone.strip():
            return None
        pending_id, err = create_pending(
            cfg, tg_user_id=tg_user_id, tg_chat_id=tg_chat_id, method="sbp"
        )
        if pending_id is None:
            return err, ""
        return format_sbp_screen(cfg, tg_user_id, pending_id), sbp_action_markup(pending_id)

    if method == "crypto":
        if not _crypto_configured(cfg):
            return None
        pending_id, err = create_pending(
            cfg, tg_user_id=tg_user_id, tg_chat_id=tg_chat_id, method="crypto"
        )
        if pending_id is None:
            return err, ""
        rates = fetch_pay_rates()
        pending = _load_pending(cfg.database_url, pending_id) or {}
        usdt = pending.get("amount_usdt")
        ton = pending.get("amount_ton")
        text = format_crypto_screen(
            cfg,
            tg_user_id,
            pending_id,
            rates,
            amount_usdt=Decimal(str(usdt)) if usdt is not None else rates.usdt_for_rub(cfg.pay_premium_rub),
            amount_ton=Decimal(str(ton)) if ton is not None else rates.ton_for_rub(cfg.pay_premium_rub),
        )
        return text, crypto_action_markup(cfg, pending_id)

    return None


def send_pay_method(
    cfg: Config,
    chat_id: int,
    tg_user_id: int,
    method: str,
    errors: list[str] | None = None,
) -> None:
    """Deep link /pay → конкретный способ или меню."""
    m = method.strip().casefold()
    if m in ("", "menu", "pay"):
        send_pay_menu(cfg, chat_id, errors)
        return

    if m == "stars":
        if not cfg.stars_enabled:
            _bot_api(
                cfg,
                "sendMessage",
                {"chat_id": str(chat_id), "text": "Stars временно недоступны."},
            )
            return
        _bot_api(
            cfg,
            "sendMessage",
            {
                "chat_id": str(chat_id),
                "text": format_stars_intro(cfg),
                "reply_markup": stars_intro_markup(cfg),
            },
        )
        if errors is not None:
            errors.append(f"pay:stars_intro tg={tg_user_id}")
        return

    screen = _method_screen(cfg, tg_user_id, chat_id, m)
    if screen is None:
        send_pay_menu(cfg, chat_id, errors)
        return
    text, markup = screen
    if not markup:
        _bot_api(cfg, "sendMessage", {"chat_id": str(chat_id), "text": text or "Ошибка оплаты."})
        return
    ok, _ = _bot_api(
        cfg,
        "sendMessage",
        {"chat_id": str(chat_id), "text": text, "reply_markup": markup},
    )
    if errors is not None and ok:
        errors.append(f"pay:{m} tg={tg_user_id}")


def send_pay_menu(cfg: Config, chat_id: int, errors: list[str] | None = None) -> None:
    """Экран 1 — меню способов оплаты."""
    if not pay_available(cfg):
        _bot_api(
            cfg,
            "sendMessage",
            {
                "chat_id": str(chat_id),
                "text": "Оплата Premium временно недоступна. Попробуйте позже или Stars.",
            },
        )
        return
    ok, _ = _bot_api(
        cfg,
        "sendMessage",
        {
            "chat_id": str(chat_id),
            "text": format_pay_menu(cfg),
            "reply_markup": pay_menu_markup(cfg),
        },
    )
    if errors is not None and ok:
        errors.append(f"pay:menu chat={chat_id}")
