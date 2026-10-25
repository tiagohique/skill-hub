# Tarefa 03 — Domínio: erros, ciclo de vida, semver e hash

**Fase:** 1 · **Depende de:** 01 · **Commit:** `feat(domain): lifecycle, errors, semver and hashing`

## Objetivo
Camada `domain/` pura (sem I/O) com erros, transições, semver e hashes.

## Arquivos
`hub/src/hub/domain/{errors,models,hashing,semver}.py`; testes `hub/tests/unit/{test_lifecycle,test_hashing,test_semver}.py`.

## Interfaces (consome / produz)
- `HubError(code: ClassVar[str])` e subclasses: `SkillValidationError`(`invalid_skill`), `LimitExceededError`(`limit_exceeded`), `VersionConflictError`(`version_exists`), `InvalidTransitionError`(`invalid_transition`), `NotFoundError`(`not_found`), `IntegrityError`(`integrity_error`).
- `Status(StrEnum)`: draft, beta, stable, deprecated, retired. `Channel(StrEnum)`: beta, stable.
- `ALLOWED_TRANSITIONS`, `check_transition(current, target) -> None`, `channel_for(status) -> Channel | None`.
- `SkillFile(path, data)`, `FileEntry(path, sha256, size)`, `sha256_hex(data) -> str`, `bundle_sha256(entries) -> str`, `is_semver(value) -> bool`.

## Regras e valores da spec
Transições permitidas: `draft→beta`, `beta→stable`, `beta→deprecated`, `stable→deprecated`, `deprecated→retired`. Mensagem: `Transição de {current} para {target} não é permitida.` `bundle_sha256` = sha256 de linhas `path\0sha256` ordenadas por path, unidas por `\n`. Semver 2.0.0 completo.

## Testes
- `test_allowed_transitions_pass` (5 pares) e `test_forbidden_transitions_raise` (todos os demais pares, incluindo `x→x` e `retired→*`).
- `test_bundle_sha256_sorted_by_path`: independe da ordem de entrada e iguala o cálculo manual.
- `test_semver`: válidos `1.0.0`, `0.1.0-beta.1`, `1.2.3+build.5`; inválidos `1.0`, `01.0.0`, `v1.0.0`, `1.0.0.0`, `""`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/unit -v
docker compose run --rm hub-test sh -c "ruff check . && mypy"
```

## Critérios de aceite
- [ ] `domain/` não importa nenhuma outra camada
- [ ] Testes, ruff e mypy verdes

## Notas de execução
—
