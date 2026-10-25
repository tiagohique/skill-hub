"""SkillService: toda a regra de negócio do hub.

É a única porta de entrada para repositórios e BlobStore. Os adaptadores
(`api/` e `mcp/`) só chamam este serviço.
"""

from dataclasses import replace
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hub.domain.errors import InvalidTransitionError, NotFoundError
from hub.domain.hashing import bundle_sha256
from hub.domain.models import (
    Channel,
    FileEntry,
    PublishedSkill,
    SkillDetail,
    SkillSummary,
    Status,
    VersionDetail,
    VersionSummary,
    channel_for,
    check_transition,
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

    async def promote(self, name: str, version: str, to: Status, actor: str) -> VersionDetail:
        if to not in (Status.BETA, Status.STABLE):
            raise InvalidTransitionError(f"Só é possível promover para beta ou stable, não {to}.")
        return await self._transition(name, version, to, actor, "promote")

    async def deprecate(self, name: str, version: str, actor: str) -> VersionDetail:
        return await self._transition(name, version, Status.DEPRECATED, actor, "deprecate")

    async def retire(self, name: str, version: str, actor: str) -> VersionDetail:
        return await self._transition(name, version, Status.RETIRED, actor, "retire")

    async def _transition(
        self, name: str, version: str, to: Status, actor: str, action: str
    ) -> VersionDetail:
        """Status, canais e auditoria na mesma transação."""
        async with self._sessions.begin() as session:
            catalog = CatalogRepository(session)
            skill = await _require_skill(catalog, name)
            row = await catalog.find_version(skill.id, version, for_update=True)
            if row is None:
                raise NotFoundError(f"Versão {version} da skill '{name}' não encontrada.")
            check_transition(row.status, to)
            await catalog.set_status(row.id, to)
            channel = channel_for(to)
            if channel is not None:
                await catalog.set_channel(skill.id, channel, row.id)
            else:  # deprecated e retired saem de qualquer canal
                await catalog.clear_channels_pointing_to(row.id)
            await AuditRepository(session).record(actor, action, name, version)
            files = await catalog.list_files(row.id)
        return _detail(name, replace(row, status=to), files)

    async def list_published(self, channel: Channel = Channel.STABLE) -> list[PublishedSkill]:
        async with self._sessions() as session:
            catalog = CatalogRepository(session)
            channels = await catalog.list_channels()
            result = []
            for skill in await catalog.list_skills():
                version = channels.get(skill.id, {}).get(channel)
                if version is not None:
                    result.append(await _published(catalog, skill, version))
        return result

    async def get_published(
        self, name: str, channel: Channel = Channel.STABLE, actor: str = "anonymous"
    ) -> PublishedSkill:
        async with self._sessions.begin() as session:
            catalog = CatalogRepository(session)
            skill = await _require_skill(catalog, name)
            published = await _published(
                catalog, skill, await _channel_version(catalog, skill, channel)
            )
            await AuditRepository(session).record(actor, "mcp_get", name, published.version)
        return published

    async def read_file(self, name: str, path: str, channel: Channel, actor: str) -> bytes:
        async with self._sessions() as session:
            catalog = CatalogRepository(session)
            skill = await _require_skill(catalog, name)
            published = await _published(
                catalog, skill, await _channel_version(catalog, skill, channel)
            )
        entry = next((f for f in published.files if f.path == path), None)
        if entry is None:
            raise NotFoundError(f"Arquivo '{path}' não encontrado na skill '{name}'.")
        data = await self._blobs.get(entry.sha256)  # confere o hash; IntegrityError se divergir
        async with self._sessions.begin() as session:
            await AuditRepository(session).record(actor, "mcp_read", name, published.version)
        return data


async def _channel_version(catalog: CatalogRepository, skill: SkillRow, channel: Channel) -> str:
    version = (await catalog.channels_of(skill.id)).get(channel)
    if version is None:
        raise NotFoundError(f"A skill '{skill.name}' não tem versão no canal {channel}.")
    return version


async def _published(catalog: CatalogRepository, skill: SkillRow, version: str) -> PublishedSkill:
    row = await catalog.find_version(skill.id, version)
    assert row is not None  # o canal só aponta para versões existentes
    return PublishedSkill(
        name=skill.name,
        description=str(row.frontmatter.get("description", "")),
        frontmatter=row.frontmatter,
        version=row.version,
        bundle_sha256=row.bundle_sha256,
        files=await catalog.list_files(row.id),
    )


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
