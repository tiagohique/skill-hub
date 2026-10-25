# Tarefas

Status: `pendente` · `em andamento` · `concluída`. Atualize no mesmo commit da tarefa.

| Nº | Tarefa | Fase | Depende de | Status |
|---|---|---|---|---|
| 00 | [Documentação em docs/](00-docs.md) | 0 | — | concluída |
| 01 | [Esqueleto do hub em contêiner](01-hub-skeleton.md) | 0 | 00 | concluída |
| 02 | [PostgreSQL com papéis separados](02-postgres-roles.md) | 0 | 01 | concluída |
| 03 | [Domínio: erros, ciclo de vida, semver, hash](03-domain.md) | 1 | 01 | concluída |
| 04 | [Validação de upload](04-upload-validation.md) | 1 | 03 | concluída |
| 05 | [Esquema, migração e grants](05-schema-migration.md) | 2 | 02 | concluída |
| 06 | [BlobStore e testes de contrato](06-blobstore.md) | 2 | 03, 05 | concluída |
| 07 | [Repositórios](07-repositories.md) | 2 | 03, 05 | concluída |
| 08 | [SkillService: upload e consultas](08-service-upload.md) | 3 | 04, 06, 07 | concluída |
| 09 | [SkillService: governança e entrega](09-service-lifecycle.md) | 3 | 08 | concluída |
| 10 | [API REST](10-rest-api.md) | 4 | 09 | concluída |
| 11 | [Spike: extensão de Skills no MCP](11-mcp-spike.md) | 4 | 01 | concluída |
| 12 | [Servidor MCP](12-mcp-server.md) | 4 | 09, 11 | concluída |
| 13 | [Portal: esqueleto e tela Skills](13-portal-skills.md) | 5 | 10 | concluída |
| 14 | [Portal: tela Detalhe](14-portal-detail.md) | 5 | 13 | concluída |
| 15 | [Portal: tela Upload](15-portal-upload.md) | 5 | 13 | concluída |
| 16 | [Compose final](16-compose-final.md) | 6 | 10, 13 | concluída |
| 17 | [Exemplos, demo e Claude Code](17-examples-demo.md) | 6 | 12, 16 | concluída |
| 18 | [arq.c4 e definição de pronto](18-architecture-and-dod.md) | 6 | todas | concluída |
| 19 | [Upload: feedback claro para versão inválida](19-upload-version-feedback.md) | correção | 15 | concluída |
| 20 | [Portal: fundação Tailwind, layout e badges](20-portal-foundation.md) | facelift | 19 | concluída |
| 21 | [Portal: lista com busca e filtro](21-portal-skills-list.md) | facelift | 20 | concluída |
| 22 | [Portal: upload redesenhado](22-portal-upload.md) | facelift | 20, 19 | concluída |
| 23 | [Portal: detalhe e verificação no celular](23-portal-detail-mobile.md) | facelift | 20, 21 | concluída |
| 24 | [CLAUDE.md e arq.c4](24-docs-claude-md-arq-c4.md) | facelift | 20 a 23 | concluída |
| 25 | [Banco e AuthService](25-auth-database.md) | login |
| 26 | [API de autenticação e status](26-auth-api.md) | login | 25 | concluída |
| 27 | [Tema claro e escuro](27-theme.md) | login | 26 | concluída |
| 28 | [Tela de login](28-login-screen.md) | login | 27 | pendente |
| 29 | [Filtro de status](29-status-filter.md) | login | 26 | pendente |
| 30 | [CLAUDE.md e arq.c4](30-docs-login-theme.md) | login | 25 a 29 | pendente |
