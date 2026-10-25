# Skills Hub (POC v3)

Repositório central e versionado de skills de IA, servido por MCP.
Esta é uma POC que roda 100% local (Docker Compose, Mac) e foi desenhada para evoluir para a nuvem sem reescrita.

Desenho de referência: **"POC v3: Postgres + camada BlobStore"**, mantido como código em [`docs/arq.c4`](docs/arq.c4) (LikeC4).
Se algo aqui contradisser o desenho, pare e pergunte.

## Como trabalhar neste projeto

- Leia este arquivo inteiro antes de gerar código.
- Entregue em passos pequenos: um módulo por vez, com testes.
- Decisão fora destas regras: pergunte antes de implementar.
- Não adicione dependências, serviços ou funcionalidades que não estejam aqui.
- Código e identificadores em inglês. Textos de interface e documentação em português do Brasil.

## Arquitetura como código

O desenho da arquitetura está em `docs/arq.c4` (LikeC4) e é a fonte da verdade dos componentes e das relações.

Views do modelo: visão geral, contêineres, camadas do hub, fluxo de upload, fluxo de leitura pelo MCP e implantação local.

- Antes de criar ou mover componentes, leia `docs/arq.c4`.
- Mudou componente, camada ou relação? Atualize `docs/arq.c4` no mesmo commit.
- Os nomes dos componentes no código seguem os do modelo: `FastAPI`, `Servidor MCP`, `SkillService`, `BlobStore`, `PostgresBlobStore`.
- Validar: `npx likec4 validate docs`
- Visualizar: `npx likec4 start docs`

## Objetivo da POC

Provar valor de ponta a ponta:

1. Dev faz upload de uma skill (`SKILL.md` ou `.zip`) no portal.
2. O hub valida, versiona e grava a skill (entra como `draft`).
3. Alguém promove a versão para `beta` e depois `stable`.
4. O Claude Code lê a skill `stable` pelo MCP.
5. O conteúdo recebido tem o hash conferido.

## Stack

| Camada | Tecnologia |
|---|---|
| Portal | React + Vite (TypeScript) |
| Hub | Python 3.12, FastAPI |
| MCP | SDK oficial `mcp` (Python). **Não usar FastMCP.** |
| Banco e blobs | PostgreSQL (imagem oficial `postgres`) |
| Acesso a dados | SQLAlchemy 2 (async) + asyncpg + Alembic |
| Infra local | Docker Compose |
| Qualidade | pytest, ruff, mypy |

Por que não FastMCP: o provider de skills dele lê só de pastas e diverge da extensão oficial de Skills (SEP-2640). O SDK oficial segue o padrão que será o destino final.

## Arquitetura

```
Dev --> [portal React] --> [hub Python] --> [PostgreSQL]
                            | FastAPI + MCP     | catalogo
Claude Code --- MCP ------> | SkillService      | blobs
                            | BlobStore (iface)
                              |- PostgresBlobStore  (POC)
                              '- S3BlobStore / AzureBlobStore (futuro)
```

Três contêineres no Compose:

| Serviço | Porta | Função |
|---|---|---|
| `portal` | 5173 | Upload, listagem, detalhe e promoção de versões |
| `hub` | 8000 | API REST em `/api` e servidor MCP em `/mcp` |
| `postgres` | 5432 | Catálogo e blobs (volume `pgdata`) |

O MCP é montado no mesmo app ASGI da FastAPI, no caminho `/mcp`. Se a montagem causar conflito, rode como segundo processo na mesma imagem.

## Camadas do hub e regras de dependência

```
api/ e mcp/  -->  service/  -->  store/ (BlobStore) e repositories/
```

- `api/` (REST) e `mcp/` (MCP) são só adaptadores finos. Nunca acessam banco nem BlobStore direto.
- Toda regra de negócio fica em `service/SkillService`.
- Só `repositories/` fala SQL. Só implementações de `BlobStore` gravam e leem conteúdo.
- O portal fala apenas com a API REST. Nunca com o MCP nem com o banco.
- Camadas inferiores nunca importam as superiores.

## BlobStore (ponto de troca para S3 e Azure)

Interface (Protocol) em `store/blob_store.py`:

