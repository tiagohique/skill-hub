from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hub.domain.errors import IntegrityError, NotFoundError
from hub.domain.hashing import sha256_hex
from hub.repositories.tables import blobs


class PostgresBlobStore:
    """BlobStore da POC: grava na tabela `blobs` (só INSERT e SELECT)."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def put(self, data: bytes) -> str:
        digest = sha256_hex(data)
        stmt = (
            insert(blobs)
            .values(sha256=digest, content=data, size=len(data))
            .on_conflict_do_nothing(index_elements=["sha256"])
        )
        async with self._sessions.begin() as session:
            await session.execute(stmt)
        return digest

    async def get(self, sha256: str) -> bytes:
        async with self._sessions() as session:
            row = (
                await session.execute(select(blobs.c.content).where(blobs.c.sha256 == sha256))
            ).first()
        if row is None:
            raise NotFoundError(f"Conteúdo não encontrado: {sha256}")
        content = bytes(row[0])
        if sha256_hex(content) != sha256:
            raise IntegrityError(f"Conteúdo adulterado: o hash de {sha256} não confere.")
        return content

    async def exists(self, sha256: str) -> bool:
        async with self._sessions() as session:
            row = (
                await session.execute(select(blobs.c.sha256).where(blobs.c.sha256 == sha256))
            ).first()
        return row is not None
