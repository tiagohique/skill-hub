import asyncio
import os
from collections.abc import AsyncIterator
from typing import Any

import mcp_types as types
import pytest
import pytest_asyncio
import uvicorn
from mcp import Client
from mcp.shared.exceptions import MCPError
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from hub.config import Settings
from hub.domain.hashing import sha256_hex
from hub.domain.models import Status
from hub.main import create_app
from hub.mcp.server import SkillsGetParams, SkillsListParams
from hub.service.skill_service import SkillService


class AnyResult(BaseModel, extra="allow"):
    pass


def skill_md(name: str = "my-skill", body: str = "# Corpo") -> bytes:
    return f"---\nname: {name}\ndescription: Faz algo útil\n---\n{body}\n".encode()


class Hub:
    def __init__(self, url: str, service: SkillService) -> None:
        self.url = url
        self.service = service

    def client(self) -> Client:
        info = types.Implementation(name="test-client", version="1.2.3")
        return Client(self.url, client_info=info)

    async def publish(self, name: str = "my-skill", to: Status = Status.STABLE) -> bytes:
        data = skill_md(name)
        await self.service.upload(filename="SKILL.md", data=data, version="1.0.0", actor="t")
        await self.service.promote(name, "1.0.0", Status.BETA, "t")
        if to is Status.STABLE:
            await self.service.promote(name, "1.0.0", Status.STABLE, "t")
        return data


@pytest_asyncio.fixture
async def hub(clean_db: None) -> AsyncIterator[Hub]:
    settings = Settings(
        database_url=os.environ["TEST_DATABASE_URL"],
        migration_database_url=os.environ["TEST_MIGRATION_DATABASE_URL"],
        blob_backend="postgres",
        max_file_bytes=1024 * 1024,
        max_bundle_bytes=5 * 1024 * 1024,
        max_files=100,
    )
    app = create_app(settings)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    task = asyncio.create_task(server.serve())
    while not server.started:  # noqa: ASYNC110 - uvicorn não expõe um Event de partida
        await asyncio.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield Hub(f"http://127.0.0.1:{port}/mcp", app.state.service)
    server.should_exit = True
    await task


async def call(client: Client, method: str, params: Any) -> dict[str, Any]:
    result = await client.session.send_request(
        types.Request(method=method, params=params), AnyResult
    )
    return result.model_dump()


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
