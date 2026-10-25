import asyncio
import os

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from hub.repositories.tables import metadata

config = context.config
url = config.get_main_option("sqlalchemy.url") or os.environ["MIGRATION_DATABASE_URL"]
config.set_main_option("sqlalchemy.url", url)


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}), poolclass=pool.NullPool
    )
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Modo offline não suportado.")
asyncio.run(_run_async())
