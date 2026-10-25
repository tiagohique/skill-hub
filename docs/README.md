# Documentação do Skills Hub (POC v3)

| Documento | Conteúdo |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Regras do projeto (fonte primária) |
| [`arq.c4`](arq.c4) | Arquitetura como código (LikeC4) |
| [`superpowers/specs/2026-10-24-skills-hub-poc-design.md`](superpowers/specs/2026-10-24-skills-hub-poc-design.md) | Especificação consolidada e decisões |
| [`superpowers/plans/2026-10-24-skills-hub-poc.md`](superpowers/plans/2026-10-24-skills-hub-poc.md) | Plano de implementação em fases |
| [`tasks/README.md`](tasks/README.md) | Índice, dependências e status das tarefas |
| `tasks/NN-*.md` | Especificação de cada tarefa |
| [`superpowers/specs/2026-10-25-portal-facelift-design.md`](superpowers/specs/2026-10-25-portal-facelift-design.md) | Spec do novo visual do portal |
| `decisions/` | Registros de decisão (ex.: extensão de Skills no MCP) |

**Tudo roda no Docker.** Subir: `docker compose up --build`. Testes: `docker compose run --rm hub-test pytest -v`.
