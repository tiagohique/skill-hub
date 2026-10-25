# Tarefa 12 — Servidor MCP em `/mcp`

**Fase:** 4 · **Depende de:** 09, 11 · **Commit:** `feat(mcp): skills extension, resources and fallback tools`

## Objetivo
Servir skills `stable` (e `beta` explícito) por Streamable HTTP, com digest e tamanho por arquivo.

## Arquivos
`hub/src/hub/mcp/server.py`; `hub/src/hub/main.py` (montagem em `/mcp` e `session_manager.run()` no lifespan; se conflitar, segundo processo na mesma imagem); `hub/tests/integration/test_mcp.py`.

## Interfaces (consome / produz)
Consome `list_published`, `get_published`, `read_file`. Produz `build_mcp_server(service) -> Server` e `build_session_manager(server) -> StreamableHTTPSessionManager`.

## Regras e valores da spec
- `skills/list` e `skills/get` no formato da SEP-2640 (nativo ou manual, conforme Tarefa 11); arquivos com `uri` `skill://<name>/<path>`, `sha256` e `size`; **nunca** `"dynamic"`; `channel` opcional (`beta` explícito).
- `resources/list` e `resources/read` para `skill://<name>/SKILL.md` e `skill://<name>/<path>` (texto UTF-8 ou blob base64); `?channel=beta` aceito.
- Tools de fallback `list_skills(channel?)` e `get_skill(name, channel?)`.
- Ator = `clientInfo.name/version` ou `anonymous`. Erros de domínio viram erro MCP em pt-BR; `IntegrityError` nunca devolve o conteúdo.

## Testes
Cliente oficial (`ClientSession`, `clientInfo` `test-client`): lista só `stable` com digests; `channel=beta`; `resources/read` com `sha256` igual ao digest; `get_skill` idem; blob adulterado → erro MCP; audit `mcp_read` com ator `test-client/<versão>`; skill em `draft` não aparece.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_mcp.py -v
```

## Critérios de aceite
- [x] `mcp/` só chama `SkillService`
- [x] Hash conferido ao ler; adulteração gera erro

## Notas de execução
Desvios em relação ao plano:
- `build_mcp_server` recebe um `ServiceProvider` (`Callable[[], SkillService]`), não o serviço: o servidor MCP é montado em `create_app` antes do lifespan criar o `SkillService`.
- O endpoint é uma `Route("/mcp")` com `StreamableHTTPASGIApp` anexada ao router da FastAPI (um `Mount` redirecionaria `/mcp` para `/mcp/`); o `StreamableHTTPSessionManager.run()` entra no lifespan da FastAPI.
- `PublishedSkill` ganhou `frontmatter` (a SEP exige o frontmatter verbatim na entrada).
- URIs de skills no canal beta carregam `?channel=beta` (entrada e arquivos), para que o `resources/read` volte ao mesmo canal.
- Proteção contra DNS rebinding ligada, aceitando `localhost`, `127.0.0.1`, `[::1]`, `hub` e `host.docker.internal`.
- Os testes sobem o app com uvicorn numa porta livre e usam o `mcp.Client` oficial por HTTP; `tests/helpers.py::running` roda o lifespan numa task própria (task group do anyio).
- As tools de fallback são só `list_skills` e `get_skill` (spec); `get_skill` devolve o texto do `SKILL.md` e a lista de arquivos; outros arquivos só por `resources/read`.
