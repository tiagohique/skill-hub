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
- [x] Testes falham antes e passam depois
- [x] Tabela e cards fiéis ao protótipo; busca e filtro funcionam

## Notas de execução
Teste vermelho primeiro (`Cannot find module src/skills.ts`), depois verde: 13 testes do portal no total. Verificado no navegador com dados reais: busca "API" → `fastapi-endpoint`; filtro Geral → 2 skills; "zzz" → "Nenhuma skill encontrada."; em 375 px a tabela some, aparecem os cards, não há rolagem horizontal, o menu hambúrguer tem itens de 48 px e fecha com Esc. Ajuste de escolha minha: o select de domínio ficou com `sm:w-56` (o `w-48` do protótipo cortava "Todos os domínios"). Linha da tabela e card inteiro levam ao detalhe.
