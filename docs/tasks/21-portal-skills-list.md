# Tarefa 21 — Portal: lista de skills com busca e filtro

**Fase:** facelift · **Depende de:** 20 · **Commit:** `feat(portal): redesigned skills list with search and domain filter`

## Objetivo
Lista moderna (tabela no desktop, cards no celular) com busca por nome e filtro por domínio.

## Arquivos
Criar `portal/src/skills.ts`, `portal/tests/skills.test.ts`. Alterar `portal/src/pages/SkillsPage.tsx`.

## Interfaces (consome / produz)
`domainsOf(skills: SkillSummary[]): string[]` (únicos, ordenados); `filterSkills(skills, search: string, domain: string): SkillSummary[]` (`"todos"` não filtra; busca sem diferenciar maiúsculas e ignorando espaços nas pontas).

## Regras e valores da spec
Cabeçalho "Skills" + subtítulo + botão "Enviar Skill"; busca "Buscar skills..."; select "Todos os domínios" + domínios reais; tabela `md+` (ícone `Terminal`, badges, `-` cinza), cards abaixo de `md`; linha/card leva ao detalhe. Estados: carregando, erro, vazio ("Nenhuma skill publicada ainda."), sem resultado ("Nenhuma skill encontrada.").

## Testes
`domainsOf`: únicos e ordenados, vazio → `[]`. `filterSkills`: por nome (parcial, maiúsculas), por domínio, combinados, `todos`, sem resultado, busca só com espaços.

## Comandos de verificação
```bash
docker compose run --rm --no-deps portal npm test
docker compose run --rm --no-deps portal npm run build
```

## Critérios de aceite
- [ ] Testes falham antes e passam depois
- [ ] Tabela e cards fiéis ao protótipo; busca e filtro funcionam

## Notas de execução
—
