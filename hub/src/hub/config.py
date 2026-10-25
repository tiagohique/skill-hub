import os
from collections.abc import Mapping
from dataclasses import dataclass


def _required(env: Mapping[str, str], name: str) -> str:
    try:
        return env[name]
    except KeyError:
        raise ValueError(f"Variável de ambiente obrigatória ausente: {name}") from None


@dataclass(frozen=True)
class Settings:
    database_url: str
    migration_database_url: str
    blob_backend: str
    max_file_bytes: int
    max_bundle_bytes: int
    max_files: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        return cls(
            database_url=_required(env, "DATABASE_URL"),
            migration_database_url=_required(env, "MIGRATION_DATABASE_URL"),
            blob_backend=env.get("BLOB_BACKEND", "postgres"),
            max_file_bytes=int(env.get("MAX_FILE_BYTES", 1048576)),
            max_bundle_bytes=int(env.get("MAX_BUNDLE_BYTES", 5242880)),
            max_files=int(env.get("MAX_FILES", 100)),
        )
