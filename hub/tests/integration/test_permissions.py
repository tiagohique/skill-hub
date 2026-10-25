import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

SHA = "a" * 64
SKILL_ID = uuid.uuid4()
VERSION_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
async def seed(owner_engine: AsyncEngine) -> None:
    """Uma linha em cada tabela, inserida como dono."""
    async with owner_engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO skills (id, name, domain, owner) VALUES (:i, 's', 'd', 'o')"),
            {"i": SKILL_ID},
        )
        await conn.execute(
            text(
                "INSERT INTO skill_versions "
                "(id, skill_id, version, status, frontmatter, bundle_sha256, created_by) "
                "VALUES (:v, :s, '1.0.0', 'draft', '{}', :h, 'u')"
            ),
            {"v": VERSION_ID, "s": SKILL_ID, "h": SHA},
        )
        await conn.execute(
            text("INSERT INTO blobs (sha256, content, size) VALUES (:h, 'x', 1)"), {"h": SHA}
        )
        await conn.execute(
            text("INSERT INTO skill_version_files VALUES (:v, 'SKILL.md', :h, 1)"),
            {"v": VERSION_ID, "h": SHA},
        )
        await conn.execute(
            text("INSERT INTO channels VALUES (:s, 'stable', :v)"),
            {"s": SKILL_ID, "v": VERSION_ID},
        )
        await conn.execute(
            text(
                "INSERT INTO audit_events (id, actor, action, skill) "
                "VALUES (gen_random_uuid(), 'a', 'upload', 's')"
            )
        )


async def _denied(engine: AsyncEngine, sql: str) -> None:
    async with engine.begin() as conn:
        with pytest.raises(ProgrammingError, match="permission denied"):
            await conn.execute(text(sql))


async def test_app_cannot_update_blobs(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "UPDATE blobs SET content = 'y'")


@pytest.mark.parametrize(
    "table",
    [
        "skills",
        "skill_versions",
        "skill_version_files",
        "channels",
        "blobs",
        "audit_events",
        "users",
        "auth_sessions",
    ],
)
async def test_app_cannot_delete_from_any_table(app_engine: AsyncEngine, table: str) -> None:
    await _denied(app_engine, f"DELETE FROM {table}")


async def test_app_cannot_truncate(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "TRUNCATE blobs CASCADE")


async def test_app_cannot_update_version_frontmatter(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "UPDATE skill_versions SET frontmatter = '[]'")


async def test_app_cannot_update_version_hash(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "UPDATE skill_versions SET bundle_sha256 = 'z'")


async def test_app_cannot_update_files(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "UPDATE skill_version_files SET size = 2")


async def test_app_cannot_update_audit(app_engine: AsyncEngine) -> None:
    await _denied(app_engine, "UPDATE audit_events SET actor = 'x'")


async def test_app_can_update_version_status(app_engine: AsyncEngine) -> None:
    async with app_engine.begin() as conn:
        await conn.execute(text("UPDATE skill_versions SET status = 'beta'"))
        status = (await conn.execute(text("SELECT status FROM skill_versions"))).scalar_one()
    assert status == "beta"


async def test_app_can_update_channel_version(app_engine: AsyncEngine) -> None:
    async with app_engine.begin() as conn:
        await conn.execute(text("UPDATE channels SET version_id = NULL"))


async def test_status_check_constraint(app_engine: AsyncEngine) -> None:
    async with app_engine.begin() as conn:
        with pytest.raises(Exception, match="ck_skill_versions_status"):
            await conn.execute(text("UPDATE skill_versions SET status = 'bogus'"))


async def test_app_can_insert_and_select(app_engine: AsyncEngine) -> None:
    async with app_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO audit_events (id, actor, action, skill) "
                "VALUES (gen_random_uuid(), 'a', 'x', 's')"
            )
        )
        n = (await conn.execute(text("SELECT count(*) FROM audit_events"))).scalar_one()
    assert n == 2
