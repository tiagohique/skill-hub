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
- [x] Testes e verificação da tarefa passam

## Notas de execução
`LoginPage` (card, ícones User/Lock, rodapé de acesso restrito, botão de tema no canto), `auth.tsx` (`AuthProvider`: `me()` ao abrir, login, logout, tema guardado no banco), `api.ts` com `setUnauthorizedHandler` (401 volta ao login). Sem sessão a tela de login aparece em qualquer rota (não há rota `#/login` separada; a URL pedida é mantida e abre depois do login). Navbar com nome do usuário e Sair (hover vermelho), também no menu do celular. `scripts/demo.py` e `verify_mcp.py` agora fazem login na API REST (admin/admin). Verificado no navegador: senha errada mostra erro, admin/admin entra, tema claro persiste ao recarregar.
