import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from hub.domain.errors import IntegrityError, InvalidTransitionError, NotFoundError
from hub.domain.hashing import sha256_hex
from hub.domain.models import Channel, Status
from hub.service.skill_service import SkillService
from hub.service.validation import UploadLimits
from hub.store.postgres_blob_store import PostgresBlobStore

LIMITS = UploadLimits(1024 * 1024, 5 * 1024 * 1024, 100)


def skill_md(body: str = "# Corpo") -> bytes:
    return f"---\nname: my-skill\ndescription: Faz algo útil\n---\n{body}\n".encode()


@pytest.fixture
def service(app_engine: AsyncEngine, clean_db: None) -> SkillService:
    sessions = async_sessionmaker(app_engine, expire_on_commit=False)
    return SkillService(sessions, PostgresBlobStore(sessions), LIMITS)


async def upload(service: SkillService, version: str = "1.0.0", body: str = "# Corpo") -> None:
    await service.upload(filename="SKILL.md", data=skill_md(body), version=version, actor="portal")


async def publish(service: SkillService, version: str = "1.0.0", body: str = "# Corpo") -> None:
    await upload(service, version, body)
    await service.promote("my-skill", version, Status.BETA, "portal")
    await service.promote("my-skill", version, Status.STABLE, "portal")


async def audit_events(engine: AsyncEngine) -> list[tuple[str, str, str | None]]:
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text("SELECT actor, action, version FROM audit_events ORDER BY at, action")
            )
        ).all()
    return [(r.actor, r.action, r.version) for r in rows]


async def test_draft_to_beta_to_stable_updates_status_channels_and_audit(
    service: SkillService, app_engine: AsyncEngine
) -> None:
    await upload(service)
    beta = await service.promote("my-skill", "1.0.0", Status.BETA, "ana")
    assert beta.status is Status.BETA
    assert (await service.get_skill("my-skill")).channels == {Channel.BETA: "1.0.0"}
    stable = await service.promote("my-skill", "1.0.0", Status.STABLE, "ana")
    assert stable.status is Status.STABLE
    detail = await service.get_skill("my-skill")
    assert detail.channels[Channel.STABLE] == "1.0.0"
    events = await audit_events(app_engine)
    assert [e[1] for e in events].count("promote") == 2
    assert all(e[0] == "ana" for e in events if e[1] == "promote")


async def test_draft_to_stable_is_rejected_without_side_effects(
    service: SkillService, app_engine: AsyncEngine
) -> None:
    await upload(service)
    with pytest.raises(InvalidTransitionError):
        await service.promote("my-skill", "1.0.0", Status.STABLE, "portal")
    detail = await service.get_skill("my-skill")
    assert detail.versions[0].status is Status.DRAFT
    assert detail.channels == {}
    assert [e[1] for e in await audit_events(app_engine)] == ["upload"]


@pytest.mark.parametrize("target", [Status.DRAFT, Status.DEPRECATED, Status.RETIRED])
async def test_promote_only_accepts_beta_or_stable(service: SkillService, target: Status) -> None:
    await upload(service)
    with pytest.raises(InvalidTransitionError):
        await service.promote("my-skill", "1.0.0", target, "portal")


async def test_new_stable_replaces_channel(service: SkillService) -> None:
    await publish(service, "1.0.0")
    await publish(service, "1.1.0", body="v2")
    detail = await service.get_skill("my-skill")
    assert detail.channels[Channel.STABLE] == "1.1.0"
    published = await service.list_published()
    assert [p.version for p in published] == ["1.1.0"]


async def test_deprecating_stable_version_stops_serving_it(service: SkillService) -> None:
    await publish(service)
    assert [p.name for p in await service.list_published()] == ["my-skill"]
    deprecated = await service.deprecate("my-skill", "1.0.0", "portal")
    assert deprecated.status is Status.DEPRECATED
    assert await service.list_published() == []
    with pytest.raises(NotFoundError):
        await service.get_published("my-skill")
    assert (await service.get_skill("my-skill")).channels == {}


