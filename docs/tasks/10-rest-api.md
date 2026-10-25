# Tarefa 10 — API REST

**Fase:** 4 · **Depende de:** 09 · **Commit:** `feat(api): REST routes for the portal`

## Objetivo
Adaptador fino REST em `/api` para o portal. Sem regra de negócio.

## Arquivos
`hub/src/hub/api/{routes,errors,schemas}.py`; `hub/src/hub/main.py` (engine e sessionmaker no lifespan, `SkillService` em `app.state.service`, handlers); `hub/tests/integration/test_api.py`.

## Interfaces (consome / produz)
Consome `SkillService`. Produz as rotas da seção 10 da spec consolidada. Upload `multipart` com `file` e `version` → 201 com `VersionDetail`. Promote recebe `{"to": "beta"|"stable"}` (`Literal`). Ator fixo `portal`.

## Regras e valores da spec
Erros sempre `{"code","message"}`; mapa: `invalid_skill` 422, `invalid_request` 422, `limit_exceeded` 413, `version_exists` 409, `invalid_transition` 409, `not_found` 404, `integrity_error` 500. Leitura do upload limitada a `max_bundle_bytes + 1` (estouro → 413). Datas em ISO 8601.

## Testes
Upload `.md` → 201 `draft`; repetido → 409 `version_exists`; zip com `../` → 422 `invalid_skill`; arquivo grande → 413; lista de skills com canais; detalhe; versão com arquivos e hashes; promote inválido → 409; `{"to":"retired"}` → 422 `invalid_request`; deprecate; skill inexistente → 404; toda resposta de erro tem exatamente `code` e `message`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_api.py -v
```

## Critérios de aceite
- [ ] `api/` não importa `repositories/` nem `store/`
- [ ] Testes verdes; ruff e mypy limpos

## Notas de execução
—
