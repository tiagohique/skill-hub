# Skills Hub POC v3 — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a POC do Skills Hub de ponta a ponta: upload de skill no portal → validação, versionamento e gravação como `draft` → promoção `beta`/`stable` → leitura pelo Claude Code via MCP com hash conferido.

**Architecture:** Um app ASGI Python (FastAPI em `/api` + servidor MCP oficial em `/mcp`) com adaptadores finos sobre `SkillService`, que é a única porta para `repositories/` (SQL) e `BlobStore` (conteúdo endereçado por SHA-256, implementação `PostgresBlobStore`). Portal React+Vite fala só com a REST. PostgreSQL com dois papéis: dono do esquema (migrações) e usuário da aplicação com permissões mínimas, para que a imutabilidade seja imposta pelo banco.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, SDK `mcp` oficial (sem FastMCP), SQLAlchemy 2 async + asyncpg + Alembic, PostgreSQL (imagem oficial), React + Vite + TypeScript, Docker Compose, pytest, ruff, mypy.

**Spec:** [`CLAUDE.md`](../../../CLAUDE.md), [`docs/arq.c4`](../../arq.c4) e a spec consolidada `docs/superpowers/specs/2026-10-24-skills-hub-poc-design.md` (criada na Task 0). Cada tarefa tem sua própria especificação em `docs/tasks/NN-<slug>.md`; o executor lê a spec da tarefa antes de começar.

## Context

A pasta `/Users/tiago/Documents/skillsHub` hoje só tem `CLAUDE.md` e `docs/arq.c4` (projeto greenfield, sem git). Este plano transforma a especificação em tarefas pequenas, com TDD e um commit por tarefa, organizadas em fases que terminam cada uma em software testável. Decisões tomadas com o usuário: `git init` na raiz; plano único em fases; `deprecated→retired` existe só no `SkillService` (sem rota nova); ator das leituras MCP = `clientInfo` do `initialize` (`"<name>/<version>"`, ou `anonymous`).

**Execução recomendada:** Subagent-driven (superpowers:subagent-driven-development) — são 18 tarefas encadeadas por interfaces (domínio → store → serviço → adaptadores), e um revisor novo por tarefa pega divergência de assinatura antes que ela se espalhe. Alternativa: Native (superpowers:executing-plans), mais barata, com uma revisão só no final.

## Regra nº 1: tudo roda no Docker

**Todo componente é um contêiner do Docker Compose. Nada da aplicação roda direto no Mac.** O único pré-requisito do host é o Docker.

| Serviço Compose | O que roda | Quando |
|---|---|---|
| `postgres` | PostgreSQL (catálogo e blobs) | sempre |
| `hub` | FastAPI `/api` + MCP `/mcp` (imagem alvo `runtime`) | sempre |
| `portal` | React + Vite (dev server na 5173) | sempre |
| `hub-test` | mesma imagem do hub, alvo `dev` (pytest, ruff, mypy, scripts) com `./hub` e `./scripts` montados | perfil `test`, sob demanda |

- **Proibido** no plano: venv no host, `pip install` no host, `uvicorn` no host, `npm install`/`npm run` no host, `python` no host.
- Testes, lint e tipos: `docker compose run --rm hub-test pytest ...`, `docker compose run --rm hub-test ruff check .`, `docker compose run --rm hub-test mypy`.
- Build/typecheck do portal: `docker compose run --rm portal npm run build`. `node_modules` fica em volume anônimo do contêiner, não no host.
- Scripts de demo e verificação: `docker compose run --rm hub-test python /scripts/<script>.py` falando com `http://hub:8000` pela rede do Compose.
- Validação do LikeC4: `docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .`
- Únicas coisas fora de contêiner: o navegador abrindo `http://localhost:5173` e o Claude Code (cliente MCP) conectando em `http://localhost:8000/mcp`.
- Subir tudo: `docker compose up --build` (sem passos manuais).

## Global Constraints

- Python **3.12** dentro da imagem `python:3.12-slim`; Node na imagem `node:22-alpine`. Nada instalado no host.
- **Não usar FastMCP.** Só o SDK oficial `mcp`.
- Dependências de runtime do hub (lista fechada): `fastapi`, `uvicorn[standard]`, `python-multipart` (exigida pela FastAPI para `multipart`), `sqlalchemy[asyncio]>=2`, `asyncpg`, `alembic`, `mcp`, `pyyaml` (frontmatter). Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`, `types-PyYAML`. Portal: `react`, `react-dom`, `vite`, `@vitejs/plugin-react`, `typescript`, `@types/react`, `@types/react-dom`. Nada além disso (sem router, sem pydantic-settings, sem testcontainers).
- Código e identificadores em inglês; textos de interface, mensagens de erro ao usuário e documentação em pt-BR.
- Camadas: `api/`, `mcp/` → `service/` → `store/` e `repositories/`. `domain/` é importável por todos e não importa ninguém. Camada inferior nunca importa superior.
- Nomes do modelo C4 no código: `FastAPI`, `Servidor MCP`, `SkillService`, `BlobStore`, `PostgresBlobStore`.
- Limites por env: `MAX_FILE_BYTES=1048576`, `MAX_BUNDLE_BYTES=5242880`, `MAX_FILES=100`.
- Env vars: `DATABASE_URL` (usuário app), `MIGRATION_DATABASE_URL` (dono do esquema — **nova**, exigida pela regra "migrações rodam com outro usuário"; documentar em `.env.example`), `BLOB_BACKEND=postgres`, `MAX_FILE_BYTES`, `MAX_BUNDLE_BYTES`, `MAX_FILES`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `APP_DB_USER`, `APP_DB_PASSWORD`. Só valores de dev no `.env.example`; `.env` no `.gitignore`.
- PKs de `skills`, `skill_versions`, `audit_events` são UUID gerados pela aplicação (evita conceder `USAGE` em sequences).
- Erros REST sempre `{"code": str, "message": str}`. Mapa fixo: `invalid_skill` 422, `invalid_request` 422, `limit_exceeded` 413, `version_exists` 409, `invalid_transition` 409, `not_found` 404, `integrity_error` 500.
- Ator REST na POC (sem login): `"portal"`. Ator MCP: `clientInfo` ou `"anonymous"`.
- `bundle_sha256` = `sha256("\n".join(f"{path}\0{sha256}" for path in sorted(paths)))` — linhas separadas por `\n`, sem `\n` final, UTF-8.
- Fora do escopo: login/SSO, S3/Azure, CI, busca, diff, multi-tenant, sync para `~/.claude/skills`.
- Commits terminam com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **`.zip` criado pelo Finder do Mac** traz `__MACOSX/` e `.DS_Store`: devem ser ignorados silenciosamente, não rejeitados como "fora da pasta da skill". Teste em Task 4.
2. **Zip bomb / tamanho declarado mentiroso:** o limite vale para bytes descomprimidos lidos de fato (ler em blocos e abortar ao passar), não só `ZipInfo.file_size`. Teste em Task 4.
3. **Dois uploads simultâneos da mesma `skill@versão`:** um 201 e um 409 — a violação de `UNIQUE` vira `VersionConflict`, nunca 500. Teste em Task 8.
4. **`SKILL.md` com BOM, CRLF, frontmatter sem `---` de fechamento ou que não é mapa YAML; `metadata.version: 1.0` (YAML vira float):** sempre 422 claro; versão comparada como `str` e `1.0` ≠ `1.0.0`. Teste em Task 4.
5. **Depreciar a versão que está no canal `stable`:** o MCP para de servi-la imediatamente (canal fica sem versão), em vez de entregar uma versão `deprecated`. Teste em Task 9.

---

## Estrutura de arquivos

```
.gitignore  .env.example  docker-compose.yml
docs/README.md                                        # índice da documentação
docs/superpowers/specs/2026-10-24-skills-hub-poc-design.md  # spec consolidada + decisões
docs/superpowers/plans/2026-10-24-skills-hub-poc.md   # este plano
docs/tasks/README.md                                  # índice e status das tarefas
docs/tasks/00-docs.md … docs/tasks/18-architecture-and-dod.md  # spec de cada tarefa
docs/decisions/mcp-skills-extension.md                # resultado da Task 11
db/init/01-app-role.sh                                # cria APP_DB_USER e banco de teste
hub/Dockerfile  hub/entrypoint.sh  hub/pyproject.toml  hub/alembic.ini
hub/alembic/env.py  hub/alembic/versions/0001_initial.py
hub/src/hub/
  main.py                 # create_app(): FastAPI + mount /mcp + lifespan
  config.py               # Settings (dataclass lida do os.environ)
  domain/errors.py        # HubError e subclasses
  domain/models.py        # Status, Channel, transições, dataclasses
  domain/hashing.py       # sha256_hex, bundle_sha256
  domain/semver.py        # is_semver
  service/validation.py   # parse_upload (md e zip) — pura
  service/skill_service.py
  store/blob_store.py     # Protocol BlobStore
  store/postgres_blob_store.py
  store/factory.py        # make_blob_store(settings, sessions)
  repositories/tables.py  # SQLAlchemy Core Table definitions
  repositories/catalog.py # CatalogRepository (skills, versions, files, channels)
  repositories/audit.py   # AuditRepository
  api/routes.py  api/errors.py  api/schemas.py
  mcp/server.py           # Servidor MCP (handlers) e session manager
