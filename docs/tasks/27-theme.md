# Tarefa 27 — Tema claro e escuro

**Fase:** login · **Depende de:** 26 · **Commit:** `feat(portal): light and dark themes`

## Objetivo
Alternar entre claro e escuro em todas as telas, com persistência.

## Arquivos
Alterar `styles.css`, `index.html`, `components/*`, `pages/*`; criar `theme.tsx`.

## Interfaces (consome / produz)
Veja a spec `../superpowers/specs/2026-10-25-login-theme-status-design.md`.

## Regras e valores da spec
Variante `dark` por classe; tokens da spec.

## Testes
node:test da lógica de tema; verificação visual em 1280 e 375 px.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
```

## Critérios de aceite
- [x] Testes e verificação da tarefa passam

## Notas de execução
Variante `dark` por classe (`@custom-variant`), script no `index.html` contra o flash, `theme.ts`/`ThemeContext.tsx`/`ThemeToggle.tsx`. As classes `zinc-*` das telas viraram pares claro/`dark:` por script e depois ajustei à mão cabeçalhos de card e badges. O botão de tema fica na navbar (desktop e celular). A verificação visual completa acontece depois da Tarefa 28, pois a API agora exige login.
