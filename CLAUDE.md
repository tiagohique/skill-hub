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
- Tudo roda em contêiner (banco, hub, portal, testes, lint, build e scripts); nada da aplicação roda direto no Mac. Testes do hub: `docker compose run --rm hub-test pytest`. Testes e build do portal: `docker compose run --rm portal npm test` e `npm run build`.
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
| Portal | React + Vite (TypeScript) + Tailwind CSS + lucide-react (ícones) |
| Hub | Python 3.12, FastAPI |
| MCP | SDK oficial `mcp` (Python). **Não usar FastMCP.** |
| Banco e blobs | PostgreSQL (imagem oficial `postgres`) |
| Acesso a dados | SQLAlchemy 2 (async) + asyncpg + Alembic |
| Infra local | Docker Compose |
| Qualidade | pytest, ruff, mypy |

Tailwind CSS (com `@tailwindcss/vite`) e `lucide-react` foram aprovados em 2026-10-25 para o novo visual do portal. Shadcn UI e Radix não entram (o protótipo aprovado não usa).

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
- Toda regra de negócio fica em `service/`: `SkillService` (skills) e `AuthService` (login, sessões e tema). `security.py` guarda o hash de senha (scrypt) e o token de sessão.
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
| `users` | `id`, `username` (único), `password_hash` (scrypt), `theme` (`light` ou `dark`), `created_at` |
| `auth_sessions` | `token_sha256` (PK), `user_id`, `created_at`, `expires_at`, `revoked_at` |

Restrições:

- `UNIQUE (skill_id, version)`.
- `bundle_sha256` = SHA-256 do texto formado pelas linhas `path\0sha256`, ordenadas por `path`.
- `audit_events.actor` e `skill_versions.created_by` guardam o username de quem agiu (texto, sem FK).
- Promoção atualiza `skill_versions.status`, `channels` e `audit_events` **na mesma transação**.

## Imutabilidade (imposta pelo banco)

O usuário do banco usado pelo hub tem permissões mínimas:

- `blobs`, `skill_version_files`, `audit_events`: apenas `INSERT` e `SELECT`.
- `skill_versions`: `INSERT`, `SELECT` e `UPDATE (status)` apenas na coluna `status`.
- `channels`: `INSERT`, `SELECT` e `UPDATE (version_id)` (promoção e depreciação).
- `users`: `INSERT`, `SELECT` e `UPDATE (theme)`. `auth_sessions`: `INSERT`, `SELECT` e `UPDATE (revoked_at)` (logout não apaga a sessão).
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

- Transporte: Streamable HTTP em `/mcp`. Sem login (só a API REST do portal exige sessão).
- Padrão: extensão de Skills (SEP-2640). Métodos `skills/list`, `skills/get` e `resources/read`, URIs `skill://<name>/SKILL.md` e `skill://<name>/<path>`.
- Cada skill é listada com a lista de arquivos, o digest SHA-256 e o tamanho de cada um. **Nunca servir como `"dynamic"`.**
- **Resultado da verificação (Tarefa 11):** o `mcp` 2.3.0 (o mais novo no PyPI, fixado em `mcp>=2.3,<3`) ainda não traz a extensão; o PR `python-sdk#3485` foi mesclado na `main` em 2026-10-11, mas não saiu em release. Por isso `skills/list` e `skills/get` são registrados à mão com o `Server` de baixo nível (`add_request_handler`), com a capability `io.modelcontextprotocol/skills`. Detalhes em `docs/decisions/mcp-skills-extension.md`. Quando o SDK publicar a extensão, troca só o adaptador `mcp/`.
- O canal `beta` é pedido de forma explícita: parâmetro `channel` em `skills/list` e `skills/get`, e `?channel=beta` na URI de `resources/read`. O ator da auditoria é o `clientInfo` do cliente MCP (ou `anonymous`).
- Fallback para clientes sem a extensão: tools `list_skills` e `get_skill`, lendo da mesma `SkillService`.
- Não implementar sincronização para `~/.claude/skills`. A especificação pede que skills de origem MCP fiquem fora dos caminhos de skills locais.

## API REST (portal)

