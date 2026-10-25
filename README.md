# Skills Hub (POC)

Repositório central e versionado de skills de IA, servido por MCP. Um desenvolvedor envia uma skill pelo portal, o hub valida, versiona e guarda; depois a skill aprovada (`stable`) é lida pelo Claude Code via MCP, com o hash do conteúdo conferido.

Esta é uma prova de conceito que roda 100% local (Docker Compose) e foi desenhada para evoluir para a nuvem sem reescrita.

## Como funciona

1. **Upload:** no portal, o dev envia um `SKILL.md` ou um `.zip` com a versão (semver). A skill entra como `draft`.
2. **Governança:** a versão é promovida `draft → beta → stable` e pode ser depreciada. Versões publicadas nunca são sobrescritas; corrigir é publicar outra versão. Tudo gera registro de auditoria.
3. **Consumo:** o Claude Code conecta no servidor MCP e lê as skills `stable` (ou `beta`, se pedido). Cada arquivo vem com o digest SHA-256, e o hub confere o hash ao ler.

## Componentes

| Serviço | Porta | Função |
|---|---|---|
| `portal` | 5173 | Interface web (React + Vite + Tailwind): login, lista com busca e filtros, detalhe, upload e promoção. Tema claro e escuro, responsivo. |
| `hub` | 8000 | Python 3.12 + FastAPI. API REST em `/api` e servidor MCP em `/mcp` (SDK oficial, extensão de Skills SEP-2640). |
| `postgres` | 5432 | PostgreSQL com catálogo, usuários e blobs (camada `BlobStore`, trocável por S3 ou Azure no futuro). |

Pontos de desenho:

- Conteúdo endereçado por SHA-256, imutável; o usuário do banco usado pelo hub não tem `DELETE` e quase nenhum `UPDATE`.
- O portal exige login; o MCP não exige login.
- Documentação da API (Swagger) em `/docs` e referência do MCP em `/mcp-docs`, protegidas por uma senha configurável.
- Arquitetura como código em [`docs/arq.c4`](docs/arq.c4) (LikeC4).

## Como rodar

Pré-requisito: Docker com Docker Compose. Nada da aplicação roda direto na máquina.

```bash
cp .env.example .env     # ajuste os valores se quiser
docker compose up --build
```

- Portal: <http://localhost:5173>
- API e Swagger: <http://localhost:8000/api> e <http://localhost:8000/docs> (também pelo portal)
- MCP: `http://localhost:8000/mcp`

O hub aplica as migrações do banco ao iniciar. O usuário inicial do portal é criado pela migração (veja `hub/alembic/versions/`); **é só para ambiente local, troque antes de expor o portal**. Para acessar pelo celular, use `http://<IP do computador>:5173` na mesma rede.

### Conectar o Claude Code ao MCP

```bash
claude mcp add --transport http skills-hub http://localhost:8000/mcp
```

### Testes e qualidade

```bash
docker compose run --rm hub-test pytest          # hub
docker compose run --rm hub-test ruff check .    # lint
docker compose run --rm hub-test mypy src        # tipos
docker compose run --rm portal npm test          # portal
```

## Estrutura

```
hub/        API REST, servidor MCP, regras de negócio, BlobStore e migrações
portal/     Interface React
examples/   Skills de exemplo
scripts/    Demonstração e verificação de hashes pelo MCP
docs/       Arquitetura (arq.c4), especificações e tarefas
CLAUDE.md   Regras detalhadas do projeto
```

## Documentação

Regras, modelo de dados, API e decisões: [`CLAUDE.md`](CLAUDE.md) e [`docs/README.md`](docs/README.md).

## Fora do escopo da POC

SSO, cadastro e troca de senha, login no MCP, adaptadores S3 e Azure, pipeline de CI com scan e assinatura, e multi-tenant.
