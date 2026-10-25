from typing import Protocol


class BlobStore(Protocol):
    """Ponto de troca de armazenamento de conteúdo (endereçado por SHA-256)."""

    async def put(self, data: bytes) -> str:
        """Grava o conteúdo (idempotente) e devolve o sha256 em hex."""
        ...

    async def get(self, sha256: str) -> bytes:
        """Lê o conteúdo, recalcula o hash e levanta IntegrityError se divergir."""
        ...

    async def exists(self, sha256: str) -> bool: ...