| Método | Rota | Função |
|---|---|---|
| GET | `/api/health` | Saúde do hub (healthcheck do Compose) |
| POST | `/api/skills/upload` | Upload (`multipart`) de `.md` ou `.zip` com a versão |
| POST | `/api/auth/login` | Corpo `{ username, password }`; devolve o usuário e grava o cookie de sessão |
| POST | `/api/auth/logout` | Revoga a sessão |
| GET | `/api/auth/me` | Usuário logado (401 sem sessão) |
| PUT | `/api/auth/theme` | Corpo `{ "theme": "light" ou "dark" }`; guarda a preferência no banco |
| GET | `/api/skills` | Lista skills, `description` (do frontmatter da versão mais recente), canais e `status` geral |
| GET | `/api/skills/{name}` | Detalhe e versões |
| GET | `/api/skills/{name}/versions/{version}` | Arquivos e hashes da versão |
| POST | `/api/skills/{name}/versions/{version}/promote` | Corpo `{ "to": "beta" ou "stable" }` |
| POST | `/api/skills/{name}/versions/{version}/deprecate` | Depreciar |

**Login:** todas as rotas de `/api/skills` exigem sessão (cookie `hub_session`, `HttpOnly`, `SameSite=Lax`, 7 dias; no banco fica só o SHA-256 do token). Sem sessão: 401 `unauthorized`. `/api/health` e `/api/auth/login` são abertas. **O MCP (`/mcp`) continua sem login.** Usuário inicial da POC criado pela migração: `admin` / `admin` (senha com `hashlib.scrypt`). **É só para ambiente local; troque antes de qualquer uso fora dele.** Não há cadastro nem troca de senha.

`status` geral da skill na lista: `stable` se há canal stable; senão `beta` se há canal beta; senão o status da versão mais recente (`draft`, `deprecated` ou `retired`).

**Documentação:** `/docs` (Swagger UI), `/openapi.json` e `/mcp-docs` (referência do MCP: métodos, tools, URIs e canais; o MCP não tem Swagger padrão) ficam fora do `/api`, com HTTP Basic e a senha `DOCS_PASSWORD` (padrão `B3123`, só para ambiente local; o usuário é ignorado). O portal tem os links "API (Swagger)" e "MCP" no rodapé e faz proxy desses caminhos. A senha da documentação não abre a API.

Erros em JSON com `code` e `message`. Upload que repete versão: 409. A transição `deprecated→retired` existe só no `SkillService` (sem rota REST).

## Portal (React)

Visual zinc + indigo com **tema claro e escuro** (Tailwind CSS, classe `dark` no `<html>`, ícones lucide-react), fiel ao protótipo aprovado em 2026-10-25. O botão Sol/Lua fica na navbar e no canto da tela de login. O tema vale no navegador (`localStorage`, sem flash ao abrir) e, logado, é guardado no banco por usuário (`PUT /api/auth/theme`) e aplicado ao entrar. Rotas por hash (`#/`, `#/skills/<nome>`, `#/upload`). Sem sessão, qualquer rota mostra a tela de login. Quatro telas:

0. **Login:** card centralizado com ícone, campos Usuário e Senha (ícones à esquerda), botão de largura total e o aviso "Acesso restrito a desenvolvedores autorizados.". Erro de credencial aparece no topo do card. A navbar tem o ícone de usuário com o nome embaixo; o "Sair" (vermelho) só aparece ao passar o mouse, focar ou clicar no ícone.

1. **Skills:** cabeçalho com botão "Enviar Skill", busca por nome, filtro por domínio e filtro por status (Todos, Stable, Beta, Deprecated; tudo no cliente, empilhados no celular), tabela no desktop e cards no celular, com colunas Status, Domínio, Stable, Beta e Descrição (truncada, texto completo no `title`; 2 linhas nos cards) e badges de versão `stable` e `beta`. Clicar leva ao detalhe.
2. **Detalhe:** versões (tabela ou cards), status em badges, arquivos com hash (copiar ao clicar), botões Promover e Depreciar.
3. **Upload:** card centralizado com área de arrastar e soltar (`.md` ou `.zip`) e campo de versão semver. Versão inválida mostra o que corrigir e oferece a correção (`explainVersion`, ex.: "Usar 1.0.0"); erros reais da API (409, 413, 422) aparecem no topo do card; spinner durante o envio.

