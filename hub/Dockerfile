FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Imagem de desenvolvimento: dependências de dev, instalação editável.
# O código vem de ./hub montado em /app (docker-compose.yml).
FROM base AS dev
COPY pyproject.toml ./
COPY src ./src
RUN pip install -e '.[dev]'
CMD ["pytest"]

# Imagem de execução: só dependências de runtime, usuário não root.
FROM base AS runtime
COPY pyproject.toml alembic.ini ./
COPY src ./src
COPY alembic ./alembic
RUN pip install . && useradd --create-home --uid 10001 hub
USER hub
EXPOSE 8000
CMD ["uvicorn", "hub.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
