# Tarefa 07 — Repositórios do catálogo e da auditoria

**Fase:** 2 · **Depende de:** 03, 05 · **Commit:** `feat(repositories): catalog and audit repositories`

## Objetivo
Única camada que fala SQL. Recebem uma `AsyncSession` já em transação e nunca fazem commit.

## Arquivos
`hub/src/hub/repositories/{catalog,audit}.py`; `hub/tests/integration/test_repositories.py`.

## Interfaces (consome / produz)
- `CatalogRepository(session)`: `get_or_create_skill(name, domain, owner) -> UUID`, `find_skill`, `list_skills`, `insert_version(skill_id, version, frontmatter, bundle_sha256, created_by) -> UUID`, `insert_files(version_id, entries)`, `find_version`, `list_versions`, `list_files`, `set_status(version_id, status)`, `set_channel(skill_id, channel, version_id | None)` (upsert), `clear_channels_pointing_to(version_id)`, `channels_of(skill_id) -> dict[Channel, str]`.
- `AuditRepository(session).record(actor, action, skill, version | None)`.
- `SkillRow`, `VersionRow` (dataclasses frozen).

## Regras e valores da spec
Violação de `UNIQUE(skill_id, version)` vira `VersionConflictError`. `channels_of` ignora canais sem versão. Testes usam o engine do usuário restrito (`app_engine`).

## Testes
Criar e reler skill/versão/arquivos; versão repetida → `VersionConflictError`; `set_channel` duas vezes atualiza; `clear_channels_pointing_to` zera só o canal certo; `channels_of` ignora nulos; `record` grava `at` automático.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_repositories.py -v
```

## Critérios de aceite
- [x] Funciona com o usuário de permissões mínimas
- [x] Nenhum commit dentro dos repositórios

## Notas de execução
Acrescentado `CatalogRepository.list_channels() -> dict[UUID, dict[Channel, str]]` (evita N+1 na listagem de skills da Tarefa 08). `insert_version` usa savepoint (`begin_nested`) para a sessão continuar utilizável após o conflito.