async def test_deprecating_beta_clears_beta_channel(service: SkillService) -> None:
    await upload(service)
    await service.promote("my-skill", "1.0.0", Status.BETA, "portal")
    await service.deprecate("my-skill", "1.0.0", "portal")
    assert (await service.get_skill("my-skill")).channels == {}


async def test_retire_requires_deprecated(service: SkillService) -> None:
    await publish(service)
    with pytest.raises(InvalidTransitionError):
        await service.retire("my-skill", "1.0.0", "portal")
    await service.deprecate("my-skill", "1.0.0", "portal")
    retired = await service.retire("my-skill", "1.0.0", "portal")
    assert retired.status is Status.RETIRED


async def test_draft_cannot_be_retired(service: SkillService) -> None:
    await upload(service)
    with pytest.raises(InvalidTransitionError):
        await service.retire("my-skill", "1.0.0", "portal")


async def test_transition_of_unknown_version(service: SkillService) -> None:
    with pytest.raises(NotFoundError):
        await service.promote("nope", "1.0.0", Status.BETA, "portal")
    await upload(service)
    with pytest.raises(NotFoundError):
        await service.deprecate("my-skill", "9.9.9", "portal")


async def test_failure_in_transaction_leaves_status_untouched(
    service: SkillService, monkeypatch: pytest.MonkeyPatch
) -> None:
    await upload(service)

    async def boom(*_: object, **__: object) -> None:
        raise RuntimeError("falha na auditoria")

    monkeypatch.setattr("hub.service.skill_service.AuditRepository.record", boom)
    with pytest.raises(RuntimeError):
        await service.promote("my-skill", "1.0.0", Status.BETA, "portal")
    monkeypatch.undo()
    detail = await service.get_skill("my-skill")
    assert detail.versions[0].status is Status.DRAFT
    assert detail.channels == {}


async def test_beta_channel_is_explicit(service: SkillService) -> None:
    await upload(service)
    await service.promote("my-skill", "1.0.0", Status.BETA, "portal")
    assert await service.list_published() == []
    with pytest.raises(NotFoundError):
        await service.get_published("my-skill")
    beta = await service.get_published("my-skill", Channel.BETA)
    assert beta.version == "1.0.0"
    assert [p.name for p in await service.list_published(Channel.BETA)] == ["my-skill"]


async def test_draft_is_never_published(service: SkillService) -> None:
    await upload(service)
    assert await service.list_published() == []
    assert await service.list_published(Channel.BETA) == []


async def test_published_skill_lists_files_with_digests(service: SkillService) -> None:
    await publish(service)
    published = await service.get_published("my-skill")
    data = skill_md()
    assert published.description == "Faz algo útil"
    assert published.bundle_sha256 == (await service.get_version("my-skill", "1.0.0")).bundle_sha256
    [file] = published.files
    assert (file.path, file.sha256, file.size) == ("SKILL.md", sha256_hex(data), len(data))


async def test_read_file_returns_content_and_audits(
    service: SkillService, app_engine: AsyncEngine
) -> None:
    await publish(service)
    content = await service.read_file("my-skill", "SKILL.md", Channel.STABLE, "claude-code/2.0")
    assert content == skill_md()
    await service.get_published("my-skill", Channel.STABLE, "claude-code/2.0")
    events = await audit_events(app_engine)
    assert ("claude-code/2.0", "mcp_read", "1.0.0") in events
    assert ("claude-code/2.0", "mcp_get", "1.0.0") in events


async def test_read_file_unknown_path(service: SkillService) -> None:
    await publish(service)
    with pytest.raises(NotFoundError):
        await service.read_file("my-skill", "nao-existe.md", Channel.STABLE, "x")


async def test_read_file_detects_tampered_blob_and_does_not_audit_delivery(
    service: SkillService, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    await publish(service)
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE blobs SET content = 'adulterado'"))
    with pytest.raises(IntegrityError):
        await service.read_file("my-skill", "SKILL.md", Channel.STABLE, "claude-code/2.0")
    assert all(e[1] != "mcp_read" for e in await audit_events(app_engine))
