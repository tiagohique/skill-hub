import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command

TABLES = "audit_events, channels, skill_version_files, skill_versions, blobs, skills"


@pytest_asyncio.fixture
async def owner_engine() -> AsyncIterator[AsyncEngine]:
    """Engine do dono do esquema (migrações e preparação de testes)."""
    engine = create_async_engine(os.environ["TEST_MIGRATION_DATABASE_URL"])
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    """Engine do usuário da aplicação, com permissões mínimas."""
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def migrated() -> None:
    """Recria o esquema do banco de teste via Alembic (fixture síncrona: env.py usa asyncio.run)."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", os.environ["TEST_MIGRATION_DATABASE_URL"])
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture
async def clean_db(migrated: None, owner_engine: AsyncEngine) -> None:
    """Esvazia as tabelas (como dono) antes de cada teste que usa o banco."""
    async with owner_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))
