from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BTC_", env_file=".env", extra="ignore")
    database_url: SecretStr = SecretStr("postgresql+psycopg://localhost/btc_quant")
    data_root: Path = Path(".runtime")
    backup_root: Path = Path(".runtime-backup")
    feed_mode: Literal["okx", "fixture"] = "okx"
    strategy_enabled: bool = False
    max_leverage: Decimal = Field(default=Decimal("1"), gt=0, le=5)
    trade_loss_budget: Decimal = Field(default=Decimal("0.005"), gt=0, le=Decimal("0.05"))
    daily_loss: Decimal = Field(default=Decimal("0.02"), gt=0, le=Decimal("0.2"))
    max_drawdown: Decimal = Field(default=Decimal("0.10"), gt=0, le=Decimal("0.5"))
    maker_fee: Decimal = Field(default=Decimal("0.0002"), ge=0, le=Decimal("0.01"))
    taker_fee: Decimal = Field(default=Decimal("0.0005"), ge=0, le=Decimal("0.01"))
    slippage_bps: Decimal = Field(default=Decimal("2"), ge=0, le=100)
    initial_cash: Decimal = Field(default=Decimal("10000"), gt=0)
    stale_seconds: float = Field(default=10, gt=0, le=60)
    order_timeout_seconds: float = Field(default=30, gt=0, le=300)
    instrument_id: str | None = None
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port: int = Field(default=8765, ge=1024, le=65535)

    @model_validator(mode="after")
    def postgres_only(self) -> "Settings":
        if not self.database_url.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("Production storage must be PostgreSQL with psycopg")
        return self
