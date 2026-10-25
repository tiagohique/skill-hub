# Tarefa 01 — Esqueleto do hub em contêiner

**Fase:** 0 · **Depende de:** 00 · **Commit:** `chore: bootstrap repo and containerized hub skeleton`

## Objetivo
Ter o hub FastAPI mínimo (`/api/health`) construído e testado dentro de contêiner, com lint e tipos.

## Arquivos
`.gitignore`, `hub/pyproject.toml`, `hub/Dockerfile` (multi-stage `base`/`runtime`/`dev`, usuário não root), `docker-compose.yml` (serviços `hub` e `hub-test` no perfil `test`, montando `./hub:/app` e `./scripts:/scripts`), `hub/src/hub/{__init__,main,config}.py`, pacotes vazios `domain service store repositories api mcp`, `hub/tests/unit/{test_health,test_config}.py`.

## Interfaces (consome / produz)
Produz `create_app(settings: Settings | None = None) -> FastAPI`; `GET /api/health -> {"status":"ok"}`; `Settings` (dataclass frozen: `database_url`, `migration_database_url`, `blob_backend`, `max_file_bytes`, `max_bundle_bytes`, `max_files`) com `Settings.from_env(env: Mapping[str,str] = os.environ)`.

## Regras e valores da spec
Defaults: `blob_backend="postgres"`, `max_file_bytes=1048576`, `max_bundle_bytes=5242880`, `max_files=100`. `DATABASE_URL` e `MIGRATION_DATABASE_URL` obrigatórias (erro cita o nome da variável). pytest `asyncio_mode="auto"`; ruff `py312`, regras `E,F,I,B,UP,ASYNC`; mypy `strict`. Dependências: só a lista fechada.

## Testes
- `test_health_returns_ok`: GET `/api/health` → 200 `{"status":"ok"}`.
- `test_settings_defaults`: limites e backend padrão.
- `test_settings_missing_database_url_raises`: erro com o nome da variável.

## Comandos de verificação
```bash
docker compose --profile test build hub-test
docker compose run --rm hub-test pytest tests/unit -v
docker compose run --rm hub-test sh -c "ruff check . && ruff format --check . && mypy"
```

## Critérios de aceite
- [x] Testes falham antes e passam depois
- [x] ruff e mypy limpos
- [x] Nada instalado no host

## Notas de execução
O serviço `hub` do Compose só sobe a partir da Tarefa 02 (precisa de `DATABASE_URL`); aqui só a imagem `runtime` foi construída. Dockerfile ganha `COPY alembic` na Tarefa 05.