hub/tests/
  conftest.py             # engines owner/app, migração, truncate
  fakes.py                # InMemoryBlobStore (só testes)
  contract/test_blob_store.py
  unit/  integration/
portal/Dockerfile  portal/package.json  portal/vite.config.ts  portal/tsconfig.json  portal/index.html
portal/src/{main.tsx, App.tsx, api.ts, types.ts, styles.css}
portal/src/pages/{SkillsPage.tsx, SkillDetailPage.tsx, UploadPage.tsx}
examples/skills/html-landing-page/{SKILL.md, templates/base.html}
examples/skills/fastapi-endpoint/{SKILL.md, reference/checklist.md}
scripts/demo.py  scripts/verify_mcp.py              # rodam dentro do hub-test
```

---

## Fase 0 — Fundação

### Task 0: Documentação do plano e das especificações em `docs/`

Primeira coisa feita após a aprovação, antes de qualquer código. Toda especificação e toda tarefa ficam versionadas dentro de `docs/`.

**Files:**
- Create: `docs/README.md` — índice em pt-BR que liga tudo abaixo e o `arq.c4`.
- Create: `docs/superpowers/specs/2026-10-24-skills-hub-poc-design.md` — especificação consolidada: objetivo, regra "tudo roda no Docker" (tabela de serviços), stack e lista fechada de dependências, camadas, `BlobStore`, modelo de dados com colunas, restrições e grants, ciclo de vida e transições, validação de upload (todas as regras da Task 4), contrato REST com mapa de erros, contrato MCP, variáveis de ambiente, **decisões tomadas** (git, plano único, `retired` só no serviço, ator MCP = `clientInfo`, ator REST = `portal`, `MIGRATION_DATABASE_URL`, UUIDs, `channels.version_id` nulo ao depreciar, `__MACOSX` ignorado, domain/owner vindos de `metadata`) e Review Focus.
- Create: `docs/superpowers/plans/2026-10-24-skills-hub-poc.md` — este plano completo.
- Create: `docs/tasks/README.md` — tabela com nº, título, fase, dependências (tarefas anteriores cujas interfaces consome) e status (`pendente`/`em andamento`/`concluída`).
- Create: `docs/tasks/NN-<slug>.md` — **uma especificação por tarefa** (00 a 18), com seções fixas: **Objetivo**, **Depende de**, **Arquivos**, **Interfaces (consome / produz)** com assinaturas exatas, **Regras e valores da spec**, **Testes** (nome de cada teste e o que afirma), **Comandos de verificação** (todos via Docker) e **Critérios de aceite** (checklist). Ex.: `docs/tasks/04-upload-validation.md`, `docs/tasks/12-mcp-server.md`.

- [ ] **Step 1:** Criar os arquivos acima a partir deste plano (conteúdo das tarefas copiado e organizado nas seções fixas; nada de "TBD").
- [ ] **Step 2:** Conferir que os 19 arquivos `docs/tasks/NN-*.md` existem e que `docs/tasks/README.md` lista todos: `ls docs/tasks | wc -l` → `20`.
- [ ] **Step 3:** Commit (junto com o `git init` da Task 1 se ainda não houver repositório: rodar `git init` aqui) `docs: POC spec, plan and per-task specifications`.

**Regra de manutenção:** ao concluir cada tarefa, o executor atualiza o status em `docs/tasks/README.md` e registra no arquivo da tarefa qualquer desvio ou decisão nova (seção **Notas de execução**), no mesmo commit da tarefa. Se a decisão mudar a spec, atualiza também `docs/superpowers/specs/...` e, se mexer em componente, `docs/arq.c4`.

### Task 1: Repositório, esqueleto do hub em contêiner e ferramentas

**Files:**
- Create: `.gitignore`, `hub/pyproject.toml`, `hub/Dockerfile` (multi-stage: `base` instala deps de runtime; `runtime` copia `src/` e roda como usuário não root; `dev` = `base` + extras `[dev]`, `WORKDIR /app`, instalação editável), `docker-compose.yml` (serviços `hub` e `hub-test` — o `hub-test` no perfil `test`, montando `./hub:/app` e `./scripts:/scripts`), `hub/src/hub/__init__.py`, `hub/src/hub/main.py`, `hub/src/hub/config.py`, pacotes vazios `domain/ service/ store/ repositories/ api/ mcp/` com `__init__.py`
- Test: `hub/tests/unit/test_health.py`, `hub/tests/unit/test_config.py`

**Interfaces:**
- Produces: `create_app(settings: Settings | None = None) -> FastAPI`; `GET /api/health -> {"status": "ok"}`; `@dataclass(frozen=True) class Settings: database_url: str; migration_database_url: str; blob_backend: str; max_file_bytes: int; max_bundle_bytes: int; max_files: int` com `Settings.from_env(env: Mapping[str, str] = os.environ) -> Settings` (defaults de limites da spec; `blob_backend` default `"postgres"`).

- [ ] **Step 1:** `.gitignore` com `.env`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `portal/node_modules/`, `portal/dist/` (o `git init` já foi feito na Task 0).
- [ ] **Step 2:** `pyproject.toml` (layout `src/`, deps da lista fechada; `[tool.pytest.ini_options] asyncio_mode = "auto"`, `testpaths = ["tests"]`; `[tool.ruff] target-version = "py312"`, `select = ["E","F","I","B","UP","ASYNC"]`; `[tool.mypy] strict = true`, `packages = ["hub"]`). `hub/Dockerfile` e `docker-compose.yml` como em Files. `docker compose --profile test build hub-test` → imagem construída.
- [ ] **Step 3: testes que falham** — `test_health_returns_ok` (httpx `ASGITransport`, `GET /api/health` → 200, `{"status": "ok"}`); `test_settings_defaults` (`from_env({"DATABASE_URL": "x", "MIGRATION_DATABASE_URL": "y"})` → `max_file_bytes == 1048576`, `max_bundle_bytes == 5242880`, `max_files == 100`, `blob_backend == "postgres"`); `test_settings_missing_database_url_raises` (`KeyError` ou `ValueError` com o nome da variável).
- [ ] **Step 4:** `docker compose run --rm hub-test pytest tests/unit -v` → FAIL.
- [ ] **Step 5:** Implementar `Settings` e `create_app` (só a rota de health por enquanto).
- [ ] **Step 6:** `docker compose run --rm hub-test pytest tests/unit -v` → PASS; `docker compose run --rm hub-test sh -c "ruff check . && ruff format --check . && mypy"` → limpos.
- [ ] **Step 7:** Commit `chore: bootstrap repo and containerized hub skeleton`.

> Daqui em diante, **todo** "rodar `pytest ...`", "ruff" ou "mypy" neste plano significa `docker compose run --rm hub-test <comando>`.

### Task 2: PostgreSQL no Compose com papéis separados

**Files:**
- Modify: `docker-compose.yml` (adiciona serviço `postgres`; `hub` e `hub-test` passam a ter `depends_on: postgres: condition: service_healthy`)
- Create: `db/init/01-app-role.sh`, `.env.example`
- Test: `hub/tests/integration/test_db_roles.py`, `hub/tests/conftest.py`

**Interfaces:**
- Produces: papel dono = `POSTGRES_USER` (`hub_owner`), papel app = `APP_DB_USER` (`hub_app`, `LOGIN`, sem `CREATEDB`); bancos `skillshub` e `skillshub_test` (ambos donos `hub_owner`; `hub_app` com `CONNECT`). Fixtures em `conftest.py`: `owner_engine`, `app_engine` (session-scoped `AsyncEngine`), lidas de `TEST_MIGRATION_DATABASE_URL` / `TEST_DATABASE_URL`, definidas no serviço `hub-test` como `postgresql+asyncpg://hub_owner:hub_owner_dev@postgres:5432/skillshub_test` e `...hub_app:hub_app_dev@postgres:5432/skillshub_test` (host `postgres` = nome do serviço na rede do Compose).

