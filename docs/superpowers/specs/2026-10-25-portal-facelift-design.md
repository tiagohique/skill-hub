# Facelift do portal: novo visual dark, responsivo e acessível no celular

## Intenção

O portal funcionava, mas era cru (tabela HTML e CSS à mão). A spec de UI/UX e o protótipo React/Tailwind trazidos pelo usuário definem a nova identidade: dark nativo, minimalista, com busca e filtro na lista e uso confortável no celular. A API REST, o hub e o MCP não mudam.

## Decisões do usuário (2026-10-25)

- Pode adicionar `tailwindcss` (+ `@tailwindcss/vite`) e `lucide-react`, as bibliotecas do protótipo. Shadcn/Radix não entram.
- A tela de Detalhe, que não existe no protótipo, é redesenhada no mesmo estilo.
- O resultado precisa ser **fiel ao protótipo** e responsivo.

## Objetivos, não objetivos

Objetivos: reproduzir o protótipo (navbar, lista, upload) com dados reais; busca e filtro por domínio; detalhe no mesmo estilo; tabela→cards e menu hambúrguer no celular; manter `explainVersion`.
Não objetivos: login, tema claro, busca no servidor, mudanças no hub/API/MCP.
Anti-objetivo: mocks do protótipo (skills fixas, 409 simulado) chegarem à aplicação.

## Fidelidade por construção

O marcado e as classes Tailwind do protótipo são copiados como estão; só os dados fixos são trocados pelos reais.

## Escolhas do construtor (minhas, fora do protótipo)

| Escolha | Motivo |
|---|---|
| Rotas por hash com `<a href>` em vez de estado interno | Links diretos e botão Voltar; o detalhe precisa de URL |
| Fonte `system-ui` (sem Inter da web) | Sem download de fonte; a spec aceita `system-ui` |
| Keyframes próprios para `animate-in/fade-in/slide-in` | Essas classes são do plugin `tailwindcss-animate`, que não está no Tailwind puro; evita uma 3ª dependência |
| Opções do filtro de domínio vindas dos dados reais | O protótipo tem lista fixa; a real muda com o catálogo |
| Linha/card inteiro leva ao detalhe | No protótipo as linhas não navegam |
| Badges `deprecated`/`retired` em vermelho escuro | A spec só define stable, beta e draft |
| Menu mobile `fixed` e alvos de toque ≥ 44 px, fecha com Esc | Acessibilidade no celular |
| Sucesso do upload mostra banner e volta à lista em ~2 s | Igual ao protótipo |
| `confirm()` do navegador mantido para Depreciar | Comportamento atual preservado |
| Botão de upload só habilita com arquivo e versão **válida** | Mantém `explainVersion` (mensagem + "Usar 1.0.0") |

## Celular

O Compose publica a porta 5173 e o Vite escuta em `0.0.0.0`; o portal faz proxy de `/api`. No aparelho, na mesma rede Wi-Fi, abra `http://<IP do Mac>:5173`. **A POC não tem login: quem estiver na mesma rede poderá ver e enviar skills.**

## Critérios de aceite

- Visual idêntico ao protótipo em 1280 px e em 375 px (capturas de tela).
- Tabela no desktop, cards abaixo de `md`; hambúrguer abaixo de `md`.
- Busca e filtro funcionam e têm testes (`node:test`).
- Upload mostra erros reais da API e o spinner; `1.0.0.` continua mostrando "Usar 1.0.0".
- Detalhe com promover/depreciar funcionando como antes.
- Build, testes do portal e do hub verdes; `likec4 validate` válido; CLAUDE.md e `arq.c4` atualizados.
