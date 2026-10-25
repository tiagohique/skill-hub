# Tarefa 11 — Spike: extensão de Skills (SEP-2640) no pacote `mcp`

**Fase:** 4 · **Depende de:** 01 · **Commit:** `docs: MCP skills extension findings`

## Objetivo
Primeira tarefa do MCP exigida pelo CLAUDE.md: descobrir se o pacote `mcp` instalado já traz `skills/list` e `skills/get` e, se não, como registrá-los manualmente. Não produz código de produção.

## Arquivos
`docs/decisions/mcp-skills-extension.md` (pt-BR). Script descartável `scripts/_spike_mcp.py`, apagado antes do commit.

## Interfaces (consome / produz)
Produz a decisão que a Tarefa 12 segue: versão do `mcp`, existência da extensão, formato exato de request/response, capability anunciada, mecanismo de registro.

## Regras e valores da spec
Não usar FastMCP. Referência: PR `python-sdk#3485` (publicação não confirmada). Sem sincronização para `~/.claude/skills`.

## Testes
Não há. Evidência = saída dos comandos registrada no documento.

## Comandos de verificação
```bash
docker compose run --rm hub-test pip show mcp
docker compose run --rm hub-test sh -c 'grep -rniE "skills/(list|get)|SEP-2640|skill://" $(python -c "import mcp,os;print(os.path.dirname(mcp.__file__))")'
```

## Critérios de aceite
- [x] Documento com versão, achados e caminho escolhido
- [x] Se não houver forma suportada de registrar os métodos sem alterar o SDK: **parar e perguntar ao usuário** antes da Tarefa 12

## Notas de execução
Resultado completo em `docs/decisions/mcp-skills-extension.md`. A extensão não existe no `mcp` 2.3.0, mas o registro manual funciona via `Server.add_request_handler`, então não houve parada. `pyproject.toml` agora fixa `mcp>=2.3,<3`.
