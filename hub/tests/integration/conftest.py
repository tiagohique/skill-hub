import asyncio
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
import uvicorn

from hub.config import Settings
from hub.main import create_app
from tests.mcp_support import Hub


@pytest.fixture(autouse=True)
def _clean(clean_db: None) -> None:
    """Todo teste de integração começa com o esquema migrado e as tabelas vazias."""


@pytest_asyncio.fixture
async def hub(clean_db: None) -> AsyncIterator[Hub]:
    settings = Settings(
        database_url=os.environ["TEST_DATABASE_URL"],
        migration_database_url=os.environ["TEST_MIGRATION_DATABASE_URL"],
        blob_backend="postgres",
        max_file_bytes=1024 * 1024,
        max_bundle_bytes=5 * 1024 * 1024,
        max_files=100,
    )
    app = create_app(settings)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    task = asyncio.create_task(server.serve())
    while not server.started:  # noqa: ASYNC110 - uvicorn não expõe um Event de partida
        await asyncio.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield Hub(f"http://127.0.0.1:{port}/mcp", app.state.service)
    server.should_exit = True
    await task
