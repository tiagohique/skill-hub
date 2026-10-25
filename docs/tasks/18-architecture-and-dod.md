# Tarefa 18 — Arquitetura como código e definição de pronto

**Fase:** 6 · **Depende de:** todas · **Commit:** `docs: update architecture model and close POC checklist`

## Objetivo
Garantir que `docs/arq.c4` reflita o código e fechar a "Definição de pronto" do CLAUDE.md com evidências.

## Arquivos
`docs/arq.c4` (somente se algo divergiu: tools de fallback no `Servidor MCP`, `repositories` como componente), `docs/tasks/README.md`.

## Interfaces (consome / produz)
Produz o modelo C4 validado e a tabela de evidências por item de pronto.

## Regras e valores da spec
Mudou componente, camada ou relação → `arq.c4` no mesmo commit. Nomes seguem o modelo: `FastAPI`, `Servidor MCP`, `SkillService`, `BlobStore`, `PostgresBlobStore`.

## Testes
Suíte completa + validação do modelo.

## Comandos de verificação
```bash
docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .
docker compose run --rm hub-test sh -c "pytest -v && ruff check . && mypy"
docker compose run --rm portal npm run build
```

## Critérios de aceite
- [x] `docker compose up --build` sobe os três serviços sem passos manuais
- [x] Upload `.md` e `.zip` com validação e erros claros
- [x] Versão repetida → 409; nada sobrescrito
- [x] Promoção `draft→beta→stable` com auditoria
- [x] Claude Code lê uma skill `stable` em `/mcp`
- [x] Hash conferido; adulteração gera erro de integridade
- [x] App não faz `UPDATE` em `blobs` nem `DELETE` (teste de integração)
- [x] Contrato do `BlobStore` passa
- [x] Duas skills de exemplo publicadas e consumidas
- [x] `arq.c4` atualizado e válido

## Notas de execução
`arq.c4` ganhou o componente `Repositories` (única camada com SQL) entre `SkillService` e o catálogo, as views dinâmicas de upload e leitura passam por ele, e a descrição do `Servidor MCP` cita o registro manual da SEP-2640 e as tools de fallback. `npx likec4 validate` (em contêiner `node:22-alpine`) → válido.

### Evidências da definição de pronto (verificadas em `docker compose down -v && docker compose up --build -d`)

| Item | Evidência |
|---|---|
| `docker compose up --build` sobe os três serviços sem passos manuais | `docker compose ps`: `postgres` e `hub` healthy, `portal` up; log do hub mostra a migração antes do uvicorn |
| Upload `.md` e `.zip` com validação e erros claros | `tests/unit/test_validation.py`, `tests/integration/test_api.py`; portal verificado no navegador |
| Versão repetida → 409; nada sobrescrito | `test_repeated_version_conflicts_and_keeps_original`, `test_repeated_version_is_409`, concorrência em `test_concurrent_identical_uploads_one_wins` |
| Promoção `draft→beta→stable` com auditoria | `test_skill_service_lifecycle.py`; botões do portal verificados no navegador |
| Claude Code conecta em `/mcp` e lê uma skill `stable` | `tests/integration/test_mcp.py` (cliente oficial por HTTP), `verify_mcp.py`; `initialize` por `localhost:8000/mcp` = 200. Registro no Claude Code: passo manual do usuário |
| Hash conferido ao ler; adulteração gera erro | `test_blob_tamper.py`, `test_tampered_blob_returns_error_not_content`; `verify_mcp.py` com blob adulterado sai com código 1 |
| App não faz `UPDATE` em `blobs` nem `DELETE` | `tests/integration/test_permissions.py`; `psql` como `hub_app`: `permission denied for table blobs` e `skills` |
| Contrato do `BlobStore` passa | `tests/contract/test_blob_store.py` (memória e Postgres) |
| Duas skills de exemplo publicadas e consumidas | `examples/skills/*`, `demo.py`, `verify_mcp.py`, `test_end_to_end.py` |
| `arq.c4` atualizado e válido | `likec4 validate` → ✓ Valid |

Suíte final: 185 testes passando, ruff e mypy limpos, `npm run build` do portal sem erros de tipo.