Rodapé global com os links "API (Swagger)" e "MCP" (nova aba). Responsivo: menu hambúrguer e cards abaixo de `md`; sem rolagem horizontal em 375 px.

Acesso pelo celular: `http://<IP do Mac>:5173`, na mesma rede (o Vite escuta em `0.0.0.0` e o portal faz proxy de `/api`, então o aparelho só precisa da porta 5173). **Com o login `admin`/`admin` (POC), quem estiver na mesma rede e souber a senha pode ver e enviar skills; troque a senha antes de expor o portal.**

Interface em português.

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
    entrypoint.sh   # migra e sobe o hub
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
      components/   # Layout (navbar), Badge e ThemeToggle
      pages/        # LoginPage, SkillsPage, SkillDetailPage, UploadPage
      api.ts auth.tsx theme.ts ThemeContext.tsx types.ts skills.ts version.ts
    tests/          # node:test (skills, version e theme)
  examples/skills/  # 2 skills de exemplo para a demonstração
  scripts/          # demo.py e verify_mcp.py (rodam no contêiner hub-test)
```

## Variáveis de ambiente

`DOCS_PASSWORD` (senha do Swagger e de `/mcp-docs`), `DATABASE_URL` (usuário da aplicação), `MIGRATION_DATABASE_URL` (dono do esquema, usado nas migrações), `BLOB_BACKEND` (`postgres`), `MAX_FILE_BYTES`, `MAX_BUNDLE_BYTES`, `MAX_FILES`, mais as variáveis do Postgres (`POSTGRES_*`, `APP_DB_*`). Todas documentadas em `.env.example`. Nenhum segredo no repositório.

## Compose

- `hub` só sobe depois de `postgres` saudável (healthcheck).
- O hub aplica `alembic upgrade head` ao iniciar.
- Volume nomeado `pgdata`.
- Comando único para subir tudo: `docker compose up --build`.

## Fora do escopo da POC

SSO, cadastro e troca de senha, login no MCP, adaptadores S3 e Azure, pipeline de CI com scan, evals e assinatura, Terraform, busca de texto no conteúdo das skills (a lista do portal só filtra por nome e domínio), diff entre versões e multi-tenant.

## Evolução prevista (não implementar)

| POC | Versão final |
|---|---|
| Portal local | Portal na nuvem, atrás do SSO |
| Um contêiner `hub` | Contêineres separados, com autoscaling |
| `PostgresBlobStore` | `S3BlobStore` ou `AzureBlobStore` imutável |
| PostgreSQL no Docker | PostgreSQL gerenciado (RDS ou Azure) |
| Upload direto | Pipeline com scan, evals e assinatura |
| Login local `admin`/`admin` | SSO corporativo (OAuth) |
| Docker Compose | ECS ou Container Apps, via Terraform |

Só a troca do adaptador do `BlobStore` deve exigir mudança de código no hub.

## Definição de pronto da POC

- [x] `docker compose up --build` sobe os três serviços sem passos manuais.
- [x] Upload de `.md` e de `.zip` funciona, com validação e erros claros.
- [x] Versão repetida devolve 409; nada é sobrescrito.
- [x] Promoção `draft→beta→stable` funciona e gera auditoria.
- [x] Claude Code conecta em `/mcp` e lê uma skill `stable`.
- [x] Hash conferido ao ler; arquivo adulterado no banco gera erro de integridade.
- [x] O usuário da aplicação não consegue `UPDATE` em `blobs` nem `DELETE` (teste de integração).
- [x] Testes de contrato do `BlobStore` passam.
- [x] Duas skills de exemplo (HTML e back-end) publicadas e consumidas.
- [x] `docs/arq.c4` atualizado e válido (`npx likec4 validate docs`).
- [x] Portal no novo visual, responsivo em 375 px (sem rolagem horizontal) e acessível pelo celular na rede local.
- [x] Lista com busca e filtros de domínio e status; testes do portal (`npm test`) passam.
- [x] Login (`admin`/`admin` no banco) protege a API; MCP segue aberto; tema claro/escuro alternável e guardado por usuário.
