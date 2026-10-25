#!/usr/bin/env bash
# Executado pela imagem postgres na primeira inicialização do volume.
# Cria o usuário da aplicação (permissões mínimas) e o banco de testes.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE ROLE "$APP_DB_USER" LOGIN PASSWORD '$APP_DB_PASSWORD' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE skillshub_test OWNER "$POSTGRES_USER";
REVOKE ALL ON DATABASE "$POSTGRES_DB" FROM PUBLIC;
REVOKE ALL ON DATABASE skillshub_test FROM PUBLIC;
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$APP_DB_USER";
GRANT CONNECT ON DATABASE skillshub_test TO "$APP_DB_USER";
SQL

for db in "$POSTGRES_DB" skillshub_test; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" \
    -c "REVOKE CREATE ON SCHEMA public FROM PUBLIC;"
done
