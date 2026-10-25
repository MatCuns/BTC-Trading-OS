from datetime import timedelta
from decimal import Decimal

import pytest
from conftest import MemoryStore, quote

from btc_os.config import Settings
from btc_os.domain import TargetRequest, now
from btc_os.engine import ReferenceStrategy, TradingEngine
from btc_os.risk import RiskRejected

D = Decimal


def request(cid="orderA", target="0.25", **kwargs):
    return TargetRequest(client_id=cid, target=D(target), **kwargs)


async def test_order_fill_fee_pnl_idempotency(engine):
    result = await engine.target(request())
    assert result[0].status == "FILLED"
    assert engine.ledger.account.quantity > 0
    assert engine.ledger.account.fees > 0
    qty = engine.ledger.account.quantity
    await engine.target(request())
    assert engine.ledger.account.quantity == qty
    assert len(engine.ledger.fills) == 1
    with pytest.raises(RiskRejected, match="different request"):
        await engine.target(request(target="0.20"))
    await engine.tick(quote("65100"))
    await engine.target(request("flatA", "0"))
    assert engine.ledger.account.quantity == 0
    assert engine.ledger.account.realized_pnl > 0
    assert (
        engine.ledger.account.cash
        == D("10000") + engine.ledger.account.realized_pnl - engine.ledger.account.fees
    )
    assert engine.store.saved.account == engine.ledger.account


async def test_reverse_commits_close_before_open_and_respects_partial(engine):
    await engine.target(request())
    await engine.target(request("reverseA", "-0.25"))
    assert engine.ledger.account.quantity == 0
    assert engine.ledger.reverse
    assert engine.store.saved.account.quantity == 0
    await engine.tick(quote("65001"))
    assert engine.ledger.account.quantity < 0
    assert engine.ledger.reverse is None
    assert engine.ledger.orders[1].reduce_only
    assert engine.ledger.orders[-1].client_id == "reverseA-target"


async def test_partial_then_timeout_cancels_reverse(engine):
    await engine.target(request())
    await engine.tick(quote(size="1"))
    await engine.target(request("reverseA", "-0.25"))
    close = engine.ledger.orders[-1]
    assert close.status == "PARTIAL"
    close.created_at = now() - timedelta(seconds=60)
    await engine.tick(quote())
    assert close.status == "CANCELLED"
    assert engine.ledger.reverse is None
    assert engine.ledger.account.quantity > 0


async def test_restart_mid_order_reconciles_and_disarms(engine):
    await engine.tick(quote(size="1"))
    await engine.target(request())
    assert engine.ledger.orders[-1].status == "PARTIAL"
    restored = TradingEngine(engine.settings, engine.store)
    restored.start()
    assert restored.ledger.orders[-1].status == "CANCELLED"
    assert restored.ledger.account.quantity == engine.ledger.account.quantity
    assert restored.ledger.account.kill_switch
    assert not restored.ledger.account.strategy_enabled
    assert restored.reconciled


async def test_db_disconnect_and_ambiguous_commit_block(engine):
    engine.store.fail = True
    with pytest.raises(RiskRejected, match="Persistence unknown"):
        await engine.target(request())
    assert engine.ledger.account.quantity == 0
    assert not engine.persistence_ok
    engine.store.fail = False
    with pytest.raises(RiskRejected):
        await engine.target(request("new"))
    engine.start()
    await engine.controls(kill=False)
    engine.store.ambiguous = True
    with pytest.raises(RiskRejected):
        await engine.target(request())
    assert not engine.reconciled
    assert engine.store.saved.account.quantity > 0
    engine.store.ambiguous = False
    engine.start()
    assert engine.ledger.account.quantity > 0
    assert len(engine.ledger.fills) == 1


async def test_stale_feed_no_open_or_blind_close(engine):
    await engine.target(request())
    qty = engine.ledger.account.quantity
    engine.quote.timestamp = now() - timedelta(seconds=30)
    with pytest.raises(RiskRejected, match="Stale"):
        await engine.target(request("flatA", "0"))
    assert engine.ledger.account.quantity == qty
    assert "STALE_FEED" in engine.snapshot()["risk_flags"]


async def test_stop_gaps_and_daily_loss(engine):
    await engine.target(request())
    await engine.tick(quote("63000"))
    assert engine.ledger.account.quantity == 0
    assert engine.ledger.account.kill_switch
    assert any(o.reason == "STOP" for o in engine.ledger.orders)
    assert engine.ledger.account.realized_pnl < 0
    await engine.controls(kill=False)
    engine.ledger.account.day_equity = D("20000")
    with pytest.raises(RiskRejected, match="Daily loss"):
        await engine.target(request("another"))


async def test_kill_switch_cancels_entry_and_allows_flat(engine):
    await engine.target(request())
    await engine.controls(kill=True)
    with pytest.raises(RiskRejected, match="Kill switch"):
        await engine.target(request("bigger", "0.3"))
    await engine.target(request("flatA", "0"))
    assert engine.ledger.account.quantity == 0


async def test_funding_once_separate_cost(engine):
    await engine.target(request())
    cash = engine.ledger.account.cash
    await engine.funding("funding1", D("0.001"), D("65000"))
    changed = engine.ledger.account.cash
    assert changed < cash
    await engine.funding("funding1", D("0.001"), D("65000"))
    assert engine.ledger.account.cash == changed
    assert engine.ledger.account.funding == changed - cash


async def test_limits_and_environment_isolation(engine):
    with pytest.raises(RiskRejected, match="cap"):
        await engine.target(request(target="5"))
    with pytest.raises(RiskRejected, match="budget"):
        await engine.target(request(target="0.9"))
    with pytest.raises(RiskRejected, match="costs"):
        await engine.target(request(expected_edge_bps=D("1")))
    with pytest.raises(RiskRejected, match="Environment"):
        await engine.target(request(environment_id="OKX_LIVE"))
    with pytest.raises(ValueError):
        Settings(database_url="sqlite://", _env_file=None)
    with pytest.raises(ValueError):
        TargetRequest(client_id="bad", target=D("5.01"))
    assert engine.snapshot()["live_enabled"] is False


async def test_limit_order_and_tick_size(engine):
    orders = await engine.target(request(limit_price=D("64990")))
    assert orders[0].status == "OPEN"
    await engine.tick(quote("64980"))
    assert orders[0].status == "FILLED"
    fill = engine.ledger.fills[-1]
    assert fill.price <= D("64990")
    assert fill.liquidity == "maker"


def test_technical_5x_risk_cap(engine):
    engine.settings.max_leverage = D("5")
    engine.settings.trade_loss_budget = D("0.05")
    a, i, q = engine.ledger.account, engine.ledger.instrument, engine.quote
    engine.risk.check(a, i, q, D("4.9"), D("0.001"), D("30"), True, True)
    with pytest.raises(RiskRejected, match="cap"):
        engine.risk.check(a, i, q, D("5.01"), D("0.001"), D("30"), True, True)


def test_strategy_warmup_default_flat():
    s = ReferenceStrategy()
    assert all(s.target(D("65000")) == 0 for _ in range(80))
    store = MemoryStore()
    e = TradingEngine(Settings(_env_file=None), store)
    e.start()
    assert not e.ledger.account.strategy_enabled
