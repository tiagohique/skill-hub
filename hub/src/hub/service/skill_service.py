"""SkillService: toda a regra de negócio do hub.

É a única porta de entrada para repositórios e BlobStore. Os adaptadores
(`api/` e `mcp/`) só chamam este serviço.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hub.domain.errors import NotFoundError
from hub.domain.hashing import bundle_sha256
from hub.domain.models import (
    Channel,
    FileEntry,
    SkillDetail,
    SkillSummary,
    VersionDetail,
    VersionSummary,
)
from hub.repositories.audit import AuditRepository
from hub.repositories.catalog import CatalogRepository, SkillRow, VersionRow
from hub.service.validation import UploadLimits, parse_upload
from hub.store.blob_store import BlobStore

DEFAULT_DOMAIN = "geral"


class SkillService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        blobs: BlobStore,
        limits: UploadLimits,
    ) -> None:
        self._sessions = sessions
        self._blobs = blobs
        self._limits = limits

    async def upload(
        self, *, filename: str, data: bytes, version: str, actor: str
    ) -> VersionDetail:
        parsed = parse_upload(filename, data, version, self._limits)

        # Blobs fora da transação: órfãos são inofensivos (endereçados por conteúdo).
        entries = [
            FileEntry(f.path, await self._blobs.put(f.data), len(f.data)) for f in parsed.files
        ]

        metadata = parsed.frontmatter.get("metadata")
        meta: dict[str, Any] = metadata if isinstance(metadata, dict) else {}
        domain = str(meta.get("domain") or DEFAULT_DOMAIN)
        owner = str(meta.get("owner") or actor)

        async with self._sessions.begin() as session:
            catalog = CatalogRepository(session)
            skill_id = await catalog.get_or_create_skill(parsed.name, domain, owner)
            version_id = await catalog.insert_version(
                skill_id, version, parsed.frontmatter, bundle_sha256(entries), actor
            )
            await catalog.insert_files(version_id, entries)
            await AuditRepository(session).record(actor, "upload", parsed.name, version)
            row = await catalog.find_version(skill_id, version)
        assert row is not None
        return _detail(parsed.name, row, entries)

    async def list_skills(self) -> list[SkillSummary]:
        async with self._sessions() as session:
            catalog = CatalogRepository(session)
            skills = await catalog.list_skills()
            channels = await catalog.list_channels()
        return [
            SkillSummary(
                name=s.name,
                domain=s.domain,
                owner=s.owner,
                stable=channels.get(s.id, {}).get(Channel.STABLE),
                beta=channels.get(s.id, {}).get(Channel.BETA),
            )
            for s in skills
        ]

    async def get_skill(self, name: str) -> SkillDetail:
        async with self._sessions() as session:
            catalog = CatalogRepository(session)
            skill = await _require_skill(catalog, name)
            versions = await catalog.list_versions(skill.id)
            channels = await catalog.channels_of(skill.id)
        description = str(versions[0].frontmatter.get("description", "")) if versions else ""
        return SkillDetail(
            name=skill.name,
            domain=skill.domain,
            owner=skill.owner,
            description=description,
            channels=channels,
            versions=[
                VersionSummary(v.version, v.status, v.bundle_sha256, v.created_by, v.created_at)
                for v in versions
            ],
        )

    async def get_version(self, name: str, version: str) -> VersionDetail:
        async with self._sessions() as session:
            catalog = CatalogRepository(session)
            skill = await _require_skill(catalog, name)
            row = await catalog.find_version(skill.id, version)
            if row is None:
                raise NotFoundError(f"Versão {version} da skill '{name}' não encontrada.")
            files = await catalog.list_files(row.id)
        return _detail(name, row, files)


async def _require_skill(catalog: CatalogRepository, name: str) -> SkillRow:
    skill = await catalog.find_skill(name)
    if skill is None:
        raise NotFoundError(f"Skill '{name}' não encontrada.")
    return skill


def _detail(name: str, row: VersionRow, files: list[FileEntry]) -> VersionDetail:
    return VersionDetail(
        name=name,
        version=row.version,
        status=row.status,
        frontmatter=row.frontmatter,
        bundle_sha256=row.bundle_sha256,
        created_by=row.created_by,
        created_at=row.created_at,
        files=files,
    )
