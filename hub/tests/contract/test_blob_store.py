"""Testes de contrato do BlobStore.

Toda implementação de BlobStore (hoje `InMemoryBlobStore` e `PostgresBlobStore`;
no futuro `S3BlobStore` e `AzureBlobStore`) precisa passar por estes testes:
basta acrescentar o nome em `params` da fixture `blob_store`.
"""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from hub.domain.errors import NotFoundError
from hub.store.blob_store import BlobStore
from hub.store.postgres_blob_store import PostgresBlobStore
from tests.fakes import InMemoryBlobStore

ABC_SHA = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest_asyncio.fixture(params=["memory", "postgres"])
async def blob_store(
    request: pytest.FixtureRequest, app_engine: AsyncEngine, clean_db: None
) -> AsyncIterator[BlobStore]:
    if request.param == "memory":
        yield InMemoryBlobStore()
    else:
        yield PostgresBlobStore(async_sessionmaker(app_engine, expire_on_commit=False))


async def test_put_returns_sha256_hex(blob_store: BlobStore) -> None:
    assert await blob_store.put(b"abc") == ABC_SHA


async def test_put_is_idempotent(blob_store: BlobStore) -> None:
    assert await blob_store.put(b"abc") == await blob_store.put(b"abc")
    assert await blob_store.get(ABC_SHA) == b"abc"


async def test_get_roundtrip(blob_store: BlobStore) -> None:
    data = bytes(range(256)) * 10
    digest = await blob_store.put(data)
    assert await blob_store.get(digest) == data


async def test_exists_true_false(blob_store: BlobStore) -> None:
    assert not await blob_store.exists(ABC_SHA)
    await blob_store.put(b"abc")
    assert await blob_store.exists(ABC_SHA)


async def test_get_unknown_raises_not_found(blob_store: BlobStore) -> None:
    with pytest.raises(NotFoundError):
        await blob_store.get("0" * 64)


async def test_put_empty_bytes(blob_store: BlobStore) -> None:
    assert await blob_store.put(b"") == EMPTY_SHA
    assert await blob_store.get(EMPTY_SHA) == b""


async def test_postgres_put_does_not_duplicate(app_engine: AsyncEngine, clean_db: None) -> None:
    store = PostgresBlobStore(async_sessionmaker(app_engine, expire_on_commit=False))
    await store.put(b"abc")
    await store.put(b"abc")
    async with app_engine.connect() as conn:
        count = (await conn.execute(text("SELECT count(*) FROM blobs"))).scalar_one()
    assert count == 1
