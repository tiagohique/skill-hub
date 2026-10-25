# Tarefa 15 — Portal: tela Upload

**Fase:** 5 · **Depende de:** 13 · **Commit:** `feat(portal): upload screen`

## Objetivo
Enviar `.md` ou `.zip` por arrastar e soltar, com versão semver.

## Arquivos
`portal/src/pages/UploadPage.tsx`.

## Interfaces (consome / produz)
Consome `uploadSkill`.

## Regras e valores da spec
Aceita `.md` e `.zip` (arrastar, soltar ou clicar). Campo versão com validação semver no cliente (mesma regra da Tarefa 03) e dica "ex.: 1.0.0". "Enviar" desabilitado sem arquivo e versão válida. Sucesso navega ao detalhe; erro mostra `message` (409, 413, 422).

## Testes
Build + checagem manual: upload ok, repetido (409), zip inválido (422).

## Comandos de verificação
```bash
docker compose run --rm portal npm run build
```

## Critérios de aceite
- [ ] Mensagens claras em pt-BR para cada erro
- [ ] Nada enviado com versão inválida

## Notas de execução
—
