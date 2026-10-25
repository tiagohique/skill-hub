# Tarefa 19 — Upload: feedback claro para versão inválida

**Fase:** correção · **Depende de:** 15 · **Commit:** `fix(portal): explain invalid version and suggest a fix`

## Objetivo
Evitar que uma versão como `1.0.0.` bloqueie o envio sem explicação. Spec: `docs/superpowers/specs/2026-10-25-upload-version-feedback-design.md`.

## Arquivos
Criar `portal/src/version.ts`, `portal/tests/version.test.ts`. Alterar `portal/src/pages/UploadPage.tsx`, `portal/src/styles.css`, `portal/package.json` (script `test`).

## Interfaces (consome / produz)
Produz `SEMVER: RegExp` e `explainVersion(value: string): { valid: true } | { valid: false; message: string; suggestion?: string }`. `UploadPage` consome as duas.

## Regras e valores da spec
Semver estrito, igual ao hub (expressão oficial). Mensagens em pt-BR. `suggestion` só quando o texto corrigido é semver válido. Sem correção silenciosa e sem dependência nova (`node:test` embutido; testes fora do `include` do `tsconfig`).

## Testes
`1.0.0.` → inválida, mensagem com "ponto final", sugestão `1.0.0`; `v1.0.0` e `1.0` → sugestão `1.0.0`; `1.0.0`, `0.1.0-beta.1`, `1.2.3+b.5` → válidas; `01.0.0`, `1.0.0.0`, `""` → inválidas sem sugestão.

## Comandos de verificação
```bash
docker compose run --rm portal npm test
docker compose run --rm portal npm run build
docker compose run --rm hub-test pytest -q
```

## Critérios de aceite
- [x] Testes falham antes e passam depois
- [x] Build sem erro de tipo
- [x] No navegador: `1.0.0.` → mensagem + "Usar 1.0.0" → "Enviar" habilitado
- [x] Upload de `331-small-team-delegation-system.md` funciona

## Notas de execução
Teste vermelho primeiro (`Cannot find module src/version.ts`), depois verde: 5 testes `node:test`. O script é `node --test "tests/**/*.test.ts"` (no Node 22 o argumento de pasta não funciona; precisa de glob). Verificado no navegador: `1.0.0.` mostra "Remova o ponto final: a versão não termina com ponto." e "Usar 1.0.0"; o clique corrige o campo e habilita "Enviar"; o envio do conteúdo completo de `331-small-team-delegation-system.md` criou a skill `small-team-delegation-system@1.0.0` (draft) no hub, que ficou lá. Hub sem alterações; 185 testes do hub seguem verdes.
