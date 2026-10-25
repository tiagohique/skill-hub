# ruff: noqa: E501  (HTML e CSS embutidos em strings)
"""Documentação interativa: Swagger da API REST e página de referência do MCP.

Protegidas por senha simples (HTTP Basic; o usuário é ignorado). Ficam fora do /api e
não usam o login do portal, para abrirem direto no navegador.
"""

import hmac
import html
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from hub.config import Settings
from hub.mcp.server import TOOLS

router = APIRouter(include_in_schema=False)
_basic = HTTPBasic(auto_error=False, realm="Skills Hub (docs)")


def require_docs_password(
    request: Request, credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic)]
) -> None:
    settings: Settings = request.app.state.settings
    given = credentials.password if credentials else ""
    if not hmac.compare_digest(given.encode(), settings.docs_password.encode()):
        raise HTTPException(
            status_code=401,
            detail="Informe a senha da documentação.",
            headers={"WWW-Authenticate": 'Basic realm="Skills Hub (docs)", charset="UTF-8"'},
        )


Protected = Depends(require_docs_password)


@router.get("/openapi.json", dependencies=[Protected])
async def openapi_json(request: Request) -> JSONResponse:
    return JSONResponse(request.app.openapi())


@router.get("/docs", dependencies=[Protected])
async def swagger() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Skills Hub: API REST",
        swagger_ui_parameters={"persistAuthorization": True, "docExpansion": "list"},
    )


def _example(method: str, params: dict[str, object]) -> str:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.dumps(body, ensure_ascii=False, indent=2)


_METHODS: list[tuple[str, str, dict[str, object]]] = [
    (
        "initialize",
        "Abre a sessão MCP (o cliente envia clientInfo; ele vira o ator da auditoria).",
        {},
    ),
    (
        "skills/list",
        "Lista as skills do canal (padrão stable). Parâmetro extra: channel.",
        {"channel": "stable"},
    ),
    (
        "skills/get",
        "Devolve o SKILL.md e a lista de arquivos com digest sha256 e tamanho.",
        {"uri": "skill://nome-da-skill/SKILL.md"},
    ),
    (
        "resources/read",
        "Lê um arquivo da skill. Beta: acrescente ?channel=beta à URI.",
        {"uri": "skill://nome-da-skill/SKILL.md"},
    ),
    ("tools/list", "Lista as tools de fallback.", {}),
    (
        "tools/call",
        "Executa uma tool de fallback.",
        {"name": "list_skills", "arguments": {"channel": "stable"}},
    ),
]


def _page() -> str:
    e = html.escape
    methods = "".join(
        f"<section><h3><code>{e(m)}</code></h3><p>{e(desc)}</p><pre>{e(_example(m, p))}</pre></section>"
        for m, desc, p in _METHODS
    )
    tools = "".join(
        f"<section><h3><code>{e(t['name'])}</code></h3><p>{e(t['description'])}</p>"
        f"<pre>{e(json.dumps(t['input_schema'], ensure_ascii=False, indent=2))}</pre></section>"
        for t in TOOLS
    )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skills Hub: MCP</title>
<style>
:root{{--bg:#fafafa;--card:#fff;--bd:#e4e4e7;--tx:#18181b;--mut:#71717a;--ac:#4f46e5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#09090b;--card:#18181b;--bd:#27272a;--tx:#fafafa;--mut:#a1a1aa;--ac:#818cf8}}}}
body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.6 system-ui,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:24px 16px 64px}}
h1{{margin:0 0 4px}} h2{{margin-top:40px}} p,li{{color:var(--mut)}}
section{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:4px 16px 12px;margin:12px 0}}
pre{{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:12px;overflow:auto;font-size:13px;color:var(--tx)}}
code{{color:var(--ac)}} pre code{{color:inherit}}
</style></head><body><main>
<h1>Skills Hub: MCP</h1>
<p>Referência do servidor MCP. O MCP não tem Swagger padrão: esta página é gerada do próprio servidor. A API REST está em <a href="/docs">/docs</a>.</p>
<h2>Conexão</h2>
<section><ul>
<li>Endpoint: <code>/mcp</code> (Streamable HTTP), sem login. Exemplo local: <code>http://localhost:8000/mcp</code></li>
<li>Cabeçalhos: <code>Content-Type: application/json</code> e <code>Accept: application/json, text/event-stream</code></li>
<li>No Claude Code: <code>claude mcp add --transport http skills-hub http://localhost:8000/mcp</code></li>
<li>Só o canal <code>stable</code> é servido por padrão; <code>beta</code> exige <code>channel=beta</code>.</li>
<li>URIs: <code>skill://&lt;nome&gt;/SKILL.md</code> e <code>skill://&lt;nome&gt;/&lt;caminho&gt;</code>. Cada arquivo traz <code>digest</code> <code>sha256:&lt;hex&gt;</code>.</li>
</ul></section>
<h2>Métodos (JSON-RPC)</h2>{methods}
<h2>Tools de fallback</h2>{tools}
</main></body></html>"""


@router.get("/mcp-docs", dependencies=[Protected])
async def mcp_docs() -> HTMLResponse:
    return HTMLResponse(_page())