- [ ] **Step 1:** `docker-compose.yml`: `postgres:17`, `env_file: .env`, porta `5432:5432` (só para inspeção opcional), volume nomeado `pgdata`, monta `./db/init` em `/docker-entrypoint-initdb.d`, healthcheck `pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}` (interval 5s, retries 10).
- [ ] **Step 2:** `01-app-role.sh` (`set -euo pipefail`, `psql -v ON_ERROR_STOP=1`): cria role app com senha `$APP_DB_PASSWORD`, `CREATE DATABASE skillshub_test OWNER $POSTGRES_USER`, `REVOKE ALL ON DATABASE ... FROM PUBLIC`, `GRANT CONNECT` ao app nos dois bancos, e `REVOKE CREATE ON SCHEMA public FROM PUBLIC` em cada banco.
- [ ] **Step 3:** `.env.example` com todas as variáveis das Global Constraints, comentadas em pt-BR, valores de dev. `cp .env.example .env`.
- [ ] **Step 4: teste que falha** — `test_app_role_cannot_create_table` (como app: `CREATE TABLE x(i int)` → `asyncpg.InsufficientPrivilegeError`); `test_app_role_can_connect` (`SELECT current_user` == `hub_app`).
- [ ] **Step 5:** `docker compose run --rm hub-test pytest tests/integration/test_db_roles.py -v` (o Compose sobe o `postgres` e espera ficar `healthy`) → PASS.
- [ ] **Step 6:** Commit `chore: postgres service with owner and app roles`.

## Fase 1 — Domínio (puro, sem I/O)

### Task 3: Erros, ciclo de vida, semver e hashing

**Files:**
- Create: `hub/src/hub/domain/{errors.py, models.py, hashing.py, semver.py}`
- Test: `hub/tests/unit/{test_lifecycle.py, test_hashing.py, test_semver.py}`

**Interfaces:**
- Produces:
  - `class HubError(Exception): code: ClassVar[str]; def __init__(self, message: str)`; subclasses `SkillValidationError("invalid_skill")`, `LimitExceededError("limit_exceeded")`, `VersionConflictError("version_exists")`, `InvalidTransitionError("invalid_transition")`, `NotFoundError("not_found")`, `IntegrityError("integrity_error")`.
  - `class Status(StrEnum): DRAFT, BETA, STABLE, DEPRECATED, RETIRED` (valores minúsculos); `class Channel(StrEnum): BETA, STABLE`.
  - `ALLOWED_TRANSITIONS: frozenset[tuple[Status, Status]]` = exatamente os 5 pares da spec; `def check_transition(current: Status, target: Status) -> None` (levanta `InvalidTransitionError` com mensagem pt-BR `"Transição de {current} para {target} não é permitida."`).
  - `def channel_for(status: Status) -> Channel | None` (`BETA→BETA`, `STABLE→STABLE`, demais `None`).
  - `@dataclass(frozen=True) class SkillFile: path: str; data: bytes`; `FileEntry: path: str; sha256: str; size: int`.
  - `def sha256_hex(data: bytes) -> str`; `def bundle_sha256(entries: Iterable[FileEntry]) -> str`.
  - `def is_semver(value: str) -> bool` — semver 2.0.0 completo (regex oficial de semver.org; aceita pré-release e build).

