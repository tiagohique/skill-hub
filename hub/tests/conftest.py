import os
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


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
