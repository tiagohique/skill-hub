# Upload: feedback claro para versão inválida

## Problema

Na tela de upload do portal, o botão "Enviar" ficou desabilitado ao enviar `331-small-team-delegation-system.md` com a versão `1.0.0.`. O campo ficou vermelho, mas a única explicação era a dica genérica "Use o formato maior.menor.patch, por exemplo 1.0.0.", e o usuário não entendeu o que estava errado.

## Causa raiz (investigada)

- A versão digitada era `1.0.0.` (ponto no fim). O regex semver do portal rejeita (`"1.0.0."` → inválida, `"1.0.0"` → válida).
- O arquivo é válido: frontmatter com `name: small-team-delegation-system` e `description`. A validação a seco do hub (`parse_upload`) devolveu OK. O hub não tem defeito.
- O ponto veio, provavelmente, da própria dica, que termina com "por exemplo 1.0.0." e foi copiada junto com a pontuação da frase.
- Falha de UX: (1) exemplo misturado com a pontuação da frase; (2) mensagem única para qualquer erro; (3) botão desabilitado sem motivo visível.

## Decisão

Semver continua **estrito**, igual ao hub. O portal não aceita versão inválida nem a corrige em silêncio. Ele **explica o erro** e **oferece a correção com um clique**.

## Comportamento

`explainVersion(value)` (função pura em `portal/src/version.ts`) devolve `{valid: true}` ou `{valid: false, message, suggestion?}`:

| Entrada | Mensagem | Sugestão |
|---|---|---|
| termina com `.` | Remova o ponto final | sem o ponto |
| começa com `v`/`V` | Remova o "v" do começo | sem o `v` |
| `maior.menor` (ex.: `1.0`) | Faltou o número do patch | `1.0.0` |
| vazio, zeros à esquerda, partes não numéricas | Mensagem genérica com o formato | nenhuma |

A sugestão só existe se o texto corrigido passar no semver. A tela mostra a mensagem abaixo do campo, o botão "Usar <sugestão>", o exemplo em `<code>` separado de pontuação e, perto do botão desabilitado, o motivo.

## Critérios de aceite

- `1.0.0.` mostra "Remova o ponto final" e "Usar 1.0.0"; clicar habilita "Enviar".
- O envio de `331-small-team-delegation-system.md` com `1.0.0` cria a skill.
- Testes de `explainVersion` passam (sem dependência nova: `node:test`).
- Hub sem alterações; testes do hub seguem verdes.