- [ ] **Step 1: testes que falham:**
  - `test_allowed_transitions_pass` parametrizado nos 5 pares; `test_forbidden_transitions_raise` parametrizado em todos os outros pares de `Status×Status` (inclui `draft→stable`, `stable→beta`, `retired→*`, `x→x`).
  - `test_bundle_sha256_sorted_by_path`: entradas `b.md`/`a.md` em qualquer ordem dão o mesmo valor, igual a `sha256_hex(b"a.md\0<ha>\nb.md\0<hb>")`.
  - `test_semver`: válidos `1.0.0`, `0.1.0-beta.1`, `1.2.3+build.5`; inválidos `1.0`, `01.0.0`, `v1.0.0`, `1.0.0.0`, `""`.
- [ ] **Step 2:** `pytest tests/unit -v` → FAIL.
- [ ] **Step 3:** Implementar os quatro módulos.
- [ ] **Step 4:** `pytest tests/unit -v` → PASS; ruff e mypy limpos.
- [ ] **Step 5:** Commit `feat(domain): lifecycle, errors, semver and hashing`.

### Task 4: Validação de upload (`SKILL.md` e `.zip`)

**Files:**
- Create: `hub/src/hub/service/validation.py`
- Test: `hub/tests/unit/test_validation.py` (zips montados em memória com `zipfile`)

**Interfaces:**
- Consumes: `SkillFile`, `SkillValidationError`, `LimitExceededError`, `is_semver` (Task 3).
- Produces: `@dataclass(frozen=True) class UploadLimits: max_file_bytes: int; max_bundle_bytes: int; max_files: int`; `@dataclass(frozen=True) class ParsedSkill: name: str; description: str; frontmatter: dict[str, Any]; files: tuple[SkillFile, ...]`; `def parse_upload(filename: str, data: bytes, version: str, limits: UploadLimits) -> ParsedSkill`.

