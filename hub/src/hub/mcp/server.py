"""Servidor MCP (adaptador fino sobre o SkillService).

Usa o `Server` de baixo nível do SDK oficial `mcp` (sem FastMCP). O `mcp` 2.3.0 ainda
não traz a extensão de Skills (SEP-2640), então `skills/list` e `skills/get` são
registrados à mão; ver docs/decisions/mcp-skills-extension.md.
"""

import base64
import json
import mimetypes
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

import mcp_types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.exceptions import MCPError

from hub.domain.errors import HubError, IntegrityError, NotFoundError
from hub.domain.models import Channel, PublishedSkill
from hub.service.skill_service import SkillService

SKILLS_EXTENSION = "io.modelcontextprotocol/skills"
SCHEME = "skill"
SKILL_MD = "SKILL.md"
RESOURCE_NOT_FOUND = -32002

ServiceProvider = Callable[[], SkillService]
Ctx = ServerRequestContext[Any, Any]


class SkillsListParams(types.PaginatedRequestParams):
    channel: str | None = None  # extensão do hub: "stable" (padrão) ou "beta"


class SkillsGetParams(types.RequestParams):
    uri: str
    channel: str | None = None


# ---------- URIs, canais e entradas ----------


def _channel(value: str | None) -> Channel:
    try:
        return Channel(value or Channel.STABLE)
    except ValueError:
        raise MCPError(types.INVALID_PARAMS, "Canal inválido: use 'stable' ou 'beta'.") from None


def _uri(name: str, path: str, channel: Channel) -> str:
    suffix = "" if channel is Channel.STABLE else f"?channel={channel}"
    return f"{SCHEME}://{name}/{path}{suffix}"


def _parse_uri(uri: str) -> tuple[str, str, Channel]:
    parts = urlsplit(uri)
    path = unquote(parts.path).lstrip("/")
    if parts.scheme != SCHEME or not parts.netloc or not path or ".." in path.split("/"):
        raise MCPError(types.INVALID_PARAMS, f"URI de skill inválida: {uri}")
    values = parse_qs(parts.query).get("channel")
    channel = _channel(values[0] if values else None)
    return parts.netloc, path, channel


def _entry(skill: PublishedSkill, channel: Channel) -> dict[str, Any]:
    """Entrada da SEP-2640. `resources` é sempre uma lista (nunca "dynamic")."""
    return {
        "uri": _uri(skill.name, SKILL_MD, channel),
        "frontmatter": skill.frontmatter,
        "resources": [
            {
                "uri": _uri(skill.name, f.path, channel),
                "digest": f"sha256:{f.sha256}",
                "size": f.size,
            }
            for f in skill.files
        ],
    }


def _mime(path: str) -> str:
    return mimetypes.guess_type(path)[0] or "application/octet-stream"


def _mcp_error(exc: HubError) -> MCPError:
    if isinstance(exc, NotFoundError):
        return MCPError(RESOURCE_NOT_FOUND, exc.message)
    if isinstance(exc, IntegrityError):
        return MCPError(types.INTERNAL_ERROR, exc.message)
    return MCPError(types.INVALID_PARAMS, exc.message)


def _actor(ctx: Ctx) -> str:
    """Quem leu: `clientInfo` do cliente MCP (nome/versão), ou "anonymous"."""
    params = ctx.session.client_params
    info: Any = params.client_info if params is not None else None
    if info is None and ctx.meta:
        info = ctx.meta.get(types.CLIENT_INFO_META_KEY)
    if info is None:
        return "anonymous"
    if isinstance(info, dict):
        name, version = info.get("name"), info.get("version")
    else:
        name, version = getattr(info, "name", None), getattr(info, "version", None)
    return f"{name}/{version}" if name and version else str(name or "anonymous")


# ---------- construção do servidor ----------


