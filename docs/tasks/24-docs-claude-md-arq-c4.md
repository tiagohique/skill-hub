# Tarefa 24 — Atualizar CLAUDE.md e arq.c4

**Fase:** facelift · **Depende de:** 20 a 23 · **Commit:** `docs: update CLAUDE.md and architecture for the portal facelift`

## Objetivo
Documentar o que de fato mudou: stack do portal, telas, estrutura de pastas, definição de pronto e a arquitetura do front.

## Arquivos
Alterar `CLAUDE.md`, `docs/arq.c4`, `docs/README.md`, `docs/tasks/README.md`.

## Interfaces (consome / produz)
Produz o `arq.c4` válido com os componentes do portal: Layout e navegação, Lista de skills, Envio de skill, Detalhe da skill e Cliente da API (que fala só com a `FastAPI`).

## Regras e valores da spec
Só o que mudou. CLAUDE.md: tabela Stack (Tailwind + lucide-react aprovados em 2026-10-25), seção Portal, estrutura de pastas, "Como trabalhar" (testes do portal), definição de pronto. `arq.c4`: tecnologia e descrição do Portal, componentes e relações, ator dev (computador ou celular na rede local), view `portal`, nota de exposição na rede local (POC sem login).

## Testes
`likec4 validate` em contêiner.

## Comandos de verificação
```bash
docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .
```

## Critérios de aceite
- [ ] `arq.c4` válido
- [ ] CLAUDE.md coerente com o código

## Notas de execução
—