Regras (decididas aqui):
- `filename` terminado em `.md` (case-insensitive) → um arquivo `SKILL.md`; `.zip` → pacote; outro → `SkillValidationError`.
- Zip: ignorar entradas de diretório, `__MACOSX/**` e qualquer `.DS_Store`. Rejeitar caminho absoluto, `\`, componente `..`, symlink (`(external_attr >> 16) & 0o170000 == 0o120000`), nomes duplicados. Raiz da skill = raiz do zip se houver `SKILL.md` lá; senão, se todas as entradas estiverem sob uma única pasta de topo com `SKILL.md`, essa pasta é a raiz e o prefixo é removido; qualquer outro arquivo fora da raiz → erro.
- Limites: `MAX_FILES` sobre arquivos aceitos; cada arquivo lido em blocos de 64 KiB e abortado ao passar `max_file_bytes`; soma abortada ao passar `max_bundle_bytes`; `.md` avulso também respeita `max_file_bytes`. Estouro → `LimitExceededError`.
- Frontmatter: decodificar UTF-8 (remover BOM), normalizar CRLF só para o parse; exigir `---` na 1ª linha e `---` de fechamento; `yaml.safe_load` deve dar `dict`; `name` casa `^[a-z0-9]+(-[a-z0-9]+)*$`; `description` string não vazia; se `metadata.version` existir, `str(valor) == version`. `version` precisa passar `is_semver`. Os bytes gravados são os originais (sem normalizar).
- Mensagens em pt-BR, citando o arquivo/campo.

- [ ] **Step 1: testes que falham** (um `test_` por regra): `.md` válido → `ParsedSkill` com 1 arquivo `SKILL.md`; zip com raiz direta; zip com pasta única `my-skill/` (prefixo removido); **zip do Finder com `__MACOSX/` e `.DS_Store` aceito sem esses arquivos** (Review Focus 1); sem `SKILL.md` → `SkillValidationError`; `../evil`, `/abs`, `a\\b`, symlink, duplicado, arquivo fora da pasta → `SkillValidationError`; 101 arquivos → `LimitExceededError`; **entrada com `file_size` declarado pequeno mas conteúdo real > limite → `LimitExceededError`** (Review Focus 2; forjar `ZipInfo` após escrever ou usar zip de 2 MB de zeros com limite 1 MB); soma > bundle → `LimitExceededError`; **BOM + CRLF aceito; sem fechamento `---`, frontmatter lista, YAML inválido → `SkillValidationError`; `metadata.version: 1.0` com versão `1.0.0` → `SkillValidationError`** (Review Focus 4); `name: My_Skill` → erro; versão `1.0` → erro; extensão `.txt` → erro.
- [ ] **Step 2:** `pytest tests/unit/test_validation.py -v` → FAIL.
- [ ] **Step 3:** Implementar `parse_upload` (funções privadas `_read_zip`, `_parse_frontmatter`, `_check_path`).
- [ ] **Step 4:** PASS; ruff e mypy limpos.
- [ ] **Step 5:** Commit `feat(service): upload validation for SKILL.md and zip`.

## Fase 2 — Persistência

### Task 5: Esquema, migração e imutabilidade imposta pelo banco

**Files:**
- Create: `hub/alembic.ini`, `hub/alembic/env.py` (async, usa `MIGRATION_DATABASE_URL`), `hub/alembic/versions/0001_initial.py`, `hub/src/hub/repositories/tables.py`
- Modify: `hub/tests/conftest.py` (fixture session-scoped `migrated` que roda `alembic downgrade base` + `upgrade head` no banco de teste com URL do dono; fixture autouse `clean_db` que faz `TRUNCATE ... CASCADE` como dono nas tabelas)
- Test: `hub/tests/integration/test_permissions.py`

**Interfaces:**
- Produces: `metadata: MetaData` e `Table`s `skills, skill_versions, skill_version_files, channels, blobs, audit_events` em `tables.py`, colunas exatamente da spec, mais: `skill_versions.status` com `CHECK` nos 5 valores; `channels` PK `(skill_id, channel)`, `channel` com `CHECK IN ('beta','stable')`, `version_id` **nullable**; `UNIQUE(skill_id, version)`; `skill_version_files` PK `(version_id, path)`, FK de `sha256` → `blobs`; `audit_events.version` nullable.
- Grants na migração (para `APP_DB_USER`, lido de env com default `hub_app`): `USAGE ON SCHEMA public`; `SELECT, INSERT` em `blobs, skill_version_files, audit_events`; `SELECT, INSERT` + `UPDATE (status)` em `skill_versions`; `SELECT, INSERT` em `skills`; `SELECT, INSERT, UPDATE (version_id)` em `channels`. Nenhum `DELETE`/`TRUNCATE`. `downgrade` remove tudo.

- [ ] **Step 1: testes que falham** (como `hub_app`, cada um esperando `InsufficientPrivilegeError`): `test_app_cannot_update_blobs`; `test_app_cannot_delete_from_any_table` (parametrizado nas 6 tabelas); `test_app_cannot_update_version_frontmatter`; `test_app_cannot_update_files`; `test_app_cannot_update_audit`. E positivos: `test_app_can_update_version_status`, `test_app_can_update_channel_version`.
- [ ] **Step 2:** `pytest tests/integration/test_permissions.py -v` → FAIL.
- [ ] **Step 3:** Implementar `tables.py`, `env.py` e `0001_initial.py` (a migração pode usar `op.create_table` espelhando `tables.py`; os grants via `op.execute`).
- [ ] **Step 4:** PASS; `docker compose run --rm hub-test alembic upgrade head` (com `MIGRATION_DATABASE_URL` do banco `skillshub`) também roda limpo.
- [ ] **Step 5:** Commit `feat(db): schema, migration and least-privilege grants`.

### Task 6: `BlobStore`, `PostgresBlobStore` e testes de contrato

**Files:**
- Create: `hub/src/hub/store/blob_store.py`, `hub/src/hub/store/postgres_blob_store.py`, `hub/src/hub/store/factory.py`, `hub/tests/fakes.py`
- Test: `hub/tests/contract/test_blob_store.py`, `hub/tests/integration/test_blob_tamper.py`

**Interfaces:**
- Consumes: `sha256_hex`, `IntegrityError`, `NotFoundError` (Task 3); `blobs` table (Task 5).
- Produces: `class BlobStore(Protocol)` exatamente como na spec (`put`, `get`, `exists`); `class PostgresBlobStore: def __init__(self, sessions: async_sessionmaker[AsyncSession])`; `def make_blob_store(settings: Settings, sessions: async_sessionmaker[AsyncSession]) -> BlobStore` (`"postgres"` → `PostgresBlobStore`; outro → `ValueError("BLOB_BACKEND não suportado: ...")`); `InMemoryBlobStore` em `tests/fakes.py` (só para testes, mesma semântica).
- `put` usa `INSERT ... ON CONFLICT (sha256) DO NOTHING` em transação própria. `get` de hash inexistente → `NotFoundError`; conteúdo cujo hash recalculado diverge → `IntegrityError`.

- [ ] **Step 1: testes de contrato que falham**, com fixture `blob_store` parametrizada em `[InMemoryBlobStore, PostgresBlobStore]` (docstring do módulo explica que toda implementação futura entra nessa lista): `test_put_returns_sha256_hex` (`put(b"abc")` == `"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"`); `test_put_is_idempotent` (2 puts, mesmo hash, sem erro; no Postgres, `count(*) == 1`); `test_get_roundtrip`; `test_exists_true_false`; `test_get_unknown_raises_not_found`; `test_put_empty_bytes`.
- [ ] **Step 2: teste de adulteração** — `test_tampered_blob_raises_integrity_error`: `put`, depois `UPDATE blobs SET content = 'x'` **como dono**, depois `get` → `IntegrityError`.
- [ ] **Step 3:** FAIL → implementar → `pytest tests/contract tests/integration/test_blob_tamper.py -v` PASS.
- [ ] **Step 4:** Commit `feat(store): BlobStore protocol, PostgresBlobStore and contract tests`.

### Task 7: Repositórios do catálogo e da auditoria

**Files:**
- Create: `hub/src/hub/repositories/catalog.py`, `hub/src/hub/repositories/audit.py`
- Test: `hub/tests/integration/test_repositories.py`

**Interfaces:**
- Consumes: tabelas (Task 5), `Status`, `Channel`, `FileEntry`, `VersionConflictError`.
- Produces (todos recebem uma `AsyncSession` já em transação; nenhum faz commit):
  - `CatalogRepository(session)`: `get_or_create_skill(name, domain, owner) -> UUID`; `find_skill(name) -> SkillRow | None`; `list_skills() -> list[SkillRow]`; `insert_version(skill_id, version, frontmatter, bundle_sha256, created_by) -> UUID` (captura `sqlalchemy.exc.IntegrityError` de `UNIQUE` → `VersionConflictError`); `insert_files(version_id, entries: Sequence[FileEntry])`; `find_version(skill_id, version) -> VersionRow | None`; `list_versions(skill_id) -> list[VersionRow]`; `list_files(version_id) -> list[FileEntry]`; `set_status(version_id, status)`; `set_channel(skill_id, channel, version_id: UUID | None)` (upsert `ON CONFLICT (skill_id, channel) DO UPDATE SET version_id`); `clear_channels_pointing_to(version_id)`; `channels_of(skill_id) -> dict[Channel, str]` (canal → versão, só os não nulos).
  - `AuditRepository(session)`: `record(actor: str, action: str, skill: str, version: str | None) -> None`.
  - `SkillRow`/`VersionRow`: dataclasses frozen em `catalog.py` com os campos das tabelas.

- [ ] **Step 1: testes que falham** (via `app_engine`, provando que funciona com o usuário restrito): criar skill/versão/arquivos e reler; `insert_version` repetido → `VersionConflictError`; `set_channel` duas vezes atualiza; `clear_channels_pointing_to` zera só o canal certo; `channels_of` ignora nulos; `record` grava `at` automático.
- [ ] **Step 2:** FAIL → implementar → PASS.
- [ ] **Step 3:** Commit `feat(repositories): catalog and audit repositories`.

## Fase 3 — Regras de negócio

### Task 8: `SkillService` — upload e consultas

**Files:**
- Create: `hub/src/hub/service/skill_service.py`
- Test: `hub/tests/integration/test_skill_service_upload.py`

**Interfaces:**
- Consumes: `parse_upload`, `UploadLimits` (Task 4); `BlobStore` (Task 6); repositórios (Task 7).
- Produces:
  - `class SkillService: def __init__(self, sessions: async_sessionmaker[AsyncSession], blobs: BlobStore, limits: UploadLimits)`
  - `async def upload(self, *, filename: str, data: bytes, version: str, actor: str) -> VersionDetail`
  - `async def list_skills(self) -> list[SkillSummary]`; `async def get_skill(self, name: str) -> SkillDetail`; `async def get_version(self, name: str, version: str) -> VersionDetail`
  - Dataclasses frozen (em `domain/models.py`): `SkillSummary(name, domain, owner, stable: str | None, beta: str | None)`; `VersionSummary(version, status: Status, bundle_sha256, created_by, created_at)`; `SkillDetail(name, domain, owner, description, channels: dict[Channel, str], versions: list[VersionSummary])` (versões em ordem de `created_at` desc); `VersionDetail(name, version, status, frontmatter, bundle_sha256, created_by, created_at, files: list[FileEntry])`.
- Fluxo `upload`: `parse_upload` → `put` de cada arquivo (fora da transação; blobs órfãos são inofensivos por serem endereçados por conteúdo) → uma transação: `get_or_create_skill` (domain = `frontmatter.metadata.domain` ou `"geral"`, owner = `frontmatter.metadata.owner` ou o `actor`), `insert_version` como `draft`, `insert_files`, `audit.record(actor, "upload", name, version)`.

- [ ] **Step 1: testes que falham:** upload `.md` → `status == draft`, 1 arquivo, `bundle_sha256` igual a `bundle_sha256(files)`; upload `.zip` com 2 arquivos; repetir `skill@versão` → `VersionConflictError` e o conteúdo original intacto; **`asyncio.gather` de dois uploads iguais → exatamente um sucesso e um `VersionConflictError`** (Review Focus 3); audit `upload` gravado; `list_skills` mostra `stable=None, beta=None`; `get_skill("nope")` → `NotFoundError`.
- [ ] **Step 2:** FAIL → implementar → PASS.
- [ ] **Step 3:** Commit `feat(service): SkillService upload and queries`.

### Task 9: `SkillService` — governança e entrega

**Files:**
- Modify: `hub/src/hub/service/skill_service.py`
- Test: `hub/tests/integration/test_skill_service_lifecycle.py`

**Interfaces:**
- Produces:
  - `async def promote(self, name: str, version: str, to: Status, actor: str) -> VersionDetail` (aceita só `BETA`/`STABLE`; outro → `InvalidTransitionError`)
  - `async def deprecate(self, name, version, actor) -> VersionDetail`; `async def retire(self, name, version, actor) -> VersionDetail`
  - `async def list_published(self, channel: Channel = Channel.STABLE) -> list[PublishedSkill]`
  - `async def get_published(self, name: str, channel: Channel = Channel.STABLE, actor: str = "anonymous") -> PublishedSkill` (grava audit `mcp_get`)
  - `async def read_file(self, name: str, path: str, channel: Channel, actor: str) -> bytes` (via `BlobStore.get`, portanto confere hash; grava audit `mcp_read`)
  - `PublishedSkill(name, description, version, bundle_sha256, files: list[FileEntry])` em `domain/models.py`.
- Cada transição: **uma transação** com `check_transition`, `set_status`, `set_channel(channel_for(to))` quando houver canal, `clear_channels_pointing_to` em `deprecate`/`retire`, e `audit.record(actor, "promote"|"deprecate"|"retire", ...)`.

- [ ] **Step 1: testes que falham:** `draft→beta→stable` atualiza status e canais e grava 2 audits `promote`; `draft→stable` → `InvalidTransitionError` sem audit e sem mudança de canal; nova versão promovida a `stable` substitui o canal; **depreciar a versão do canal `stable` → `list_published()` não a contém e `get_published` → `NotFoundError`** (Review Focus 5); `deprecated→retired` ok, `draft→retired` erro; `read_file` com blob adulterado (UPDATE como dono) → `IntegrityError`; `read_file` de path inexistente → `NotFoundError`; `get_published(channel=BETA)` serve a beta; audits `mcp_get`/`mcp_read` com o actor passado; falha no meio da transação (forçar erro no audit com monkeypatch) não deixa status alterado.
- [ ] **Step 2:** FAIL → implementar → PASS.
- [ ] **Step 3:** Commit `feat(service): promotion, deprecation and delivery`.

## Fase 4 — Adaptadores

### Task 10: API REST (`FastAPI`)

**Files:**
- Create: `hub/src/hub/api/routes.py`, `hub/src/hub/api/errors.py`, `hub/src/hub/api/schemas.py`
- Modify: `hub/src/hub/main.py` (engine/sessionmaker no lifespan, `SkillService` em `app.state.service`, `include_router(prefix="/api")`, handlers de erro)
- Test: `hub/tests/integration/test_api.py`

**Interfaces:**
- Consumes: `SkillService` (Tasks 8–9).
- Produces: as 6 rotas da tabela da spec + `/api/health`. `POST /api/skills/upload` recebe `multipart` com `file: UploadFile` e `version: str` → 201 com `VersionDetail`. `promote` com corpo `{"to": "beta" | "stable"}` (pydantic `Literal`). Ator fixo `"portal"`. `api/errors.py` registra handler de `HubError` (mapa das Global Constraints) e de `RequestValidationError` → 422 `invalid_request`. Schemas pydantic espelham os dataclasses (datas em ISO 8601). Rotas não têm regra de negócio: só traduzem.
- Leitura do arquivo enviado limitada a `max_bundle_bytes + 1` bytes (estouro → 413 antes de chegar ao serviço).

- [ ] **Step 1: testes que falham** (httpx + app real contra banco de teste): upload `.md` → 201 e `status: "draft"`; repetido → 409 `{"code":"version_exists"}`; zip com `../` → 422 `invalid_skill`; arquivo grande → 413; `GET /api/skills` lista `stable`/`beta`; detalhe; versão com arquivos e hashes; promote inválido → 409 `invalid_transition`; `{"to":"retired"}` → 422 `invalid_request`; deprecate; skill inexistente → 404 `not_found`; toda resposta de erro tem exatamente `code` e `message`.
- [ ] **Step 2:** FAIL → implementar → PASS.
- [ ] **Step 3:** Commit `feat(api): REST routes for the portal`.

### Task 11: Spike — extensão de Skills (SEP-2640) no pacote `mcp`

**Files:**
- Create: `docs/decisions/mcp-skills-extension.md` (pt-BR)

Primeira tarefa do MCP exigida pela spec. Não produz código de produção.

- [ ] **Step 1:** Registrar versão: `docker compose run --rm hub-test pip show mcp`.
- [ ] **Step 2:** Procurar a extensão: `docker compose run --rm hub-test sh -c 'grep -rniE "skills/(list|get)|SEP-2640|skill://" $(python -c "import mcp,os;print(os.path.dirname(mcp.__file__))")'` e verificar o estado do PR `modelcontextprotocol/python-sdk#3485` (WebFetch do GitHub).
- [ ] **Step 3:** Ler a SEP-2640 e anotar no documento o formato exato de request/response de `skills/list` e `skills/get` (campos, nomes, como digests e tamanhos aparecem, capability anunciada no `initialize`).
- [ ] **Step 4:** Se a extensão não existir: provar num script descartável (rodado com `docker compose run --rm hub-test python /scripts/_spike_mcp.py`, apagado antes do commit) como registrar métodos customizados no `mcp.server.lowlevel.Server` (o parse de `ClientRequest` é uma união fechada; verificar se há gancho para métodos de extensão). Registrar no documento o caminho escolhido.
- [ ] **Step 5: ponto de parada:** se não houver forma suportada de registrar `skills/list`/`skills/get` sem modificar o SDK, **parar e perguntar ao usuário** antes da Task 12 (a alternativa seria só resources + tools de fallback).
- [ ] **Step 6:** Commit `docs: MCP skills extension findings`.

