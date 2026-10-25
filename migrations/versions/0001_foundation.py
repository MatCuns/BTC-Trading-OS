"""Separated market, system, paper and disabled live ledgers."""

from alembic import op

from btc_os.storage import metadata

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for schema in ("market", "system", "paper", "live"):
        op.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    metadata.create_all(op.get_bind())


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade disabled: restore to a separate database")
