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
| 11 | [Spike: extensão de Skills no MCP](11-mcp-spike.md) | 4 | 01 | pendente |
| 12 | [Servidor MCP](12-mcp-server.md) | 4 | 09, 11 | pendente |
| 13 | [Portal: esqueleto e tela Skills](13-portal-skills.md) | 5 | 10 | pendente |
| 14 | [Portal: tela Detalhe](14-portal-detail.md) | 5 | 13 | pendente |
| 15 | [Portal: tela Upload](15-portal-upload.md) | 5 | 13 | pendente |
| 16 | [Compose final](16-compose-final.md) | 6 | 10, 13 | pendente |
| 17 | [Exemplos, demo e Claude Code](17-examples-demo.md) | 6 | 12, 16 | pendente |
| 18 | [arq.c4 e definição de pronto](18-architecture-and-dod.md) | 6 | todas | pendente |
