# Tarefa 28 — Tela de login no portal

**Fase:** login · **Depende de:** 27 · **Commit:** `feat(portal): login screen and session handling`

## Objetivo
Criar login, contexto de sessão, redirecionamento e botão Sair.

## Arquivos
Criar `pages/LoginPage.tsx`, `auth.tsx`; alterar `App.tsx`, `api.ts`, `types.ts`, `Layout.tsx`.

## Interfaces (consome / produz)
Veja a spec `../superpowers/specs/2026-10-25-login-theme-status-design.md`.

## Regras e valores da spec
Rodapé de acesso restrito; botão de tema flutuante; 401 volta ao login.

## Testes
Verificação no navegador.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest -q
docker compose run --rm --no-deps portal npm test
```

## Critérios de aceite
- [ ] Testes e verificação da tarefa passam

## Notas de execução
(a preencher)
