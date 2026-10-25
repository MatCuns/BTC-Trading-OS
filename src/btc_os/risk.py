from decimal import Decimal

from btc_os.config import Settings
from btc_os.domain import Account, Instrument, Quote, now


class RiskRejected(ValueError):
    pass


class RiskEngine:
    """Independent pre-trade checks. No strategy or LLM can override these."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def check(
        self,
        account: Account,
        instrument: Instrument,
        quote: Quote | None,
        target: Decimal,
        stop_fraction: Decimal,
        edge_bps: Decimal,
        persistence_ok: bool,
        reconciled: bool,
        reducing: bool = False,
    ) -> None:
        s = self.settings
        if not persistence_ok or not reconciled:
            raise RiskRejected("Persistence or order state unknown: NO NEW ORDERS")
        if quote is None or (now() - quote.timestamp).total_seconds() > s.stale_seconds:
            raise RiskRejected("Stale market feed: execution paused")
        if (now() - quote.timestamp).total_seconds() < -2:
            raise RiskRejected("Clock skew: execution paused")
        if reducing:
            return
        if instrument.expiry and (instrument.expiry - now()).total_seconds() < 3600:
            raise RiskRejected("Contract expiring: manual reconciliation required")
        equity = account.equity(quote.last, instrument.contract_btc)
        if account.kill_switch:
            raise RiskRejected("Kill switch enabled")
        if equity <= 0:
            raise RiskRejected("No available equity")
        if abs(target) > min(Decimal("5"), s.max_leverage):
            raise RiskRejected("Exposure exceeds configured or hard 5x cap")
        if equity <= account.day_equity * (1 - s.daily_loss):
            raise RiskRejected("Daily loss limit reached")
        if equity <= account.peak_equity * (1 - s.max_drawdown):
            raise RiskRejected("Maximum drawdown reached")
        costs = 2 * (s.taker_fee + s.slippage_bps / 10000) + (quote.ask - quote.bid) / quote.last
        if edge_bps / 10000 <= costs:
            raise RiskRejected("Expected edge does not cover configured round-trip costs")
        if abs(target) * (stop_fraction + costs) > s.trade_loss_budget:
            raise RiskRejected("Planned stop and cost loss exceeds trade budget")
        # Conservative isolated-margin approximation at the configured leverage.
        if abs(target) / s.max_leverage + abs(target) * costs >= 1:
            raise RiskRejected("Insufficient free margin after estimated costs")
