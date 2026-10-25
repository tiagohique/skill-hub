"""Dublês de teste. Não fazem parte do código do hub."""

from hub.domain.errors import IntegrityError, NotFoundError
from hub.domain.hashing import sha256_hex


class InMemoryBlobStore:
    """BlobStore em memória, com a mesma semântica das implementações reais."""

    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}

    async def put(self, data: bytes) -> str:
        digest = sha256_hex(data)
        self.blobs.setdefault(digest, data)
        return digest

    async def get(self, sha256: str) -> bytes:
        try:
            data = self.blobs[sha256]
        except KeyError:
            raise NotFoundError(f"Conteúdo não encontrado: {sha256}") from None
        if sha256_hex(data) != sha256:
            raise IntegrityError(f"Conteúdo adulterado: {sha256}")
        return data

    async def exists(self, sha256: str) -> bool:
        return sha256 in self.blobs
