# Tarefa 18 — Arquitetura como código e definição de pronto

**Fase:** 6 · **Depende de:** todas · **Commit:** `docs: update architecture model and close POC checklist`

## Objetivo
Garantir que `docs/arq.c4` reflita o código e fechar a "Definição de pronto" do CLAUDE.md com evidências.

## Arquivos
`docs/arq.c4` (somente se algo divergiu: tools de fallback no `Servidor MCP`, `repositories` como componente), `docs/tasks/README.md`.

## Interfaces (consome / produz)
Produz o modelo C4 validado e a tabela de evidências por item de pronto.

## Regras e valores da spec
Mudou componente, camada ou relação → `arq.c4` no mesmo commit. Nomes seguem o modelo: `FastAPI`, `Servidor MCP`, `SkillService`, `BlobStore`, `PostgresBlobStore`.

## Testes
Suíte completa + validação do modelo.

## Comandos de verificação
```bash
docker run --rm -v "$PWD/docs:/docs" -w /docs node:22-alpine npx -y likec4 validate .
docker compose run --rm hub-test sh -c "pytest -v && ruff check . && mypy"
docker compose run --rm portal npm run build
```

## Critérios de aceite
- [ ] `docker compose up --build` sobe os três serviços sem passos manuais
- [ ] Upload `.md` e `.zip` com validação e erros claros
- [ ] Versão repetida → 409; nada sobrescrito
- [ ] Promoção `draft→beta→stable` com auditoria
- [ ] Claude Code lê uma skill `stable` em `/mcp`
- [ ] Hash conferido; adulteração gera erro de integridade
- [ ] App não faz `UPDATE` em `blobs` nem `DELETE` (teste de integração)
- [ ] Contrato do `BlobStore` passa
- [ ] Duas skills de exemplo publicadas e consumidas
- [ ] `arq.c4` atualizado e válido

## Notas de execução
—
