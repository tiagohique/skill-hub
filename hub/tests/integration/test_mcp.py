import mcp_types as types
import pytest
from mcp.shared.exceptions import MCPError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from hub.domain.hashing import sha256_hex
from hub.domain.models import Status
from hub.mcp.server import SkillsGetParams, SkillsListParams
from tests.mcp_support import Hub, call, skill_md


async def test_capabilities_advertise_skills_extension(hub: Hub) -> None:
    async with hub.client() as client:
        caps = client.server_capabilities
        assert caps.extensions is not None
        assert "io.modelcontextprotocol/skills" in caps.extensions
        assert caps.resources is not None


async def test_skills_list_returns_only_stable_with_digests(hub: Hub) -> None:
    data = await hub.publish("my-skill")
    await hub.publish("only-beta", to=Status.BETA)
    await hub.service.upload(
        filename="SKILL.md", data=skill_md("draft-one"), version="1.0.0", actor="t"
    )
    async with hub.client() as client:
        result = await call(client, "skills/list", SkillsListParams())
    [entry] = result["skills"]
    assert entry["uri"] == "skill://my-skill/SKILL.md"
    assert entry["frontmatter"]["name"] == "my-skill"
    assert entry["resources"] == [
        {
            "uri": "skill://my-skill/SKILL.md",
            "digest": f"sha256:{sha256_hex(data)}",
            "size": len(data),
        }
    ]
    assert entry["resources"] != "dynamic"


async def test_skills_list_beta_is_explicit(hub: Hub) -> None:
    await hub.publish("only-beta", to=Status.BETA)
    async with hub.client() as client:
        stable = await call(client, "skills/list", SkillsListParams())
        beta = await call(client, "skills/list", SkillsListParams(channel="beta"))
    assert stable["skills"] == []
    [entry] = beta["skills"]
    assert entry["uri"] == "skill://only-beta/SKILL.md?channel=beta"
    assert entry["resources"][0]["uri"].endswith("?channel=beta")


async def test_invalid_channel_is_rejected(hub: Hub) -> None:
    async with hub.client() as client:
        with pytest.raises(MCPError, match="Canal inválido"):
            await call(client, "skills/list", SkillsListParams(channel="alpha"))


async def test_skills_get(hub: Hub) -> None:
    await hub.publish("my-skill")
    async with hub.client() as client:
        result = await call(client, "skills/get", SkillsGetParams(uri="skill://my-skill/SKILL.md"))
        assert result["skill"]["frontmatter"]["description"] == "Faz algo útil"
        with pytest.raises(MCPError, match="não encontrada"):
            await call(client, "skills/get", SkillsGetParams(uri="skill://nope/SKILL.md"))
        with pytest.raises(MCPError):
            await call(client, "skills/get", SkillsGetParams(uri="http://x/SKILL.md"))
        with pytest.raises(MCPError, match="SKILL.md"):
            await call(client, "skills/get", SkillsGetParams(uri="skill://my-skill/other.md"))


async def test_resources_list_only_stable_files(hub: Hub) -> None:
    await hub.publish("my-skill")
    await hub.publish("only-beta", to=Status.BETA)
    async with hub.client() as client:
        resources = (await client.list_resources()).resources
    assert [r.uri for r in resources] == ["skill://my-skill/SKILL.md"]
    assert resources[0].mime_type == "text/markdown"


async def test_resources_read_matches_listed_digest(hub: Hub) -> None:
    data = await hub.publish("my-skill")
    async with hub.client() as client:
        listing = await call(client, "skills/list", SkillsListParams())
        digest = listing["skills"][0]["resources"][0]["digest"]
        result = await client.read_resource("skill://my-skill/SKILL.md")
    [content] = result.contents
    assert isinstance(content, types.TextResourceContents)
    assert content.text.encode() == data
    assert f"sha256:{sha256_hex(content.text.encode())}" == digest


async def test_resources_read_beta_needs_explicit_channel(hub: Hub) -> None:
    await hub.publish("only-beta", to=Status.BETA)
    async with hub.client() as client:
        with pytest.raises(MCPError):
            await client.read_resource("skill://only-beta/SKILL.md")
        result = await client.read_resource("skill://only-beta/SKILL.md?channel=beta")
    assert result.contents


async def test_resources_read_unknown_file(hub: Hub) -> None:
    await hub.publish("my-skill")
    async with hub.client() as client:
        with pytest.raises(MCPError, match="não encontrado"):
            await client.read_resource("skill://my-skill/nada.md")


async def test_fallback_tools(hub: Hub) -> None:
    data = await hub.publish("my-skill")
    async with hub.client() as client:
        tools = {t.name for t in (await client.list_tools()).tools}
        listed = await client.call_tool("list_skills", {})
        got = await client.call_tool("get_skill", {"name": "my-skill"})
        missing = await client.call_tool("get_skill", {"name": "nope"})
    assert tools == {"list_skills", "get_skill"}
    import json

    [first] = json.loads(listed.content[0].text)["skills"]  # type: ignore[union-attr]
    assert first["files"][0]["sha256"] == sha256_hex(data)
    payload = json.loads(got.content[0].text)  # type: ignore[union-attr]
    assert payload["skill_md"].encode() == data
    assert payload["version"] == "1.0.0"
    assert missing.is_error


async def test_tampered_blob_returns_error_not_content(hub: Hub, owner_engine: AsyncEngine) -> None:
    await hub.publish("my-skill")
    async with owner_engine.begin() as conn:
        await conn.execute(text("UPDATE blobs SET content = 'adulterado'"))
    async with hub.client() as client:
        with pytest.raises(MCPError, match="adulterado") as exc:
            await client.read_resource("skill://my-skill/SKILL.md")
        assert "adulterado" not in (exc.value.error.data or "")
        tool = await client.call_tool("get_skill", {"name": "my-skill"})
    assert tool.is_error


async def test_audit_records_client_identity(hub: Hub, app_engine: AsyncEngine) -> None:
    await hub.publish("my-skill")
    async with hub.client() as client:
        await client.read_resource("skill://my-skill/SKILL.md")
        await call(client, "skills/get", SkillsGetParams(uri="skill://my-skill/SKILL.md"))
    async with app_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT actor, action, version FROM audit_events"))).all()
    events = {(r.actor, r.action, r.version) for r in rows}
    assert ("test-client/1.2.3", "mcp_read", "1.0.0") in events
    assert ("test-client/1.2.3", "mcp_get", "1.0.0") in events
