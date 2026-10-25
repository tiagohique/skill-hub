#!/bin/sh
# Aplica as migrações (usuário dono do esquema) e só então sobe o hub.
set -eu
alembic upgrade head
exec uvicorn hub.main:create_app --factory --host 0.0.0.0 --port 8000
