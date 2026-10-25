# Tarefa 08 — SkillService: upload e consultas

**Fase:** 3 · **Depende de:** 04, 06, 07 · **Commit:** `feat(service): SkillService upload and queries`

## Objetivo
Regra de negócio de upload (draft, imutabilidade, auditoria) e consultas de catálogo.

## Arquivos
`hub/src/hub/service/skill_service.py`; dataclasses em `hub/src/hub/domain/models.py`; `hub/tests/integration/test_skill_service_upload.py`.

## Interfaces (consome / produz)
Consome `parse_upload`, `UploadLimits`, `BlobStore`, repositórios. Produz `SkillService(sessions, blobs, limits)` com `upload(*, filename, data, version, actor) -> VersionDetail`, `list_skills() -> list[SkillSummary]`, `get_skill(name) -> SkillDetail`, `get_version(name, version) -> VersionDetail`; modelos `SkillSummary`, `VersionSummary`, `SkillDetail` (versões por `created_at` desc), `VersionDetail`.

## Regras e valores da spec
Fluxo: `parse_upload` → `put` de cada arquivo (fora da transação) → uma transação com `get_or_create_skill` (domain = `metadata.domain` ou `geral`; owner = `metadata.owner` ou ator), `insert_version` como `draft`, `insert_files`, `audit upload`. Versão repetida → 409 sem sobrescrever.

## Testes
Upload `.md` (draft, 1 arquivo, `bundle_sha256` correto); upload `.zip` com 2 arquivos; repetição → `VersionConflictError` e conteúdo intacto; **dois uploads simultâneos via `asyncio.gather`: um sucesso e um conflito**; audit `upload`; `list_skills` com `stable=None, beta=None`; `get_skill("nope")` → `NotFoundError`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_skill_service_upload.py -v
```

## Critérios de aceite
- [ ] Review Focus 3 coberto
- [ ] Serviço não executa SQL direto

## Notas de execução
—
