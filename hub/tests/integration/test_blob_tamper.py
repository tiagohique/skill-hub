import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from hub.domain.errors import IntegrityError
from hub.store.postgres_blob_store import PostgresBlobStore


async def test_tampered_blob_raises_integrity_error(
    app_engine: AsyncEngine, owner_engine: AsyncEngine
) -> None:
    store = PostgresBlobStore(async_sessionmaker(app_engine, expire_on_commit=False))
    digest = await store.put(b"conteudo original")
    async with owner_engine.begin() as conn:  # só o dono consegue adulterar
        await conn.execute(text("UPDATE blobs SET content = 'adulterado'"))
    with pytest.raises(IntegrityError):
        await store.get(digest)
