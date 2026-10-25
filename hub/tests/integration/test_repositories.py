import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from hub.domain.errors import VersionConflictError
from hub.domain.models import Channel, FileEntry, Status
from hub.repositories.audit import AuditRepository
from hub.repositories.catalog import CatalogRepository

SHA_A = "a" * 64
SHA_B = "b" * 64


@pytest_asyncio.fixture
async def session(app_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with async_sessionmaker(app_engine, expire_on_commit=False).begin() as s:
        # blobs existem antes dos arquivos (FK); aqui inseridos direto.
        for sha in (SHA_A, SHA_B):
            await s.execute(
                text("INSERT INTO blobs (sha256, content, size) VALUES (:h, 'x', 1)"), {"h": sha}
            )
        yield s


async def make_version(
    repo: CatalogRepository, version: str = "1.0.0"
) -> tuple[uuid.UUID, uuid.UUID]:
    skill_id = await repo.get_or_create_skill("my-skill", "geral", "tiago")
    version_id = await repo.insert_version(
        skill_id, version, {"name": "my-skill"}, "h" * 64, "portal"
    )
    return skill_id, version_id


async def test_skill_create_find_list(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    first = await repo.get_or_create_skill("b-skill", "geral", "x")
    again = await repo.get_or_create_skill("b-skill", "outro", "y")
    await repo.get_or_create_skill("a-skill", "geral", "x")
    assert first == again
    found = await repo.find_skill("b-skill")
    assert found is not None
    assert (found.id, found.name, found.domain, found.owner) == (first, "b-skill", "geral", "x")
    assert await repo.find_skill("nope") is None
    assert [s.name for s in await repo.list_skills()] == ["a-skill", "b-skill"]


async def test_version_files_roundtrip(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, version_id = await make_version(repo)
    await repo.insert_files(
        version_id, [FileEntry("z.md", SHA_B, 1), FileEntry("SKILL.md", SHA_A, 1)]
    )
    row = await repo.find_version(skill_id, "1.0.0")
    assert row is not None
    assert row.id == version_id
    assert row.status is Status.DRAFT
    assert row.frontmatter == {"name": "my-skill"}
    assert row.created_by == "portal"
    assert [f.path for f in await repo.list_files(version_id)] == ["SKILL.md", "z.md"]
    assert await repo.find_version(skill_id, "9.9.9") is None


async def test_duplicate_version_raises_conflict(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, _ = await make_version(repo)
    with pytest.raises(VersionConflictError, match="1.0.0"):
        await repo.insert_version(skill_id, "1.0.0", {}, "h" * 64, "portal")
    # a sessão continua utilizável depois do conflito
    assert await repo.find_skill("my-skill") is not None


async def test_list_versions_newest_first(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, _ = await make_version(repo, "1.0.0")
    await repo.insert_version(skill_id, "1.1.0", {}, "h" * 64, "portal")
    versions = await repo.list_versions(skill_id)
    # created_at é igual dentro da transação; o desempate é a versão, decrescente
    assert [v.version for v in versions] == ["1.1.0", "1.0.0"]


async def test_set_status(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, version_id = await make_version(repo)
    await repo.set_status(version_id, Status.BETA)
    row = await repo.find_version(skill_id, "1.0.0")
    assert row is not None and row.status is Status.BETA


async def test_set_channel_twice_updates(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, v1 = await make_version(repo, "1.0.0")
    v2 = await repo.insert_version(skill_id, "2.0.0", {}, "h" * 64, "portal")
    await repo.set_channel(skill_id, Channel.STABLE, v1)
    assert await repo.channels_of(skill_id) == {Channel.STABLE: "1.0.0"}
    await repo.set_channel(skill_id, Channel.STABLE, v2)
    assert await repo.channels_of(skill_id) == {Channel.STABLE: "2.0.0"}


async def test_clear_channels_pointing_to_only_that_version(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, v1 = await make_version(repo, "1.0.0")
    v2 = await repo.insert_version(skill_id, "2.0.0", {}, "h" * 64, "portal")
    await repo.set_channel(skill_id, Channel.BETA, v2)
    await repo.set_channel(skill_id, Channel.STABLE, v1)
    await repo.clear_channels_pointing_to(v1)
    assert await repo.channels_of(skill_id) == {Channel.BETA: "2.0.0"}


async def test_channels_of_ignores_null(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    skill_id, _ = await make_version(repo)
    await repo.set_channel(skill_id, Channel.STABLE, None)
    assert await repo.channels_of(skill_id) == {}


async def test_list_channels_for_all_skills(session: AsyncSession) -> None:
    repo = CatalogRepository(session)
    s1, v1 = await make_version(repo)
    s2 = await repo.get_or_create_skill("other", "geral", "x")
    await repo.set_channel(s1, Channel.STABLE, v1)
    assert await repo.list_channels() == {s1: {Channel.STABLE: "1.0.0"}}
    assert s2 not in await repo.list_channels()


async def test_audit_record_sets_timestamp(session: AsyncSession) -> None:
    await AuditRepository(session).record("portal", "upload", "my-skill", "1.0.0")
    await AuditRepository(session).record("portal", "x", "my-skill", None)
    rows = (
        await session.execute(
            text("SELECT actor, action, skill, version, at FROM audit_events ORDER BY action")
        )
    ).all()
    assert [(r.actor, r.action, r.skill, r.version) for r in rows] == [
        ("portal", "upload", "my-skill", "1.0.0"),
        ("portal", "x", "my-skill", None),
    ]
    assert all(r.at is not None for r in rows)
