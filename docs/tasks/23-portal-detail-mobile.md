# Tarefa 23 — Portal: detalhe redesenhado e verificação no celular

**Fase:** facelift · **Depende de:** 20, 21 · **Commit:** `feat(portal): redesigned skill detail and mobile checks`

## Objetivo
Levar a tela de detalhe para a mesma identidade e conferir todo o portal em 375 px e 1280 px.

## Arquivos
Alterar `portal/src/pages/SkillDetailPage.tsx`. Remover CSS antigo que sobrar.

## Interfaces (consome / produz)
Consome `getSkill`, `getVersion`, `promote`, `deprecate`, `Badge`. Comportamento e chamadas à API iguais aos atuais.

## Regras e valores da spec
Breadcrumb; card com nome, descrição e chips (domínio, responsável, canais); versões em tabela (`md+`) e cards (celular); painel da versão com "Promover para beta|stable" (indigo) e "Depreciar" (contorno red-500, `confirm()`); hash do pacote e arquivos com SHA-256 em fonte mono, copiar ao clicar, quebra de linha no celular.

## Testes
Verificação visual e funcional no navegador, sem criar, promover ou apagar nada.

## Comandos de verificação
```bash
docker compose run --rm --no-deps portal npm test
docker compose run --rm --no-deps portal npm run build
curl -s http://<IP do Mac>:5173/api/skills
```

## Critérios de aceite
- [ ] Detalhe fiel ao estilo do resto
- [ ] Nada de rolagem horizontal em 375 px
- [ ] Portal acessível pelo IP da rede local

## Notas de execução
—
