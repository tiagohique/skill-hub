import hashlib
from collections.abc import Iterable

from hub.domain.models import FileEntry


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_sha256(entries: Iterable[FileEntry]) -> str:
    """SHA-256 do texto `path\\0sha256`, uma linha por arquivo, ordenado por path."""
    lines = [f"{e.path}\0{e.sha256}" for e in sorted(entries, key=lambda e: e.path)]
    return sha256_hex("\n".join(lines).encode())
