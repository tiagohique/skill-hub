# Tarefa 26 — API de autenticação e status na lista

**Fase:** login · **Depende de:** 25 · **Commit:** `feat(hub): auth routes, protected API and skill status`

## Objetivo
Expor login/logout/me/tema, exigir login nas rotas de skills, usar o username como ator e devolver `status` na lista.

## Arquivos
Criar `api/auth.py`; alterar `api/routes.py`, `api/errors.py`, `api/schemas.py`, `main.py`, `config.py` se preciso, `service/skill_service.py`, `repositories/catalog.py`, testes de API.

## Interfaces (consome / produz)
Veja a spec `../superpowers/specs/2026-10-25-login-theme-status-design.md`.

## Regras e valores da spec
401 `unauthorized`; cookie HttpOnly SameSite=Lax; /mcp e /api/health abertos.

## Testes
Rotas sem cookie → 401; com login funcionam; ator na auditoria; MCP continua aberto.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
```

## Critérios de aceite
- [x] Testes e verificação da tarefa passam

## Notas de execução
`api/auth.py` (login, logout, me, theme; cookie `hub_session` HttpOnly SameSite=Lax), `CurrentUser` em todas as rotas de skills, ator = username, `status` geral na lista (`_overall_status`; `latest_statuses` com `DISTINCT ON`). `/api/health` e `/mcp` seguem abertos. Testes de API existentes passaram a logar como admin (fixture `client`; `anon` é o cliente sem login).