```python
class BlobStore(Protocol):
    async def put(self, data: bytes) -> str: ...      # devolve o sha256 em hex
    async def get(self, sha256: str) -> bytes: ...    # recalcula e confere o hash
    async def exists(self, sha256: str) -> bool: ...
```

Regras:

- Endereçamento por conteúdo: a chave é o SHA-256. Gravar o mesmo conteúdo duas vezes não duplica.
- `get` sempre recalcula o hash e levanta `IntegrityError` se divergir.
- POC: `PostgresBlobStore` (tabela `blobs`).
- Futuro: `S3BlobStore` e `AzureBlobStore`. **Não implementar agora.**
- Backend escolhido por `BLOB_BACKEND` (`postgres` na POC).
- Escreva testes de contrato (`tests/contract/test_blob_store.py`) que qualquer implementação futura deve passar.
- SHA-256 é impressão digital, não criptografia.

## Modelo de dados (PostgreSQL)

| Tabela | Campos principais |
|---|---|
| `skills` | `id`, `name` (único), `domain`, `owner`, `created_at` |
| `skill_versions` | `id`, `skill_id`, `version` (semver), `status`, `frontmatter` (jsonb), `bundle_sha256`, `created_by`, `created_at` |
| `skill_version_files` | `version_id`, `path`, `sha256`, `size` |
| `channels` | `skill_id`, `channel` (`beta` ou `stable`), `version_id` |
| `blobs` | `sha256` (PK), `content` (bytea), `size`, `created_at` |
| `audit_events` | `id`, `actor`, `action`, `skill`, `version`, `at` |

Restrições:

- `UNIQUE (skill_id, version)`.
- `bundle_sha256` = SHA-256 do texto formado pelas linhas `path\0sha256`, ordenadas por `path`.
- Promoção atualiza `skill_versions.status`, `channels` e `audit_events` **na mesma transação**.

## Imutabilidade (imposta pelo banco)

O usuário do banco usado pelo hub tem permissões mínimas:

- `blobs`, `skill_version_files`, `audit_events`: apenas `INSERT` e `SELECT`.
- `skill_versions`: `INSERT`, `SELECT` e `UPDATE (status)` apenas na coluna `status`.
- Nenhum `DELETE` em lugar nenhum.
- Migrações rodam com outro usuário (dono do esquema).

## Governança

Ciclo de vida da versão:

```
draft --> beta --> stable --> deprecated --> retired
```

- Transições permitidas: `draft→beta`, `beta→stable`, `beta→deprecated`, `stable→deprecated`, `deprecated→retired`. Qualquer outra é erro 409.
- Todo upload entra como `draft`.
- Uma versão publicada nunca é sobrescrita. Reenviar a mesma `skill@versão` devolve 409. Corrigir é publicar outra versão.
- Versionamento semver. A versão vem do formulário de upload (se o frontmatter trouxer `metadata.version`, precisa coincidir).
- Todo upload, promoção e depreciação gera um `audit_event`. Toda entrega de skill pelo MCP também gera um evento (quem leu, qual versão).
- Por padrão o MCP serve só `stable`. Aceitar `channel=beta` de forma explícita.

## Validação de upload

- `SKILL.md` é obrigatório na raiz.
- Frontmatter obrigatório: `name` (minúsculas, números e hífens) e `description`.
- Limites configuráveis por variável de ambiente (valores iniciais: arquivo 1 MB, pacote 5 MB, 100 arquivos).
- `.zip`: rejeitar caminhos absolutos, `..` (zip slip), links simbólicos e arquivos fora da pasta da skill.
- Nunca executar conteúdo enviado. Skill é dado, não código do hub.
- Tratar o conteúdo de skills como entrada não confiável em qualquer ponto.

## Servidor MCP

- Transporte: Streamable HTTP em `/mcp`.
- Padrão: extensão de Skills (SEP-2640). Métodos `skills/list`, `skills/get` e `resources/read`, URIs `skill://<name>/SKILL.md` e `skill://<name>/<path>`.
- Cada skill é listada com a lista de arquivos, o digest SHA-256 e o tamanho de cada um. **Nunca servir como `"dynamic"`.**
- **Primeira tarefa do MCP:** verificar na versão instalada do pacote `mcp` se a extensão já existe (o pull request de referência é `python-sdk#3485`; não confirmei que foi publicado). Se não existir, registrar `skills/list` e `skills/get` manualmente, seguindo a especificação.
- Fallback para clientes sem a extensão: tools `list_skills` e `get_skill`, lendo da mesma `SkillService`.
- Não implementar sincronização para `~/.claude/skills`. A especificação pede que skills de origem MCP fiquem fora dos caminhos de skills locais.

