# Tarefa 25 — Banco e AuthService

**Fase:** login · **Depende de:** 24 · **Commit:** `feat(hub): users table, sessions and AuthService`

## Objetivo
Criar as tabelas `users` e `auth_sessions`, o seed admin, o repositório e o AuthService.

## Arquivos
Criar `hub/alembic/versions/0002_auth.py`, `repositories/users.py`, `service/auth_service.py`, `domain`; alterar `repositories/tables.py`, `tests/conftest.py`.

## Interfaces (consome / produz)
Veja a spec `../superpowers/specs/2026-10-25-login-theme-status-design.md`.

## Regras e valores da spec
scrypt com salt aleatório; token de sessão de 32 bytes, só o SHA-256 no banco; 7 dias; sem DELETE.

## Testes
Unit de hash/verificação; integração de login, logout, expiração e grants (hub_app sem DELETE em users e auth_sessions).

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
```

## Critérios de aceite
- [ ] Testes e verificação da tarefa passam

## Notas de execução
(a preencher)
