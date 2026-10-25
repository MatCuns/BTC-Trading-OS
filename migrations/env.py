from alembic import context
from sqlalchemy import create_engine

from btc_os.config import Settings
from btc_os.storage import metadata


def run() -> None:
    engine = create_engine(Settings().database_url.get_secret_value())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata, include_schemas=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run()
