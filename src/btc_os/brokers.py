import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from pydantic import SecretStr

from btc_os.config import Settings
from btc_os.domain import Account, Fill, Instrument, Order, Quote


class BrokerAdapter(Protocol):
    environment_id: str

    def execute(
        self, order: Order, quote: Quote, instrument: Instrument, account: Account
    ) -> Fill | None: ...


class InternalPaperBroker:
    environment_id = "INTERNAL_PAPER"

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(
        self, order: Order, quote: Quote, instrument: Instrument, account: Account
    ) -> Fill | None:
        if (
            any(
                item.environment_id != self.environment_id
                for item in (order, quote, instrument, account)
            )
            or quote.inst_id != order.inst_id
        ):
            raise ValueError("Environment or instrument mismatch")
        if order.status not in {"OPEN", "PARTIAL"}:
            return None
        buy = order.side == "buy"
        touch = quote.ask if buy else quote.bid
        if order.limit_price is not None and (
            touch > order.limit_price if buy else touch < order.limit_price
        ):
            return None
        remaining = order.quantity - order.filled
        quantity = instrument.round_size(min(remaining, quote.ask_size if buy else quote.bid_size))
        if order.reduce_only:
            if not account.quantity or (account.quantity > 0) == buy:
                order.status = "CANCELLED"
                return None
            quantity = min(quantity, abs(account.quantity))
        if quantity <= 0:
            return None
        # Resting limits are maker only after a later quote crosses the limit.
        maker = order.limit_price is not None and quote.timestamp > order.created_at
        slip = self.settings.slippage_bps / 10000
        price = touch * (1 + slip if buy else 1 - slip)
        if order.limit_price is not None:
            price = min(price, order.limit_price) if buy else max(price, order.limit_price)
        price = instrument.round_price(price)
        fee = (
            quantity
            * instrument.contract_btc
            * price
            * (self.settings.maker_fee if maker else self.settings.taker_fee)
        )
        delta = quantity if buy else -quantity
        old = account.quantity
        closed = min(abs(old), quantity) if old * delta < 0 else Decimal("0")
        realized = (
            closed
            * instrument.contract_btc
            * (price - account.average_price)
            * (1 if old > 0 else -1)
        )
        new = old + delta
        if old * delta >= 0:
            account.average_price = (abs(old) * account.average_price + quantity * price) / abs(new)
        elif abs(delta) > abs(old):
            account.average_price = price
        elif new == 0:
            account.average_price = Decimal("0")
        account.quantity = new
        account.realized_pnl += realized
        account.fees += fee
        account.cash += realized - fee
        if new == 0:
            account.stop_price = None
        elif order.stop_price is not None:
            account.stop_price = order.stop_price
        order.filled += quantity
        order.status = "FILLED" if order.filled == order.quantity else "PARTIAL"
        return Fill(
            id=uuid4().hex,
            client_id=order.client_id,
            inst_id=order.inst_id,
            quantity=quantity,
            price=price,
            fee=fee,
            realized_pnl=realized,
            liquidity="maker" if maker else "taker",
        )


class OkxLiveAdapter:
    environment_id = "OKX_LIVE"

    def execute(
        self, order: Order, quote: Quote, instrument: Instrument, account: Account
    ) -> Fill | None:
        raise PermissionError("LIVE is disabled in R1")


class OkxDemoAdapter:
    """Opt-in integration utility; never connected to the R1 PAPER runtime or ledger."""

    environment_id = "OKX_DEMO"
    base_url = "https://eea.okx.com"

    def __init__(
        self, key: SecretStr, secret: SecretStr, passphrase: SecretStr, client: httpx.AsyncClient
    ):
        self.key, self.secret, self.passphrase, self.client = key, secret, passphrase, client

    async def request(
        self, method: str, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        allowed = {
            ("GET", "/api/v5/account/instruments"),
            ("GET", "/api/v5/account/balance"),
            ("GET", "/api/v5/trade/order"),
            ("POST", "/api/v5/trade/order"),
        }
        if (method, path) not in allowed:
            raise PermissionError("Unsupported demo operation")
        stamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        body = json.dumps(data, separators=(",", ":")) if data and method == "POST" else ""
        query = "?" + urlencode(data) if data and method == "GET" else ""
        signature = base64.b64encode(
            hmac.new(
                self.secret.get_secret_value().encode(),
                (stamp + method + path + query + body).encode(),
                hashlib.sha256,
            ).digest()
        ).decode()
        response = await self.client.request(
            method,
            self.base_url + path + query,
            content=body or None,
            headers={
                "OK-ACCESS-KEY": self.key.get_secret_value(),
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": stamp,
                "OK-ACCESS-PASSPHRASE": self.passphrase.get_secret_value(),
                "x-simulated-trading": "1",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        if result.get("code") != "0":
            raise ValueError("Demo API rejected request; inspect redacted local diagnostics")
        return result

    async def place(
        self, order: Order, instrument: Instrument, account_eligible: bool
    ) -> dict[str, Any]:
        if order.environment_id != "OKX_DEMO" or not account_eligible:
            raise PermissionError("Demo account instrument eligibility must be verified")
        if instrument.inst_type != "FUTURES" or instrument.rule_type != "xperp":
            raise PermissionError("Unsupported demo instrument")
        return await self.request(
            "POST",
            "/api/v5/trade/order",
            {
                "instId": instrument.inst_id,
                "tdMode": "isolated",
                "side": order.side,
                "ordType": "market",
                "sz": str(order.quantity),
                "clOrdId": order.client_id,
                "reduceOnly": order.reduce_only,
            },
        )