def build_mcp_server(get_service: ServiceProvider) -> Server[Any]:
    async def skills_list(ctx: Ctx, params: SkillsListParams) -> dict[str, Any]:
        channel = _channel(params.channel)
        skills = await get_service().list_published(channel)
        return {"resultType": "complete", "skills": [_entry(s, channel) for s in skills]}

    async def skills_get(ctx: Ctx, params: SkillsGetParams) -> dict[str, Any]:
        name, path, uri_channel = _parse_uri(params.uri)
        if path != SKILL_MD:
            raise MCPError(types.INVALID_PARAMS, f"A URI deve apontar para {SKILL_MD}.")
        channel = _channel(params.channel) if params.channel else uri_channel
        try:
            skill = await get_service().get_published(name, channel, _actor(ctx))
        except HubError as exc:
            raise _mcp_error(exc) from None
        return {"resultType": "complete", "skill": _entry(skill, channel)}

    async def list_resources(
        ctx: Ctx, params: types.PaginatedRequestParams | None
    ) -> types.ListResourcesResult:
        skills = await get_service().list_published(Channel.STABLE)
        return types.ListResourcesResult(
            resources=[
                types.Resource(
                    uri=_uri(s.name, f.path, Channel.STABLE),
                    name=f"{s.name}/{f.path}",
                    mime_type=_mime(f.path),
                    size=f.size,
                )
                for s in skills
                for f in s.files
            ]
        )

    async def read_resource(
        ctx: Ctx, params: types.ReadResourceRequestParams
    ) -> types.ReadResourceResult:
        name, path, channel = _parse_uri(params.uri)
        try:
            data = await get_service().read_file(name, path, channel, _actor(ctx))
        except HubError as exc:
            raise _mcp_error(exc) from None
        mime = _mime(path)
        try:
            content: types.TextResourceContents | types.BlobResourceContents = (
                types.TextResourceContents(uri=params.uri, mime_type=mime, text=data.decode())
            )
        except UnicodeDecodeError:
            content = types.BlobResourceContents(
                uri=params.uri, mime_type=mime, blob=base64.b64encode(data).decode()
            )
        return types.ReadResourceResult(contents=[content])

    channel_schema = {"type": "string", "enum": ["stable", "beta"], "default": "stable"}

    async def list_tools(
        ctx: Ctx, params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name="list_skills",
                    description="Lista as skills aprovadas (versão, arquivos e digests SHA-256).",
                    input_schema={"type": "object", "properties": {"channel": channel_schema}},
                ),
                types.Tool(
                    name="get_skill",
                    description="Devolve o SKILL.md de uma skill aprovada e seus arquivos.",
                    input_schema={
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "channel": channel_schema},
                        "required": ["name"],
                    },
                ),
            ]
        )

    async def call_tool(ctx: Ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
        args = params.arguments or {}
        try:
            channel = _channel(args.get("channel"))
            service = get_service()
            if params.name == "list_skills":
                skills = await service.list_published(channel)
                payload: dict[str, Any] = {"skills": [_summary(s) for s in skills]}
            elif params.name == "get_skill":
                name = args.get("name")
                if not isinstance(name, str):
                    raise MCPError(types.INVALID_PARAMS, "O argumento 'name' é obrigatório.")
                actor = _actor(ctx)
                skill = await service.get_published(name, channel, actor)
                text = (await service.read_file(name, SKILL_MD, channel, actor)).decode()
                payload = {**_summary(skill), "skill_md": text}
            else:
                raise MCPError(types.INVALID_PARAMS, f"Tool desconhecida: {params.name}")
        except HubError as exc:
            return _tool_result(exc.message, is_error=True)
        except MCPError as exc:
            return _tool_result(exc.error.message, is_error=True)
        return _tool_result(json.dumps(payload, ensure_ascii=False))

    server: Server[Any] = Server(
        "skills-hub",
        version="0.1.0",
        title="Skills Hub",
        instructions=(
            "Repositório central de skills aprovadas. Descubra com skills/list (ou a tool "
            "list_skills) e leia os arquivos com resources/read. Só o canal stable é servido "
            "por padrão; beta exige channel=beta."
        ),
        on_list_resources=list_resources,
        on_read_resource=read_resource,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )
    server.add_request_handler("skills/list", SkillsListParams, skills_list)
    server.add_request_handler("skills/get", SkillsGetParams, skills_get)
    server.extensions[SKILLS_EXTENSION] = {}
    return server


def _summary(skill: PublishedSkill) -> dict[str, Any]:
    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "bundle_sha256": skill.bundle_sha256,
        "files": [{"path": f.path, "sha256": f.sha256, "size": f.size} for f in skill.files],
    }


def _tool_result(text: str, *, is_error: bool = False) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(text=text)], is_error=is_error)


def build_session_manager(server: Server[Any]) -> StreamableHTTPSessionManager:
    # Proteção contra DNS rebinding: aceita só os nomes pelos quais o hub é alcançado
    # (Claude Code no host e outros contêineres do Compose).
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["localhost:*", "127.0.0.1:*", "[::1]:*", "hub:*", "host.docker.internal:*"],
        allowed_origins=["http://localhost:*", "http://127.0.0.1:*", "http://[::1]:*"],
    )
    return StreamableHTTPSessionManager(app=server, security_settings=security)
