import asyncio
import json
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx
from websockets.asyncio.client import connect

from btc_os.domain import Instrument, Quote, now
from btc_os.engine import TradingEngine

REST = "https://eea.okx.com"
WS = "wss://wseea.okx.com/ws/v5/public"


def discover(rows: list[dict[str, Any]], selected: str | None = None) -> Instrument:
    candidates = []
    for row in rows:
        if (
            row.get("instType") != "FUTURES"
            or row.get("ruleType") != "xperp"
            or row.get("state") != "live"
        ):
            continue
        if not row.get("instId", "").startswith("BTC-"):
            continue
        if selected and row["instId"] != selected:
            continue
        # This ledger models only linear BTC-valued contracts in a stable quote currency.
        if (
            row.get("ctType") != "linear"
            or row.get("ctValCcy") != "BTC"
            or row.get("settleCcy") not in {"USDT", "USDC", "USD"}
        ):
            continue
        try:
            expiry = datetime.fromtimestamp(int(row["expTime"]) / 1000, UTC)
            if expiry <= now() + timedelta(hours=1):
                continue
            candidates.append(
                Instrument(
                    inst_id=row["instId"],
                    inst_type="FUTURES",
                    rule_type="xperp",
                    tick=Decimal(row["tickSz"]),
                    lot=Decimal(row["lotSz"]),
                    min_size=Decimal(row["minSz"]),
                    contract_btc=Decimal(row["ctVal"]) * Decimal(row.get("ctMult") or "1"),
                    settle_ccy=row["settleCcy"],
                    expiry=expiry,
                    source="OKX_EEA_PUBLIC",
                    metadata=row,
                )
            )
        except (ValueError, KeyError, ArithmeticError):
            continue
    if not candidates:
        raise ValueError(
            "No supported linear BTC X-Perp visible on EEA public API. No substitution; choose fixture explicitly for offline PAPER."
        )
    if len(candidates) > 1 and not selected:
        raise ValueError(
            "Multiple BTC X-Perps: set BTC_INSTRUMENT_ID to one of "
            + ", ".join(x.inst_id for x in candidates)
        )
    return candidates[0]


def fixture_instrument() -> Instrument:
    return Instrument(
        inst_id="FIXTURE-BTC-LINEAR",
        inst_type="SYNTHETIC",
        rule_type="fixture",
        tick=Decimal("0.1"),
        lot=Decimal("1"),
        min_size=Decimal("1"),
        contract_btc=Decimal("0.001"),
        settle_ccy="USD",
        source="SYNTHETIC_FIXTURE",
    )


def parse_ticker(row: dict[str, Any], instrument: Instrument) -> Quote:
    return Quote(
        inst_id=row["instId"],
        bid=Decimal(row["bidPx"]),
        ask=Decimal(row["askPx"]),
        last=Decimal(row["last"]),
        bid_size=Decimal(row["bidSz"]),
        ask_size=Decimal(row["askSz"]),
        timestamp=datetime.fromtimestamp(int(row["ts"]) / 1000, UTC),
        source="OKX_EEA_PUBLIC",
    )


