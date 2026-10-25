# Tarefa 14 — Portal: tela Detalhe

**Fase:** 5 · **Depende de:** 13 · **Commit:** `feat(portal): skill detail with promote and deprecate`

## Objetivo
Mostrar versões, status e arquivos com hash, e permitir promover e depreciar.

## Arquivos
`portal/src/pages/SkillDetailPage.tsx`.

## Interfaces (consome / produz)
Consome `getSkill`, `getVersion`, `promote`, `deprecate`.

## Regras e valores da spec
Cabeçalho com nome, descrição, domínio e canais; tabela de versões (versão, status como etiqueta, autor, data `pt-BR`); arquivos com caminho, tamanho e SHA-256 (fonte mono, cópia com clique). Botões: `draft` → "Promover para beta"; `beta` → "Promover para stable" e "Depreciar"; `stable` → "Depreciar"; demais: nenhum. Depreciar pede `confirm()`. Erro 409 mostra `message`; recarrega após a ação.

## Testes
Build + checagem manual: promover `draft→beta→stable`, depreciar, conferir a lista.

## Comandos de verificação
```bash
docker compose run --rm portal npm run build
```

## Critérios de aceite
- [ ] Botões corretos por status
- [ ] Transição inválida exibe a mensagem do hub

## Notas de execução
—
