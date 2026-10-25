import dataclasses

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from hub.config import Settings
from hub.store.factory import make_blob_store
from hub.store.postgres_blob_store import PostgresBlobStore

SETTINGS = Settings("x", "y", "postgres", 1, 1, 1)


def test_factory_postgres() -> None:
    sessions = async_sessionmaker(create_async_engine("postgresql+asyncpg://u:p@h/d"))
    assert isinstance(make_blob_store(SETTINGS, sessions), PostgresBlobStore)


def test_factory_unknown_backend() -> None:
    sessions = async_sessionmaker(create_async_engine("postgresql+asyncpg://u:p@h/d"))
    with pytest.raises(ValueError, match="BLOB_BACKEND não suportado: s3"):
        make_blob_store(dataclasses.replace(SETTINGS, blob_backend="s3"), sessions)
