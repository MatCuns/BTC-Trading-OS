from datetime import timedelta
from decimal import Decimal

import pytest

from btc_os.config import Settings
from btc_os.domain import Ledger, Quote, now
from btc_os.engine import TradingEngine
from btc_os.feed import fixture_instrument


class MemoryStore:
    """Explicit unit-test double. Production never uses this store."""

    def __init__(self):
        self.saved = None
        self.fail = False
        self.ambiguous = False
        self.events = []

    def load(self):
        if self.fail:
            raise ConnectionError("test failure")
        return self.saved.model_copy(deep=True) if self.saved else None

    def save(self, ledger: Ledger, expected_version: int):
        if self.fail:
            raise ConnectionError("test failure")
        assert (self.saved.version if self.saved else 0) == expected_version
        self.saved = ledger.model_copy(deep=True)
        if self.ambiguous:
            raise ConnectionError("test failure after commit")

    def lookup_request(self, client_id):
        if self.fail:
            raise ConnectionError("test failure")
        if self.saved and client_id in self.saved.requests:
            return self.saved.requests[client_id], [
                o.model_dump(mode="json")
                for o in self.saved.orders
                if o.client_id.startswith(client_id + "-")
            ]
        return None

    def event(self, quote):
        if self.fail:
            raise ConnectionError("test failure")
        self.events.append(quote)

    def ping(self):
        return not self.fail


_last_stamp = now()


def quote(price="65000", size="1000", stamp=None):
    global _last_stamp
    if stamp is None:
        stamp = max(now(), _last_stamp + timedelta(microseconds=1))
        _last_stamp = stamp
    p = Decimal(price)
    return Quote(
        inst_id="FIXTURE-BTC-LINEAR",
        bid=p - 1,
        ask=p + 1,
        last=p,
        bid_size=Decimal(size),
        ask_size=Decimal(size),
        timestamp=stamp or now(),
        source="SYNTHETIC_FIXTURE",
    )


@pytest.fixture
async def engine(tmp_path):
    store = MemoryStore()
    settings = Settings(data_root=tmp_path, _env_file=None)
    e = TradingEngine(settings, store)
    e.start()
    e.set_instrument(fixture_instrument())
    await e.tick(quote())
    await e.controls(kill=False)
    return e
