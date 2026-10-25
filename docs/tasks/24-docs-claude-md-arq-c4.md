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
- [x] `arq.c4` válido
- [x] CLAUDE.md coerente com o código

## Notas de execução
`CLAUDE.md`: Stack (Tailwind + lucide-react), seção Portal reescrita (telas, responsivo, acesso pelo celular e aviso de que a POC não tem login), estrutura de pastas (`components`, `pages`, `tests`, `scripts`, `entrypoint.sh`), "Como trabalhar" (tudo em contêiner e comandos de teste), definição de pronto (itens do portal; os itens da POC, já verificados na Tarefa 18, foram marcados). Aproveitei para corrigir o que tinha ficado desatualizado desde as tarefas anteriores: resultado da verificação do `mcp` 2.3.0, canal beta e ator da auditoria no MCP, rota `/api/health`, `retired` só no serviço, `MIGRATION_DATABASE_URL` e demais variáveis, grant de `channels`, e o esclarecimento de que "busca de texto" fora do escopo é no conteúdo das skills (a lista filtra por nome e domínio). `arq.c4`: o `Portal` ganhou 5 componentes (Layout e navegação, Lista de skills, Envio de skill, Detalhe da skill, Cliente da API), todos saindo do hub só pelo `Cliente da API` → `FastAPI`; nova view `portal` ("Telas do portal"); a view dinâmica de upload passa pelo `Envio de skill`; ator `dev` e descrição do portal citam celular, rede local e ausência de login. `likec4 validate` → válido.
