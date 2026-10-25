# Tarefa 29 — Filtro de status

**Fase:** login · **Depende de:** 26 · **Commit:** `feat(portal): status filter and status column`

## Objetivo
Filtrar a lista por Stable, Beta e Deprecated.

## Arquivos
Alterar `skills.ts`, `tests/skills.test.ts`, `pages/SkillsPage.tsx`, `types.ts`.

## Interfaces (consome / produz)
Veja a spec `../superpowers/specs/2026-10-25-login-theme-status-design.md`.

## Regras e valores da spec
Filtros empilham no celular; coluna Status.

## Testes
TDD em `skills.test.ts`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
```

## Critérios de aceite
- [x] Testes e verificação da tarefa passam

## Notas de execução
`filterSkills(skills, search, domain, status = "todos")` (testes escritos antes: 16 passando), segundo `select` (Todos os status, Stable, Beta, Deprecated) ao lado do domínio, empilhados abaixo de `sm`, coluna Status na tabela e badge de status nos cards. Verificado no navegador: filtro por deprecated lista só as skills deprecated; sem rolagem horizontal em 375 px.
