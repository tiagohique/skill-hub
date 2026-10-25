# Tarefa 06 — BlobStore, PostgresBlobStore e testes de contrato

**Fase:** 2 · **Depende de:** 03, 05 · **Commit:** `feat(store): BlobStore protocol, PostgresBlobStore and contract tests`

## Objetivo
Ponto de troca de armazenamento com endereçamento por conteúdo e verificação de hash na leitura.

## Arquivos
`hub/src/hub/store/{blob_store,postgres_blob_store,factory}.py`, `hub/tests/fakes.py` (`InMemoryBlobStore`), `hub/tests/contract/test_blob_store.py`, `hub/tests/integration/test_blob_tamper.py`.

## Interfaces (consome / produz)
Consome `sha256_hex`, `IntegrityError`, `NotFoundError`, tabela `blobs`. Produz `BlobStore(Protocol)` (`put`, `get`, `exists`, exatamente como no CLAUDE.md), `PostgresBlobStore(sessions: async_sessionmaker[AsyncSession])`, `make_blob_store(settings, sessions) -> BlobStore`.

## Regras e valores da spec
`put` usa `INSERT ... ON CONFLICT (sha256) DO NOTHING` em transação própria. `get` recalcula o hash: inexistente → `NotFoundError`; divergente → `IntegrityError`. `BLOB_BACKEND` desconhecido → `ValueError("BLOB_BACKEND não suportado: ...")`. S3/Azure: não implementar.

## Testes
Contrato parametrizado em `[InMemoryBlobStore, PostgresBlobStore]` (implementações futuras entram na lista): `test_put_returns_sha256_hex` (`abc` → `ba7816bf…15ad`), `test_put_is_idempotent`, `test_get_roundtrip`, `test_exists_true_false`, `test_get_unknown_raises_not_found`, `test_put_empty_bytes`. Integração: `test_tampered_blob_raises_integrity_error` (UPDATE como dono, depois `get`).

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/contract tests/integration/test_blob_tamper.py -v
```

## Critérios de aceite
- [x] Contrato passa nas duas implementações
- [x] Adulteração gera `IntegrityError`

## Notas de execução
A fixture `migrated` roda o Alembic numa thread separada (o `env.py` usa `asyncio.run`, que falha se já houver loop). `tests/` virou pacote (`tests/__init__.py`) para importar `tests.fakes`. Extras: teste unitário da factory (backend desconhecido) e `test_postgres_put_does_not_duplicate`.
