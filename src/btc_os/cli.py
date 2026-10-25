"""Secret-free local diagnostics, bootstrap and PostgreSQL backup helpers."""

import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import psycopg
from psycopg import sql
from sqlalchemy import text

from btc_os.config import Settings
from btc_os.domain import now
from btc_os.storage import PostgresStore


def database_setup(
    config_path: Path,
    host: str,
    port: int,
    admin: str,
    database: str,
    password: str,
    data_root: str,
    backup_root: str,
    feed_mode: str,
) -> None:
    """Called locally with admin password on stdin by the Windows wizard."""
    role = "btc_app"
    pending = config_path.parent / ".runtime" / "db-bootstrap.pending.json"
    identity = {"host": host, "port": port, "admin": admin, "database": database}
    journal = json.loads(pending.read_text()) if pending.exists() else None
    if journal and any(journal[k] != v for k, v in identity.items()):
        raise ValueError("Resume with the same PostgreSQL host/port/admin/database")
    app_password = journal["app_password"] if journal else secrets.token_urlsafe(32)
    with psycopg.connect(
        host=host, port=port, user=admin, password=password, dbname="postgres", autocommit=True
    ) as conn:
        if conn.info.server_version < 160000:
            raise ValueError("PostgreSQL 16 or newer is required; no resources were changed")
        exists = conn.execute(
            "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=%s", (database,)
        ).fetchone()
        role_exists = conn.execute(
            "SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=%s", (role,)
        ).fetchone()
        if config_path.exists():
            raise ValueError(
                "Configuration exists; resume first_run instead of replacing credentials"
            )
        if (exists or role_exists) and not journal:
            raise ValueError(
                "Existing database or role without our setup journal; refusing to overwrite"
            )
        if exists and exists[0] != admin:
            raise ValueError("Database owner mismatch; refusing to alter")
        if role_exists and any(role_exists):
            raise ValueError("Application role privileges mismatch; refusing to alter")
        if not journal:
            pending.parent.mkdir(parents=True, exist_ok=True)
            with pending.open("x", encoding="utf-8") as output:
                json.dump({**identity, "app_password": app_password}, output)
            pending.chmod(0o600)
        if not role_exists:
            conn.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(sql.Identifier(role), sql.Literal(app_password))
            )
        if not exists:
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(admin)
                )
            )
        location = conn.execute("SHOW data_directory").fetchone()
        print(
            "PostgreSQL uses the existing cluster directory: "
            + str(location[0] if location else "unknown")
        )
        print(
            "Application data_root stores logs/exports; the wizard never relocates an existing database cluster."
        )
    # Administrative URL is process-local and never written to disk.
    admin_url = f"postgresql+psycopg://{quote(admin, safe='')}:{quote(password, safe='')}@{host}:{port}/{database}"
    env = {**os.environ, "BTC_DATABASE_URL": admin_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], env=env, capture_output=True
    )
    if result.returncode:
        raise RuntimeError(
            "Migration failed; no credentials printed. Inspect database with local administrator."
        )
    with psycopg.connect(
        host=host, port=port, user=admin, password=password, dbname=database, autocommit=True
    ) as conn:
        conn.execute(
            sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database))
        )
        conn.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(database), sql.Identifier(role)
            )
        )
        conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        conn.execute("REVOKE ALL ON SCHEMA live FROM PUBLIC")
        for schema in ("paper", "market", "system"):
            conn.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(role)
                )
            )
            conn.execute(
                sql.SQL("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(role)
                )
            )
        conn.execute(
            sql.SQL("GRANT SELECT ON TABLE public.alembic_version TO {}").format(
                sql.Identifier(role)
            )
        )
    url = f"postgresql+psycopg://{role}:{app_password}@{host}:{port}/{database}"
    contents = f"BTC_DATABASE_URL={url}\nBTC_DATA_ROOT={json.dumps(data_root, ensure_ascii=False)}\nBTC_BACKUP_ROOT={json.dumps(backup_root, ensure_ascii=False)}\nBTC_FEED_MODE={feed_mode}\n"
    temporary = pending.parent / "configured.env.pending"
    temporary.write_text(contents, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(config_path)
    pending.unlink()


def backup(executable: str, restore: bool = False) -> None:
    settings = Settings()
    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url.get_secret_value())
    env = {**os.environ, "PGPASSWORD": url.password or ""}
    args = [
        "-h",
        url.host or "127.0.0.1",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "btc_app",
    ]
    settings.backup_root.mkdir(parents=True, exist_ok=True)
    if restore:
        files = sorted(settings.backup_root.glob("paper-*.dump"))
        if not files:
            raise ValueError("No backup available")
        # Archive readability check only; real restore uses an isolated new DB in CI.
        result = subprocess.run([executable, "--list", str(files[-1])], capture_output=True)
        if result.returncode:
            raise RuntimeError("Backup archive is unreadable")
        print(json.dumps({"archive_readable": True, "restore_to_database_tested": False}))
    else:
        destination = settings.backup_root / ("paper-" + now().strftime("%Y%m%d-%H%M%S") + ".dump")
        result = subprocess.run(
            [
                executable,
                *args,
                "-d",
                url.database or "btc_quant",
                "-Fc",
                "-n",
                "paper",
                "-n",
                "system",
                "-n",
                "market",
                "-f",
                str(destination),
            ],
            env=env,
            capture_output=True,
        )
        if result.returncode:
            destination.unlink(missing_ok=True)
            raise RuntimeError("Backup failed; credentials redacted")
        print(json.dumps({"backup": str(destination), "bytes": destination.stat().st_size}))


