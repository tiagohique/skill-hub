# Tarefa 09 — SkillService: governança e entrega

**Fase:** 3 · **Depende de:** 08 · **Commit:** `feat(service): promotion, deprecation and delivery`

## Objetivo
Promoção, depreciação, aposentadoria e entrega de skills publicadas (consumida pelo MCP).

## Arquivos
`hub/src/hub/service/skill_service.py` (extensão), `hub/src/hub/domain/models.py` (`PublishedSkill`), `hub/tests/integration/test_skill_service_lifecycle.py`.

## Interfaces (consome / produz)
`promote(name, version, to: Status, actor)`, `deprecate(name, version, actor)`, `retire(name, version, actor)`, `list_published(channel=STABLE) -> list[PublishedSkill]`, `get_published(name, channel=STABLE, actor="anonymous")` (audit `mcp_get`), `read_file(name, path, channel, actor) -> bytes` (via `BlobStore.get`; audit `mcp_read`). `PublishedSkill(name, description, version, bundle_sha256, files)`.

## Regras e valores da spec
Cada transição em **uma transação**: `check_transition`, `set_status`, canal (`channel_for`), `clear_channels_pointing_to` em deprecate/retire, `audit` (`promote`/`deprecate`/`retire`). `promote` só aceita `BETA`/`STABLE`. `retire` existe só no serviço (sem rota REST). MCP serve `stable` por padrão; `beta` só explícito.

## Testes
`draft→beta→stable` atualiza status e canais e grava 2 audits; `draft→stable` → `InvalidTransitionError` sem audit nem mudança de canal; nova `stable` substitui o canal; **depreciar a `stable` tira a skill de `list_published` e `get_published` → `NotFoundError`**; `deprecated→retired` ok e `draft→retired` erro; `read_file` com blob adulterado → `IntegrityError`; path inexistente → `NotFoundError`; `channel=BETA` serve a beta; audits `mcp_get`/`mcp_read` com o ator; falha no meio da transação não altera status (monkeypatch no audit).

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_skill_service_lifecycle.py -v
```

## Critérios de aceite
- [ ] Review Focus 5 coberto
- [ ] Atomicidade provada por teste

## Notas de execução
—
