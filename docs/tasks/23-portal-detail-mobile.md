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
- [x] Detalhe fiel ao estilo do resto
- [x] Nada de rolagem horizontal em 375 px
- [x] Portal acessível pelo IP da rede local

## Notas de execução
Detalhe redesenhado (breadcrumb, card de cabeçalho com domínio/responsável/stable/beta, versões em tabela `md+` e cards no celular, painel da versão com "Promover para …" indigo e "Depreciar" contorno vermelho, hash do pacote e arquivos com SHA-256 mono e botão de copiar). `CopyHash` fica fora do componente da página (senão remontava a cada render). Comportamento e chamadas à API iguais aos anteriores. Verificado em `fastapi-endpoint` (somente leitura): em 375 px não há rolagem horizontal, as tabelas somem e entram os cards, os hashes quebram linha. Acesso pela rede: `http://192.168.3.218:5173/` e `/api/skills` respondem 200 a partir do Mac (IP em `en1`; o IP pode mudar com o Wi-Fi; o teste no aparelho é do usuário). Nenhuma skill foi criada, promovida, depreciada ou apagada durante a verificação. Hub: 185 testes seguem verdes.
