from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hub.config import Settings
from hub.store.blob_store import BlobStore
from hub.store.postgres_blob_store import PostgresBlobStore


def make_blob_store(settings: Settings, sessions: async_sessionmaker[AsyncSession]) -> BlobStore:
    if settings.blob_backend == "postgres":
        return PostgresBlobStore(sessions)
    raise ValueError(f"BLOB_BACKEND não suportado: {settings.blob_backend}")
