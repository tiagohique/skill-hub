"""Apoio aos testes do MCP: app real sob uvicorn e cliente oficial."""

from typing import Any

import mcp_types as types
from mcp import Client
from pydantic import BaseModel

from hub.domain.models import Status
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


async def call(client: Client, method: str, params: Any) -> dict[str, Any]:
    result = await client.session.send_request(
        types.Request(method=method, params=params), AnyResult
    )
    return result.model_dump()