## API REST (portal)

| Método | Rota | Função |
|---|---|---|
| POST | `/api/skills/upload` | Upload (`multipart`) de `.md` ou `.zip` com a versão |
| GET | `/api/skills` | Lista skills e canais |
| GET | `/api/skills/{name}` | Detalhe e versões |
| GET | `/api/skills/{name}/versions/{version}` | Arquivos e hashes da versão |
| POST | `/api/skills/{name}/versions/{version}/promote` | Corpo `{ "to": "beta" ou "stable" }` |
| POST | `/api/skills/{name}/versions/{version}/deprecate` | Depreciar |

Erros em JSON com `code` e `message`. Upload que repete versão: 409.

## Portal (React)

Três telas:

1. **Skills:** lista com nome, domínio, versão `stable` e versão `beta`.
2. **Detalhe:** versões, status, arquivos com hash, botões Promover e Depreciar.
3. **Upload:** arrastar e soltar `.md` ou `.zip`, campo de versão semver.

Sem login na POC. Interface simples e limpa, em português.

## Estrutura de pastas

```
skills-hub/
  CLAUDE.md
  docs/
    arq.c4          # arquitetura como código (LikeC4)
  docker-compose.yml
  .env.example
  hub/
    Dockerfile
    pyproject.toml
    alembic/
    src/hub/
      api/          # rotas REST
      mcp/          # servidor MCP
      service/      # SkillService (regras)
      store/        # BlobStore e PostgresBlobStore
      repositories/ # SQL
      domain/       # modelos e erros
    tests/
      contract/     # testes de contrato do BlobStore
      unit/
      integration/
  portal/
    Dockerfile
    src/
  examples/skills/  # 2 skills de exemplo para a demonstração
```

## Variáveis de ambiente

`DATABASE_URL`, `BLOB_BACKEND` (`postgres`), `MAX_FILE_BYTES`, `MAX_BUNDLE_BYTES`, `MAX_FILES`. Todas documentadas em `.env.example`. Nenhum segredo no repositório.

## Compose

- `hub` só sobe depois de `postgres` saudável (healthcheck).
- O hub aplica `alembic upgrade head` ao iniciar.
- Volume nomeado `pgdata`.
- Comando único para subir tudo: `docker compose up --build`.

## Fora do escopo da POC

Login e SSO, adaptadores S3 e Azure, pipeline de CI com scan, evals e assinatura, Terraform, busca de texto, diff entre versões e multi-tenant.

## Evolução prevista (não implementar)

| POC | Versão final |
|---|---|
| Portal local | Portal na nuvem, atrás do SSO |
| Um contêiner `hub` | Contêineres separados, com autoscaling |
| `PostgresBlobStore` | `S3BlobStore` ou `AzureBlobStore` imutável |
| PostgreSQL no Docker | PostgreSQL gerenciado (RDS ou Azure) |
| Upload direto | Pipeline com scan, evals e assinatura |
| Sem login | SSO corporativo (OAuth) |
| Docker Compose | ECS ou Container Apps, via Terraform |

Só a troca do adaptador do `BlobStore` deve exigir mudança de código no hub.

## Definição de pronto da POC

- [ ] `docker compose up --build` sobe os três serviços sem passos manuais.
- [ ] Upload de `.md` e de `.zip` funciona, com validação e erros claros.
- [ ] Versão repetida devolve 409; nada é sobrescrito.
- [ ] Promoção `draft→beta→stable` funciona e gera auditoria.
- [ ] Claude Code conecta em `/mcp` e lê uma skill `stable`.
- [ ] Hash conferido ao ler; arquivo adulterado no banco gera erro de integridade.
- [ ] O usuário da aplicação não consegue `UPDATE` em `blobs` nem `DELETE` (teste de integração).
- [ ] Testes de contrato do `BlobStore` passam.
- [ ] Duas skills de exemplo (HTML e back-end) publicadas e consumidas.
- [ ] `docs/arq.c4` atualizado e válido (`npx likec4 validate docs`).
