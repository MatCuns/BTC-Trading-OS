from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

D = Decimal
Environment = Literal["INTERNAL_PAPER", "OKX_DEMO", "OKX_LIVE"]


def now() -> datetime:
    return datetime.now(UTC)


class DTO(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, validate_assignment=True)
    environment_id: Environment = "INTERNAL_PAPER"


class Instrument(DTO):
    inst_id: str
    inst_type: str
    rule_type: str
    tick: Decimal = Field(gt=0)
    lot: Decimal = Field(gt=0)
    min_size: Decimal = Field(gt=0)
    contract_btc: Decimal = Field(gt=0)
    settle_ccy: str
    expiry: datetime | None = None
    source: str
    min_notional: Decimal = Field(default=D("5"), ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def round_size(self, size: Decimal) -> Decimal:
        return (size / self.lot).to_integral_value(rounding=ROUND_DOWN) * self.lot

    def round_price(self, price: Decimal) -> Decimal:
        return (price / self.tick).to_integral_value(rounding=ROUND_DOWN) * self.tick


class Quote(DTO):
    inst_id: str
    bid: Decimal = Field(gt=0)
    ask: Decimal = Field(gt=0)
    last: Decimal = Field(gt=0)
    bid_size: Decimal = Field(default=D("1"), ge=0)
    ask_size: Decimal = Field(default=D("1"), ge=0)
    timestamp: datetime
    ingest_time: datetime = Field(default_factory=now)
    source: str

    @model_validator(mode="after")
    def valid_spread(self) -> "Quote":
        if self.ask < self.bid or self.timestamp.tzinfo is None:
            raise ValueError("Crossed quote or missing timezone")
        return self


class Order(DTO):
    client_id: str
    decision_id: str
    inst_id: str
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)  # contracts, not BTC
    filled: Decimal = D("0")
    status: Literal["OPEN", "PARTIAL", "FILLED", "CANCELLED", "UNKNOWN"] = "OPEN"
    reduce_only: bool = False
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    created_at: datetime = Field(default_factory=now)
    reason: str


class Fill(DTO):
    id: str
    client_id: str
    inst_id: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal
    liquidity: Literal["maker", "taker"]
    timestamp: datetime = Field(default_factory=now)


class Account(DTO):
    cash: Decimal
    quantity: Decimal = D("0")  # signed contracts
    average_price: Decimal = D("0")
    realized_pnl: Decimal = D("0")
    fees: Decimal = D("0")
    funding: Decimal = D("0")
    peak_equity: Decimal
    day_equity: Decimal
    day: str = Field(default_factory=lambda: now().date().isoformat())
    stop_price: Decimal | None = None
    kill_switch: bool = True
    strategy_enabled: bool = False

    def equity(self, mark: Decimal, contract_btc: Decimal) -> Decimal:
        return self.cash + self.quantity * contract_btc * (mark - self.average_price)


class TargetRequest(DTO):
    client_id: str = Field(min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9]+$")
    target: Decimal = Field(ge=-5, le=5)
    stop_fraction: Decimal = Field(default=D("0.01"), gt=0, le=D("0.25"))
    limit_price: Decimal | None = Field(default=None, gt=0)
    expected_edge_bps: Decimal = Field(default=D("30"), ge=0, le=10000)


class Ledger(DTO):
    account: Account
    instrument: Instrument | None = None
    last_quote: Quote | None = None
    orders: list[Order] = Field(default_factory=list)
    fills: list[Fill] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    requests: dict[str, dict[str, Any]] = Field(default_factory=dict)
    reverse: dict[str, Any] | None = None
    funding_ids: list[str] = Field(default_factory=list)
    funding_events: list[dict[str, Any]] = Field(default_factory=list)
    version: int = 0
