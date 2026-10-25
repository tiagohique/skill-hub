# Skills Hub POC v3 — Especificação consolidada

Fonte primária: [`CLAUDE.md`](../../../CLAUDE.md) e [`arq.c4`](../../arq.c4). Este documento consolida essas fontes e registra as decisões tomadas durante o planejamento. Em caso de conflito, o `CLAUDE.md` vence; pare e pergunte.

## 1. Objetivo

Provar valor de ponta a ponta: upload de skill (`SKILL.md` ou `.zip`) no portal → validação, versionamento e gravação como `draft` → promoção `beta` e `stable` → leitura da skill `stable` pelo Claude Code via MCP → hash conferido na entrega.

## 2. Regra nº 1: tudo roda no Docker

Todo componente é um contêiner do Docker Compose. Nada da aplicação roda direto no Mac; o único pré-requisito do host é o Docker.

| Serviço | O que roda | Porta | Quando |
|---|---|---|---|
| `postgres` | PostgreSQL (catálogo e blobs), volume `pgdata` | 5432 | sempre |
| `hub` | FastAPI em `/api` + servidor MCP em `/mcp` (alvo `runtime`) | 8000 | sempre |
| `portal` | React + Vite | 5173 | sempre |
| `hub-test` | imagem do hub, alvo `dev`: pytest, ruff, mypy e scripts | — | perfil `test`, sob demanda |

Proibido: venv, `pip`, `uvicorn`, `npm` ou `python` no host. Testes, lint, build do portal, scripts e validação do LikeC4 rodam em contêiner (comandos em cada tarefa). Fora de contêiner ficam apenas o navegador (`localhost:5173`) e o Claude Code (cliente MCP em `localhost:8000/mcp`). Subir tudo: `docker compose up --build`.

## 3. Stack e dependências (lista fechada)

- Hub: Python 3.12, FastAPI, uvicorn, python-multipart, SQLAlchemy 2 async, asyncpg, Alembic, SDK oficial `mcp` (**sem FastMCP**), pyyaml. Dev: pytest, pytest-asyncio, httpx, ruff, mypy, types-PyYAML.
- Portal: React, Vite, TypeScript (+ plugin react e tipos). Sem biblioteca de rotas.
- Banco: imagem oficial `postgres`.
- Nada além disso sem perguntar.

## 4. Camadas e dependências

```
api/ e mcp/  -->  service/  -->  store/ (BlobStore) e repositories/
```

`api/` e `mcp/` são adaptadores finos. Regra de negócio só em `service/SkillService`. Só `repositories/` fala SQL; só implementações de `BlobStore` gravam/leem conteúdo. `domain/` não importa ninguém. O portal fala só com a REST.

## 5. BlobStore

Protocol em `store/blob_store.py`: `put(data) -> sha256`, `get(sha256) -> bytes` (recalcula e levanta `IntegrityError` se divergir), `exists(sha256) -> bool`. Endereçamento por conteúdo (gravar duas vezes não duplica). Implementação da POC: `PostgresBlobStore` (tabela `blobs`). Escolha por `BLOB_BACKEND=postgres`. Testes de contrato em `tests/contract/test_blob_store.py`. S3/Azure: não implementar.

## 6. Modelo de dados

| Tabela | Colunas |
|---|---|
| `skills` | `id` (uuid), `name` (único), `domain`, `owner`, `created_at` |
| `skill_versions` | `id` (uuid), `skill_id`, `version`, `status` (CHECK nos 5 estados), `frontmatter` (jsonb), `bundle_sha256`, `created_by`, `created_at`; `UNIQUE(skill_id, version)` |
| `skill_version_files` | `version_id`, `path`, `sha256` (FK `blobs`), `size`; PK `(version_id, path)` |
| `channels` | `skill_id`, `channel` (`beta`/`stable`), `version_id` (**nulável**); PK `(skill_id, channel)` |
| `blobs` | `sha256` (PK), `content` (bytea), `size`, `created_at` |
| `audit_events` | `id` (uuid), `actor`, `action`, `skill`, `version` (nulável), `at` |

`bundle_sha256` = SHA-256 de `"\n".join(f"{path}\0{sha256}")` sobre os arquivos ordenados por `path` (UTF-8, sem `\n` final). Promoção atualiza status, canais e auditoria **na mesma transação**.

## 7. Imutabilidade imposta pelo banco

Dois papéis: dono do esquema (`hub_owner`, roda migrações) e usuário da aplicação (`hub_app`). Grants do app: `SELECT, INSERT` em `blobs`, `skill_version_files`, `audit_events`, `skills`; `skill_versions` com `SELECT, INSERT` e `UPDATE (status)`; `channels` com `SELECT, INSERT` e `UPDATE (version_id)`. Nenhum `DELETE` em lugar nenhum.

