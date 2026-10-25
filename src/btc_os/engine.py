import asyncio
import math
from collections import deque
from decimal import Decimal
from typing import Any
from uuid import uuid4

from btc_os.brokers import InternalPaperBroker
from btc_os.config import Settings
from btc_os.domain import Account, Instrument, Ledger, Order, Quote, TargetRequest, now
from btc_os.risk import RiskEngine, RiskRejected
from btc_os.storage import Store

D = Decimal


class ReferenceStrategy:
    """Transparent 60-sample minute trend/volatility reference, NOT an evaluated trading alpha."""

    def __init__(self) -> None:
        self.prices: deque[float] = deque(maxlen=60)

    def target(self, price: Decimal) -> Decimal:
        self.prices.append(float(price))
        if len(self.prices) < 60:
            return D("0")
        p = list(self.prices)
        returns = [math.log(b / a) for a, b in zip(p, p[1:], strict=False)]
        vol = math.sqrt(sum(x * x for x in returns) / len(returns))
        trend = sum(p[-10:]) / 10 / (sum(p) / len(p)) - 1
        if vol == 0 or vol > 0.005 or abs(trend) < max(0.0015, 3 * vol):
            return D("0")
        return D("0.25") if trend > 0 else D("-0.25")


class TradingEngine:
    def __init__(self, settings: Settings, store: Store):
        self.settings, self.store = settings, store
        self.broker = InternalPaperBroker(settings)
        self.risk = RiskEngine(settings)
        self.lock = asyncio.Lock()
        a = Account(
            cash=settings.initial_cash,
            peak_equity=settings.initial_cash,
            day_equity=settings.initial_cash,
            strategy_enabled=False,
        )
        self.ledger = Ledger(account=a)
        self.quote: Quote | None = None
        self.persistence_ok = False
        self.reconciled = False
        self.reason = "Starting: reconciliation required"
        self.strategy = ReferenceStrategy()
        self.history: deque[dict[str, Any]] = deque(maxlen=3600)
        self.last_snapshot = now()
        self.last_strategy = now()

    def start(self) -> None:
        try:
            loaded = self.store.load()
            if loaded:
                self.ledger = loaded
            # PAPER has no external pending fills. Cancel unfilled remainder and
            # never resume a reverse-open leg after restart without a new decision.
            for order in self.ledger.orders:
                if order.status in {"OPEN", "PARTIAL", "UNKNOWN"}:
                    order.status = "CANCELLED"
            self.ledger.reverse = None
            self.ledger.account.kill_switch = True
            self.ledger.account.strategy_enabled = False
            self.persistence_ok = True
            self.reconciled = True
            self.commit(self.ledger.model_copy(deep=True))
            self.reason = "Reconciled; unlock PAPER explicitly"
        except Exception:
            self.persistence_ok = self.reconciled = False
            self.reason = "Database unavailable: NO NEW ORDERS; restart after doctor"

    def commit(self, before: Ledger) -> None:
        # PostgreSQL retains complete history and request idempotency. Runtime stays bounded.
        active = [o for o in self.ledger.orders if o.status in {"OPEN", "PARTIAL", "UNKNOWN"}]
        complete = [o for o in self.ledger.orders if o.status not in {"OPEN", "PARTIAL", "UNKNOWN"}]
        self.ledger.orders = complete[-500:] + active
        self.ledger.fills = self.ledger.fills[-1000:]
        self.ledger.requests = dict(list(self.ledger.requests.items())[-1000:])
        self.ledger.funding_ids = self.ledger.funding_ids[-1000:]
        self.ledger.funding_events = self.ledger.funding_events[-1000:]
        expected = before.version
        self.ledger.version = expected + 1
        try:
            self.store.save(self.ledger, expected)
            self.persistence_ok = True
        except Exception:
            self.ledger = before
            # Commit may have succeeded before the connection failed. No retry
            # until startup loads the authoritative DB state.
            self.persistence_ok = self.reconciled = False
            self.reason = "Persistence unknown: NO NEW ORDERS; restart to reconcile"
            raise RiskRejected(self.reason) from None

    def set_instrument(self, instrument: Instrument) -> None:
        old = self.ledger.instrument
        if (
            old
            and old.inst_id != instrument.inst_id
            and (self.ledger.account.quantity or self.pending())
        ):
            raise RiskRejected(
                "Instrument changed with open exposure: manual reconciliation required"
            )
        if old and self.ledger.account.quantity and old.model_dump() != instrument.model_dump():
            raise RiskRejected("Contract metadata changed while position open")
        self.ledger.instrument = instrument

    def pending(self) -> list[Order]:
        return [o for o in self.ledger.orders if o.status in {"OPEN", "PARTIAL", "UNKNOWN"}]

    def decision(self, action: str, reason: str, client_id: str = "") -> str:
        decision_id = uuid4().hex
        self.ledger.decisions.append(
            {
                "decision_id": decision_id,
                "environment_id": "INTERNAL_PAPER",
                "timestamp": now().isoformat(),
                "action": action,
                "reason": reason,
                "client_id": client_id,
            }
        )
        self.ledger.decisions = self.ledger.decisions[-500:]
        self.reason = reason
        return decision_id

    def _target(self, request: TargetRequest, reverse_open: bool = False) -> list[Order]:
        if request.environment_id != "INTERNAL_PAPER":
            raise RiskRejected("Environment is disabled")
        body = request.model_dump(mode="json")
        if request.client_id in self.ledger.requests:
            if self.ledger.requests[request.client_id] != body:
                raise RiskRejected("Client ID reused with different request")
            return [
                o for o in self.ledger.orders if o.client_id.startswith(request.client_id + "-")
            ]
        try:
            prior = self.store.lookup_request(request.client_id) if not reverse_open else None
        except Exception:
            self.persistence_ok = self.reconciled = False
            raise RiskRejected("Persistence unknown: NO NEW ORDERS; restart to reconcile") from None
        if prior:
            saved_request, saved_orders = prior
            if saved_request != body:
                raise RiskRejected("Client ID reused with different persisted request")
            return [Order.model_validate(o) for o in saved_orders]
        if self.pending() or self.ledger.reverse:
            raise RiskRejected("Pending order: reconcile before a new target")
        instrument, q, a = self.ledger.instrument, self.quote, self.ledger.account
        if not instrument or not q:
            raise RiskRejected("No validated instrument/feed")
        equity = a.equity(q.last, instrument.contract_btc)
        desired = instrument.round_size(
            abs(request.target) * equity / (q.last * instrument.contract_btc)
        )
        if request.target < 0:
            desired = -desired
        reducing = desired * a.quantity >= 0 and abs(desired) <= abs(a.quantity)
        self.risk.check(
            a,
            instrument,
            q,
            request.target,
            request.stop_fraction,
            request.expected_edge_bps,
            self.persistence_ok,
            self.reconciled,
            reducing,
        )
        if desired and (
            abs(desired) < instrument.min_size
            or abs(desired) * instrument.contract_btc * q.last < instrument.min_notional
        ):
            raise RiskRejected("Below instrument min size/notional")
        self.ledger.requests[request.client_id] = body
        old = a.quantity
        reverse = old * desired < 0
        delta = -old if reverse else desired - old
        if not delta:
            self.decision("HOLD", "Target already reached", request.client_id)
            return []
        if reverse:
            self.ledger.reverse = {"request": body, "created_at": now().isoformat()}
        action = (
            "REVERSE_CLOSE"
            if reverse
            else (
                "FLAT"
                if not desired
                else "REDUCE"
                if reducing
                else "OPEN_LONG"
                if delta > 0
                else "OPEN_SHORT"
            )
        )
        decision_id = self.decision(
            action, f"Target {request.target}x; PAPER simulation", request.client_id
        )
        stop = instrument.round_price(
            q.last * (1 - request.stop_fraction if desired > 0 else 1 + request.stop_fraction)
        )
        order = Order(
            client_id=request.client_id + "-close" if reverse else request.client_id + "-target",
            decision_id=decision_id,
            inst_id=instrument.inst_id,
            side="buy" if delta > 0 else "sell",
            quantity=abs(delta),
            reduce_only=reducing or reverse,
            stop_price=stop if desired and not reverse else None,
            limit_price=request.limit_price,
            reason=action,
        )
        self.ledger.orders.append(order)
        self.fill(order)
        return [order]

    async def target(self, request: TargetRequest) -> list[Order]:
        async with self.lock:
            before = self.ledger.model_copy(deep=True)
            try:
                result = self._target(request)
                self.commit(before)
                return result
            except Exception:
                if self.persistence_ok:
                    self.ledger = before
                raise

    def fill(self, order: Order) -> None:
        if self.quote and self.ledger.instrument:
            a, i, q = self.ledger.account, self.ledger.instrument, self.quote
            if not order.reduce_only:
                remaining = order.quantity - order.filled
                projected = a.quantity + (remaining if order.side == "buy" else -remaining)
                equity = a.equity(q.last, i.contract_btc)
                if equity <= 0:
                    order.status = "CANCELLED"
                    return
                target = projected * i.contract_btc * q.last / equity
                distance = abs(q.last - order.stop_price) / q.last if order.stop_price else D("1")
                try:
                    self.risk.check(
                        a, i, q, target, distance, D("30"), self.persistence_ok, self.reconciled
                    )
                except RiskRejected as exc:
                    order.status = "CANCELLED"
                    self.decision("BLOCKED", str(exc), order.client_id)
                    return
            fill = self.broker.execute(
                order, self.quote, self.ledger.instrument, self.ledger.account
            )
            if fill:
                self.ledger.fills.append(fill)

    async def controls(self, kill: bool | None = None, strategy: bool | None = None) -> None:
        async with self.lock:
            if not self.persistence_ok or not self.reconciled:
                raise RiskRejected("Persistence unknown: restart to reconcile")
            before = self.ledger.model_copy(deep=True)
            if kill is not None:
                self.ledger.account.kill_switch = kill
                if kill:
                    self.ledger.reverse = None
                    for order in self.pending():
                        if not order.reduce_only:
                            order.status = "CANCELLED"
            if strategy is not None:
                self.ledger.account.strategy_enabled = strategy
            self.decision(
                "CONTROL",
                f"Kill={self.ledger.account.kill_switch}; strategy={self.ledger.account.strategy_enabled}",
            )
            self.commit(before)

    async def tick(self, quote: Quote) -> None:
        async with self.lock:
            if self.quote and quote.timestamp <= self.quote.timestamp:
                return
            self.quote = quote
            i, a = self.ledger.instrument, self.ledger.account
            if not i or quote.inst_id != i.inst_id:
                return
            if not self.persistence_ok or not self.reconciled:
                return
            before = self.ledger.model_copy(deep=True)
            try:
                self.store.event(quote)
                self.ledger.last_quote = quote
                equity = a.equity(quote.last, i.contract_btc)
                self.history.append(
                    {
                        "timestamp": quote.timestamp.isoformat(),
                        "price": str(quote.last),
                        "equity": str(equity),
                    }
                )
                a.peak_equity = max(a.peak_equity, equity)
                if a.day != now().date().isoformat():
                    a.day, a.day_equity = now().date().isoformat(), equity
                self.risk.check(a, i, quote, D("0"), D("0.01"), D("30"), True, True, True)
                stop = a.stop_price
                hit_stop = stop is not None and (
                    quote.bid <= stop if a.quantity > 0 else quote.ask >= stop
                )
                loss = equity <= a.day_equity * (
                    1 - self.settings.daily_loss
                ) or equity <= a.peak_equity * (1 - self.settings.max_drawdown)
                if hit_stop or loss:
                    a.kill_switch = True
                    self.ledger.reverse = None
                    for o in self.pending():
                        o.status = "CANCELLED"
                    if a.quantity:
                        cid = uuid4().hex
                        did = self.decision(
                            "STOP" if hit_stop else "LOSS_LIMIT",
                            "Protective paper close; fills may gap",
                            cid,
                        )
                        self.ledger.orders.append(
                            Order(
                                client_id=cid,
                                decision_id=did,
                                inst_id=i.inst_id,
                                side="sell" if a.quantity > 0 else "buy",
                                quantity=abs(a.quantity),
                                reduce_only=True,
                                reason="STOP" if hit_stop else "LOSS_LIMIT",
                            )
                        )
                for o in self.pending():
                    if (
                        now() - o.created_at
                    ).total_seconds() > self.settings.order_timeout_seconds and o.reason not in {
                        "STOP",
                        "LOSS_LIMIT",
                    }:
                        o.status = "CANCELLED"
                        self.ledger.reverse = None
                        self.decision(
                            "TIMEOUT",
                            "Unfilled remainder cancelled; no automatic retry",
                            o.client_id,
                        )
                    else:
                        self.fill(o)
                # Close acknowledgement is durably committed on a previous tick.
                # Open opposite side only when persisted position is flat.
                if (
                    self.ledger.reverse
                    and not self.pending()
                    and not a.quantity
                    and not before.account.quantity
                ):
                    req = TargetRequest.model_validate(self.ledger.reverse["request"])
                    self.ledger.reverse = None
                    self.ledger.requests.pop(req.client_id, None)
                    self._target(req, reverse_open=True)
                if (
                    (now() - self.last_strategy).total_seconds() >= 60
                    and not self.pending()
                    and not self.ledger.reverse
                    and a.strategy_enabled
                    and not a.kill_switch
                ):
                    self.last_strategy = now()
                    target = self.strategy.target(quote.last)
                    if len(self.strategy.prices) >= 60:
                        try:
                            self._target(TargetRequest(client_id=uuid4().hex, target=target))
                        except RiskRejected as exc:
                            self.decision("BLOCKED", str(exc))
                # Durable position, stop and day/high-water state on each accepted tick.
                self.commit(before)
                self.last_snapshot = now()
            except Exception:
                if self.persistence_ok:
                    self.ledger = before
                self.persistence_ok = self.reconciled = False
                self.reason = "Feed persistence/risk failed: NO NEW ORDERS; restart to reconcile"

    async def funding(self, event_id: str, rate: Decimal, mark: Decimal) -> None:
        async with self.lock:
            if not self.persistence_ok or not self.reconciled:
                raise RiskRejected("Persistence unknown")
            if event_id in self.ledger.funding_ids or not self.ledger.instrument:
                return
            before = self.ledger.model_copy(deep=True)
            amount = (
                -self.ledger.account.quantity * self.ledger.instrument.contract_btc * mark * rate
            )
            self.ledger.account.cash += amount
            self.ledger.account.funding += amount
            self.ledger.funding_ids.append(event_id)
            self.ledger.funding_events.append(
                {
                    "id": event_id,
                    "rate": str(rate),
                    "amount": str(amount),
                    "timestamp": now().isoformat(),
                    "environment_id": "INTERNAL_PAPER",
                }
            )
            self.commit(before)

    def snapshot(self) -> dict[str, Any]:
        i, a, q = self.ledger.instrument, self.ledger.account, self.quote
        equity = a.equity(q.last, i.contract_btc) if q and i else a.cash
        age = (now() - q.timestamp).total_seconds() if q else None
        flags = []
        if age is None or age > self.settings.stale_seconds:
            flags.append("STALE_FEED")
        if not self.persistence_ok:
            flags.append("PERSISTENCE_UNKNOWN")
        if not self.reconciled:
            flags.append("RECONCILIATION_REQUIRED")
        if a.kill_switch:
            flags.append("KILL_SWITCH")
        notional = abs(a.quantity) * i.contract_btc * q.last if i and q else D("0")
        return {
            "environment_id": "INTERNAL_PAPER",
            "live_enabled": False,
            "instrument": i.model_dump(mode="json") if i else None,
            "quote": q.model_dump(mode="json") if q else None,
            "account": a.model_dump(mode="json"),
            "equity": str(equity),
            "unrealized_pnl": str(equity - a.cash),
            "notional": str(notional),
            "leverage": str(notional / equity if equity > 0 else 0),
            "drawdown": str(1 - equity / a.peak_equity),
            "feed_age_seconds": age,
            "risk_flags": flags,
            "reason": self.reason,
            "orders": [o.model_dump(mode="json") for o in self.ledger.orders[-100:]],
            "fills": [f.model_dump(mode="json") for f in self.ledger.fills[-100:]],
            "decisions": self.ledger.decisions[-100:],
            "history": list(self.history),
            "assumptions": {
                "maker_fee": str(self.settings.maker_fee),
                "taker_fee": str(self.settings.taker_fee),
                "slippage_bps": str(self.settings.slippage_bps),
                "max_leverage": str(self.settings.max_leverage),
                "trade_loss_budget": str(self.settings.trade_loss_budget),
                "funding": "settled public funding events when available; otherwise unavailable",
            },
        }
