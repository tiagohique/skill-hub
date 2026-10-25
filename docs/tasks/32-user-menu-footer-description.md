# Tarefa 32 — Menu do usuário, rodapé e descrição das skills

**Fase:** login · **Depende de:** 31 · **Commit:** `feat: user menu, footer links and skill description column`

## Objetivo
Seguir o protótipo HTML aprovado: ícone de usuário com "Sair" em menu, links de API e MCP no rodapé e coluna Descrição na lista.

## Arquivos
Hub: `domain/models.py`, `api/schemas.py`, `repositories/catalog.py` (`latest_descriptions`), `service/skill_service.py`, `tests/integration/test_api.py`. Portal: `types.ts`, `components/Layout.tsx`, `pages/SkillsPage.tsx`, `tests/skills.test.ts`. Docs: `CLAUDE.md`, `docs/arq.c4`.

## Regras e valores da spec
- `GET /api/skills` devolve `description` (frontmatter da versão mais recente; vazio se não houver).
- Navbar: ícone `User` em círculo com o username embaixo; "Sair" só aparece com hover, foco ou clique; fecha com clique fora e Esc.
- API (Swagger) e MCP saem da navbar e vão para o rodapé (centralizados, nova aba). Menu mobile mantém só Skills, Enviar skill e Sair.
- Tabela: coluna Descrição após Beta (truncada em 200 px, `title` com o texto); cards: `line-clamp-2`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
docker compose run --rm --no-deps portal npm run build
```

## Critérios de aceite
- [x] Lista e API trazem a descrição
- [x] Sair só aparece ao passar o mouse ou clicar no ícone
- [x] Links no rodapé; sem rolagem horizontal em 375 px
