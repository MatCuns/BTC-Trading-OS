import hashlib
import json
from typing import Any, Protocol

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from btc_os.domain import Ledger, Quote, now

metadata = MetaData()
runtime = Table(
    "runtime",
    metadata,
    Column("id", String, primary_key=True),
    Column("version", Integer, nullable=False),
    Column("payload", JSONB, nullable=False),
    schema="system",
)
events = Table(
    "event",
    metadata,
    Column("dedupe_hash", String(64), primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("ingest_time", DateTime(timezone=True), nullable=False),
    Column("source", String, nullable=False),
    Column("quality", String, nullable=False),
    Column("payload_reference", String, nullable=False),
    Column("payload", JSONB, nullable=False),
    schema="market",
)
Index("ix_event_timestamp", events.c.timestamp)


def ledger_tables(schema: str) -> dict[str, Table]:
    result: dict[str, Table] = {}
    for name in (
        "account",
        "orders",
        "fills",
        "positions",
        "balances",
        "snapshots",
        "funding",
        "requests",
        "decisions",
    ):
        cols: list[Any] = [
            Column("id", String, primary_key=True),
            Column("environment_id", String, nullable=False),
            Column("timestamp", DateTime(timezone=True), nullable=False),
            Column("payload", JSONB, nullable=False),
        ]
        if name == "fills":
            cols.append(
                Column("order_id", String, ForeignKey(f"{schema}.orders.id"), nullable=False)
            )
            cols.append(Column("fee", Numeric(30, 12), nullable=False))
        cols.append(
            CheckConstraint(
                "environment_id = '"
                + ("INTERNAL_PAPER" if schema == "paper" else "OKX_LIVE")
                + "'",
                name=f"ck_{schema}_{name}_environment",
            )
        )
        result[name] = Table(name, metadata, *cols, schema=schema)
        Index(f"ix_{schema}_{name}_time", result[name].c.timestamp)
    return result


TABLES = {name: ledger_tables(name) for name in ("paper", "live")}


class Store(Protocol):
    def load(self) -> Ledger | None: ...
    def save(self, ledger: Ledger, expected_version: int) -> None: ...
    def lookup_request(
        self, client_id: str
    ) -> tuple[dict[str, Any], list[dict[str, Any]]] | None: ...
    def event(self, quote: Quote) -> None: ...
    def ping(self) -> bool: ...


class PostgresStore:
    def __init__(self, url: str):
        if not url.startswith("postgresql+psycopg://"):
            raise ValueError("PostgreSQL required")
        self.fingerprints: dict[tuple[str, str], str] = {}
        self.engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
            pool_timeout=3,
            connect_args={"connect_timeout": 3},
        )

    def ping(self) -> bool:
        with self.engine.connect() as conn:
            conn.execute(text("select 1"))
        return True

    def load(self) -> Ledger | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(runtime.c.payload).where(runtime.c.id == "INTERNAL_PAPER")
            ).first()
        return Ledger.model_validate(row[0]) if row else None

    def save(self, ledger: Ledger, expected_version: int) -> None:
        if ledger.environment_id != "INTERNAL_PAPER":
            raise PermissionError("R1 store only accepts INTERNAL_PAPER")
        if any(
            item.environment_id != "INTERNAL_PAPER"
            for item in [ledger.account, *ledger.orders, *ledger.fills]
        ):
            raise PermissionError("Nested ledger environment mismatch")
        tables = TABLES["paper"]
        next_fingerprints = dict(self.fingerprints)
        payload = ledger.model_dump(mode="json")
        with self.engine.begin() as conn:
            # Serialize even the first write; exactly one runtime writer per database.
            conn.execute(text("SELECT pg_advisory_xact_lock(82461327)"))
            version = conn.execute(
                select(runtime.c.version).where(runtime.c.id == "INTERNAL_PAPER")
            ).scalar()
            if (version or 0) != expected_version:
                raise RuntimeError("Concurrent writer: reconciliation required")
            conn.execute(
                insert(runtime)
                .values(id="INTERNAL_PAPER", version=ledger.version, payload=payload)
                .on_conflict_do_update(
                    index_elements=[runtime.c.id],
                    set_={"version": ledger.version, "payload": payload},
                )
            )
            stamp = now()
            items: dict[str, list[tuple[str, dict[str, Any]]]] = {
                "account": [("primary", payload["account"])],
                "requests": list(ledger.requests.items()),
                "positions": [
                    (
                        "primary",
                        {
                            "quantity": str(ledger.account.quantity),
                            "average_price": str(ledger.account.average_price),
                        },
                    )
                ],
                "balances": [
                    (
                        "primary",
                        {
                            "cash": str(ledger.account.cash),
                            "fees": str(ledger.account.fees),
                            "funding": str(ledger.account.funding),
                        },
                    )
                ],
                "snapshots": [
                    (
                        str(ledger.version),
                        {
                            "account": payload["account"],
                            "quote": payload.get("last_quote"),
                            "equity": str(
                                ledger.account.equity(
                                    ledger.last_quote.last, ledger.instrument.contract_btc
                                )
                            )
                            if ledger.last_quote and ledger.instrument
                            else str(ledger.account.cash),
                        },
                    )
                ],
                "orders": [(o.client_id, o.model_dump(mode="json")) for o in ledger.orders],
                "fills": [(f.id, f.model_dump(mode="json")) for f in ledger.fills],
                "funding": [(f["id"], f) for f in ledger.funding_events],
                "decisions": [(d["decision_id"], d) for d in ledger.decisions],
            }
            for name, values in items.items():
                table = tables[name]
                for item_id, item in values:
                    fingerprint = hashlib.sha256(
                        json.dumps(item, sort_keys=True).encode()
                    ).hexdigest()
                    key = (name, item_id)
                    if self.fingerprints.get(key) == fingerprint:
                        continue
                    next_fingerprints[key] = fingerprint
                    row: dict[str, Any] = {
                        "id": item_id,
                        "environment_id": "INTERNAL_PAPER",
                        "timestamp": stamp,
                        "payload": item,
                    }
                    if name == "fills":
                        row.update(order_id=item["client_id"], fee=item["fee"])
                    stmt = insert(table).values(**row)
                    if name in {"account", "positions", "balances", "orders"}:
                        stmt = stmt.on_conflict_do_update(
                            index_elements=[table.c.id], set_={"payload": item, "timestamp": stamp}
                        )
                    else:
                        stmt = stmt.on_conflict_do_nothing(index_elements=[table.c.id])
                    conn.execute(stmt)
        # Cache only bounded, current runtime entities. Immutable history remains in PostgreSQL.
        current_keys = {
            (name, item_id)
            for name, values in items.items()
            if name != "snapshots"
            for item_id, _ in values
        }
        self.fingerprints = {k: v for k, v in next_fingerprints.items() if k in current_keys}

    def lookup_request(self, client_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
        tables = TABLES["paper"]
        with self.engine.connect() as conn:
            row = conn.execute(
                select(tables["requests"].c.payload).where(tables["requests"].c.id == client_id)
            ).first()
            if not row:
                return None
            orders = conn.execute(
                select(tables["orders"].c.payload).where(
                    tables["orders"].c.id.in_([client_id + "-close", client_id + "-target"])
                )
            ).all()
            return row[0], [o[0] for o in orders]

    def event(self, quote: Quote) -> None:
        payload = quote.model_dump(mode="json")
        canonical = {k: v for k, v in payload.items() if k != "ingest_time"}
        digest = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        with self.engine.begin() as conn:
            conn.execute(
                insert(events)
                .values(
                    dedupe_hash=digest,
                    timestamp=quote.timestamp,
                    ingest_time=quote.ingest_time,
                    source=quote.source,
                    quality="validated",
                    payload_reference=f"market.event/{digest}",
                    payload=payload,
                )
                .on_conflict_do_nothing()
            )

    def close(self) -> None:
        self.engine.dispose()