### Task 12: Servidor MCP em `/mcp`

**Files:**
- Create: `hub/src/hub/mcp/server.py`
- Modify: `hub/src/hub/main.py` (montar `StreamableHTTPSessionManager` em `/mcp` e rodar `session_manager.run()` dentro do lifespan da FastAPI; se a montagem conflitar, segundo processo na mesma imagem conforme spec — registrar no documento da Task 11)
- Test: `hub/tests/integration/test_mcp.py`

**Interfaces:**
- Consumes: `SkillService.list_published`, `get_published`, `read_file` (Task 9); formato da Task 11.
- Produces: `def build_mcp_server(service: SkillService) -> Server`; `def build_session_manager(server: Server) -> StreamableHTTPSessionManager`.
  - `skills/list` e `skills/get` no formato da SEP-2640 (via extensão nativa ou registro manual decidido na Task 11); cada skill lista arquivos com `uri` `skill://<name>/<path>`, `sha256` e `size`; **nunca** `"dynamic"`. Parâmetro opcional `channel` (`"beta"` explícito; default `stable`; outro → erro de parâmetros MCP).
  - `resources/list` (só arquivos das skills `stable`) e `resources/read` para `skill://<name>/SKILL.md` e `skill://<name>/<path>` (texto UTF-8 como `TextResourceContents`, senão `BlobResourceContents` base64); aceitar `?channel=beta` na URI.
  - Tools de fallback `list_skills(channel?)` e `get_skill(name, channel?)` retornando JSON com os mesmos dados (inclusive digests e o conteúdo do `SKILL.md` em `get_skill`).
  - `_actor()` = `f"{clientInfo.name}/{clientInfo.version}"` de `server.request_context.session.client_params`, ou `"anonymous"`.
  - Erros de domínio viram erro MCP com a mensagem pt-BR; `IntegrityError` nunca devolve o conteúdo adulterado.

