# Tarefa 31 — Swagger da API e referência do MCP

**Fase:** login · **Depende de:** 30 · **Commit:** `feat: swagger and MCP reference pages behind a docs password`

## Objetivo
Liberar o Swagger da API REST e uma página de referência do MCP, acessíveis pelo portal, protegidos por uma senha simples.

## Arquivos
Criar `hub/src/hub/api/docs.py` e `hub/tests/integration/test_docs.py`. Alterar `hub/src/hub/main.py`, `config.py`, `api/errors.py` (preserva `WWW-Authenticate`), `mcp/server.py` (`TOOLS` compartilhado), `portal/vite.config.ts` (proxy), `portal/src/components/Layout.tsx`, `.env.example`, `CLAUDE.md`, `docs/arq.c4`.

## Interfaces (consome / produz)
Produz `/docs` (Swagger UI), `/openapi.json` e `/mcp-docs`. Consome `app.openapi()` e a lista `TOOLS` do servidor MCP.

## Regras e valores da spec
- Senha `B3123` (HTTP Basic; o usuário é ignorado), vinda de `DOCS_PASSWORD` (padrão `B3123`). Só para ambiente local.
- Independente do login do portal; não abre a API (`/api/*` segue exigindo sessão).
- O MCP não tem Swagger padrão: a página `/mcp-docs` é gerada do próprio servidor (métodos, tools, URIs, canais, como registrar no Claude Code).
- Navbar: links "API (Swagger)" e "MCP" em nova aba. O Swagger UI carrega os assets de um CDN (precisa de internet).

## Testes
`test_docs.py`: 401 sem senha ou com senha errada (com `WWW-Authenticate`), 200 com a senha, `openapi.json` com as rotas, `/mcp-docs` lista tools e métodos, a senha da documentação não abre `/api`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
curl -u x:B3123 http://localhost:5173/docs
```

## Critérios de aceite
- [x] Swagger e página do MCP protegidos e acessíveis pelo portal

## Notas de execução
Os caminhos nativos do FastAPI foram desligados (`docs_url=None`, `openapi_url=None`) e recriados em `api/docs.py` com a senha. O handler de erros passou a repetir os cabeçalhos da exceção (sem isso o navegador não pedia a senha). 221 testes passando; via proxy do portal os três caminhos respondem 401 sem senha e 200 com ela.