## 8. Governança

`draft → beta → stable → deprecated → retired`. Permitidas: `draft→beta`, `beta→stable`, `beta→deprecated`, `stable→deprecated`, `deprecated→retired`; o resto é 409. Todo upload entra `draft`. Reenviar `skill@versão` → 409. Semver; se o frontmatter trouxer `metadata.version`, precisa coincidir. Upload, promoção, depreciação e toda entrega pelo MCP geram `audit_event`. MCP serve só `stable`, e `channel=beta` apenas explícito.

## 9. Validação de upload

`SKILL.md` na raiz obrigatório; frontmatter com `name` (`^[a-z0-9]+(-[a-z0-9]+)*$`) e `description`; limites por env (1 MB arquivo, 5 MB pacote, 100 arquivos); `.zip` rejeita caminho absoluto, `..`, `\`, symlink, duplicados e arquivos fora da pasta da skill; `__MACOSX/` e `.DS_Store` são ignorados; limites medidos nos bytes realmente descomprimidos. Nunca executar conteúdo; conteúdo é entrada não confiável.

## 10. API REST

| Método | Rota | Função |
|---|---|---|
| GET | `/api/health` | saúde |
| POST | `/api/skills/upload` | multipart: `file` + `version` → 201 |
| GET | `/api/skills` | lista skills e canais |
| GET | `/api/skills/{name}` | detalhe e versões |
| GET | `/api/skills/{name}/versions/{version}` | arquivos e hashes |
| POST | `/api/skills/{name}/versions/{version}/promote` | `{"to": "beta"\|"stable"}` |
| POST | `/api/skills/{name}/versions/{version}/deprecate` | depreciar |

Erros: `{"code", "message"}`. Mapa: `invalid_skill` 422, `invalid_request` 422, `limit_exceeded` 413, `version_exists` 409, `invalid_transition` 409, `not_found` 404, `integrity_error` 500.

## 11. Servidor MCP

Streamable HTTP em `/mcp`. Extensão de Skills (SEP-2640): `skills/list`, `skills/get`, `resources/read`; URIs `skill://<name>/SKILL.md` e `skill://<name>/<path>`; cada skill lista arquivos com digest SHA-256 e tamanho; nunca `"dynamic"`. Primeira tarefa: verificar se o pacote `mcp` instalado já traz a extensão (PR `python-sdk#3485`, não confirmado); se não, registrar manualmente. Fallback: tools `list_skills` e `get_skill`. Sem sincronização para `~/.claude/skills`.

## 12. Variáveis de ambiente

`DATABASE_URL` (usuário app), `MIGRATION_DATABASE_URL` (dono), `BLOB_BACKEND`, `MAX_FILE_BYTES`, `MAX_BUNDLE_BYTES`, `MAX_FILES`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `APP_DB_USER`, `APP_DB_PASSWORD`. Documentadas em `.env.example`; sem segredos no repositório.

## 13. Decisões tomadas no planejamento

| Decisão | Escolha |
|---|---|
| Git | `git init` na raiz; um commit por tarefa |
| Estrutura do plano | Plano único em fases |
| `deprecated→retired` | Só no `SkillService`; sem rota REST nova |
| Ator das leituras MCP | `clientInfo` do `initialize` (`nome/versão`), ou `anonymous` |
| Ator da REST | `portal` (POC sem login) |
| Migrações | `MIGRATION_DATABASE_URL` nova, com usuário dono |
| PKs | UUID gerado pela aplicação (sem grant em sequences) |
| Depreciar versão em canal | Canal fica sem versão (`version_id` nulo); MCP deixa de servi-la |
| `domain` / `owner` | Vêm de `metadata.domain` / `metadata.owner`; padrão `geral` / ator |
| Docker | Tudo em contêiner, inclusive testes, lint, build e scripts |

## 14. Review Focus

1. Zip do Finder (`__MACOSX/`, `.DS_Store`) aceito.
2. Zip bomb / tamanho declarado mentiroso: limite nos bytes reais.
3. Dois uploads simultâneos da mesma versão: um 201, um 409.
4. Frontmatter com BOM/CRLF/sem fechamento/não-mapa e `metadata.version: 1.0`: 422 claro.
5. Depreciar versão do canal `stable`: MCP para de servi-la.

## 15. Fora do escopo

Login e SSO, adaptadores S3 e Azure, CI com scan, evals e assinatura, Terraform, busca de texto, diff entre versões, multi-tenant.
