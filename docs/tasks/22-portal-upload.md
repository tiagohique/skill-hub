# Tarefa 22 — Portal: tela de upload redesenhada

**Fase:** facelift · **Depende de:** 20, 19 · **Commit:** `feat(portal): redesigned upload screen`

## Objetivo
Upload no card centralizado do protótipo, com dados reais e a ajuda de versão da Tarefa 19.

## Arquivos
Alterar `portal/src/pages/UploadPage.tsx`.

## Interfaces (consome / produz)
Consome `uploadSkill`, `explainVersion`/`SEMVER` (`src/version.ts`).

## Regras e valores da spec
Breadcrumb; card `max-w-2xl`; dropzone com altura mínima 160 px (arrastar = borda indigo sólida e fundo indigo; com arquivo = nome, KB e "Trocar arquivo"); campo "Versão (SemVer)" com helper abaixo; alerta de erro/sucesso no topo do card; botão "Fazer Upload" com spinner durante o envio, desabilitado sem arquivo ou com versão inválida. Erros reais da API (409, 413, 422) no banner; sucesso: "Skill enviada com sucesso! Entrando no canal draft." e volta à lista em ~2 s. Sem mocks.

## Testes
`version.test.ts` segue verde. Verificação visual no navegador sem enviar skills.

## Comandos de verificação
```bash
docker compose run --rm --no-deps portal npm test
docker compose run --rm --no-deps portal npm run build
```

## Critérios de aceite
- [ ] Estados do dropzone fiéis ao protótipo
- [ ] `1.0.0.` mostra "Usar 1.0.0"

## Notas de execução
—
