# Decisão: extensão de Skills (SEP-2640) no servidor MCP

**Data:** 2026-10-24 · **Tarefa:** 11 (spike) · **Status:** decidido

## Achados

| Pergunta | Resposta |
|---|---|
| Versão do pacote `mcp` instalada | **2.3.0** (a mais recente no PyPI; traz também `mcp-types` 2.3.0). É a série 2.x, com API nova (handlers `on_*` no construtor de `Server`). |
| O pacote já traz `skills/list` e `skills/get`? | **Não.** `grep` por `skills/(list\|get)`, `SEP-2640` e `skill://` em `site-packages/mcp` não acha nada. |
| E o PR `python-sdk#3485`? | Está **mesclado** na `main` (2026-10-11, adiciona a extensão e um cliente `Skills`), mas **ainda não saiu em release**: o PyPI não tem nada acima de 2.3.0. |
| Dá para registrar os métodos sem mexer no SDK? | **Sim.** `mcp.server.lowlevel.Server.add_request_handler(method, params_type, handler)` aceita métodos arbitrários, e `server.extensions["io.modelcontextprotocol/skills"] = {}` anuncia a capability (SEP-2133). |
| Dá para usar `MCPServer` (alto nível)? | Não usar: é o sucessor do FastMCP embutido no SDK, e o CLAUDE.md proíbe FastMCP. O hub usa só o `Server` de baixo nível. |

Prova (script descartável, removido do repositório): um `Server` com `on_list_resources` + `add_request_handler("skills/list", ...)` e `("skills/get", ...)`, consumido pelo `mcp.Client` oficial com `client.session.send_request(types.Request(...))`. Resultado: o cliente enxerga `capabilities.resources` e `capabilities.extensions["io.modelcontextprotocol/skills"]`; `skills/list` e `skills/get` respondem; um parâmetro extra (`channel`) chega ao handler.

## Formato da SEP-2640 (resumo do que o hub implementa)

- **Capability:** `extensions["io.modelcontextprotocol/skills"] = {}` (sem `directoryRead`) e capability `resources` obrigatória.
- **URIs:** `skill://<name>/SKILL.md` e `skill://<name>/<path>`; o último segmento do caminho da skill é o `name` do frontmatter.
- **`skills/list`** (params: `cursor` opcional) → `{"resultType": "complete", "skills": [entrada...]}`.
- **`skills/get`** (params: `{"uri": "skill://<name>/SKILL.md"}`) → `{"resultType": "complete", "skill": entrada}`.
- **Entrada:** `{"uri", "frontmatter" (cópia verbatim em JSON), "resources": [{"uri", "digest": "sha256:<64 hex minúsculos>", "size"}...]}`. `resources` é completo (inclui o `SKILL.md`) e **nunca** `"dynamic"` no hub.
- **Arquivos:** lidos com o `resources/read` existente; o host confere digest e tamanho.

## Decisões para a Tarefa 12

1. **Registro manual** de `skills/list` e `skills/get` com `Server.add_request_handler`, em `hub/mcp/server.py`. Quando o SDK publicar a extensão, trocar o registro manual pelo oficial (só o adaptador `mcp/` muda).
2. **Fixar a versão:** `mcp>=2.3,<3` no `pyproject.toml` (a API 2.x difere bastante da 1.x).
3. **Canal beta explícito:** a SEP não tem canais. O hub aceita o parâmetro extra opcional `channel` (`"stable"` padrão, `"beta"`) em `skills/list` e `skills/get`, e `?channel=beta` na URI de `resources/read`. Qualquer outro valor é erro de parâmetros.
4. **Fallback** para clientes sem a extensão: tools `list_skills` e `get_skill`, lendo da mesma `SkillService`.
5. **Ator da auditoria:** `clientInfo` do cliente (`nome/versão`), ou `anonymous`. Na era legada vem de `ctx.session.client_params`; na moderna, do `_meta` da requisição. Confirmar empiricamente na Tarefa 12.
6. **Montagem:** `Server.streamable_http_app(...)` devolve um app Starlette cujo lifespan roda o `StreamableHTTPSessionManager`. O `Mount` do Starlette não executa o lifespan de sub-apps, então o lifespan da FastAPI precisa entrar em `server.session_manager.run()`. Se a montagem em `/mcp` conflitar, usar um segundo processo na mesma imagem (previsto no CLAUDE.md).

## Fontes

- SEP-2640: <https://modelcontextprotocol.io/seps/2640-skills-extension>
- PR do SDK Python: <https://github.com/modelcontextprotocol/python-sdk/pull/3485>
