"""Acesso SQL ao catálogo. Única camada que fala SQL. Nenhum método faz commit."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hub.domain.errors import VersionConflictError
from hub.domain.models import Channel, FileEntry, Status
from hub.repositories.tables import channels, skill_version_files, skill_versions, skills

_UNIQUE_VERSION = "uq_skill_versions_skill_id_version"


@dataclass(frozen=True)
class SkillRow:
    id: uuid.UUID
    name: str
    domain: str
    owner: str
    created_at: datetime


@dataclass(frozen=True)
class VersionRow:
    id: uuid.UUID
    skill_id: uuid.UUID
    version: str
    status: Status
    frontmatter: dict[str, Any]
    bundle_sha256: str
    created_by: str
    created_at: datetime


def _version_row(r: Any) -> VersionRow:
    return VersionRow(
        id=r.id,
        skill_id=r.skill_id,
        version=r.version,
        status=Status(r.status),
        frontmatter=r.frontmatter,
        bundle_sha256=r.bundle_sha256,
        created_by=r.created_by,
        created_at=r.created_at,
    )


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_skill(self, name: str, domain: str, owner: str) -> uuid.UUID:
        await self._session.execute(
            pg_insert(skills)
            .values(id=uuid.uuid4(), name=name, domain=domain, owner=owner)
            .on_conflict_do_nothing(index_elements=["name"])
        )
        result = await self._session.execute(select(skills.c.id).where(skills.c.name == name))
        skill_id: uuid.UUID = result.scalar_one()
        return skill_id

    async def find_skill(self, name: str) -> SkillRow | None:
        row = (await self._session.execute(select(skills).where(skills.c.name == name))).first()
        return SkillRow(row.id, row.name, row.domain, row.owner, row.created_at) if row else None

    async def list_skills(self) -> list[SkillRow]:
        rows = (await self._session.execute(select(skills).order_by(skills.c.name))).all()
        return [SkillRow(r.id, r.name, r.domain, r.owner, r.created_at) for r in rows]

    async def insert_version(
        self,
        skill_id: uuid.UUID,
        version: str,
        frontmatter: dict[str, Any],
        bundle_sha256: str,
        created_by: str,
    ) -> uuid.UUID:
        version_id = uuid.uuid4()
        try:
            async with self._session.begin_nested():  # savepoint: a sessão segue usável
                await self._session.execute(
                    insert(skill_versions).values(
                        id=version_id,
                        skill_id=skill_id,
                        version=version,
                        status=Status.DRAFT.value,
                        frontmatter=frontmatter,
                        bundle_sha256=bundle_sha256,
                        created_by=created_by,
                    )
                )
        except SAIntegrityError as exc:
            if _UNIQUE_VERSION in str(exc.orig):
                raise VersionConflictError(
                    f"A versão {version} desta skill já existe e não pode ser sobrescrita."
                ) from None
            raise
        return version_id

    async def insert_files(self, version_id: uuid.UUID, entries: Sequence[FileEntry]) -> None:
        if not entries:
            return
        await self._session.execute(
            insert(skill_version_files),
            [
                {"version_id": version_id, "path": e.path, "sha256": e.sha256, "size": e.size}
                for e in entries
            ],
        )

    async def find_version(
        self, skill_id: uuid.UUID, version: str, *, for_update: bool = False
    ) -> VersionRow | None:
        stmt = select(skill_versions).where(
            skill_versions.c.skill_id == skill_id, skill_versions.c.version == version
        )
        if for_update:  # serializa transições concorrentes da mesma versão
            stmt = stmt.with_for_update()
        row = (await self._session.execute(stmt)).first()
        return _version_row(row) if row else None

    async def list_versions(self, skill_id: uuid.UUID) -> list[VersionRow]:
        rows = (
            await self._session.execute(
                select(skill_versions)
                .where(skill_versions.c.skill_id == skill_id)
                .order_by(skill_versions.c.created_at.desc(), skill_versions.c.version.desc())
            )
        ).all()
        return [_version_row(r) for r in rows]

    async def list_files(self, version_id: uuid.UUID) -> list[FileEntry]:
        rows = (
            await self._session.execute(
                select(skill_version_files).where(skill_version_files.c.version_id == version_id)
            )
        ).all()
        # Ordem binária por path, a mesma do bundle_sha256 (a collation do banco difere).
        return sorted((FileEntry(r.path, r.sha256, r.size) for r in rows), key=lambda e: e.path)

    async def set_status(self, version_id: uuid.UUID, status: Status) -> None:
        await self._session.execute(
            update(skill_versions)
            .where(skill_versions.c.id == version_id)
            .values(status=status.value)
        )

    async def set_channel(
        self, skill_id: uuid.UUID, channel: Channel, version_id: uuid.UUID | None
    ) -> None:
        stmt = pg_insert(channels).values(
            skill_id=skill_id, channel=channel.value, version_id=version_id
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["skill_id", "channel"],
                set_={"version_id": stmt.excluded.version_id},
            )
        )

    async def clear_channels_pointing_to(self, version_id: uuid.UUID) -> None:
        await self._session.execute(
            update(channels).where(channels.c.version_id == version_id).values(version_id=None)
        )

    async def latest_statuses(self) -> dict[uuid.UUID, Status]:
        """Status da versão mais recente de cada skill."""
        stmt = (
            select(skill_versions.c.skill_id, skill_versions.c.status)
            .order_by(skill_versions.c.skill_id, skill_versions.c.created_at.desc())
            .ext(distinct_on(skill_versions.c.skill_id))
        )
        return {r.skill_id: Status(r.status) for r in (await self._session.execute(stmt)).all()}

    async def channels_of(self, skill_id: uuid.UUID) -> dict[Channel, str]:
        return (await self._channels(skill_id)).get(skill_id, {})

    async def list_channels(self) -> dict[uuid.UUID, dict[Channel, str]]:
        return await self._channels(None)

    async def _channels(self, skill_id: uuid.UUID | None) -> dict[uuid.UUID, dict[Channel, str]]:
        stmt = select(channels.c.skill_id, channels.c.channel, skill_versions.c.version).join(
            skill_versions, skill_versions.c.id == channels.c.version_id
        )
        if skill_id is not None:
            stmt = stmt.where(channels.c.skill_id == skill_id)
        result: dict[uuid.UUID, dict[Channel, str]] = {}
        for r in (await self._session.execute(stmt)).all():
            result.setdefault(r.skill_id, {})[Channel(r.channel)] = r.version
        return result