def restore_drill(executable: str) -> None:
    """Restore only into a newly generated database; never replace or drop a DB."""
    settings = Settings()
    files = sorted(settings.backup_root.glob("paper-*.dump"))
    if not files:
        raise ValueError("No backup available")
    data = json.loads(input())
    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url.get_secret_value())
    admin = data["admin"]
    password = data["password"]
    database = "btc_restore_check_" + now().strftime("%Y%m%d%H%M%S") + "_" + secrets.token_hex(3)
    with psycopg.connect(
        host=url.host,
        port=url.port or 5432,
        user=admin,
        password=password,
        dbname="postgres",
        autocommit=True,
    ) as conn:
        conn.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(database), sql.Identifier(admin)
            )
        )
    env = {**os.environ, "PGPASSWORD": password}
    result = subprocess.run(
        [
            executable,
            "-h",
            url.host or "127.0.0.1",
            "-p",
            str(url.port or 5432),
            "-U",
            admin,
            "--no-owner",
            "--no-privileges",
            "-d",
            database,
            str(files[-1]),
        ],
        env=env,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError("Isolated restore failed; operational DB unchanged")
    with psycopg.connect(
        host=url.host, port=url.port or 5432, user=admin, password=password, dbname=database
    ) as conn:
        row = conn.execute(
            "SELECT payload FROM system.runtime WHERE id='INTERNAL_PAPER'"
        ).fetchone()
        if not row:
            raise RuntimeError("Restored runtime missing")
        from btc_os.domain import Ledger

        ledger = Ledger.model_validate(row[0])
        count = conn.execute("SELECT count(*) FROM paper.fills").fetchone()
        if not count or count[0] < len(ledger.fills):
            raise RuntimeError("Restored fills do not match runtime")
    print(
        json.dumps(
            {
                "restore_to_isolated_database": True,
                "test_database": database,
                "operational_database_changed": False,
                "action": "Test database retained for review; no automatic deletion",
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "doctor",
            "smoke",
            "db-setup",
            "backup",
            "restore-check",
            "restore-drill",
            "archive",
        ],
    )
    parser.add_argument("--executable", default="pg_dump")
    args = parser.parse_args()
    try:
        if args.command == "db-setup":
            data = json.loads(input())
            database_setup(config_path=Path(".env"), **data)
            print('{"database_setup": "complete"}')
            return
        if args.command == "restore-drill":
            restore_drill(args.executable)
            return
        if args.command in {"backup", "restore-check"}:
            backup(args.executable, args.command == "restore-check")
            return
        store = PostgresStore(Settings().database_url.get_secret_value())
        store.ping()
        with store.engine.connect() as conn:
            revision = conn.execute(text("select version_num from alembic_version")).scalar()
            if revision != "0001":
                raise RuntimeError("Unsupported database revision")
            if args.command == "archive":
                directory = Settings().backup_root
                directory.mkdir(parents=True, exist_ok=True)
                path = directory / ("market-archive-" + now().strftime("%Y%m%d-%H%M%S") + ".jsonl")
                rows = conn.execution_options(stream_results=True).execute(
                    text(
                        "SELECT payload FROM market.event WHERE timestamp < now() - interval '30 days' ORDER BY timestamp"
                    )
                )
                with path.open("w", encoding="utf-8") as output:
                    for row in rows:
                        output.write(json.dumps(row[0]) + "\n")
                print('{"archive_exported": true, "source_deleted": false}')
                return
        store.close()
        print(
            json.dumps(
                {
                    "postgresql": True,
                    "revision": revision,
                    "live_enabled": False,
                    "credentials_included": False,
                }
            )
        )
    except Exception as exc:
        # No DB exception text: drivers can embed credentials or connection strings.
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "action": "Check local PostgreSQL service, .env and migration using OPERATIONS.md",
                }
            )
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
