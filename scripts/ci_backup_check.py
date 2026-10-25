"""Full non-destructive restore to an isolated CI database (not an operational DB)."""

import os
import subprocess
import tempfile
from pathlib import Path

import psycopg

url = os.environ["BTC_TEST_DATABASE_URL"].replace("postgresql+psycopg", "postgresql")
with tempfile.TemporaryDirectory() as temporary:
    archive = str(Path(temporary) / "paper.dump")
    subprocess.run(["pg_dump", "-d", url, "-Fc", "-f", archive], check=True)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("CREATE DATABASE btc_restore_ci")
    target = url.rsplit("/", 1)[0] + "/btc_restore_ci"
    subprocess.run(
        ["pg_restore", "--no-owner", "--no-privileges", "-d", target, archive], check=True
    )
    with psycopg.connect(target) as restored:
        assert restored.execute("SELECT count(*) FROM paper.fills").fetchone()[0] == 1
        assert restored.execute("SELECT count(*) FROM live.fills").fetchone()[0] == 0
        assert restored.execute("SELECT count(*) FROM system.runtime").fetchone()[0] == 1
    print("PASS: full isolated PostgreSQL restore, PAPER ledger and empty LIVE ledger")