- [ ] **Step 1: testes que falham** usando o cliente oficial (`mcp.client.streamable_http.streamablehttp_client` + `ClientSession`, `clientInfo` nome `test-client`, contra uvicorn em porta livre ou transporte ASGI): `skills/list` mostra só a skill `stable`, com digests; `channel=beta` mostra a beta; `resources/read` de `skill://<name>/SKILL.md` devolve conteúdo cujo `sha256` == digest listado; tool `get_skill` idem; blob adulterado → erro MCP; audit `mcp_read` com actor `test-client/<versão>`; skill só em `draft` não aparece.
- [ ] **Step 2:** FAIL → implementar → PASS.
- [ ] **Step 3:** Commit `feat(mcp): skills extension, resources and fallback tools`.

## Fase 5 — Portal

Sem framework de testes no portal (fora da lista de dependências). Verificação = `docker compose run --rm portal npm run build` (inclui `tsc --noEmit`) + checagem manual no navegador em `http://localhost:5173` com `docker compose up --build` no ar. Nenhum `npm` no host.

### Task 13: Esqueleto do portal em contêiner, cliente da API e tela Skills

**Files:**
- Create: `portal/Dockerfile` (`node:22-alpine`, `WORKDIR /app`, copia `package*.json`, `npm ci`, copia o resto, `CMD ["npm","run","dev","--","--host","0.0.0.0"]`), `portal/.dockerignore` (`node_modules`, `dist`)
- Modify: `docker-compose.yml` (serviço `portal`: porta `5173:5173`, `API_TARGET=http://hub:8000`, bind mount `./portal:/app` + volume anônimo `/app/node_modules` para hot reload sem `node_modules` no host, `depends_on: hub`)
- Create: `portal/package.json`, `portal/vite.config.ts` (proxy `/api` → `process.env.API_TARGET ?? "http://localhost:8000"`, `server.host = true`, porta 5173), `portal/tsconfig.json`, `portal/index.html` (`lang="pt-BR"`), `portal/src/{main.tsx, App.tsx, api.ts, types.ts, styles.css}`, `portal/src/pages/SkillsPage.tsx`

**Interfaces:**
- Produces: `types.ts` espelha os schemas da Task 10; `api.ts`: `listSkills()`, `getSkill(name)`, `getVersion(name, version)`, `uploadSkill(file: File, version: string)`, `promote(name, version, to: "beta" | "stable")`, `deprecate(name, version)`, todas `Promise<T>`, lançando `ApiError { code: string; message: string }` quando `!res.ok`. Navegação por hash em `App.tsx` (`#/`, `#/skills/<name>`, `#/upload`) sem biblioteca de rotas.
- Tela Skills: tabela nome, domínio, versão `stable`, versão `beta` (traço quando vazio); estado vazio "Nenhuma skill publicada ainda."; erro mostra `message`.

- [ ] **Step 1:** Criar arquivos; gerar `package-lock.json` dentro do contêiner (`docker run --rm -v "$PWD/portal:/app" -w /app node:22-alpine npm install`); `docker compose run --rm portal npm run build` → sucesso sem erros de tipo.
- [ ] **Step 2:** `docker compose up --build -d` e abrir `http://localhost:5173` no browser pane: estado vazio aparece; após um upload (`docker compose run --rm hub-test python /scripts/demo.py` quando existir, ou upload pela própria API via `hub-test`), a lista mostra a skill.
- [ ] **Step 3:** Commit `feat(portal): scaffold, API client and skills list`.

### Task 14: Tela Detalhe com Promover e Depreciar

**Files:**
- Create: `portal/src/pages/SkillDetailPage.tsx`