class MarketFeed:
    def __init__(self, engine: TradingEngine):
        self.engine = engine
        self.metrics: dict[str, Any] = {
            "connected": False,
            "reconnects": 0,
            "exceptions": 0,
            "last_message": None,
            "clock_offset_ms": None,
            "trade_count": 0,
            "trade_contracts": "0",
            "queue_lag_ms": None,
            "funding_status": "unavailable",
        }
        self.message = "Starting public discovery"
        self.funding_start = now()

    async def public(
        self, client: httpx.AsyncClient, path: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        await asyncio.sleep(0.25)  # bounded public REST use, below documented per-route limits
        response = await client.get(REST + path, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != "0":
            raise ValueError("Public OKX endpoint rejected request")
        rows: list[dict[str, Any]] = result["data"]
        return rows

    async def funding_loop(self, instrument: Instrument) -> None:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    rows = await self.public(
                        client,
                        "/api/v5/public/funding-rate-history",
                        {"instId": instrument.inst_id, "limit": "10"},
                    )
                    for row in sorted(rows, key=lambda r: int(r["fundingTime"])):
                        stamp = datetime.fromtimestamp(int(row["fundingTime"]) / 1000, UTC)
                        if self.funding_start < stamp <= now() and row.get("realizedRate"):
                            await self.engine.funding(
                                instrument.inst_id + ":" + row["fundingTime"],
                                Decimal(row["realizedRate"]),
                                self.engine.quote.last if self.engine.quote else Decimal("0"),
                            )
                    self.metrics["funding_status"] = (
                        "public settled rates; no backfill across downtime"
                    )
                except (httpx.HTTPError, ValueError, KeyError):
                    self.metrics["funding_status"] = "unavailable; funding PnL incomplete"
                await asyncio.sleep(60)

    async def session(self) -> None:
        async with httpx.AsyncClient() as client:
            times = await self.public(client, "/api/v5/public/time", {})
            offset = int(times[0]["ts"]) - now().timestamp() * 1000
            self.metrics["clock_offset_ms"] = round(offset)
            if abs(offset) > 2000:
                raise ValueError("Windows clock differs from OKX by >2s; synchronize clock")
            rows = await self.public(client, "/api/v5/public/instruments", {"instType": "FUTURES"})
            instrument = discover(rows, self.engine.settings.instrument_id)
            self.engine.set_instrument(instrument)
            ticker = await self.public(
                client, "/api/v5/market/ticker", {"instId": instrument.inst_id}
            )
            await self.engine.tick(parse_ticker(ticker[0], instrument))
        async with connect(
            WS, ping_interval=None, open_timeout=10, max_queue=16, max_size=2**20
        ) as socket:
            await socket.send(
                json.dumps(
                    {
                        "op": "subscribe",
                        "args": [
                            {"channel": "tickers", "instId": instrument.inst_id},
                            {"channel": "trades", "instId": instrument.inst_id},
                        ],
                    }
                )
            )
            self.metrics["connected"] = True
            self.message = "OKX EEA public stream; account eligibility NOT verified"
            funding_task = asyncio.create_task(self.funding_loop(instrument))
            try:
                while True:
                    try:
                        raw = await asyncio.wait_for(socket.recv(), timeout=20)
                    except TimeoutError:
                        await socket.send("ping")
                        raw = await asyncio.wait_for(socket.recv(), timeout=5)
                    if raw == "pong":
                        continue
                    body = json.loads(raw)
                    if body.get("event") == "error":
                        raise ValueError("WebSocket subscription rejected")
                    self.metrics["last_message"] = now().isoformat()
                    for row in body.get("data", []):
                        channel = body.get("arg", {}).get("channel")
                        if channel == "tickers":
                            quote = parse_ticker(row, instrument)
                            self.metrics["queue_lag_ms"] = max(
                                0, round((now() - quote.timestamp).total_seconds() * 1000)
                            )
                            await self.engine.tick(quote)
                        elif channel == "trades":
                            self.metrics["trade_count"] += 1
                            self.metrics["trade_contracts"] = str(
                                Decimal(self.metrics["trade_contracts"]) + Decimal(row["sz"])
                            )
            finally:
                funding_task.cancel()
                await asyncio.gather(funding_task, return_exceptions=True)

    async def run(self) -> None:
        if self.engine.settings.feed_mode == "fixture":
            self.engine.set_instrument(fixture_instrument())
            self.metrics["connected"] = True
            self.message = "SYNTHETIC FIXTURE — not live market data, not measured performance"
            rng = random.Random(7301)
            price = Decimal("65000")
            while True:
                price += Decimal(str(rng.uniform(-20, 20))).quantize(Decimal("0.1"))
                await self.engine.tick(
                    Quote(
                        inst_id="FIXTURE-BTC-LINEAR",
                        bid=price - 1,
                        ask=price + 1,
                        last=price,
                        bid_size=Decimal("15"),
                        ask_size=Decimal("15"),
                        timestamp=now(),
                        source="SYNTHETIC_FIXTURE",
                    )
                )
                self.metrics["last_message"] = now().isoformat()
                await asyncio.sleep(1)
        attempt = 0
        while True:
            try:
                await self.session()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.metrics["connected"] = False
                self.metrics["reconnects"] += 1
                self.metrics["exceptions"] += 1
                self.message = (
                    str(exc)
                    if isinstance(exc, ValueError)
                    else "Public feed unavailable; reconnecting; no new exposure on stale feed"
                )
                attempt += 1
                await asyncio.sleep(min(60, 2 ** min(attempt, 6)) + random.uniform(0, 1))
