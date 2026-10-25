# Tarefa 00 — Documentação em `docs/`

**Fase:** 0 · **Depende de:** — · **Commit:** `docs: POC spec, plan and per-task specifications`

## Objetivo
Versionar dentro de `docs/` a spec consolidada, o plano e a especificação de cada tarefa, antes de qualquer código.

## Arquivos
`docs/README.md`, `docs/superpowers/specs/2026-10-24-skills-hub-poc-design.md`, `docs/superpowers/plans/2026-10-24-skills-hub-poc.md`, `docs/tasks/README.md`, `docs/tasks/00..18-*.md`, `git init` na raiz.

## Interfaces (consome / produz)
Produz a documentação que as demais tarefas leem antes de começar.

## Regras e valores da spec
Cada tarefa segue as seções fixas: Objetivo, Arquivos, Interfaces, Regras e valores, Testes, Comandos de verificação, Critérios de aceite, Notas de execução. Ao concluir uma tarefa, atualizar o status em `tasks/README.md` e as Notas de execução, no mesmo commit.

## Testes
Não há código. Verificação por contagem de arquivos.

## Comandos de verificação
```bash
ls docs/tasks | wc -l   # 20 (README + 19 tarefas)
```

## Critérios de aceite
- [ ] Repositório git inicializado
- [ ] 19 arquivos de tarefa + README em `docs/tasks`
- [ ] Spec consolidada e plano em `docs/superpowers`

## Notas de execução
—