- [ ] **Step 1:** Implementar: cabeçalho com nome, descrição, domínio, canais; tabela de versões (versão, status como etiqueta, autor, data em `pt-BR`); ao selecionar versão, lista de arquivos com caminho, tamanho e SHA-256 (fonte mono, cópia com clique); botões conforme status — `draft`: "Promover para beta"; `beta`: "Promover para stable" e "Depreciar"; `stable`: "Depreciar"; demais: nenhum. `deprecate` pede `confirm()`. Erro 409 mostra `message`. Recarrega após ação.
- [ ] **Step 2:** `docker compose run --rm portal npm run build` → sucesso; com o Compose no ar, no browser pane, promover `draft→beta→stable` e depreciar, conferindo que a lista principal reflete os canais.
- [ ] **Step 3:** Commit `feat(portal): skill detail with promote and deprecate`.

### Task 15: Tela Upload

**Files:**
- Create: `portal/src/pages/UploadPage.tsx`

- [ ] **Step 1:** Implementar: área de arrastar e soltar (e clique para escolher) aceitando `.md` e `.zip`; campo versão com validação semver no cliente (mesma regex da Task 3) e dica "ex.: 1.0.0"; botão "Enviar" desabilitado até haver arquivo e versão válida; sucesso → navega para o detalhe; erro → mostra `message` do hub (409, 413, 422).
- [ ] **Step 2:** `docker compose run --rm portal npm run build`; com o Compose no ar, no browser pane: upload de `.md` ok, repetido mostra mensagem de versão existente, zip inválido mostra erro de validação.
- [ ] **Step 3:** Commit `feat(portal): upload screen`.

## Fase 6 — Integração e demonstração

### Task 16: Compose final — subida única, migração automática e healthchecks

**Files:**
- Create: `hub/entrypoint.sh` (`alembic upgrade head` com `MIGRATION_DATABASE_URL`, depois `exec uvicorn hub.main:app --host 0.0.0.0 --port 8000`)
- Modify: `hub/Dockerfile` (alvo `runtime` usa o `entrypoint.sh`), `docker-compose.yml` (`hub`: porta `8000:8000`, healthcheck em `/api/health` via `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"`; `portal`: `depends_on: hub: condition: service_healthy`)

- [ ] **Step 1:** `docker compose down -v && docker compose up --build -d` → os três serviços sobem e ficam `healthy`/`running` sem passo manual (`docker compose ps`).
- [ ] **Step 2:** `docker compose run --rm hub-test python -c "import httpx; print(httpx.get('http://hub:8000/api/health').json())"` → `{'status': 'ok'}`; abrir `http://localhost:5173` no navegador → portal carrega a lista (proxy `/api` funcionando dentro do Compose).
- [ ] **Step 3:** `docker compose logs hub` mostra a migração aplicada antes do uvicorn.
- [ ] **Step 4:** Commit `chore: single-command compose with auto-migration`.

### Task 17: Skills de exemplo, demo e consumo pelo Claude Code

**Files:**
- Create: `examples/skills/html-landing-page/SKILL.md` + `templates/base.html` (skill de HTML, enviada como `.zip`), `examples/skills/fastapi-endpoint/SKILL.md` + `reference/checklist.md` (skill de back-end), `scripts/demo.py`, `scripts/verify_mcp.py`
- Modify: `docker-compose.yml` (`hub-test` também monta `./examples:/examples:ro`)
- Test: `hub/tests/integration/test_end_to_end.py`

**Interfaces:**
- `scripts/demo.py [api_url]` (default `http://hub:8000/api`; usa `httpx` e `zipfile`, ambos já na imagem `dev`): empacota cada pasta de `/examples/skills` em zip em memória, faz upload `1.0.0`, promove `beta` e `stable`, e imprime `GET /api/skills`. Em 409 avisa e segue.
- `scripts/verify_mcp.py [url]` (default `http://hub:8000/mcp`): conecta com o cliente oficial, chama `skills/list`, lê cada arquivo via `resources/read`, recalcula SHA-256, compara com o digest e com `bundle_sha256`, imprime OK/FALHA por arquivo e sai com código ≠ 0 em divergência.

- [ ] **Step 1: teste que falha** — `test_end_to_end`: upload das duas skills de exemplo pelo app → promoção `beta`→`stable` → via cliente MCP, ambas listadas e todo conteúdo bate com os digests → audits `upload`, `promote`×2, `mcp_read` presentes.
- [ ] **Step 2:** FAIL → escrever exemplos → PASS.
- [ ] **Step 3:** Com o Compose no ar: `docker compose run --rm hub-test python /scripts/demo.py` e `docker compose run --rm hub-test python /scripts/verify_mcp.py` → todos OK.
- [ ] **Step 4:** Adulterar um blob (`docker compose exec postgres psql -U hub_owner -d skillshub -c "UPDATE blobs SET content='x' WHERE sha256=(SELECT sha256 FROM blobs LIMIT 1)"`) e rodar `verify_mcp.py` de novo → erro de integridade reportado; `docker compose down -v` para limpar.
- [ ] **Step 5:** Conectar o Claude Code: `claude mcp add --transport http skills-hub http://localhost:8000/mcp` e, numa sessão, pedir para ler a skill `fastapi-endpoint` — confirmar que veio pela MCP.
- [ ] **Step 6:** Commit `feat: example skills, demo and MCP verification script`.

### Task 18: Arquitetura como código e definição de pronto

**Files:**
- Modify: `docs/arq.c4` (só se algo divergiu: por exemplo, descrever as tools de fallback no `Servidor MCP` ou adicionar `repositories` como componente se o modelo precisar refletir o código)

- [ ] **Step 1:** Comparar componentes e relações do código com `docs/arq.c4`; atualizar o que divergir.
- [ ] **Step 2:** `docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .` → sem erros.
- [ ] **Step 3:** Rodar tudo em contêiner: `docker compose run --rm hub-test sh -c "pytest -v && ruff check . && mypy"` e `docker compose run --rm portal npm run build`.
- [ ] **Step 4:** Percorrer a "Definição de pronto da POC" do `CLAUDE.md` item a item e marcar com a evidência (teste ou comando).
- [ ] **Step 5:** Commit `docs: update architecture model and close POC checklist`.

---

## Verificação ponta a ponta

Tudo via Docker; o host só tem navegador e Claude Code como clientes.

1. `docker compose down -v && docker compose up --build` — `postgres`, `hub` e `portal` saudáveis, migração aplicada sozinha.
2. Portal em `http://localhost:5173`: upload `.md` e `.zip`, erro de versão repetida (409), promoção `draft→beta→stable`, depreciação.
3. `docker compose run --rm hub-test pytest -v` — contrato do `BlobStore`, permissões do banco, serviço, API, MCP e ponta a ponta passando.
4. `docker compose run --rm hub-test python /scripts/verify_mcp.py` — hashes conferidos; com blob adulterado, falha de integridade.
5. Claude Code no host conectado em `http://localhost:8000/mcp` lendo uma skill `stable`.
6. `docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .` sem erros.
