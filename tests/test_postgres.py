import os

import pytest
from conftest import quote
from sqlalchemy import text

from btc_os.config import Settings
from btc_os.domain import TargetRequest
from btc_os.engine import TradingEngine
from btc_os.feed import fixture_instrument
from btc_os.storage import PostgresStore


@pytest.mark.skipif(
    not os.environ.get("BTC_TEST_DATABASE_URL"),
    reason="Requires an isolated PostgreSQL test database",
)
async def test_real_transaction_ledger_restart_and_separation():
    url = os.environ["BTC_TEST_DATABASE_URL"]
    store = PostgresStore(url)
    e = TradingEngine(Settings(database_url=url, _env_file=None), store)
    e.start()
    assert e.reconciled
    e.set_instrument(fixture_instrument())
    await e.tick(quote())
    await e.controls(kill=False)
    await e.target(TargetRequest(client_id="integrationA", target="0.25"))
    with store.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM paper.fills")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM live.fills")).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM market.event")).scalar() == 1
        assert (
            conn.execute(text("SELECT environment_id FROM paper.fills LIMIT 1")).scalar()
            == "INTERNAL_PAPER"
        )
    recovered = TradingEngine(e.settings, store)
    recovered.start()
    assert recovered.ledger.account.quantity == e.ledger.account.quantity
    assert recovered.ledger.account.kill_switch
    store.close()


@pytest.mark.skipif(
    not os.environ.get("BTC_TEST_DATABASE_URL"), reason="Requires isolated PostgreSQL"
)
def test_resumable_bootstrap_and_minimum_runtime_privileges(tmp_path):
    from subprocess import CompletedProcess
    from unittest.mock import patch

    import psycopg
    from dotenv import dotenv_values
    from sqlalchemy.engine import make_url

    from btc_os.cli import database_setup

    url = make_url(os.environ["BTC_TEST_DATABASE_URL"])
    params = dict(
        config_path=tmp_path / ".env",
        host=url.host,
        port=url.port or 5432,
        admin=url.username,
        database="btc_bootstrap_ci",
        password=url.password or "",
        data_root=str(tmp_path),
        backup_root=str(tmp_path / "backup"),
        feed_mode="fixture",
    )
    with patch("btc_os.cli.subprocess.run", return_value=CompletedProcess([], 1)):
        with pytest.raises(RuntimeError, match="Migration failed"):
            database_setup(**params)
    assert (tmp_path / ".runtime" / "db-bootstrap.pending.json").exists()
    database_setup(**params)
    assert not (tmp_path / ".runtime" / "db-bootstrap.pending.json").exists()
    app_url = dotenv_values(tmp_path / ".env")["BTC_DATABASE_URL"]
    with psycopg.connect(
        app_url.replace("postgresql+psycopg", "postgresql"), autocommit=True
    ) as conn:
        assert conn.execute("select current_user").fetchone()[0] == "btc_app"
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT * FROM live.fills")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("DELETE FROM paper.fills")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("CREATE TABLE paper.forbidden (id int)")

    # The generated runtime credentials must also support the real backup path.
    import json
    from io import StringIO

    from btc_os.cli import backup, restore_drill

    with patch.dict(
        os.environ, {"BTC_DATABASE_URL": app_url, "BTC_BACKUP_ROOT": str(tmp_path / "backup")}
    ):
        app_store = PostgresStore(app_url)
        runtime = TradingEngine(Settings(database_url=app_url, _env_file=None), app_store)
        runtime.start()
        assert runtime.reconciled
        backup("pg_dump")
        backup("pg_restore", restore=True)
        with patch(
            "sys.stdin",
            StringIO(json.dumps({"admin": url.username, "password": url.password or ""}) + "\n"),
        ):
            restore_drill("pg_restore")
        app_store.close()
