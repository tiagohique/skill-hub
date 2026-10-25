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
- [x] Estados do dropzone fiéis ao protótipo
- [x] `1.0.0.` mostra "Usar 1.0.0"

## Notas de execução
Verificado no navegador sem enviar nada: dropzone com estados (arrastando = borda indigo sólida e fundo indigo; formato inválido = banner "Formato inválido. Use apenas .zip ou .md."; arquivo escolhido = nome, KB e "Trocar arquivo"); `1.0.0.` mostra "Remova o ponto final…" com "Usar 1.0.0", e o clique corrige e habilita o botão; sem rolagem horizontal em 375 px. Escolhas minhas: helper em zinc-400 (como na spec; o protótipo usava zinc-500), dropzone acessível por teclado (`role="button"`, Enter/Espaço), `min-h-40` (160 px), botão e mensagem do motivo na mesma linha no desktop. O botão com spinner e o envio real não foram acionados para não criar skills no hub; o usuário testa pela tela.
