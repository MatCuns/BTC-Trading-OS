import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from conftest import MemoryStore
from fastapi.testclient import TestClient
from pydantic import SecretStr

from btc_os.api import create_app
from btc_os.brokers import OkxDemoAdapter, OkxLiveAdapter
from btc_os.config import Settings
from btc_os.domain import Order, now
from btc_os.feed import MarketFeed, discover


def metadata():
    return {
        "instId": "BTC-USDC-301227",
        "instType": "FUTURES",
        "ruleType": "xperp",
        "state": "live",
        "ctType": "linear",
        "ctValCcy": "BTC",
        "ctVal": "0.001",
        "ctMult": "1",
        "settleCcy": "USDC",
        "tickSz": "0.1",
        "lotSz": "1",
        "minSz": "1",
        "expTime": str(int((now() + timedelta(days=100)).timestamp() * 1000)),
    }


def test_discovery_no_swap_or_inverse_fallback():
    row = metadata()
    assert discover([row]).contract_btc == Decimal("0.001")
    for field, value in [
        ("instType", "SWAP"),
        ("ruleType", "normal"),
        ("ctType", "inverse"),
        ("ctVal", "0"),
        ("expTime", "1"),
    ]:
        with pytest.raises(ValueError):
            discover([{**row, field: value}])
    with pytest.raises(ValueError, match="Multiple"):
        discover([row, {**row, "instId": "BTC-USDT-301227"}])
    assert discover([row], row["instId"]).inst_id == row["instId"]


def test_api_no_keys_csrf_live_disabled_and_websocket(tmp_path):
    app = create_app(Settings(data_root=tmp_path, _env_file=None), MemoryStore(), start_feed=False)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["reconciled"]
        assert client.post("/api/paper/controls", json={"kill_switch": False}).status_code == 403
        assert (
            client.post(
                "/api/paper/controls",
                json={"kill_switch": False},
                headers={"X-BTC-OS": "paper-terminal", "Origin": "http://evil.example"},
            ).status_code
            == 403
        )
        assert client.post("/api/live/target", json={}).status_code == 404
        assert (
            client.post(
                "/api/paper/controls",
                json={"kill_switch": False},
                headers={"X-BTC-OS": "paper-terminal"},
            ).status_code
            == 200
        )
        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert msg["environment_id"] == "INTERNAL_PAPER"
            assert msg["live_enabled"] is False
            assert msg["equity"] == "10000"


async def test_demo_header_signature_and_environment_gate():
    captured = []

    def handler(req):
        captured.append(req)
        return httpx.Response(200, json={"code": "0", "data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = OkxDemoAdapter(
            SecretStr("demo"), SecretStr("testsecret"), SecretStr("testpass"), client
        )
        result = await adapter.request("GET", "/api/v5/account/balance")
        assert result["code"] == "0"
        assert captured[0].headers["x-simulated-trading"] == "1"
        assert captured[0].url.host == "eea.okx.com"
        assert captured[0].headers["OK-ACCESS-SIGN"]
        with pytest.raises(PermissionError):
            await adapter.request("POST", "/api/v5/asset/withdrawal")
        with pytest.raises(PermissionError):
            await adapter.place(
                Order(
                    client_id="a",
                    decision_id="d",
                    inst_id="BTC-USDC-301227",
                    side="buy",
                    quantity=1,
                    reason="test",
                ),
                discover([metadata()]),
                True,
            )
    with pytest.raises(PermissionError):
        OkxLiveAdapter().execute(None, None, None, None)


async def test_mock_websocket_heartbeat_and_timeout(engine):
    # A fresh discovery must not reuse the fixture's previous settlement context.
    engine.ledger.instrument = None
    engine.quote = None
    feed = MarketFeed(engine)
    row = metadata()
    ticker = {
        "instId": row["instId"],
        "bidPx": "65000",
        "askPx": "65001",
        "last": "65000",
        "bidSz": "1",
        "askSz": "1",
        "ts": str(int(now().timestamp() * 1000)),
    }
    public = AsyncMock(side_effect=[[{"ts": str(int(now().timestamp() * 1000))}], [row], [ticker]])
    socket = AsyncMock()
    socket.recv.side_effect = [TimeoutError(), "pong", json.dumps({"event": "error"})]
    cm = AsyncMock()
    cm.__aenter__.return_value = socket
    with patch("btc_os.feed.connect", return_value=cm), patch.object(feed, "public", public):
        with pytest.raises(ValueError, match="subscription"):
            await feed.session()
    assert any(call.args[0] == "ping" for call in socket.send.call_args_list)


async def test_reconnect_backoff_and_cancellation(engine):
    feed = MarketFeed(engine)
    with (
        patch.object(feed, "session", AsyncMock(side_effect=ValueError("test unavailable"))),
        patch(
            "btc_os.feed.asyncio.sleep", AsyncMock(side_effect=__import__("asyncio").CancelledError)
        ),
    ):
        with pytest.raises(__import__("asyncio").CancelledError):
            await feed.run()
    assert feed.metrics["reconnects"] == 1
    assert not feed.metrics["connected"]


def test_unavailable_database_does_not_invent_account_kpis(tmp_path):
    store = MemoryStore()
    store.fail = True
    app = create_app(Settings(data_root=tmp_path, _env_file=None), store, start_feed=False)
    with TestClient(app) as client:
        state = client.get("/api/state").json()
        assert state["equity"] is None
        assert state["leverage"] is None
        assert state["system"]["reconciled"] is False
        assert "PERSISTENCE_UNKNOWN" in state["risk_flags"]
