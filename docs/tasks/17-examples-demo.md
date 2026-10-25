# Tarefa 17 — Skills de exemplo, demo e consumo pelo Claude Code

**Fase:** 6 · **Depende de:** 12, 16 · **Commit:** `feat: example skills, demo and MCP verification script`

## Objetivo
Duas skills reais (HTML e back-end) publicadas e consumidas, e prova de hash conferido de ponta a ponta.

## Arquivos
`examples/skills/html-landing-page/{SKILL.md,templates/base.html}`, `examples/skills/fastapi-endpoint/{SKILL.md,reference/checklist.md}`, `scripts/demo.py`, `scripts/verify_mcp.py`, `hub/tests/integration/test_end_to_end.py`; `docker-compose.yml` (`hub-test` monta `./examples:/examples:ro`).

## Interfaces (consome / produz)
`demo.py [api_url]` (padrão `http://hub:8000/api`): zipa cada pasta de `/examples/skills`, envia `1.0.0`, promove `beta` e `stable`, imprime a lista; 409 só avisa. `verify_mcp.py [url]` (padrão `http://hub:8000/mcp`): lista, lê cada arquivo, recalcula SHA-256, compara com digest e `bundle_sha256`; sai ≠ 0 em divergência.

## Regras e valores da spec
Skills em pt-BR com frontmatter válido (`name`, `description`, `metadata.version`). Skill HTML enviada como `.zip`.

## Testes
`test_end_to_end`: upload das duas → `beta` → `stable` → via cliente MCP ambas listadas e conteúdos batem com os digests → audits `upload`, `promote`×2 e `mcp_read` presentes.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/integration/test_end_to_end.py -v
docker compose run --rm hub-test python /scripts/demo.py
docker compose run --rm hub-test python /scripts/verify_mcp.py
claude mcp add --transport http skills-hub http://localhost:8000/mcp
```

## Critérios de aceite
- [ ] Hash conferido em todos os arquivos
- [ ] Blob adulterado no banco → `verify_mcp.py` reporta integridade e sai ≠ 0
- [ ] Claude Code lê `fastapi-endpoint` pelo MCP

## Notas de execução
—
