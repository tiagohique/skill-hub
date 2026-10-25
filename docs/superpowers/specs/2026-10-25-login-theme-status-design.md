# Login, tema claro/escuro e filtro de status — especificação

Data: 2026-10-25 · Plano: `../plans/2026-10-25-login-theme-status.md` · Tarefas 25 a 30.

## Intenção
Proteger o portal com login (usuário `admin`, senha `admin`, guardados no banco), permitir tema claro e escuro e filtrar a lista de skills por status. Visual e tokens: spec de UI/UX e protótipo aprovados em 2026-10-25.

## Decisões do usuário
- Campo **Usuário** (texto), não e-mail.
- A **API REST exige login**; o **MCP continua aberto** (o Claude Code lê sem credencial).
- O **tema fica no banco**, por usuário.
- Senha com `hashlib.scrypt` da biblioteca padrão (nenhuma dependência nova).

## Escolhas do assistente (registradas para revisão)
- Sessão por cookie `HttpOnly`, `SameSite=Lax`, token aleatório de 32 bytes; só o SHA-256 do token vai ao banco. Validade de 7 dias.
- O banco proíbe `DELETE`: logout grava `revoked_at`; sessão expirada é ignorada por `expires_at`.
- `audit_events.actor` e `created_by` guardam o username (texto, sem FK), então o histórico antigo (`portal`) continua válido.
- **Status da skill na lista:** `stable` se há canal stable; senão `beta` se há canal beta; senão o status da versão mais recente (`draft`, `deprecated` ou `retired`). O filtro é no cliente.
- Seed `admin/admin` criado pela migração `0002`. É só de POC e está documentado como tal.
- Tema inicial: preferência salva no navegador; senão preferência do sistema; senão dark. Ao entrar, vale o tema do banco.

## Banco
`users(id uuid pk, username unique, password_hash, theme 'light'|'dark', created_at)` e `auth_sessions(token_sha256 pk, user_id fk, created_at, expires_at, revoked_at)`.
Grants de `hub_app`: `users` SELECT, INSERT e UPDATE(theme); `auth_sessions` SELECT, INSERT e UPDATE(revoked_at). Nenhum DELETE.

## API
`POST /api/auth/login` `{username,password}` → cookie + usuário; `POST /api/auth/logout`; `GET /api/auth/me`; `PUT /api/auth/theme` `{theme}`. Erros: 401 `unauthorized` (credencial inválida ou sem sessão). Todas as rotas de skills exigem login; `/api/health` e `/api/auth/login` não.
`GET /api/skills` passa a devolver `status`.

## Portal
- Tema: classe `dark` no `<html>`, script no `index.html` evita o flash. Claro: `#fafafa` fundo, `#fff` superfícies, `#e4e4e7` bordas, `#18181b` texto, `#71717a` secundário. Dark: `#09090b`, `#18181b`, `#27272a`, `#fafafa`, `#a1a1aa`.
- Badges: stable verde, beta amarelo, deprecated vermelho (fundo 950/texto 400/borda 800 no dark), draft e geral cinza.
- Login: card centralizado, ícone `Box`, inputs com `User` e `Lock`, botão largura total, rodapé "Acesso restrito a desenvolvedores autorizados.", botão Sol/Lua flutuante no canto superior direito.
- Navbar: Skills, Enviar skill, botão de tema, "Sair" (hover vermelho).
- Lista: busca + filtro de domínio + filtro de status (Todos, Stable, Beta, Deprecated), empilhados no celular; coluna Status.

## Fora do escopo
Troca de senha, cadastro de usuários, papéis, login no MCP, bloqueio por tentativas.
