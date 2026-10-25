import asyncio
import io
import zipfile

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from hub.domain.errors import NotFoundError, SkillValidationError, VersionConflictError
from hub.domain.hashing import bundle_sha256, sha256_hex
from hub.domain.models import Channel, Status
from hub.service.skill_service import SkillService
from hub.service.validation import UploadLimits
from hub.store.postgres_blob_store import PostgresBlobStore

LIMITS = UploadLimits(1024 * 1024, 5 * 1024 * 1024, 100)


def skill_md(name: str = "my-skill", body: str = "# Corpo", extra: str = "") -> bytes:
    return f"---\nname: {name}\ndescription: Faz algo útil\n{extra}---\n{body}\n".encode()


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


@pytest.fixture
def service(app_engine: AsyncEngine, clean_db: None) -> SkillService:
    sessions = async_sessionmaker(app_engine, expire_on_commit=False)
    return SkillService(sessions, PostgresBlobStore(sessions), LIMITS)


async def test_upload_md_creates_draft(service: SkillService) -> None:
    data = skill_md()
    detail = await service.upload(filename="SKILL.md", data=data, version="1.0.0", actor="portal")
    assert (detail.name, detail.version, detail.status) == ("my-skill", "1.0.0", Status.DRAFT)
    assert [f.path for f in detail.files] == ["SKILL.md"]
    assert detail.files[0].sha256 == sha256_hex(data)
    assert detail.files[0].size == len(data)
    assert detail.bundle_sha256 == bundle_sha256(detail.files)
    assert detail.created_by == "portal"
    assert detail.frontmatter["description"] == "Faz algo útil"


async def test_upload_zip_with_two_files(service: SkillService) -> None:
    data = make_zip({"SKILL.md": skill_md(), "ref/guia.md": b"guia"})
    detail = await service.upload(filename="s.zip", data=data, version="1.0.0", actor="portal")
    assert [f.path for f in detail.files] == ["SKILL.md", "ref/guia.md"]
    again = await service.get_version("my-skill", "1.0.0")
    assert again == detail


async def test_repeated_version_conflicts_and_keeps_original(service: SkillService) -> None:
    first = await service.upload(
        filename="SKILL.md", data=skill_md(body="original"), version="1.0.0", actor="portal"
    )
    with pytest.raises(VersionConflictError):
        await service.upload(
            filename="SKILL.md", data=skill_md(body="outro"), version="1.0.0", actor="portal"
        )
    assert await service.get_version("my-skill", "1.0.0") == first


async def test_concurrent_identical_uploads_one_wins(service: SkillService) -> None:
    async def go() -> object:
        return await service.upload(
            filename="SKILL.md", data=skill_md(), version="1.0.0", actor="portal"
        )

    results = await asyncio.gather(go(), go(), return_exceptions=True)
    conflicts = [r for r in results if isinstance(r, VersionConflictError)]
    assert len(conflicts) == 1
    assert len(results) - len(conflicts) == 1


async def test_invalid_upload_writes_nothing(
    service: SkillService, app_engine: AsyncEngine
) -> None:
    with pytest.raises(SkillValidationError):
        await service.upload(
            filename="SKILL.md", data=b"sem frontmatter", version="1.0.0", actor="p"
        )
    async with app_engine.connect() as conn:
        n = (await conn.execute(text("SELECT count(*) FROM skills"))).scalar_one()
        b = (await conn.execute(text("SELECT count(*) FROM blobs"))).scalar_one()
    assert (n, b) == (0, 0)


async def test_upload_writes_audit_event(service: SkillService, app_engine: AsyncEngine) -> None:
    await service.upload(filename="SKILL.md", data=skill_md(), version="1.0.0", actor="tiago")
    async with app_engine.connect() as conn:
        rows = (
            await conn.execute(text("SELECT actor, action, skill, version FROM audit_events"))
        ).all()
    assert [tuple(r) for r in rows] == [("tiago", "upload", "my-skill", "1.0.0")]


async def test_domain_and_owner_from_metadata_with_defaults(service: SkillService) -> None:
    await service.upload(
        filename="SKILL.md",
        data=skill_md("com-meta", extra="metadata:\n  domain: web\n  owner: time-web\n"),
        version="1.0.0",
        actor="portal",
    )
    await service.upload(
        filename="SKILL.md", data=skill_md("sem-meta"), version="1.0.0", actor="ana"
    )
    by_name = {s.name: s for s in await service.list_skills()}
    assert (by_name["com-meta"].domain, by_name["com-meta"].owner) == ("web", "time-web")
    assert (by_name["sem-meta"].domain, by_name["sem-meta"].owner) == ("geral", "ana")


async def test_list_skills_without_channels(service: SkillService) -> None:
    await service.upload(filename="SKILL.md", data=skill_md(), version="1.0.0", actor="portal")
    [summary] = await service.list_skills()
    assert (summary.name, summary.stable, summary.beta) == ("my-skill", None, None)


async def test_get_skill_detail(service: SkillService) -> None:
    await service.upload(filename="SKILL.md", data=skill_md(), version="1.0.0", actor="portal")
    await service.upload(
        filename="SKILL.md", data=skill_md(body="v2"), version="1.1.0", actor="portal"
    )
    detail = await service.get_skill("my-skill")
    assert detail.name == "my-skill"
    assert detail.description == "Faz algo útil"
    assert detail.channels == {}
    assert {v.version for v in detail.versions} == {"1.0.0", "1.1.0"}
    assert all(v.status is Status.DRAFT for v in detail.versions)
    assert Channel.STABLE not in detail.channels


async def test_not_found(service: SkillService) -> None:
    with pytest.raises(NotFoundError):
        await service.get_skill("nope")
    await service.upload(filename="SKILL.md", data=skill_md(), version="1.0.0", actor="portal")
    with pytest.raises(NotFoundError):
        await service.get_version("my-skill", "9.9.9")
    with pytest.raises(NotFoundError):
        await service.get_version("nope", "1.0.0")
