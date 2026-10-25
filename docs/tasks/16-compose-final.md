# Tarefa 16 — Compose final: subida única, migração automática, healthchecks

**Fase:** 6 · **Depende de:** 10, 13 · **Commit:** `chore: single-command compose with auto-migration`

## Objetivo
`docker compose up --build` sobe os três serviços sem passos manuais.

## Arquivos
`hub/entrypoint.sh` (`alembic upgrade head` com `MIGRATION_DATABASE_URL`, depois `exec uvicorn hub.main:app --host 0.0.0.0 --port 8000`), `hub/Dockerfile` (alvo `runtime`), `docker-compose.yml`.

## Interfaces (consome / produz)
Produz healthcheck do `hub` em `/api/health`; `portal` depende de `hub` saudável; `hub` depende de `postgres` saudável.

## Regras e valores da spec
Volume `pgdata`; hub aplica migração ao iniciar; portas 5173, 8000, 5432. Nenhum segredo no repositório.

## Testes
Verificação operacional (sem pytest).

## Comandos de verificação
```bash
docker compose down -v && docker compose up --build -d
docker compose ps
docker compose run --rm hub-test python -c "import httpx; print(httpx.get('http://hub:8000/api/health').json())"
docker compose logs hub
```

## Critérios de aceite
- [ ] Três serviços de pé sem intervenção
- [ ] Log do hub mostra migração antes do uvicorn
- [ ] Portal carrega a lista via proxy

## Notas de execução
—
