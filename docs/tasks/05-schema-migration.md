# Tarefa 05 — Esquema, migração e grants

**Fase:** 2 · **Depende de:** 02 · **Commit:** `feat(db): schema, migration and least-privilege grants`

## Objetivo
Criar o esquema por Alembic (usuário dono) e impor a imutabilidade pelos grants do usuário da aplicação.

## Arquivos
`hub/alembic.ini`, `hub/alembic/env.py` (async, `MIGRATION_DATABASE_URL`), `hub/alembic/versions/0001_initial.py`, `hub/src/hub/repositories/tables.py`; `hub/tests/conftest.py` (fixtures `migrated` e `clean_db`); `hub/tests/integration/test_permissions.py`.

## Interfaces (consome / produz)
Produz `metadata: MetaData` e as `Table`s `skills, skill_versions, skill_version_files, channels, blobs, audit_events` com as colunas da spec.

## Regras e valores da spec
CHECK em `status` (5 valores) e `channel` (`beta`,`stable`); `channels.version_id` nulável; `UNIQUE(skill_id, version)`; FK `skill_version_files.sha256 → blobs`. Grants a `APP_DB_USER` (default `hub_app`): `USAGE` no schema; `SELECT, INSERT` em `blobs`, `skill_version_files`, `audit_events`, `skills`; `skill_versions` `SELECT, INSERT, UPDATE (status)`; `channels` `SELECT, INSERT, UPDATE (version_id)`. Nunca `DELETE`/`TRUNCATE`. `downgrade` remove tudo.

## Testes
Como `hub_app`, esperando `InsufficientPrivilegeError`: `test_app_cannot_update_blobs`, `test_app_cannot_delete_from_any_table` (6 tabelas), `test_app_cannot_update_version_frontmatter`, `test_app_cannot_update_files`, `test_app_cannot_update_audit`. Positivos: `test_app_can_update_version_status`, `test_app_can_update_channel_version`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_permissions.py -v
docker compose run --rm hub-test alembic upgrade head
```

## Critérios de aceite
- [ ] UPDATE em `blobs` e DELETE em qualquer tabela falham para o app (item da definição de pronto)
- [ ] Migração sobe e desce limpa

## Notas de execução
—
