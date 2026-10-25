# Tarefa 02 — PostgreSQL com papéis separados

**Fase:** 0 · **Depende de:** 01 · **Commit:** `chore: postgres service with owner and app roles`

## Objetivo
Subir o `postgres` no Compose com dois papéis (dono do esquema e usuário mínimo da aplicação) e bancos de dev e de teste.

## Arquivos
`docker-compose.yml` (serviço `postgres`; `hub` e `hub-test` com `depends_on` saudável), `db/init/01-app-role.sh`, `.env.example` (e `.env` local, ignorado pelo git), `hub/tests/conftest.py`, `hub/tests/integration/test_db_roles.py`.

## Interfaces (consome / produz)
Produz papéis `hub_owner` (= `POSTGRES_USER`) e `hub_app` (`LOGIN`, sem `CREATEDB`); bancos `skillshub` e `skillshub_test`; fixtures `owner_engine` e `app_engine` (session-scoped `AsyncEngine`) lendo `TEST_MIGRATION_DATABASE_URL` / `TEST_DATABASE_URL` (host `postgres`, definidos no serviço `hub-test`).

## Regras e valores da spec
`postgres:17`, volume nomeado `pgdata`, healthcheck `pg_isready` (5s, 10 tentativas). `REVOKE ALL ON DATABASE FROM PUBLIC`, `GRANT CONNECT` ao app, `REVOKE CREATE ON SCHEMA public FROM PUBLIC`. Script com `set -euo pipefail` e `ON_ERROR_STOP=1`. Só valores de dev no `.env.example`.

## Testes
- `test_app_role_can_connect`: `SELECT current_user` = `hub_app`.
- `test_app_role_cannot_create_table`: `InsufficientPrivilegeError`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_db_roles.py -v
```

## Critérios de aceite
- [x] Postgres sobe `healthy` sozinho
- [x] App não cria tabelas
- [x] `.env` fora do git

## Notas de execução
Fixtures `owner_engine`/`app_engine` ficaram com escopo de função (engines asyncpg presos ao loop de cada teste). O script `db/init/01-app-role.sh` precisa de `chmod +x` (sem isso a imagem falha com `bad interpreter`).
