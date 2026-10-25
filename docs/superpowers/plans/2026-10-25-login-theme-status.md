# Login, tema e filtro de status — plano

Spec: `../specs/2026-10-25-login-theme-status-design.md`. Seis tarefas, um commit cada, tudo em Docker. Detalhes em `../../tasks/25..30`.

| Tarefa | Entrega |
|---|---|
| 25 | Migração 0002 (`users`, `auth_sessions`, seed), `UserRepository`, `AuthService` (scrypt, sessões) e testes |
| 26 | Rotas `/api/auth/*`, dependência `CurrentUser`, proteção das rotas, actor real, `status` na lista |
| 27 | Tema claro/escuro (`dark:` em todas as telas, persistência local e no banco) |
| 28 | `LoginPage`, `AuthContext`, navbar com Sair |
| 29 | Filtro de status e coluna Status (TDD) |
| 30 | `CLAUDE.md`, `arq.c4`, READMEs |

Verificação global: `docker compose run --rm hub-test pytest -q`, `ruff`, `mypy`, `portal npm test` e `build`, `likec4 validate`.
